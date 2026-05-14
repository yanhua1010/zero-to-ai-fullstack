"""
FastAPI 接口测试。

分两类：
- 不依赖 DB 的：健康检查、请求体校验、文件类型校验 —— 任何环境都能跑
- 依赖 DB 的：增删查改 —— 加 live_db fixture 守门，没起 Postgres 就跳过

依赖 DB 的测试一律强制降级模式（删掉 ANTHROPIC_API_KEY），
保证测试不会真的去调 LLM：不花钱、不依赖网络、结果可重复。

对照 Java：TestClient 相当于 Spring 的 MockMvc —— 不真的起 HTTP 端口，
直接把请求喂给 app 对象，快且无副作用。
"""

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


# ── 不依赖 DB ─────────────────────────────────────────────────────────────────
def test_health():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_chat_requires_question():
    """缺必填字段 question，应被 Pydantic 拦在 422。"""
    r = client.post("/api/chat", json={"kb_name": "x"})
    assert r.status_code == 422


def test_create_kb_rejects_empty_name():
    """空名字违反 min_length=1，应 422。"""
    r = client.post("/api/knowledge-bases", json={"name": ""})
    assert r.status_code == 422


def test_upload_rejects_unsupported_type():
    """.exe 不在支持列表里，应 415。"""
    r = client.post(
        "/api/documents",
        files={"file": ("bad.exe", b"x", "application/octet-stream")},
        data={"kb_name": "whatever"},
    )
    assert r.status_code == 415


# ── 依赖 DB ───────────────────────────────────────────────────────────────────
@pytest.fixture
def kb_name(live_db):
    """每个测试用一个唯一知识库名，避免重复跑时互相干扰 / 撞 409。"""
    return f"test-kb-{uuid.uuid4().hex[:8]}"


def test_create_and_list_knowledge_base(live_db, kb_name):
    # 创建
    r = client.post(
        "/api/knowledge-bases",
        json={"name": kb_name, "description": "pytest"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == kb_name
    assert body["document_count"] == 0

    # 重名应 409
    r2 = client.post("/api/knowledge-bases", json={"name": kb_name})
    assert r2.status_code == 409

    # 列表里能查到
    r3 = client.get("/api/knowledge-bases")
    assert r3.status_code == 200
    assert any(kb["name"] == kb_name for kb in r3.json())


def test_upload_document_runs_etl(live_db, kb_name):
    content = "# 测试文档\n\nRAG 是检索增强生成。pgvector 负责存向量。".encode("utf-8")
    r = client.post(
        "/api/documents",
        files={"file": ("note.md", content, "text/markdown")},
        data={"kb_name": kb_name},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["kb_name"] == kb_name
    assert body["chunks"] > 0
    assert body["loaded"] == body["chunks"]


def test_chat_flow_and_conversation_persisted(live_db, kb_name, monkeypatch):
    """灌一篇文档 → SSE 问答 → 历史接口能查到这轮对话。"""
    # 强制降级，测试不调真 LLM
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    # 先灌一篇文档进知识库
    content = "# RAG\n\nRAG 先检索再生成，检索质量决定回答上限。".encode("utf-8")
    up = client.post(
        "/api/documents",
        files={"file": ("rag.md", content, "text/markdown")},
        data={"kb_name": kb_name},
    )
    assert up.status_code == 201

    # 问答：SSE 流式
    r = client.post(
        "/api/chat",
        json={"kb_name": kb_name, "question": "RAG 是什么？"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")

    # 解析 SSE：每行 "data: {json}"
    events = [
        json.loads(line[len("data: "):])
        for line in r.text.splitlines()
        if line.startswith("data: ")
    ]
    types = [e["type"] for e in events]
    assert types[0] == "sources"     # 先推来源
    assert types[-1] == "done"       # 最后收尾
    assert "delta" in types          # 中间有文本增量

    # 流结束后这轮对话应已落库，能从历史接口查到
    conv = client.get("/api/conversations", params={"kb_name": kb_name})
    assert conv.status_code == 200
    rows = conv.json()
    assert len(rows) >= 1
    assert rows[0]["query"] == "RAG 是什么？"
    assert rows[0]["response"]  # 降级模式也会有内容（检索到的原文）
