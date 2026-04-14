"""
PgVectorRetriever — RAG 管道的检索层

职责：给定一个查询字符串，从 pgvector 中找出最相关的 chunk 列表。
不关心这些 chunk 之后如何使用，只负责检索。

对照 Java：相当于 @Repository，只是 "查" 这一件事。
"""

import logging
import os
from typing import Any

from sqlalchemy import create_engine, text

from backend.etl.transformers import TextTransformer

logger = logging.getLogger(__name__)


def _build_db_url() -> str:
    return (
        f"postgresql+psycopg2://"
        f"{os.getenv('POSTGRES_USER', 'postgres')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'knowledge_base')}"
    )


class PgVectorRetriever:
    """
    从 pgvector 检索与查询语义最接近的文档 chunk。

    设计要点：
    - 必须用和写入时完全相同的 embedding 实例（TextTransformer）
      否则两批向量来自不同空间，余弦距离没有意义
    - top_k 默认 3：实践中 3-5 个 chunk 能覆盖大多数问题所需上下文
    - score 是余弦"距离"（0 = 完全相同，2 = 完全相反），数值越小越相关
    """

    def __init__(
        self,
        kb_name: str,
        top_k: int = 3,
        db_url: str | None = None,
    ):
        self.kb_name = kb_name
        self.top_k = top_k
        self.transformer = TextTransformer()
        self.engine = create_engine(db_url or _build_db_url())

    def retrieve(self, query: str) -> list[dict[str, Any]]:
        """
        检索与 query 最相关的 top_k 个 chunk。

        Args:
            query: 用户查询字符串

        Returns:
            chunk 列表，每项包含 text / score / source / metadata
            按相关性从高到低排列（score 从小到大）
        """
        # 使用与写入时完全相同的 embedding 实例生成查询向量
        q_vec = self.transformer.embed_query(query)
        vec_str = "[" + ",".join(f"{x:.6f}" for x in q_vec) + "]"

        logger.debug(f"[Retriever] 查询: {query!r}，知识库: {self.kb_name}，top_k={self.top_k}")

        with self.engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT
                        dc.chunk_text,
                        dc.metadata_,
                        dc.chunk_index,
                        ROUND((dc.embedding <=> :vec)::numeric, 4) AS score,
                        d.title  AS doc_title,
                        d.source_type
                    FROM   document_chunks dc
                    JOIN   documents d ON d.id = dc.document_id
                    JOIN   knowledge_bases kb ON kb.id = d.kb_id
                    WHERE  kb.name = :kb_name
                    ORDER  BY dc.embedding <=> :vec
                    LIMIT  :top_k
                """),
                {"vec": vec_str, "kb_name": self.kb_name, "top_k": self.top_k},
            ).fetchall()

        results = [
            {
                "text": row.chunk_text,
                "score": float(row.score),       # 余弦距离，越小越相关
                "source": row.doc_title,
                "source_type": row.source_type,
                "chunk_index": row.chunk_index,
                "metadata": dict(row.metadata_) if row.metadata_ else {},
            }
            for row in rows
        ]

        logger.debug(f"[Retriever] 命中 {len(results)} 个 chunk")
        return results

    def retrieve_with_score_filter(
        self, query: str, max_score: float = 0.5
    ) -> list[dict[str, Any]]:
        """
        带相关性过滤的检索：丢弃余弦距离超过阈值的 chunk。

        用于生产场景：当没有任何相关文档时，宁可返回空列表，
        也不要用低质量内容误导 LLM 生成错误答案。
        """
        chunks = self.retrieve(query)
        filtered = [c for c in chunks if c["score"] <= max_score]
        if len(filtered) < len(chunks):
            logger.info(
                f"[Retriever] 过滤后: {len(filtered)}/{len(chunks)} 个 chunk"
                f"（阈值 score <= {max_score}）"
            )
        return filtered
