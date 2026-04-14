"""
Day 15 — PostgreSQL 速通（对照 MySQL）

运行前提：
    docker compose up -d
    等 healthcheck 变绿（docker compose ps 看状态）

运行方式：
    uv run python scripts/week3/day15_postgres_basics.py
"""

import os
import psycopg2
import psycopg2.extras  # RealDictCursor
import json
from dotenv import load_dotenv

load_dotenv()

# ── 连接 ──────────────────────────────────────────────────────────────────────
# MySQL:      mysql -h host -u user -p dbname
# PostgreSQL: psycopg2.connect(host=..., user=..., password=..., dbname=...)
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", 5432)),
    dbname=os.getenv("POSTGRES_DB", "knowledge_base"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
)
conn.autocommit = True
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print("✓ 连接成功\n")


# ── 1. MySQL vs PostgreSQL 基础差异 ───────────────────────────────────────────
print("=" * 50)
print("1. 基础语法差异")
print("=" * 50)

# MySQL AUTO_INCREMENT → PostgreSQL SERIAL / IDENTITY
# 查 PostgreSQL 版本（MySQL: SELECT VERSION()，PG 一样）
cur.execute("SELECT version()")
row = cur.fetchone()
print(f"PG 版本: {row['version'][:40]}...\n")


# ── 2. JSONB —— PostgreSQL 独有，RAG metadata 存储核心 ────────────────────────
print("=" * 50)
print("2. JSONB 操作（MySQL 没有原生等价物）")
print("=" * 50)

# 建一张临时测试表
cur.execute("DROP TABLE IF EXISTS _test_jsonb")
cur.execute("""
    CREATE TABLE _test_jsonb (
        id       SERIAL PRIMARY KEY,
        name     TEXT,
        metadata JSONB
    )
""")

# 插入带 JSONB 的行
docs = [
    ("RAG 论文",  {"source": "arxiv", "year": 2020, "tags": ["rag", "nlp"], "pages": 12}),
    ("pgvector",  {"source": "github", "year": 2021, "tags": ["vector", "pg"], "pages": 8}),
    ("LangChain", {"source": "docs",   "year": 2022, "tags": ["rag", "llm"], "pages": 30}),
]
for name, meta in docs:
    cur.execute(
        "INSERT INTO _test_jsonb (name, metadata) VALUES (%s, %s)",
        (name, json.dumps(meta))
    )

# ->> 取 JSONB 字段为文本（MySQL 没有对等语法）
cur.execute("SELECT name, metadata->>'source' AS source FROM _test_jsonb")
print("metadata->>'source' 提取字符串:")
for row in cur.fetchall():
    print(f"  {row['name']:12s} | source={row['source']}")

# @> 包含查询（MySQL 完全没有）
cur.execute("SELECT name FROM _test_jsonb WHERE metadata @> '{\"tags\": [\"rag\"]}'")
rows = cur.fetchall()
print(f"\nmetadata @> '{{\"tags\":[\"rag\"]}}' 的文档:")
for row in rows:
    print(f"  {row['name']}")

# jsonb_set 更新嵌套字段
cur.execute("""
    UPDATE _test_jsonb
    SET metadata = jsonb_set(metadata, '{year}', '2023')
    WHERE name = 'LangChain'
""")
cur.execute("SELECT name, metadata->>'year' FROM _test_jsonb WHERE name='LangChain'")
row = cur.fetchone()
print(f"\njsonb_set 更新后 LangChain year: {row['?column?']}\n")


# ── 3. CTE —— WITH ... AS ()，RAG 场景高频 ───────────────────────────────────
print("=" * 50)
print("3. CTE（MySQL 8.0 也有，但 PG 更常用）")
print("=" * 50)

# 模拟场景：找 tags 包含 "rag" 且 pages > 10 的文档
cur.execute("""
    WITH rag_docs AS (
        SELECT name,
            (metadata->>'pages')::int  AS pages,
            metadata->'tags'           AS tags
        FROM   _test_jsonb
        WHERE  metadata @> '{"tags": ["rag"]}'
    )
    SELECT name, pages
    FROM   rag_docs
    WHERE  pages > 10
    ORDER  BY pages DESC
""")
print("CTE：tags 含 rag 且 pages > 10 的文档:")
for row in cur.fetchall():
    print(f"  {row['name']:12s} | pages={row['pages']}")

print()


# ── 4. Schema 概念差异 ────────────────────────────────────────────────────────
print("=" * 50)
print("4. Schema 概念")
print("=" * 50)
# MySQL: Schema ≈ Database（USE mydb）
# PostgreSQL: Schema 是 Database 内的命名空间
#   默认 schema = public
#   可以创建 schema 隔离不同模块的表（如 rag.documents, etl.jobs）
cur.execute("""
    SELECT table_schema, table_name
    FROM   information_schema.tables
    WHERE  table_schema = 'public'
    AND  table_type = 'BASE TABLE'
    ORDER  BY table_name
""")
print("public schema 下的表:")
for row in cur.fetchall():
    print(f"  {row['table_schema']}.{row['table_name']}")

print()


# ── 5. 布尔类型 ───────────────────────────────────────────────────────────────
print("=" * 50)
print("5. 原生 BOOLEAN（MySQL 用 TINYINT(1) 模拟）")
print("=" * 50)
cur.execute("SELECT TRUE::boolean, FALSE::boolean, 'yes'::boolean")
row = cur.fetchone()
print(f"  TRUE={row['bool']}, FALSE 和 'yes' 也是合法的 boolean 字面量\n")


# ── 清理 ─────────────────────────────────────────────────────────────────────
cur.execute("DROP TABLE IF EXISTS _test_jsonb")
cur.close()
conn.close()
print("Day 15 完成 ✓")
print("\n关键记忆点:")
print("  ->>  取 JSONB 字段为文本")
print("  ->   取 JSONB 字段（保持 JSON 类型）")
print("  @>   JSONB 包含查询")
print("  WITH ... AS ()  CTE，让复杂查询可读")
print("  Schema 是 Database 内的命名空间，默认 public")
