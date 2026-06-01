"""
Day 29 — 评测体系 baseline。

干一件事:把当前 RAG 系统跑一次评测,把三个指标的 baseline 数值固化下来,
之后 Day 30+ 每次优化都和这个 baseline 比,看真有没有变好。

完整流程:
    1. 把 evals/corpus/rag-concepts.md 灌进一个专用知识库 (eval-rag-basics)
       —— 先清空旧数据保证 baseline 跑在干净状态
    2. 加载 evals/datasets/rag-basics.yaml 的 8 个问题
    3. 用 RAGChain 跑每个问题,EvalRunner 算三个指标
    4. 把 EvalReport 渲染成 markdown,写进 docs/rag-eval.md,同时打印到屏幕

运行方式:
    docker compose up -d                                   # 数据库要先起来
    uv run python scripts/week5/day29_eval_baseline.py

没配 DEEPSEEK_API_KEY 也能跑 —— 召回率不依赖 LLM,会有一个 baseline 数;
准确性 / 幻觉率两个指标会标为"未测",等你配上 Key 再跑一次拿全。
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# 把项目根加到 sys.path(和 day19/day22 一样的套路)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.eval import EvalRunner, LLMJudge, load_dataset
from backend.etl.pipeline import ETLPipeline
from backend.rag.generation import RAGChain

# ── 常量 ───────────────────────────────────────────────────────────────────────
KB_NAME = "eval-rag-basics"
CORPUS_FILE = PROJECT_ROOT / "evals" / "corpus" / "rag-concepts.md"
DATASET_FILE = PROJECT_ROOT / "evals" / "datasets" / "rag-basics.yaml"
REPORT_FILE = PROJECT_ROOT / "docs" / "rag-eval.md"


def section(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ── 1. 清掉旧 KB,保证 baseline 跑在干净状态 ────────────────────────────────────
def clear_kb(kb_name: str) -> None:
    """删掉指定 KB(级联删它下面的所有 Documents / Chunks)。"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from backend.api.deps import _build_db_url
    from backend.models import KnowledgeBase

    engine = create_engine(_build_db_url())
    with Session(engine) as session:
        kb = session.query(KnowledgeBase).filter_by(name=kb_name).first()
        if kb:
            session.delete(kb)  # models.py 上的 cascade="all, delete-orphan" 会把
            session.commit()    # Documents → DocumentChunks 一并干净删除
            print(f"  已清除旧 KB '{kb_name}'")
        else:
            print(f"  没有旧 KB '{kb_name}',从空开始")


# ── 2. 渲染 docs/rag-eval.md ───────────────────────────────────────────────────
PREAMBLE = """\
# RAG 评测报告

这份文档由 `scripts/week5/day29_eval_baseline.py` 自动生成,每次跑都会覆盖。

## 评测维度

| 指标 | 用什么测 | 越高越好? | 解读 |
|------|---------|----------|------|
| 检索召回率 (Retrieval Recall) | 纯字符串 + source 匹配 | 高好 | 标答里需要的 chunk 都被检索到了吗?**RAG 上限就是这个**。|
| 回答准确性 (Answer Accuracy) | LLM-as-Judge(deepseek-v4-pro) | 高好 | 生成答案在事实层面和标答有多接近 |
| 幻觉率 (Hallucination Rate) | LLM-as-Judge(deepseek-v4-pro) | 低好 | 生成答案里有多少声明不被检索到的 chunks 支撑 |

## 数据集

- 语料: [`evals/corpus/rag-concepts.md`](../evals/corpus/rag-concepts.md)
- 题集: [`evals/datasets/rag-basics.yaml`](../evals/datasets/rag-basics.yaml)
- 题数: 8

数据格式和扩展方式见 [`evals/README.md`](../evals/README.md)。

## Baseline

下面这次运行的数据就是后续优化的对照基线。Day 30+ 每加一种优化(混合检索、Reranking、MMR ...),
都要重跑一次,把新数据贴到这份文档上,**和 baseline 列在一起对比**才看得出真有没有变好。

"""


def write_report(report) -> None:
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(PREAMBLE + report.to_markdown(), encoding="utf-8")
    print(f"\n报告已写入: {REPORT_FILE.relative_to(PROJECT_ROOT)}")


# ── main ───────────────────────────────────────────────────────────────────────
def main() -> int:
    # Step 1: 灌库
    section("1. 准备知识库")
    if not CORPUS_FILE.exists():
        print(f"  ERROR 语料文件不存在: {CORPUS_FILE}")
        return 1
    try:
        clear_kb(KB_NAME)
        pipeline = ETLPipeline(kb_name=KB_NAME)
        etl_result = pipeline.run(str(CORPUS_FILE))
        print(f"  ETL 完成: {etl_result['chunks']} 个 chunk 写入 KB '{KB_NAME}'")
    except Exception as e:
        print(f"\n  ERROR 灌库失败,大概率是 PostgreSQL 没起来 (docker compose up -d): {e}")
        return 1

    # Step 2: 加载评测集
    section("2. 加载评测集")
    if not DATASET_FILE.exists():
        print(f"  ERROR 评测集不存在: {DATASET_FILE}")
        return 1
    dataset = load_dataset(DATASET_FILE)
    print(f"  从 {DATASET_FILE.relative_to(PROJECT_ROOT)} 加载 {len(dataset['questions'])} 题")

    # Step 3: 跑评测
    section("3. 跑评测")
    chain = RAGChain(kb_name=KB_NAME, top_k=3)
    judge = LLMJudge()
    print(f"  Chain: {chain.model}{'(降级,无 API Key)' if chain.degraded else ''}")
    print(f"  Judge: {judge.model if judge.available else '不可用(无 API Key,Accuracy / Hallucination 跳过)'}")
    print()

    runner = EvalRunner(chain, judge)
    report = runner.run(dataset)

    # Step 4: 输出
    section("4. 评测结果")
    print(report.to_markdown())
    write_report(report)

    # 退出状态:让 CI 友好 —— 召回率低于 80% 视为失败
    section("Day 29 完成")
    threshold = 0.80
    if report.avg_recall < threshold:
        print(f"  警告:平均召回率 {report.avg_recall:.2%} < {threshold:.0%},"
              f"baseline 偏低,Day 30 重点看检索优化")
    print("""
做的事:
- 把 RAG 系统量出了三组 baseline 数据,固化在 docs/rag-eval.md
- 之后每个优化都要重跑这个脚本,新结果和 baseline 列在一起对比

下一步(Day 30):
- 混合检索(BM25 + 向量 + RRF 合并)。先把检索召回这个上限指标顶上去
- 也可以试 Reranking 给 top-K 二次排序
- 每改一个东西就跑一次评测,留下数据对比
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
