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

# 默认 embedding 模型。OpenAI 官方 text-embedding-3-small 是 1536 维,
# 正好和项目 DB schema 的 vector(1536) 对得上。
# 用 OpenAI 兼容代理(阿里通义、智谱等)时如果走其他模型,通过环境变量
# EMBEDDING_MODEL 覆盖即可,但务必确认输出维度仍是 1536,否则要同步改
# sql/init.sql 和 models.py 里的 vector 维度。
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


def _openai_key_available() -> bool:
    """判断是否配置了可用的 OpenAI(兼容)API Key。占位符值视为未配置。"""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return key not in {"", "your_openai_api_key_here", "sk-..."}


class TextTransformer():
    """文本转换器:分块 + 向量化。

    Embedding 选择策略(和 chain.py / judge.py 一脉相承):
    - 有 OPENAI_API_KEY 且 langchain-openai 可用 → 真 OpenAI(兼容)嵌入,
      base_url 走 OPENAI_BASE_URL 可指向任何兼容代理
    - 没有 → 本地 SHA256 降级,1536 维,语义为零,只保证代码能跑

    重要约束:换 embedding 实例意味着向量空间换了,**之前灌进 DB 的向量会作废**,
    要把那个知识库清空重灌(eval-rag-basics 的 day29 脚本已经自动做这件事)。
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        if _openai_key_available() and OpenAIEmbeddings is not None:
            model = os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
            base_url = os.getenv("OPENAI_BASE_URL") or None
            self.embeddings = OpenAIEmbeddings(
                model=model,
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=base_url,
            )
            logger.info(
                f"[TextTransformer] 使用 OpenAI(兼容)嵌入: model={model}, "
                f"base_url={base_url or '官方默认 (api.openai.com)'}"
            )
        else:
            self.embeddings = _LocalEmbeddings(dim=1536)
            logger.warning(
                "[TextTransformer] 未检测到 OPENAI_API_KEY,使用本地 SHA256 降级嵌入。"
                "语义检索基本无效,只用于跑通流程。生产/评测请配 OPENAI_API_KEY。"
            )

    def embed_query(self, text: str) -> List[float]:
        """生成查询向量，和 transform() 使用同一个 embedding 实例，保证向量空间一致。"""
        return self.embeddings.embed_documents([text])[0]

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
