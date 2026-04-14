"""
PgvectorLoader — ETL 管道的 Load 层

职责：把 TextTransformer 的输出（chunks + embeddings）持久化到 PostgreSQL。
不关心数据从哪里来，只负责写入。
"""

import logging
import os
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from backend.models import Base, Document, DocumentChunk, KnowledgeBase

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


class PgvectorLoader:
    """
    把 ETL 输出的 chunks 写入 PostgreSQL + pgvector。

    对照 Java 的 Repository 层（JPA Repository.saveAll()），
    这里用 SQLAlchemy Session 做批量写入。
    """

    def __init__(self, db_url: str | None = None):
        self.engine = create_engine(db_url or _build_db_url())
        # 确保扩展和表已存在（开发便利，生产用 Alembic 管理）
        self._ensure_extension()

    def _ensure_extension(self) -> None:
        with self.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()

    def load(
        self,
        chunks: list[dict[str, Any]],
        source_file: str,
        kb_name: str = "default",
    ) -> int:
        """
        将 chunks 写入数据库。

        Args:
            chunks:      TextTransformer.transform() 的输出
            source_file: 原始文件路径（用于 Document.metadata）
            kb_name:     写入哪个知识库（不存在则自动创建）

        Returns:
            写入的 chunk 数量
        """
        if not chunks:
            logger.warning("没有 chunk 可写入")
            return 0

        with Session(self.engine) as session:
            # 1. 获取或创建知识库
            kb = session.query(KnowledgeBase).filter_by(name=kb_name).first()
            if not kb:
                kb = KnowledgeBase(name=kb_name, description="Auto-created by ETL pipeline")
                session.add(kb)
                session.flush()  # 拿到 id，类似 JPA 的 save() 后 getId()
                logger.info(f"创建知识库: {kb_name} (id={kb.id})")

            # 2. 创建 Document 记录（一个文件对应一个 Document）
            full_text = "\n".join(c["text"] for c in chunks)
            source_type = self._detect_type(source_file)
            doc = Document(
                kb_id=kb.id,
                title=os.path.basename(source_file),
                source_type=source_type,
                content=full_text,
                metadata_={"file_path": source_file},
            )
            session.add(doc)
            session.flush()
            logger.info(f"创建文档: {doc.title} (id={doc.id}), {len(chunks)} 个 chunk")

            # 3. 批量写入 DocumentChunk（含 embedding 向量）
            db_chunks = []
            for chunk in chunks:
                meta = chunk.get("metadata", {})
                db_chunks.append(DocumentChunk(
                    document_id=doc.id,
                    chunk_index=meta.get("chunk_index", 0),
                    chunk_text=chunk["text"],
                    token_count=meta.get("chunk_size"),
                    metadata_=meta,
                    embedding=chunk.get("embedding"),
                ))

            session.add_all(db_chunks)
            session.commit()

        logger.info(f"Load 完成，共写入 {len(db_chunks)} 个 chunk")
        return len(db_chunks)

    @staticmethod
    def _detect_type(file_path: str) -> str:
        suffix = os.path.splitext(file_path)[1].lower()
        return {"pdf": "pdf", ".md": "md", ".txt": "txt"}.get(suffix, "unknown")
