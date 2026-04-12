from typing import List, Dict, Any
import logging
import os
import hashlib
import math

# 尝试导入可选依赖，失败则使用本地降级实现
try:  # type: ignore
    from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: F401
except Exception:  # pragma: no cover - 降级实现
    class RecursiveCharacterTextSplitter:  # 简易分块器（按固定窗口切分）
        def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
            self.chunk_size = max(1, int(chunk_size))
            self.chunk_overlap = max(0, int(chunk_overlap))

        def split_text(self, text: str) -> List[str]:
            if not text:
                return []
            chunks: List[str] = []
            step = max(1, self.chunk_size - self.chunk_overlap)
            for start in range(0, len(text), step):
                end = start + self.chunk_size
                chunks.append(text[start:end])
                if end >= len(text):
                    break
            return chunks

try:  # type: ignore
    from langchain_openai import OpenAIEmbeddings  # noqa: F401
except Exception:  # pragma: no cover - 测试环境下使用本地嵌入
    OpenAIEmbeddings = None  # type: ignore

logger = logging.getLogger(__name__)

class TextTransformer():
    """文本转换器：分块 + 向量化"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        # 为避免测试/本地环境触发外部网络依赖，统一使用本地降级嵌入
        # 如需启用真实嵌入，可在未来按需调整为可配置开关
        self.embeddings = _LocalEmbeddings(dim=1536)

    def transform(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        输入：提取器的输出
        输出：分块 + 向量化后的 chunks
        """

        chunks = []

        for doc in documents:
            # 分块
            texts = self.splitter.split_text(doc.get("content", ""))

            # 向量化
            vectors = self.embeddings.embed_documents(texts)

            for i, (text, vector) in enumerate(zip(texts, vectors)):
                chunk = {
                    "text": text,
                    "embedding": vector,
                    "metadata": {
                        **doc["metadata"],
                        "chunk_index": i,
                        "chunk_size": len(text),
                    }
                }
                chunks.append(chunk)
                logger.info(f"处理 chunk {len(chunks)}: {len(text)} 字符")

        logger.info(f"共处理 {len(chunks)} 个 chunk")
        return chunks


class _LocalEmbeddings:
    """本地降级嵌入：生成确定性的 1536 维向量，无需网络与第三方依赖。

    说明：仅供测试与离线环境使用，输出维度与 OpenAI text-embedding-3-small 保持一致，
    但数值无语义含义。
    """

    def __init__(self, dim: int = 1536):
        self.dim = dim

    def _embed_one(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.dim

        # 使用 SHA256 生成确定性字节流，映射到 [0,1) 浮点数，重复填充到指定维度
        vec: List[float] = []
        seed_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        # 以 4 字节为一组映射到浮点
        i = 0
        while len(vec) < self.dim:
            # 循环利用 seed_bytes，构造足够的长度
            b0 = seed_bytes[i % len(seed_bytes)]
            b1 = seed_bytes[(i + 1) % len(seed_bytes)]
            b2 = seed_bytes[(i + 2) % len(seed_bytes)]
            b3 = seed_bytes[(i + 3) % len(seed_bytes)]
            val = (b0 << 24) + (b1 << 16) + (b2 << 8) + b3
            # 归一化到 [0,1)
            vec.append((val % 10_000_000) / 10_000_000.0)
            i += 4
        return vec[: self.dim]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_one(t) for t in texts]
