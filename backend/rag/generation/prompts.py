"""
Prompt 模板 — RAG 问答专用

RAG 的 Prompt 设计只有两件事：
1. 告诉 LLM 它的角色和约束（System Prompt）
2. 把检索到的文档 + 用户问题拼装成 User 消息

把 Prompt 单独放一个文件而不是散落在业务代码里，
原因和把 SQL 放 Repository 层一样：集中管理、容易替换、方便 review。
"""

# ── System Prompt ─────────────────────────────────────────────────────────────
#
# 核心约束只有一条：只能用提供的文档回答，不知道就说不知道。
# 这是避免 LLM "幻觉"的最直接手段——把允许回答的边界明确写出来。
#
RAG_SYSTEM_PROMPT = """\
你是一个专业的知识库问答助手。

规则：
1. 只能基于下方"参考文档"中的内容回答问题
2. 如果参考文档中没有相关信息，直接回答"根据现有文档，我无法找到相关信息"
3. 回答时引用来源（格式：【来源: 文件名】）
4. 保持回答简洁，聚焦用户问题，不要添加文档中没有的内容
5. 多轮对话中，结合上下文理解问题的指代关系\
"""

# ── User 消息模板 ──────────────────────────────────────────────────────────────
#
# 结构：参考文档区 + 分隔线 + 用户问题
# 把"上下文"放 User 消息而不是 System 消息，原因：
# - 每轮对话上下文不同（每次检索结果不同）
# - System Prompt 是静态的全局规则，不适合放动态内容
#
RAG_USER_TEMPLATE = """\
参考文档：
{context}

---

问题：{question}\
"""

# ── 上下文格式化 ───────────────────────────────────────────────────────────────


def format_context(chunks: list[dict]) -> str:
    """
    把检索到的 chunk 列表格式化为 LLM 可读的上下文字符串。

    格式：
        [来源 1: filename.md（相关度: 0.12）]
        chunk 内容...

        [来源 2: ...]
        ...

    score 是余弦距离（越小越相关），显示给 LLM 是为了让它知道哪个更权威。
    """
    if not chunks:
        return "（当前知识库中没有找到相关文档）"

    parts = []
    for i, chunk in enumerate(chunks, 1):
        source_label = f"[来源 {i}: {chunk['source']}（相关度: {chunk['score']:.2f}）]"
        parts.append(f"{source_label}\n{chunk['text']}")

    return "\n\n".join(parts)


def build_user_message(question: str, chunks: list[dict]) -> str:
    """组装完整的 user 消息：上下文 + 问题。"""
    context = format_context(chunks)
    return RAG_USER_TEMPLATE.format(context=context, question=question)
