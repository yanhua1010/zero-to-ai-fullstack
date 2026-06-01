# 评测数据集

这个目录放的是人工编辑的评测语料和题集，喂给 `backend/eval/` 里的代码跑评测。

## 结构

```
evals/
├── corpus/                  # 给 RAG 系统灌库用的源文档
│   └── rag-concepts.md
└── datasets/                # 评测题集，每个 YAML 对应一份语料
    └── rag-basics.yaml
```

## YAML 数据集格式

```yaml
corpus: <对应 corpus 文件名>       # 例：rag-concepts.md

questions:
  - id: q1                       # 唯一 ID，方便指标按题展开看
    question: <要问 RAG 的问题>
    reference_answer: <人工写的标准答案>
    required_sources:            # 用来判定召回率
      - source: <文件名>
        must_contain_any:        # chunk 含其中任一关键词 = 命中
          - 关键词 A
          - 关键词 B
```

判定逻辑：检索结果里只要有一个 chunk 同时满足 source 匹配和关键词命中，
这条 `required_source` 就算被召回。该题的召回率 = 命中的 required_sources 数 / 总数。

## 怎么扩

1. 想加问题：在 `datasets/rag-basics.yaml` 里追加新的 question 条目，ID 不要冲突。
2. 想换语料：在 `corpus/` 下新建 markdown，再建一份对应的 YAML 题集，
   在 day29 脚本里指定要跑哪份。
3. 关键词的选择原则：选语义代表词，避免太生僻、太长——分块时不要被切碎。
