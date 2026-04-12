import pytest
from backend.etl.pipeline import ETLPipeline
from pathlib import Path


def test_txt_extraction():
    """测试 TXT 文件提取"""
    pipeline = ETLPipeline()
    chunks = pipeline.run("scripts/week2/data/sample.txt")
    
    assert len(chunks) > 0
    assert "text" in chunks[0]
    assert "embedding" in chunks[0]
    assert len(chunks[0]["embedding"]) == 1536  # embedding 维度