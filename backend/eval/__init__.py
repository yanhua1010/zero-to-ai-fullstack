"""
RAG 评测模块 —— 给检索增强生成系统装一把尺子。

三个指标:
    retrieval_recall    检索召回率（纯字符串匹配，无 LLM 依赖）
    answer_accuracy     回答准确性（LLM-as-Judge）
    hallucination_rate  幻觉率（LLM-as-Judge）

入口:
    >>> from backend.eval import EvalRunner, LLMJudge, load_dataset
    >>> from backend.rag.generation import RAGChain
    >>> dataset = load_dataset("evals/datasets/rag-basics.yaml")
    >>> runner = EvalRunner(RAGChain(kb_name="eval-rag-basics"), LLMJudge())
    >>> report = runner.run(dataset)
    >>> print(report.to_markdown())
"""

from .dataset import Dataset, Question, RequiredSource, load_dataset
from .judge import LLMJudge
from .metrics import retrieval_recall
from .report import EvalReport, QuestionResult
from .runner import EvalRunner

__all__ = [
    "Dataset",
    "Question",
    "RequiredSource",
    "load_dataset",
    "LLMJudge",
    "retrieval_recall",
    "EvalReport",
    "QuestionResult",
    "EvalRunner",
]
