"""
Day 19-21 — 端到端验证：文件 → ETL → PostgreSQL → 语义检索

这是 Week 3 的终点：
文档文件
    → ETLPipeline.run()（Extract + Transform + Load）
    → PostgreSQL document_chunks 表（含 embedding 向量）
    → 向量检索（pgvector <=> 余弦距离）
    → 返回相关 chunk

运行方式：
    uv run python scripts/week3/day19_etl_to_pg.py
"""

import os
import sys
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# 把项目根目录加入 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.etl.pipeline import ETLPipeline
from backend.etl.transformers import TextTransformer


# ── 1. 准备测试文件 ────────────────────────────────────────────────────────────
print("=" * 55)
print("1. 准备测试文件")
print("=" * 55)

test_dir = Path("data")
test_dir.mkdir(exist_ok=True)

test_file = test_dir / "week3_test.md"
test_file.write_text("""# RAG 系统核心概念

## 什么是 RAG

RAG（Retrieval-Augmented Generation）是一种将信息检索与大语言模型生成相结合的技术架构。
它通过在生成回答前先检索相关文档，将外部知识注入 LLM 的上下文窗口，
从而显著提升回答的准确性并减少幻觉现象。

## pgvector 的作用

pgvector 是 PostgreSQL 的向量扩展，允许在关系数据库中存储和查询高维向量。
在 RAG 系统中，pgvector 负责存储文档 chunk 的 embedding 向量，
并通过近似最近邻搜索找出与用户查询语义最相关的文档片段。

## 索引选择

HNSW 索引适合数据量小于 100 万的场景，查询速度快且无需预先大量数据。
IVFFlat 索引适合超大规模数据，内存占用更小但需要在建索引前有足够数据量。
本项目开发阶段使用 HNSW，生产扩容时可迁移到 IVFFlat。

## ETL 管道设计

ETL 管道分为三层：Extract 负责读取原始文档，Transform 负责分块和向量化，
Load 负责将结果持久化到 PostgreSQL。三层职责清晰，互不干扰。
""", encoding="utf-8")

print(f"测试文件: {test_file}（{test_file.stat().st_size} 字节）\n")


# ── 2. 运行完整 ETL ────────────────────────────────────────────────────────────
print("=" * 55)
print("2. 运行 ETLPipeline（Extract → Transform → Load）")
print("=" * 55)

pipeline = ETLPipeline(kb_name="week3-demo")
result = pipeline.run(str(test_file))

print(f"\n结果:")
print(f"  原始文档数:  {result['documents']}")
print(f"  chunk 数:    {result['chunks']}")
print(f"  写入 DB:     {result['loaded']}")
print(f"  耗时:        {result['elapsed_s']}s\n")


# ── 3. 直接查 DB，验证数据落库 ─────────────────────────────────────────────────
print("=" * 55)
print("3. 验证数据落库")
print("=" * 55)

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", 5432)),
    dbname=os.getenv("POSTGRES_DB", "knowledge_base"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT d.title, COUNT(dc.id) AS chunks,
        COUNT(dc.embedding) AS with_embedding
    FROM   documents d
    JOIN   document_chunks dc ON dc.document_id = d.id
    JOIN   knowledge_bases kb ON kb.id = d.kb_id
    WHERE  kb.name = 'week3-demo'
    GROUP  BY d.title
""")
for row in cur.fetchall():
    print(f"  {row['title']}")
    print(f"    chunks={row['chunks']}, 有向量={row['with_embedding']}")
print()


# ── 4. 语义检索验证 ────────────────────────────────────────────────────────────
print("=" * 55)
print("4. 语义检索验证")
print("=" * 55)

# 查询向量必须和 ETL 用同一个 embedding 实例，否则向量空间不一致
transformer = TextTransformer()

def vec_to_pg(v):
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"

queries = [
    "如何减少 LLM 的幻觉问题",
    "向量索引该怎么选",
    "ETL 管道的设计原则",
]

for query in queries:
    q_vec = transformer.embed_query(query)
    cur.execute("""
        SELECT dc.chunk_text,
            ROUND((dc.embedding <=> %s)::numeric, 4) AS cos_dist
        FROM   document_chunks dc
        JOIN   documents d ON d.id = dc.document_id
        JOIN   knowledge_bases kb ON kb.id = d.kb_id
        WHERE  kb.name = 'week3-demo'
        ORDER  BY dc.embedding <=> %s
        LIMIT  2
    """, (vec_to_pg(q_vec), vec_to_pg(q_vec)))

    rows = cur.fetchall()
    print(f"查询: 「{query}」")
    for i, row in enumerate(rows, 1):
        print(f"  [{i}] dist={row['cos_dist']} | {row['chunk_text'][:60]}...")
    print()


cur.close()
conn.close()

print("=" * 55)
print("Week 3 完整链路验证通过 ✓")
print("=" * 55)
print("""
完成的内容：
Day 15-16  PostgreSQL 速通（JSONB / CTE / Schema）
Day 17     pgvector 底层操作（距离算子 / 索引选择）
Day 18     LangChain PGVector 封装
Day 19-21  SQLAlchemy ORM + Alembic + PgvectorLoader + 完整 ETL 链路

下周（Week 4）：FastAPI 后端 + 完整 RAG 问答接口
""")
