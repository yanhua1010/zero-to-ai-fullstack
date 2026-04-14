"""
ETL Pipeline — 完整三层管道

Extract  → DocumentExtractor（读文件，统一格式）
Transform → TextTransformer（分块 + 向量化）
Load      → PgvectorLoader（写入 PostgreSQL + pgvector）
"""

import logging
import time
from typing import Any

from .extractors import get_extractor
from .transformers import TextTransformer
from .loaders import PgvectorLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ETLPipeline:
    def __init__(self, kb_name: str = "default"):
        self.transformer = TextTransformer()
        self.loader = PgvectorLoader()
        self.kb_name = kb_name

    def run(self, file_path: str) -> dict[str, Any]:
        """
        完整 ETL 流程：文件路径 → 数据落库。

        Returns:
            {
                "file": str,
                "documents": int,   # 提取的原始文档数
                "chunks": int,      # 分块数
                "loaded": int,      # 成功写入 DB 的 chunk 数
                "elapsed_s": float,
            }
        """
        t0 = time.time()
        logger.info(f"[ETL] 开始处理: {file_path}")

        # ── Extract ──────────────────────────────────────────────────────────
        extractor = get_extractor(file_path)
        documents = extractor.extract(file_path)
        logger.info(f"[Extract] {len(documents)} 个原始文档")

        # ── Transform ────────────────────────────────────────────────────────
        chunks = self.transformer.transform(documents)
        logger.info(f"[Transform] {len(chunks)} 个 chunk（含向量）")

        # ── Load ─────────────────────────────────────────────────────────────
        loaded = self.loader.load(chunks, source_file=file_path, kb_name=self.kb_name)
        logger.info(f"[Load] {loaded} 个 chunk 写入 PostgreSQL")

        elapsed = round(time.time() - t0, 2)
        logger.info(f"[ETL] 完成，耗时 {elapsed}s")

        return {
            "file": file_path,
            "documents": len(documents),
            "chunks": len(chunks),
            "loaded": loaded,
            "elapsed_s": elapsed,
        }

    def run_batch(self, file_paths: list[str]) -> list[dict[str, Any]]:
        """批量处理多个文件"""
        return [self.run(fp) for fp in file_paths]
