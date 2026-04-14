"""
Day 17 — pgvector 实战

覆盖内容：
1. 向量列操作：写入、查询
2. 三种距离算子：<-> 欧式 / <=> 余弦 / <#> 内积
3. IVFFlat vs HNSW 索引的选择逻辑
4. 把 Day 16 插入的 NULL embedding 填充上

运行方式：
    uv run python scripts/week3/day17_pgvector.py
"""

import os
import math
import hashlib
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
conn.autocommit = False
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
print("✓ 连接成功\n")


# ── 工具函数：本地确定性向量（替代真实 Embedding API）────────────────────────
# 和 TextTransformer 里的 _LocalEmbeddings 逻辑一致
def local_embed(text: str, dim: int = 1536) -> list[float]:
    """SHA256 哈希 → 确定性 1536 维向量，归一化到单位长度"""
    seed = hashlib.sha256(text.encode()).digest()
    vec = []
    i = 0
    while len(vec) < dim:
        b = seed[i % len(seed)]
        vec.append((b / 255.0) * 2 - 1)  # 映射到 [-1, 1]
        i += 1
    vec = vec[:dim]
    # L2 归一化（余弦相似度要求单位向量）
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec]


def vec_to_pg(v: list[float]) -> str:
    """Python list → pgvector 字符串格式 '[0.1, 0.2, ...]'"""
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


# ── 1. 确认 pgvector 扩展已启用 ───────────────────────────────────────────────
print("=" * 50)
print("1. 确认 pgvector 扩展")
print("=" * 50)
cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'")
row = cur.fetchone()
print(f"pgvector 版本: {row['extversion']}\n")


# ── 2. 建一张演示表，感受向量列 ───────────────────────────────────────────────
print("=" * 50)
print("2. 向量列基础操作")
print("=" * 50)

cur.execute("DROP TABLE IF EXISTS _demo_vectors")
cur.execute("""
    CREATE TABLE _demo_vectors (
        id      SERIAL PRIMARY KEY,
        label   TEXT,
        content TEXT,
        vec     vector(8)   -- 用 8 维演示，原理和 1536 维完全一样
    )
""")

# 手工造几个有语义关系的向量（8 维，方便肉眼看）
items = [
    ("机器学习",   [0.9, 0.8, 0.1, 0.1, 0.0, 0.0, 0.1, 0.0]),
    ("深度学习",   [0.85, 0.9, 0.15, 0.1, 0.0, 0.0, 0.1, 0.0]),
    ("神经网络",   [0.8, 0.85, 0.2, 0.1, 0.0, 0.0, 0.1, 0.0]),
    ("数据库索引", [0.1, 0.0, 0.9, 0.8, 0.7, 0.0, 0.1, 0.0]),
    ("SQL 优化",  [0.1, 0.0, 0.85, 0.9, 0.8, 0.0, 0.1, 0.0]),
    ("今天天气好", [0.0, 0.1, 0.0, 0.0, 0.1, 0.9, 0.8, 0.7]),
]

for label, vec in items:
    # 归一化
    norm = math.sqrt(sum(x * x for x in vec))
    vec_norm = [x / norm for x in vec]
    cur.execute(
        "INSERT INTO _demo_vectors (label, content, vec) VALUES (%s, %s, %s)",
        (label, label, vec_to_pg(vec_norm))
    )
conn.commit()
print(f"插入 {len(items)} 条演示数据\n")


# ── 3. 三种距离算子对比 ────────────────────────────────────────────────────────
print("=" * 50)
print("3. 距离算子对比（查询：'机器学习'）")
print("=" * 50)

query_label = "机器学习"
query_vec = None
cur.execute("SELECT vec FROM _demo_vectors WHERE label = %s", (query_label,))
query_vec = cur.fetchone()["vec"]  # 直接取已归一化的向量

print(f"查询向量来自：'{query_label}'\n")

# <-> 欧式距离（L2）：越小越相似
cur.execute("""
    SELECT label, ROUND((vec <-> %s)::numeric, 4) AS l2_dist
    FROM   _demo_vectors
    ORDER  BY vec <-> %s
    LIMIT  4
""", (query_vec, query_vec))
print("L2 欧式距离 <->（越小越相似）:")
for row in cur.fetchall():
    print(f"  {row['label']:12s}  dist={row['l2_dist']}")

# <=> 余弦距离：1 - cosine_similarity，越小越相似
cur.execute("""
    SELECT label, ROUND((vec <=> %s)::numeric, 4) AS cos_dist
    FROM   _demo_vectors
    ORDER  BY vec <=> %s
    LIMIT  4
""", (query_vec, query_vec))
print("\n余弦距离 <=>（越小越相似，RAG 推荐用这个）:")
for row in cur.fetchall():
    print(f"  {row['label']:12s}  dist={row['cos_dist']}")

# <#> 内积（负值，越小越相似，即内积越大越相似）
cur.execute("""
    SELECT label, ROUND((vec <#> %s)::numeric, 4) AS neg_dot
    FROM   _demo_vectors
    ORDER  BY vec <#> %s
    LIMIT  4
""", (query_vec, query_vec))
print("\n负内积 <#>（越小越相似）:")
for row in cur.fetchall():
    print(f"  {row['label']:12s}  neg_dot={row['neg_dot']}")

print("""
结论：
- RAG 场景用 <=>（余弦）：OpenAI Embedding 已归一化，余弦 ≈ L2，但语义更稳定
- <-> L2：向量未归一化时用，电商图片搜索常见
- <#> 内积：模型训练时用，日常 RAG 不用
""")


# ── 4. 索引：IVFFlat vs HNSW ─────────────────────────────────────────────────
print("=" * 50)
print("4. 索引选择")
print("=" * 50)
print("""
IVFFlat（倒排文件索引）：
- 原理：把向量空间分成 N 个簇（list），查询时只搜最近的几个簇
- 优点：内存占用小，适合大数据量（>100 万）
  - 缺点：建索引前必须有足够数据（建议 rows >= 列数 * 16），召回率略低
- 语法：USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)

HNSW（分层可导航小世界图）：
- 原理：多层图结构，查询沿图跳跃找邻居
- 优点：查询快、召回率高，不需要预先数据
- 缺点：内存占用大（约为 IVFFlat 的 2-3 倍）
- 语法：USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)

选择建议（针对本项目）：
- 开发阶段（数据量 < 10 万）→ HNSW，不用调参
- 生产大规模（> 100 万）→ IVFFlat，内存可控
- init.sql 里已经建了 HNSW 索引，本项目够用
""")

# 查看 document_chunks 上的索引
cur.execute("""
    SELECT indexname, indexdef
    FROM   pg_indexes
    WHERE  tablename = 'document_chunks'
""")
print("document_chunks 当前索引:")
for row in cur.fetchall():
    print(f"  {row['indexname']}")
    print(f"    {row['indexdef'][:80]}")
print()


# ── 5. 给 Day 16 插入的 NULL embedding 填充向量 ───────────────────────────────
print("=" * 50)
print("5. 填充 Day 16 的 NULL embedding")
print("=" * 50)

cur.execute("""
    SELECT dc.id, dc.chunk_text
    FROM   document_chunks dc
    WHERE  dc.embedding IS NULL
""")
pending = cur.fetchall()
print(f"待填充: {len(pending)} 条\n")

for row in pending:
    vec = local_embed(row["chunk_text"])
    cur.execute(
        "UPDATE document_chunks SET embedding = %s WHERE id = %s",
        (vec_to_pg(vec), row["id"])
    )

conn.commit()
print(f"已填充 {len(pending)} 条 embedding ✓")

# 验证
cur.execute("SELECT COUNT(*) AS n FROM document_chunks WHERE embedding IS NULL")
remaining = cur.fetchone()["n"]
print(f"剩余 NULL embedding: {remaining}\n")


# ── 6. 端到端向量检索演示 ─────────────────────────────────────────────────────
print("=" * 50)
print("6. 端到端语义检索（对 document_chunks 做 top-3 查询）")
print("=" * 50)

query_text = "如何用向量数据库做语义检索"
query_vec = local_embed(query_text)

cur.execute("""
    SELECT dc.id,
        dc.chunk_text,
        ROUND((dc.embedding <=> %s)::numeric, 4) AS cos_dist,
        d.title AS doc_title
    FROM   document_chunks dc
    JOIN   documents d ON d.id = dc.document_id
    ORDER  BY dc.embedding <=> %s
    LIMIT  3
""", (vec_to_pg(query_vec), vec_to_pg(query_vec)))

print(f"查询：'{query_text}'\n")
print("Top-3 结果:")
for i, row in enumerate(cur.fetchall(), 1):
    print(f"  [{i}] cos_dist={row['cos_dist']} | {row['doc_title']}")
    print(f"       {row['chunk_text'][:60]}...")

# ── 清理 ─────────────────────────────────────────────────────────────────────
cur.execute("DROP TABLE IF EXISTS _demo_vectors")
conn.commit()
cur.close()
conn.close()
print("\nDay 17 完成 ✓")
