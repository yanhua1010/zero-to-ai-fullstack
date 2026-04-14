# RAG 系统核心概念

## 什么是 RAG

RAG（Retrieval-Augmented Generation）是一种将信息检索与大语言模型生成相结合的技术架构。
它通过在生成回答前先检索相关文档，将外部知识注入 LLM 的上下文窗口，
从而显著提升回答的准确性并减少幻觉现象。

## pgvector 的作用

pgvector 是 PostgreSQL 的向量扩展，允许在关系数据库中存储和查询高维向量。
在 RAG 系统中，pgvector 负责存储文档 chunk 的 embedding 向量，
并通过近似最近邻搜索找出与用户查询语义最相关的文档片段。

## 索引选择

HNSW 索引适合数据量小于 100 万的场景，查询速度快且无需预先大量数据。
IVFFlat 索引适合超大规模数据，内存占用更小但需要在建索引前有足够数据量。
本项目开发阶段使用 HNSW，生产扩容时可迁移到 IVFFlat。

## ETL 管道设计

ETL 管道分为三层：Extract 负责读取原始文档，Transform 负责分块和向量化，
Load 负责将结果持久化到 PostgreSQL。三层职责清晰，互不干扰。
