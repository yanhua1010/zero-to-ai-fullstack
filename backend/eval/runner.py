"""
EvalRunner —— 评测编排层。

把 dataset / chain / judge 串起来跑完一轮,产出 EvalReport。
自己不算指标也不调 LLM,只是按顺序串各个组件,聚合成报告。

对照 Java: 这就是 @Service 编排层。
"""

import logging
import time

from backend.eval.dataset import Dataset, Question
from backend.eval.judge import LLMJudge
from backend.eval.metrics import retrieval_recall
from backend.eval.report import EvalReport, QuestionResult
from backend.rag.generation.chain import RAGChain

logger = logging.getLogger(__name__)


class EvalRunner:
    def __init__(self, chain: RAGChain, judge: LLMJudge | None = None):
        """
        Args:
            chain:  被评测的 RAG 链。它的检索 / 生成行为就是被量的对象。
            judge:  评判模型。不传则默认创建一个,可能 unavailable(无 API Key 时)。
        """
        self.chain = chain
        self.judge = judge or LLMJudge()

    def run(self, dataset: Dataset) -> EvalReport:
        """跑完整个数据集,产出一份报告。"""
        logger.info(
            f"[EvalRunner] 开始评测: {len(dataset['questions'])} 题,"
            f"chain={self.chain.model}{'(降级)' if self.chain.degraded else ''},"
            f"judge={'可用' if self.judge.available else '不可用'}"
        )

        report = EvalReport(
            dataset_name=dataset["corpus"],
            chain_model=self.chain.model,
            judge_model=self.judge.model if self.judge.available else None,
            chain_degraded=self.chain.degraded,
        )

        for i, q in enumerate(dataset["questions"], 1):
            logger.info(f"[EvalRunner] ({i}/{len(dataset['questions'])}) 跑 {q['id']}: {q['question']}")
            report.questions.append(self._run_one(q))

        logger.info(
            f"[EvalRunner] 完成。平均召回 {report.avg_recall:.2%},"
            f"平均准确性 {('未测' if report.avg_accuracy is None else f'{report.avg_accuracy:.2%}')},"
            f"平均幻觉率 {('未测' if report.avg_hallucination is None else f'{report.avg_hallucination:.2%}')}"
        )
        return report

    # ── 单题流程 ──────────────────────────────────────────────────────────────
    def _run_one(self, q: Question) -> QuestionResult:
        t0 = time.time()

        # 1. 跑一次 RAG。chain.ask() 返回的 dict 同时带 sources(轻)和 chunks(完整带正文),
        #    评测要用 chunks 做幻觉判定,所以拿 chunks。
        result = self.chain.ask(q["question"])
        retrieved_chunks = result["chunks"]
        generated = result["answer"]

        # 2. 检索召回率(纯函数,无 LLM 依赖,永远能算)
        recall, hits = retrieval_recall(retrieved_chunks, q.get("required_sources", []))

        # 3. 回答准确性(LLM-as-Judge,judge 不可用时返回 None)
        acc = self.judge.score_answer(q["question"], generated, q["reference_answer"])

        # 4. 幻觉率(LLM-as-Judge)
        hall = self.judge.score_hallucination(generated, retrieved_chunks)

        return QuestionResult(
            question_id=q["id"],
            question=q["question"],
            retrieved_chunks=retrieved_chunks,
            generated_answer=generated,
            reference_answer=q["reference_answer"],
            recall=recall,
            recall_hits=hits,
            accuracy=acc["score"],
            accuracy_reasoning=acc.get("reasoning"),
            hallucination_rate=hall["rate"],
            hallucination_claims=hall.get("claims"),
            elapsed_s=round(time.time() - t0, 2),
        )
