"""
Day 22 — RAG Chain：把检索和生成接通

Week 3 的终点是"文件 → ETL → PG → 检索"，但检索出来的还只是 chunk 列表。
Day 22 要补上最后一段：把 chunk 喂给 LLM，生成带来源的自然语言答案。

完整链路：
    问题
      → PgVectorRetriever.retrieve()      检索相关 chunk
      → prompts.build_user_message()      拼成带上下文的 Prompt
      → Claude API（或本地降级模式）       生成答案
      → RAGChain 统一返回 {answer, sources, ...}

运行方式：
    docker compose up -d            # 先把数据库起起来
    uv run python scripts/week4/day22_rag_chain.py

说明：没配 ANTHROPIC_API_KEY 也能跑 —— RAGChain 会自动进入"本地降级模式"，
只检索、不调用 LLM，把检索到的原文摊开返回。链路一样是通的。
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# 把项目根目录加入 Python 路径（和 day19 一样的套路）
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.etl.pipeline import ETLPipeline
from backend.rag.generation import RAGChain

KB_NAME = "week4-demo"


def section(title: str) -> None:
    print("\n" + "=" * 55)
    print(title)
    print("=" * 55)


# ── 1. 准备测试数据：灌一份文档进知识库 ────────────────────────────────────────
section("1. 准备测试数据（ETL 灌库）")

test_dir = Path("data")
test_dir.mkdir(exist_ok=True)
test_file = test_dir / "week4_test.md"
test_file.write_text("""# RAG 问答系统设计笔记

## RAG 的两个阶段

RAG 系统在运行时分为两个阶段：检索阶段和生成阶段。
检索阶段把用户问题转成向量，在向量库里找出语义最接近的文档片段。
生成阶段把这些片段连同问题一起交给大语言模型，由模型组织出最终答案。

## 为什么要标注来源

RAG 回答必须标注来源，原因有两个：一是让用户能核实答案是否可信，
二是当模型答错时能快速定位是哪段文档误导了它。
没有来源的 RAG 回答和直接问 LLM 没有本质区别。

## 检索质量决定上限

RAG 的回答质量上限由检索质量决定。如果检索阶段没有把相关文档找出来，
生成阶段再强的模型也只能基于错误的上下文作答。
所以调优 RAG 时，应该先确认检索召回是否准确，再去优化 Prompt。

## 多轮对话的指代问题

多轮对话中用户经常用"它""这个"指代前文。RAG 链需要把对话历史一起带给模型，
模型才能理解"它"到底指什么，再据此决定这一轮该检索什么。
""", encoding="utf-8")
print(f"测试文件: {test_file}（{test_file.stat().st_size} 字节）")

pipeline = ETLPipeline(kb_name=KB_NAME)
etl_result = pipeline.run(str(test_file))
print(f"ETL 完成：{etl_result['chunks']} 个 chunk 写入知识库 '{KB_NAME}'")


# ── 2. 单次问答 ask()：互相独立的一问一答 ──────────────────────────────────────
section("2. 单次问答 ask()")

chain = RAGChain(kb_name=KB_NAME, top_k=3)
print(f"模式：{'本地降级（未配 API Key）' if chain.degraded else 'LLM 生成'}\n")

for question in [
    "RAG 系统运行时分成哪几个阶段？",
    "为什么 RAG 的回答要标注来源？",
    "调优 RAG 应该先看什么？",
]:
    result = chain.ask(question)
    print(f"问题：{question}")
    print(f"答案：{result['answer']}")
    print(f"来源：{[s['source'] for s in result['sources']]}  "
          f"| chunk 数：{result['chunks_used']}  | 耗时：{result['elapsed_s']}s")
    print("-" * 55)


# ── 3. 多轮对话 chat()：带历史，能理解指代 ─────────────────────────────────────
section("3. 多轮对话 chat()")

# 注意第二个问题用了"它"——只有把历史带上，模型才知道"它"指 RAG
turns = [
    "RAG 的回答质量由什么决定？",
    "那它（指上一轮说的那个东西）没找准会怎样？",
]
for question in turns:
    result = chain.chat(question)
    print(f"你：{question}")
    print(f"AI：{result['answer']}")
    print(f"（当前历史轮数：{len(chain.history) // 2}）")
    print("-" * 55)


# ── 4. reset()：清空历史，回到干净状态 ─────────────────────────────────────────
section("4. reset() 清空历史")

chain.reset()
print(f"reset 后历史轮数：{len(chain.history) // 2}")


# ── 5. 收尾 ────────────────────────────────────────────────────────────────────
section("Day 22 完成 ✓")
print("""
打通的链路：
    retriever.py   检索层    —— 从 pgvector 找相关 chunk
    prompts.py     模板      —— System 规则 + User 上下文拼装
    chain.py       编排层    —— ask() / chat() / ask_stream()

关键设计点：
- ask() 无状态，chat() 维护 history；history 存"干净问答"，
  检索上下文只拼进当前轮，不污染历史
- ask_stream() 产出 sources / delta / done 三类事件，给 Day 24 的 SSE 接口用
- 没有 API Key 时走本地降级模式，整条链路依然可跑、可测

下一步（Day 24-25）：FastAPI 把这条链路包成 HTTP 接口。
""")
