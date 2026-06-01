"""
评测指标 —— 纯函数实现,不依赖任何外部资源。

目前只有一个指标在这里: retrieval_recall(检索召回率)。
它不需要 LLM,纯字符串和 source 匹配,在任何环境下都能跑。
这是 RAG 评测里**最重要**的指标 —— 检索没召回,后面 LLM 再强也救不回来。

LLM-as-Judge 的两个指标(answer_accuracy / hallucination_rate)
放在 judge.py 里,因为它们要调外部模型,职责不同。

对照 Java: 这就是一个纯函数 utility class(`RetrievalMetricsUtil`),
无状态、可单测、不依赖 Spring 容器或外部资源。
"""

from .dataset import RequiredSource


def retrieval_recall(
    retrieved: list[dict],
    required: list[RequiredSource],
) -> tuple[float, list[bool]]:
    """
    检索召回率:标准答案需要的来源/关键词,检索结果命中了多少。

    判定每条 required:
        retrieved 里存在某个 chunk,满足:
            chunk["source"]   == required["source"]
            AND chunk["text"] 包含 must_contain_any 中至少一个关键词

    Args:
        retrieved: PgVectorRetriever.retrieve() 的输出,
                   每项包含 source / text / score / ...
        required:  评测数据里的 required_sources 列表

    Returns:
        (recall_score, hits)
            recall_score: 命中的 required 条数 / 总 required 条数
            hits:         布尔列表,逐条对应 required,方便报告里展开看哪条没命中

    特殊情况:
        - required 为空 → 视为"不卡来源",返回 (1.0, [])
        - retrieved 为空 + required 非空 → 全部未命中,返回 (0.0, [False]*N)
    """
    if not required:
        return 1.0, []

    hits: list[bool] = []
    for req in required:
        target_source = req["source"]
        keywords = req["must_contain_any"]

        hit = any(
            chunk.get("source") == target_source
            and any(kw in chunk.get("text", "") for kw in keywords)
            for chunk in retrieved
        )
        hits.append(hit)

    score = sum(hits) / len(hits)
    return score, hits
