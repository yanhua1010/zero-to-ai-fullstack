"""
Day 18 — LangChain PGVector 集成

Day 17 是手写 SQL 理解底层。
Day 18 是用 LangChain 的 PGVector 把这些操作封装起来——
这才是生产代码里实际用的方式。

对比 Week 2 用 Chroma：
Chroma.from_documents(docs, embeddings)   → 内存，进程退出数据消失
PGVector.from_documents(docs, embeddings) → 持久化 PostgreSQL

运行方式：
    uv run python scripts/week3/day18_langchain_pgvector.py
"""

import os
from dotenv import load_dotenv
from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

load_dotenv()

# ── 连接字符串 ─────────────────────────────────────────────────────────────────
# PGVector 用标准 PostgreSQL 连接字符串
CONNECTION_STRING = (
    f"postgresql+psycopg2://"
    f"{os.getenv('POSTGRES_USER', 'postgres')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'knowledge_base')}"
)

COLLECTION_NAME = "week3_demo"

# ── Embedding 模型（需要 OPENAI_API_KEY） ─────────────────────────────────────
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

# ── 1. 准备文档 ───────────────────────────────────────────────────────────────
print("=" * 50)
print("1. 文档向量化并写入 PGVector")
print("=" * 50)

docs = [
    Document(
        page_content="RAG 通过检索相关文档来增强 LLM 的回答质量，减少幻觉。",
        metadata={"source": "rag_intro.md", "topic": "rag"},
    ),
    Document(
        page_content="pgvector 是 PostgreSQL 的向量扩展，支持 HNSW 和 IVFFlat 索引。",
        metadata={"source": "pgvector_guide.md", "topic": "database"},
    ),
    Document(
        page_content="LangChain 的 PGVector 封装了向量的写入和检索，无需手写 SQL。",
        metadata={"source": "langchain_docs.md", "topic": "langchain"},
    ),
    Document(
        page_content="chunk_size 影响检索粒度：太大检索噪音多，太小语义不完整。",
        metadata={"source": "rag_intro.md", "topic": "rag"},
    ),
    Document(
        page_content="HNSW 索引适合开发阶段，查询快、不需要预先大量数据。",
        metadata={"source": "pgvector_guide.md", "topic": "database"},
    ),
]

# from_documents 自动完成：向量化 → 写入 PG
# pre_delete_collection=True 每次运行先清空，方便重复测试
vectorstore = PGVector.from_documents(
    documents=docs,
    embedding=embeddings,
    collection_name=COLLECTION_NAME,
    connection_string=CONNECTION_STRING,
    pre_delete_collection=True,
)
print(f"已写入 {len(docs)} 条文档\n")


# ── 2. 相似度检索 ─────────────────────────────────────────────────────────────
print("=" * 50)
print("2. 相似度检索")
print("=" * 50)

query = "如何选择向量索引类型"
results = vectorstore.similarity_search(query, k=3)

print(f"查询：'{query}'\n")
for i, doc in enumerate(results, 1):
    print(f"  [{i}] {doc.metadata['source']}")
    print(f"       {doc.page_content}")
    print()


# ── 3. 带分数的检索 ───────────────────────────────────────────────────────────
print("=" * 50)
print("3. 带相似度分数的检索")
print("=" * 50)

results_with_score = vectorstore.similarity_search_with_score(query, k=3)
print(f"查询：'{query}'\n")
for doc, score in results_with_score:
    # PGVector 返回的 score 是余弦距离（越小越相似）
    similarity = 1 - score
    print(f"  相似度={similarity:.4f} | {doc.page_content[:50]}...")
print()


# ── 4. metadata 过滤检索 ──────────────────────────────────────────────────────
print("=" * 50)
print("4. metadata 过滤（只在 topic=rag 的文档里检索）")
print("=" * 50)

# LangChain PGVector 支持 filter 参数做 metadata 过滤
results_filtered = vectorstore.similarity_search(
    "减少 LLM 幻觉的方法",
    k=3,
    filter={"topic": "rag"},
)
print("过滤条件: topic=rag\n")
for i, doc in enumerate(results_filtered, 1):
    print(f"  [{i}] {doc.metadata}")
    print(f"       {doc.page_content[:60]}...")
print()


# ── 5. 对比 Chroma 和 PGVector ────────────────────────────────────────────────
print("=" * 50)
print("5. Chroma vs PGVector 总结")
print("=" * 50)
print("""
            Chroma（Week 2）          PGVector（Week 3）
    存储        内存（进程退出消失）       PostgreSQL（持久化）
    配置        零配置                    需要 PG + pgvector 扩展
    SQL 支持    无                        完整 SQL，可做混合查询
    生产可用    原型/开发                  生产
    LangChain   Chroma.from_documents()   PGVector.from_documents()
    接口        完全一致，一行代码切换
""")

print("Day 18 完成 ✓")
print("\n下一步 Day 19-21：把 ETLPipeline 接上 PGVector，跑通完整链路")
