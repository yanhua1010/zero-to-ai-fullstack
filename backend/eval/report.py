"""
评测报告 —— 跑完一轮的结果聚合 + Markdown 渲染。

设计要点:
- 单题结果(QuestionResult)和整轮报告(EvalReport)都是 dataclass,
  方便 dict 化、序列化、单测
- 聚合属性(avg_recall 等)对 None 容忍,只对真正测到的题取平均
- to_markdown() 直接给 docs/rag-eval.md 用,可加可减,不要锁死格式

对照 Java: 这两个 dataclass 就是 ResponseDTO,渲染逻辑放进去算是
"DTO 自己懂怎么序列化",和 Java 里 Lombok @ToString 思路类似。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# ── 单题结果 ───────────────────────────────────────────────────────────────────
@dataclass
class QuestionResult:
    question_id: str
    question: str

    # 检索阶段
    retrieved_chunks: list[dict[str, Any]]   # 全字段,含 text、score、source

    # 生成阶段
    generated_answer: str
    reference_answer: str

    # 指标(None = 未测,通常是 judge 不可用或调用失败)
    recall: float                              # 召回率永远能算出来
    recall_hits: list[bool]                    # 逐条 required 是否命中
    accuracy: float | None
    accuracy_reasoning: str | None
    hallucination_rate: float | None
    hallucination_claims: list[dict] | None

    elapsed_s: float


# ── 整轮报告 ───────────────────────────────────────────────────────────────────
@dataclass
class EvalReport:
    dataset_name: str
    chain_model: str
    judge_model: str | None                    # None = judge 不可用
    chain_degraded: bool                       # chain 是否在降级模式
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    questions: list[QuestionResult] = field(default_factory=list)

    # ── 聚合 ───────────────────────────────────────────────────────────────────
    @property
    def avg_recall(self) -> float:
        if not self.questions:
            return 0.0
        return sum(q.recall for q in self.questions) / len(self.questions)

    @property
    def avg_accuracy(self) -> float | None:
        scored = [q.accuracy for q in self.questions if q.accuracy is not None]
        return (sum(scored) / len(scored)) if scored else None

    @property
    def avg_hallucination(self) -> float | None:
        scored = [q.hallucination_rate for q in self.questions if q.hallucination_rate is not None]
        return (sum(scored) / len(scored)) if scored else None

    # ── 渲染 ───────────────────────────────────────────────────────────────────
    def to_markdown(self) -> str:
        """渲染成 Markdown,直接贴进 docs/rag-eval.md 当一节。"""
        lines: list[str] = []

        # 头部
        lines.append(f"### 评测运行 - {self.timestamp}\n")
        lines.append(f"- 数据集: `{self.dataset_name}`")
        lines.append(f"- 生成模型: `{self.chain_model}`"
                     + ("(降级模式,未调真 LLM)" if self.chain_degraded else ""))
        lines.append(f"- 评判模型: " + (f"`{self.judge_model}`" if self.judge_model else "未配置(Accuracy / Hallucination 跳过)"))
        lines.append(f"- 题目数: {len(self.questions)}\n")

        # 聚合指标
        lines.append("**聚合指标:**\n")
        lines.append(f"| 指标 | 数值 |")
        lines.append(f"|------|------|")
        lines.append(f"| 平均检索召回率 | {self.avg_recall:.2%} |")
        lines.append(f"| 平均回答准确性 | {_fmt_pct(self.avg_accuracy)} |")
        lines.append(f"| 平均幻觉率(越低越好) | {_fmt_pct(self.avg_hallucination)} |")
        lines.append("")

        # 逐题明细
        lines.append("**逐题明细:**\n")
        lines.append("| ID | 召回 | 准确 | 幻觉 | 耗时 |")
        lines.append("|----|------|------|------|------|")
        for q in self.questions:
            lines.append(
                f"| {q.question_id} "
                f"| {q.recall:.0%} "
                f"| {_fmt_pct(q.accuracy)} "
                f"| {_fmt_pct(q.hallucination_rate)} "
                f"| {q.elapsed_s:.1f}s |"
            )
        lines.append("")

        # 失败题展开 —— 召回没满或准确性 < 0.6 的,提示要看一眼
        problems = [
            q for q in self.questions
            if q.recall < 1.0 or (q.accuracy is not None and q.accuracy < 0.6)
        ]
        if problems:
            lines.append("**需要重点看的题:**\n")
            for q in problems:
                lines.append(f"- `{q.question_id}` {q.question}")
                if q.recall < 1.0:
                    missed = sum(1 for h in q.recall_hits if not h)
                    lines.append(f"    - 召回未满:{missed}/{len(q.recall_hits)} 条 required_source 没命中")
                if q.accuracy is not None and q.accuracy < 0.6:
                    lines.append(f"    - 准确性 {q.accuracy:.0%},判语:{q.accuracy_reasoning}")
            lines.append("")

        return "\n".join(lines)


def _fmt_pct(v: float | None) -> str:
    """聚合指标格式化,None 显示为'未测'。"""
    return "未测" if v is None else f"{v:.2%}"
