"""
Day 16 — 把 Week 2 ETL 输出的 metadata 存进 PG

目标：
- 用 documents + document_chunks 表存储 ETL 结果
- 练习 JSONB 写入和查询
- 为 Day 17 接入 pgvector 做铺垫（embedding 列暂时留空）

运行方式：
    uv run python scripts/week3/day16_jsonb_metadata.py
"""

import os
import json
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", 5432)),
    dbname=os.getenv("POSTGRES_DB", "knowledge_base"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
)
conn.autocommit = False  # 手动事务控制
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print("✓ 连接成功\n")

# ── 1. 插入知识库 ─────────────────────────────────────────────────────────────
cur.execute("""
    INSERT INTO knowledge_bases (name, description)
    VALUES (%s, %s)
    RETURNING id
""", ("Week3 测试知识库", "用于 Day 16 练习"))
kb_id = cur.fetchone()["id"]
print(f"创建知识库 id={kb_id}\n")


# ── 2. 模拟 ETL 输出，插入 documents + document_chunks ───────────────────────
# 模拟 Week 2 ETL 的输出格式
mock_etl_results = [
    {
        "file_path": "data/rag_intro.md",
        "source_type": "md",
        "title": "RAG 入门介绍",
        "chunks": [
            {
                "chunk_index": 0,
                "text": "RAG（检索增强生成）是一种将信息检索与语言模型生成相结合的技术。",
                "metadata": {"source": "data/rag_intro.md", "chunk_index": 0, "chunk_size": 35},
            },
            {
                "chunk_index": 1,
                "text": "通过检索相关文档片段并将其注入提示词，RAG 显著减少了 LLM 的幻觉现象。",
                "metadata": {"source": "data/rag_intro.md", "chunk_index": 1, "chunk_size": 38},
            },
        ],
    },
    {
        "file_path": "data/pgvector_guide.pdf",
        "source_type": "pdf",
        "title": "pgvector 使用指南",
        "chunks": [
            {
                "chunk_index": 0,
                "text": "pgvector 是 PostgreSQL 的向量相似度搜索扩展，支持精确和近似最近邻搜索。",
                "metadata": {"source": "data/pgvector_guide.pdf", "chunk_index": 0, "page": 1, "chunk_size": 40},
            },
        ],
    },
]

total_chunks = 0
for doc_data in mock_etl_results:
    # 插入 document
    cur.execute("""
        INSERT INTO documents (kb_id, title, source_type, content, metadata)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (
        kb_id,
        doc_data["title"],
        doc_data["source_type"],
        " ".join(c["text"] for c in doc_data["chunks"]),  # 原文拼接
        json.dumps({"file_path": doc_data["file_path"]}),
    ))
    doc_id = cur.fetchone()["id"]

    # 插入 chunks（embedding 暂时为 NULL，Day 17 填充）
    for chunk in doc_data["chunks"]:
        cur.execute("""
            INSERT INTO document_chunks
                (document_id, chunk_index, chunk_text, token_count, metadata)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            doc_id,
            chunk["chunk_index"],
            chunk["text"],
            len(chunk["text"]),         # 用字符数近似 token 数
            json.dumps(chunk["metadata"]),
        ))
        total_chunks += 1

    print(f"  文档 '{doc_data['title']}' → doc_id={doc_id}，{len(doc_data['chunks'])} 个 chunk")

conn.commit()
print(f"\n共插入 {total_chunks} 个 chunk ✓\n")


# ── 3. 查询验证 ───────────────────────────────────────────────────────────────
print("=" * 50)
print("查询验证")
print("=" * 50)

# 3-1. JSONB 过滤：只查 PDF 来源的 chunk
cur.execute("""
    SELECT dc.id, dc.chunk_text, dc.metadata->>'page' AS page
    FROM   document_chunks dc
    JOIN   documents d ON d.id = dc.document_id
    WHERE  d.kb_id = %s
    AND  d.source_type = 'pdf'
""", (kb_id,))
print("\nPDF 来源的 chunks:")
for row in cur.fetchall():
    print(f"  [{row['id']}] page={row['page']} | {row['chunk_text'][:50]}...")

# 3-2. CTE：统计每篇文档的 chunk 数
cur.execute("""
    WITH doc_stats AS (
        SELECT d.title,
            COUNT(dc.id)      AS chunk_count,
            SUM(dc.token_count) AS total_tokens
        FROM   documents d
        JOIN   document_chunks dc ON dc.document_id = d.id
        WHERE  d.kb_id = %s
        GROUP  BY d.title
    )
    SELECT * FROM doc_stats ORDER BY chunk_count DESC
""", (kb_id,))
print("\n各文档 chunk 统计:")
for row in cur.fetchall():
    print(f"  {row['title']:20s} | chunks={row['chunk_count']}, tokens≈{row['total_tokens']}")

# 3-3. 查 embedding 为 NULL 的 chunk（Day 17 需要填充这些）
cur.execute("""
    SELECT COUNT(*) AS pending
    FROM   document_chunks dc
    JOIN   documents d ON d.id = dc.document_id
    WHERE  d.kb_id = %s
    AND  dc.embedding IS NULL
""", (kb_id,))
row = cur.fetchone()
print(f"\n待向量化的 chunk 数: {row['pending']}（Day 17 处理）")

cur.close()
conn.close()
print("\nDay 16 完成 ✓")
