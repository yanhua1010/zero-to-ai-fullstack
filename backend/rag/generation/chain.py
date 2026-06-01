"""
RAGChain — RAG 管道的"生成层 + 编排层"

把前面两块拼起来：
    PgVectorRetriever（检索）  →  prompts（拼 Prompt）  →  DeepSeek API（生成）

对照 Java：retriever 是 @Repository，prompts 是模板，
RAGChain 就是 @Service —— 它不自己干活，而是把各层"编排"成一个完整业务流程。

设计要点：
- ask()  单次问答，无历史，每次都是干净的一问一答
- chat() 多轮对话，维护 self.history，能理解"它/这个"之类的指代
- ask_stream() 流式输出，给 FastAPI 的 SSE 接口用
- 没配 DEEPSEEK_API_KEY 时自动进入"本地降级模式"：
  不调用 LLM，直接把检索结果拼成答案返回。
  这样测试 / 离线环境也能跑通整条链路（和 TextTransformer 的本地降级是同一个思路）。

LLM 选型说明：
- DeepSeek API 是 OpenAI 格式兼容的，用 `openai` SDK + 修改 base_url 调用
- 默认走 deepseek-v4-flash（便宜快）。要更高质量改成 deepseek-v4-pro
- 老模型名 deepseek-chat / deepseek-reasoner 会在 2026-07-24 弃用，别再用了
"""

import logging
import os
import time
from collections.abc import Iterator
from typing import Any

from backend.rag.retrieval.retriever import PgVectorRetriever
from backend.rag.generation.prompts import (
    RAG_SYSTEM_PROMPT,
    build_user_message,
    format_context,
)

logger = logging.getLogger(__name__)

# 默认模型用 DeepSeek 的便宜快档（v4-flash）。要更高质量改 deepseek-v4-pro。
# 自建代理可以通过 DEEPSEEK_BASE_URL 覆盖；不设的话走官方 https://api.deepseek.com
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_BASE_URL = "https://api.deepseek.com"
MAX_TOKENS = 1024


def _api_key_available() -> bool:
    """判断是否配置了可用的 API Key。占位符值（.env.example 里的默认文案）视为未配置。"""
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    placeholders = {"", "your_deepseek_api_key_here", "sk-..."}
    return key not in placeholders


class RAGChain:
    """
    一条完整的 RAG 问答链。

    用法：
        chain = RAGChain(kb_name="week3-demo")
        result = chain.ask("什么是 RAG？")
        print(result["answer"])

    每个返回的 dict 结构统一为：
        {
            "question":    str,        # 原始问题
            "answer":      str,        # LLM（或降级模式）生成的答案
            "sources":     list[dict], # 检索命中的 chunk（含 source / score）
            "chunks_used": int,        # 实际喂给 LLM 的 chunk 数
            "model":       str,        # 用的模型名（降级模式为 "local-degraded"）
            "degraded":    bool,       # 是否走了本地降级模式
            "elapsed_s":   float,      # 本次问答耗时
        }
    """

    def __init__(
        self,
        kb_name: str,
        model: str = DEFAULT_MODEL,
        top_k: int = 3,
        db_url: str | None = None,
        max_score: float | None = None,
    ):
        """
        Args:
            kb_name:   在哪个知识库里检索
            model:     LLM 模型名
            top_k:     每次检索取多少个 chunk
            db_url:    数据库连接串，默认从环境变量拼
            max_score: 余弦距离上限。设了的话，超过阈值的 chunk 会被丢弃
                       （用 retrieve_with_score_filter）；不设则不过滤。
        """
        self.kb_name = kb_name
        self.model = model
        self.max_score = max_score
        self.retriever = PgVectorRetriever(kb_name, top_k=top_k, db_url=db_url)

        # 多轮对话的历史。结构：[{"role": "user"/"assistant", "content": str}, ...]
        # 注意：这里存的是"干净"的原始问答，不含检索拼进去的上下文（见 chat() 的说明）
        self.history: list[dict[str, str]] = []

        # 懒加载的 OpenAI 客户端（指向 DeepSeek）。没 Key 就一直是 None，走降级模式。
        self._client = None
        self.degraded = not _api_key_available()
        if self.degraded:
            logger.warning(
                "[RAGChain] 未检测到 DEEPSEEK_API_KEY，进入本地降级模式"
                "（只检索、不调用 LLM）"
            )

    # ── 客户端懒加载 ──────────────────────────────────────────────────────────
    def _get_client(self):
        """
        第一次用到时才创建 OpenAI 客户端（DeepSeek 走 OpenAI 兼容协议）。

        对照 Java：相当于 Spring 的懒加载 Bean —— 不用就不初始化，
        避免在降级模式 / 测试环境里白白要求依赖就位。
        """
        if self._client is None:
            from openai import OpenAI  # 局部导入：降级模式下根本不需要这个包

            self._client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url=os.getenv("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL,
            )
        return self._client

    # ── 检索 ──────────────────────────────────────────────────────────────────
    def _retrieve(self, question: str) -> list[dict[str, Any]]:
        """按是否设了 max_score，选择普通检索还是带过滤的检索。"""
        if self.max_score is not None:
            return self.retriever.retrieve_with_score_filter(
                question, max_score=self.max_score
            )
        return self.retriever.retrieve(question)

    # ── 生成（非流式）─────────────────────────────────────────────────────────
    def _generate(
        self, messages: list[dict[str, str]]
    ) -> str:
        """
        调用 LLM 生成答案。messages 是 user/assistant 的对话消息列表。

        和 Anthropic SDK 的关键区别：OpenAI 格式里 system 不是顶层参数，
        而是 messages 数组里 role="system" 的第一条。这里在最前面拼上。
        """
        client = self._get_client()
        api_messages = [
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            *messages,
        ]
        resp = client.chat.completions.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            messages=api_messages,
        )
        # OpenAI 返回结构：resp.choices[0].message.content 直接拿文本
        return resp.choices[0].message.content or ""

    def _degraded_answer(self, question: str, chunks: list[dict[str, Any]]) -> str:
        """
        降级模式的"答案"：不生成，只是把检索结果摊开给用户看。

        目的不是给好答案，而是让整条链路在没有 API Key 时也能跑通、能测。
        """
        if not chunks:
            return "（本地降级模式）根据现有文档，我无法找到相关信息。"
        return (
            "（本地降级模式：未配置 DEEPSEEK_API_KEY，以下为检索到的原文，未经 LLM 总结）\n\n"
            + format_context(chunks)
        )

    # ── 对外：单次问答 ────────────────────────────────────────────────────────
    def ask(self, question: str) -> dict[str, Any]:
        """
        单次问答：检索 → 拼 Prompt → 生成。不读也不写 self.history。

        适合"互相独立的一问一答"场景，比如 FastAPI 的无状态接口。
        """
        t0 = time.time()
        chunks = self._retrieve(question)
        logger.info(f"[RAGChain.ask] 问题={question!r}，检索到 {len(chunks)} 个 chunk")

        user_msg = build_user_message(question, chunks)

        if self.degraded:
            answer = self._degraded_answer(question, chunks)
        else:
            answer = self._generate([{"role": "user", "content": user_msg}])

        return self._build_result(question, answer, chunks, t0)

    # ── 对外：多轮对话 ────────────────────────────────────────────────────────
    def chat(self, question: str) -> dict[str, Any]:
        """
        多轮对话：在 ask() 的基础上带上历史，让 LLM 能理解指代关系。

        历史管理的关键设计 —— self.history 里存的是"干净的原始问答"，
        不是"拼了检索上下文的消息"。原因：
        - 检索上下文每轮都不同，是临时的，没必要塞进历史里反复带着跑
        - 只有"当前这一轮"的问题需要 RAG 上下文；历史轮次只需保留问答本身，
          供 LLM 理解"它指的是什么"
        所以：发给 API 的 messages = 历史（干净）+ 当前轮（带检索上下文）
             存回 history 的是：当前轮的"干净问题" + LLM 答案
        """
        t0 = time.time()
        chunks = self._retrieve(question)
        logger.info(
            f"[RAGChain.chat] 问题={question!r}，检索到 {len(chunks)} 个 chunk，"
            f"历史轮数={len(self.history) // 2}"
        )

        user_msg = build_user_message(question, chunks)
        # 历史（干净）+ 当前轮（带上下文）
        api_messages = self.history + [{"role": "user", "content": user_msg}]

        if self.degraded:
            answer = self._degraded_answer(question, chunks)
        else:
            answer = self._generate(api_messages)

        # 存回历史：注意存的是原始 question，不是 user_msg
        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": answer})

        return self._build_result(question, answer, chunks, t0)

    def reset(self) -> None:
        """清空多轮对话历史。对照 chatbot.py 里的 'clear' 命令。"""
        self.history.clear()
        logger.info("[RAGChain] 对话历史已清空")

    # ── 对外：流式问答 ────────────────────────────────────────────────────────
    def ask_stream(self, question: str) -> Iterator[dict[str, Any]]:
        """
        流式单次问答，产出一连串"事件"，给 FastAPI 的 SSE 接口用。

        事件类型（每个都是一个 dict）：
            {"type": "sources", "sources": [...]}        —— 先把检索来源发出去
            {"type": "delta",   "text": "..."}           —— LLM 逐段吐出的文本
            {"type": "done",    "answer": "...", ...}     —— 收尾，带完整结果

        为什么先发 sources：前端可以马上把"参考来源"渲染出来，
        不用等 LLM 把整段答案生成完，体验更好。
        """
        t0 = time.time()
        chunks = self._retrieve(question)
        logger.info(f"[RAGChain.ask_stream] 问题={question!r}，检索到 {len(chunks)} 个 chunk")

        # 事件 1：来源
        yield {"type": "sources", "sources": self._format_sources(chunks)}

        # 事件 2..N：文本增量
        answer_parts: list[str] = []
        if self.degraded:
            answer = self._degraded_answer(question, chunks)
            answer_parts.append(answer)
            yield {"type": "delta", "text": answer}
        else:
            user_msg = build_user_message(question, chunks)
            client = self._get_client()
            stream = client.chat.completions.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                messages=[
                    {"role": "system", "content": RAG_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                stream=True,
            )
            # OpenAI 流式：每个 chunk 是 ChatCompletionChunk，
            # 增量文本在 chunk.choices[0].delta.content（可能为 None，比如最后一条）
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    answer_parts.append(delta)
                    yield {"type": "delta", "text": delta}

        # 事件 N+1：收尾
        answer = "".join(answer_parts)
        result = self._build_result(question, answer, chunks, t0)
        yield {"type": "done", **result}

    # ── 内部：统一组装返回结构 ────────────────────────────────────────────────
    @staticmethod
    def _format_sources(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """从检索到的 chunk 里抽出"来源"信息（去掉大段正文，只留元数据）。"""
        return [
            {
                "source": c["source"],
                "source_type": c.get("source_type"),
                "score": c["score"],
                "chunk_index": c.get("chunk_index"),
            }
            for c in chunks
        ]

    def _build_result(
        self,
        question: str,
        answer: str,
        chunks: list[dict[str, Any]],
        t0: float,
    ) -> dict[str, Any]:
        # 注意 chunks 和 sources 同时返回的设计：
        # - sources 是元数据视图（轻量，FastAPI 前端用，不带正文，省带宽）
        # - chunks 是完整 chunk（带 text），评测层（backend.eval）需要拿正文做幻觉判定
        # 调用方按需选用，不重复请求 retriever。
        return {
            "question": question,
            "answer": answer,
            "sources": self._format_sources(chunks),
            "chunks": chunks,
            "chunks_used": len(chunks),
            "model": "local-degraded" if self.degraded else self.model,
            "degraded": self.degraded,
            "elapsed_s": round(time.time() - t0, 2),
        }
