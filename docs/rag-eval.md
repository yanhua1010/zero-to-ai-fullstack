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

### 评测运行 - 2026-06-01T18:10:50

- 数据集: `rag-concepts.md`
- 生成模型: `deepseek-v4-flash`
- 评判模型: `deepseek-v4-pro`
- 题目数: 8

**聚合指标:**

| 指标 | 数值 |
|------|------|
| 平均检索召回率 | 100.00% |
| 平均回答准确性 | 93.75% |
| 平均幻觉率(越低越好) | 0.00% |

**逐题明细:**

| ID | 召回 | 准确 | 幻觉 | 耗时 |
|----|------|------|------|------|
| q1 | 100% | 100.00% | 未测 | 27.5s |
| q2 | 100% | 90.00% | 未测 | 36.8s |
| q3 | 100% | 100.00% | 0.00% | 15.9s |
| q4 | 100% | 80.00% | 0.00% | 36.5s |
| q5 | 100% | 80.00% | 未测 | 43.0s |
| q6 | 100% | 100.00% | 未测 | 17.8s |
| q7 | 100% | 100.00% | 0.00% | 17.6s |
| q8 | 100% | 100.00% | 未测 | 27.4s |
