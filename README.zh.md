**中文** | [English](README.md)

# zero-to-ai-fullstack

一个 Java 后端工程师学习 AI 全栈的记录。从零搭一个 RAG 知识库系统，每周推进一步。

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-14+-black?logo=next.js)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue?logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 这个项目适合谁

如果你是后端工程师（Java / Go / Node），想搞清楚 RAG、向量数据库、LLM API 在真实项目里是怎么配合的，这个仓库可以参考。它记录的不只是代码，还有每个技术决策背后的原因，以及一个习惯了 Java 思维的人转向 Python + AI 全栈时的视角。

---

## 在构建什么

一个可自托管的 RAG 知识库系统：上传文档、提问、得到带来源引用的回答。

```
┌─────────────────────────────────────────────┐
│              Next.js 前端                    │
│    文档上传 · 知识库管理 · 对话问答 · 引用来源  │
└──────────────────┬──────────────────────────┘
                   │ REST API / SSE
┌──────────────────┴──────────────────────────┐
│            Python 后端（FastAPI）             │
│   ETL 管道 · RAG 引擎 · LLM 路由             │
└────┬─────────────────┬───────────────────┬──┘
     │                 │                   │
┌────┴─────┐   ┌───────┴──────┐   ┌────────┴───┐
│PostgreSQL│   │   pgvector   │   │  LLM API   │
│ 元数据   │   │  向量存储    │   │ Claude/GPT │
└──────────┘   └──────────────┘   └────────────┘
```

技术栈：Python · FastAPI · LangChain · PostgreSQL · pgvector · Next.js · Docker

---

## 8 周计划

| 周次 | 重点 | 状态 |
|------|------|------|
| 第 1 周 | Python 速通 + Claude API + Prompt Engineering | 完成 |
| 第 2 周 | LangChain + Embedding + 向量检索 | 完成 |
| 第 3 周 | PostgreSQL + pgvector + 向量检索 | 完成 |
| 第 4 周 | 完整 RAG Pipeline + FastAPI 后端 | 完成 |
| 第 5 周 | RAG 优化 + 质量评测 | 待开始 |
| 第 6 周 | 在生产 SaaS 中集成 AI 功能 | 待开始 |
| 第 7 周 | Docker 部署 + CI/CD | 待开始 |
| 第 8 周 | 面试准备 + 开始投递 | 待开始 |

---

## 学习日志

每周记录学了什么、哪里卡住了、和 Java 怎么对应上。

→ [完整学习日志](LEARNING_LOG.md)

最近一周（第 3 周）：pgvector 说到底就两件事，把向量存进 Postgres，用 `<=>` 找最近邻。真正的坑是 embedding 一致性，查询向量和文档向量必须来自同一个实例，否则余弦距离没有意义。这个 bug 是自己排查出来的。

---

## 项目结构

```
zero-to-ai-fullstack/
├── backend/                  # Python FastAPI 服务
│   ├── etl/                  # ETL 管道
│   │   ├── extractors/       # 文档加载器（PDF、MD、TXT、HTML）
│   │   ├── transformers/     # 文本清洗与分块
│   │   └── loaders/          # 数据库写入
│   ├── rag/                  # RAG 管道
│   │   ├── embeddings/       # Embedding 模型封装
│   │   ├── retrieval/        # 向量检索
│   │   └── generation/       # RAG Chain、LLM 集成与 Prompt 管理
│   ├── api/                  # FastAPI 路由
│   ├── models/               # SQLAlchemy ORM 模型
│   └── prompts/              # Prompt 模板（版本管理）
├── frontend/                 # Next.js 前端
├── scripts/                  # 每周学习练习
│   ├── week1/                # Python 基础 + Claude API 聊天机器人
│   ├── week2/                # LangChain + 文档处理管道
│   ├── week3/                # PostgreSQL + pgvector + 检索
│   └── week4/                # RAG Chain 端到端演示
├── sql/                      # Alembic 迁移脚本
├── docker-compose.yml
├── .env.example
└── LEARNING_LOG.md
```

---

## 快速启动

后端目前已经能跑起来：

```bash
git clone https://github.com/yanhua1010/zero-to-ai-fullstack.git
cd zero-to-ai-fullstack
cp .env.example .env        # 填入 API Key，不填则用本地降级模式

docker compose up -d        # 启动 PostgreSQL + pgvector

uv sync                                          # 安装依赖
uv run uvicorn backend.api.main:app --reload     # 启动 API，文档在 http://localhost:8000/docs
uv run pytest backend/                           # 跑测试
```

安装 uv：`curl -LsSf https://astral.sh/uv/install.sh | sh`

前端和完整的容器化部署在第 7 周。

---

## 关于

Java 后端工程师，8 年经验，做过分布式系统、高并发服务、数据管道，技术栈一直是 Java/Spring。现在在学 AI 全栈。

有问题可以开 Issue。

→ [GitHub: @yanhua1010](https://github.com/yanhua1010)

---

## 开源协议

MIT
