**中文** | [English](README.md)

# 🧠 zero-to-ai-fullstack

> 一个 Java 后端工程师学习 AI 全栈的真实历程。
> 从零开始构建一个 RAG 知识库系统——每周一步。

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-14+-black?logo=next.js)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue?logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/状态-第二周核心完成-brightgreen)

---

## 👋 这个项目适合谁

如果你是：

- **后端工程师**（Java / Go / Node），对 AI 全栈开发感兴趣
- 想搞清楚 RAG、向量数据库、LLM API 在真实项目里是怎么配合的
- 在找一条**有工程实感的学习路径**，而不是又一篇教程

……那就跟着看。这个仓库记录的不只是代码，还有每一个技术决策背后的**原因**——从一个用 Java 思维写代码的人，转向 Python + AI 全栈的视角。

---

## 🗺️ 在构建什么

一个可自托管的、基于 RAG 的知识库系统：

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

**技术栈：** Python · FastAPI · LangChain · PostgreSQL · pgvector · Next.js · Docker

---

## 📅 8 周计划

| 周次 | 重点 | 状态 |
|------|------|------|
| 第 1 周 | Python 速通 + Claude API + Prompt Engineering | ✅ 完成 |
| 第 2 周 | LangChain + Embedding + 向量检索 | ✅ 核心完成 |
| 第 3 周 | PostgreSQL + pgvector + 向量检索 | ⬜ |
| 第 4 周 | 完整 RAG Pipeline + FastAPI 后端 | ⬜ |
| 第 5 周 | RAG 优化 + 质量评测 | ⬜ |
| 第 6 周 | 在生产 SaaS 中集成 AI 功能 | ⬜ |
| 第 7 周 | Docker 部署 + CI/CD | ⬜ |
| 第 8 周 | 面试准备 + 开始投递 | ⬜ |

---

## 📓 学习日志

每周记录学了什么、踩了什么坑、和 Java 怎么对应上的。

→ [阅读完整学习日志](LEARNING_LOG.md)

**近期记录：**

- **第 1 周** — Python 上手比想象中快，不用跟缩进语法死磕。最有意思的发现是 Claude API 的多轮对话是无状态的，就像 HTTP——"记住上下文"完全靠客户端维护消息列表。[阅读 →](LEARNING_LOG.md#第一周)

---

## 📁 项目结构

```
zero-to-ai-fullstack/
├── backend/                  # Python FastAPI 服务
│   ├── etl/                  # ETL 管道
│   │   ├── extractors/       # 文档加载器（PDF、MD、TXT、HTML）
│   │   ├── transformers/     # 文本清洗与分块
│   │   └── loaders/          # 数据库写入
│   ├── rag/                  # RAG 管道
│   │   ├── embeddings/       # Embedding 模型封装
│   │   ├── retrieval/        # 向量检索 + 混合检索
│   │   └── generation/       # LLM 集成与 Prompt 管理
│   ├── api/                  # FastAPI 路由
│   ├── models/               # SQLAlchemy ORM 模型
│   └── prompts/              # Prompt 模板（版本管理）
├── frontend/                 # Next.js 前端
├── scripts/                  # 每周学习练习
│   ├── week1/                # Python 基础 + Claude API 聊天机器人
│   └── week2/                # LangChain + 文档处理管道
├── sql/                      # Alembic 迁移脚本
├── docker-compose.yml
├── .env.example
└── LEARNING_LOG.md
```

---

## 🚀 快速启动（完成后）

```bash
git clone https://github.com/yanhua1010/zero-to-ai-fullstack.git
cd zero-to-ai-fullstack
cp .env.example .env   # 填入你的 API Key
docker compose up -d
# 打开 http://localhost:3000
```

*完整部署文档将在第 7 周提供。*

---

## 💬 关于我

Java 后端工程师，8 年经验。做过分布式系统、高并发服务、数据管道——全是 Java/Spring。现在在学 AI 全栈：Python、FastAPI、RAG、pgvector、LangChain、Next.js。

感兴趣？点 **Watch** 订阅每周更新，有问题欢迎开 Issue。

→ [GitHub: @yanhua1010](https://github.com/yanhua1010)

---

## 📄 开源协议

MIT
