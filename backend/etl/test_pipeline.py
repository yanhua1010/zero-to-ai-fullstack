"""
ETLPipeline 端到端测试。

注意：pipeline.run() 跑的是完整三层（Extract + Transform + Load），
Load 层要写 PostgreSQL，所以这个测试需要本地数据库 —— 用 live_db fixture 守门，
没起 Postgres 时自动跳过。
"""

from backend.etl.pipeline import ETLPipeline


def test_txt_pipeline_end_to_end(live_db):
    """TXT 文件 → 分块 → 向量化 → 落库，验证整条 ETL 链路。"""
    pipeline = ETLPipeline(kb_name="test-pipeline")
    result = pipeline.run("scripts/week2/data/sample.txt")

    # run() 返回的是统计 dict：{file, documents, chunks, loaded, elapsed_s}
    assert result["documents"] >= 1
    assert result["chunks"] > 0
    assert result["loaded"] == result["chunks"]  # 所有 chunk 都成功写进了 DB
    assert result["elapsed_s"] >= 0
