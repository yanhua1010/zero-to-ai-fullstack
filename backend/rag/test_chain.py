"""
RAGChain 单元测试 —— 全部跑在"本地降级模式"，不连数据库、不调 LLM。

为什么能不连 DB：
RAGChain.__init__ 里 retriever 的 create_engine 是惰性的，构造时不会真的连接，
要等第一次执行 SQL 才连。所以我们只要在测试里把 retriever.retrieve 换成假数据，
整个 RAGChain 就能在没有 Postgres 的环境里跑。

为什么强制降级：
pytest.ini 配了 env_files = .env，如果你的 .env 里有真 API Key，
不强制降级测试就会真的去调 LLM —— 又慢又花钱又不可重复。
所以 fixture 里先 delenv 掉 ANTHROPIC_API_KEY。
"""

import pytest

from backend.rag.generation.chain import RAGChain, _api_key_available
from backend.rag.generation.prompts import build_user_message, format_context

# 假的检索结果，结构和 PgVectorRetriever.retrieve() 的真实输出一致
FAKE_CHUNKS = [
    {"text": "RAG 先检索再生成。", "score": 0.12, "source": "doc_a.md",
     "source_type": "md", "chunk_index": 0, "metadata": {"k": "v"}},
    {"text": "检索质量决定回答上限。", "score": 0.20, "source": "doc_b.md",
     "source_type": "md", "chunk_index": 1, "metadata": {}},
]


@pytest.fixture
def chain(monkeypatch):
    """一个强制降级、retriever 被换成假数据的 RAGChain。"""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    c = RAGChain(kb_name="test-kb")
    monkeypatch.setattr(c.retriever, "retrieve", lambda q: list(FAKE_CHUNKS))
    monkeypatch.setattr(
        c.retriever, "retrieve_with_score_filter",
        lambda q, max_score: list(FAKE_CHUNKS),
    )
    assert c.degraded is True, "没有 API Key 时应进入降级模式"
    return c


# ── ask() ─────────────────────────────────────────────────────────────────────
def test_ask_result_shape(chain):
    r = chain.ask("什么是 RAG？")
    assert r["question"] == "什么是 RAG？"
    assert r["degraded"] is True
    assert r["model"] == "local-degraded"
    assert r["chunks_used"] == 2
    assert r["elapsed_s"] >= 0
    assert "本地降级" in r["answer"]


def test_sources_exclude_chunk_text(chain):
    """sources 只带元数据，不该把大段正文塞回去。"""
    r = chain.ask("q")
    assert len(r["sources"]) == 2
    for s in r["sources"]:
        assert set(s) == {"source", "source_type", "score", "chunk_index"}
        assert "text" not in s


def test_ask_is_stateless(chain):
    """ask() 不读也不写历史。"""
    chain.ask("q1")
    chain.ask("q2")
    assert chain.history == []


# ── chat() ────────────────────────────────────────────────────────────────────
def test_chat_maintains_history(chain):
    chain.chat("第一轮")
    chain.chat("第二轮")
    assert len(chain.history) == 4  # 两轮 = user/assistant 各 2 条


def test_chat_history_stores_clean_question(chain):
    """历史里存的应是干净的原始问题，不是拼了检索上下文的长消息。"""
    chain.chat("RAG 是什么")
    assert chain.history[0] == {"role": "user", "content": "RAG 是什么"}
    assert chain.history[1]["role"] == "assistant"


def test_reset_clears_history(chain):
    chain.chat("q")
    assert chain.history
    chain.reset()
    assert chain.history == []


# ── ask_stream() ──────────────────────────────────────────────────────────────
def test_ask_stream_event_sequence(chain):
    events = list(chain.ask_stream("q"))
    assert events[0]["type"] == "sources"
    assert events[-1]["type"] == "done"
    assert any(e["type"] == "delta" for e in events)
    # done 事件应带完整结果
    done = events[-1]
    assert done["chunks_used"] == 2
    assert "answer" in done and done["answer"]


# ── max_score 分支 ────────────────────────────────────────────────────────────
def test_max_score_uses_filter(monkeypatch):
    """设了 max_score 时应走带过滤的检索方法，而不是普通 retrieve。"""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    c = RAGChain(kb_name="test-kb", max_score=0.5)
    called = {}
    monkeypatch.setattr(
        c.retriever, "retrieve_with_score_filter",
        lambda q, max_score: called.update(max_score=max_score) or list(FAKE_CHUNKS),
    )
    monkeypatch.setattr(
        c.retriever, "retrieve",
        lambda q: pytest.fail("设了 max_score 不该调用无过滤的 retrieve"),
    )
    c.ask("q")
    assert called["max_score"] == 0.5


# ── _api_key_available 工具函数 ───────────────────────────────────────────────
@pytest.mark.parametrize("value,expected", [
    ("", False),
    ("your_anthropic_api_key_here", False),  # .env.example 的占位符
    ("sk-ant-...", False),                   # 进度文档里的占位符
    ("sk-ant-real-key-xxx", True),
])
def test_api_key_available(monkeypatch, value, expected):
    monkeypatch.setenv("ANTHROPIC_API_KEY", value)
    assert _api_key_available() is expected


# ── prompts.py ────────────────────────────────────────────────────────────────
def test_format_context_empty():
    assert "没有找到相关文档" in format_context([])


def test_format_context_includes_source_and_score():
    out = format_context(FAKE_CHUNKS)
    assert "doc_a.md" in out and "doc_b.md" in out
    assert "0.12" in out  # score 会显示给 LLM


def test_build_user_message_has_question_and_context():
    msg = build_user_message("我的问题", FAKE_CHUNKS)
    assert "我的问题" in msg
    assert "RAG 先检索再生成" in msg
