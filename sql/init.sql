-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 知识库表
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 文档表（原始文档，不含向量）
CREATE TABLE IF NOT EXISTS documents (
    id          SERIAL PRIMARY KEY,
    kb_id       INTEGER      REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    title       VARCHAR(500),
    source_type VARCHAR(50)  NOT NULL,          -- pdf / md / txt / url
    content     TEXT         NOT NULL,
    metadata    JSONB        NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 文档分块表（含向量）
CREATE TABLE IF NOT EXISTS document_chunks (
    id          SERIAL PRIMARY KEY,
    document_id INTEGER      NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER      NOT NULL,
    chunk_text  TEXT         NOT NULL,
    token_count INTEGER,
    metadata    JSONB        NOT NULL DEFAULT '{}',
    embedding   vector(1536),                   -- OpenAI text-embedding-3-small 维度
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 对话记录表
CREATE TABLE IF NOT EXISTS conversations (
    id              SERIAL PRIMARY KEY,
    kb_id           INTEGER  REFERENCES knowledge_bases(id) ON DELETE SET NULL,
    query           TEXT     NOT NULL,
    response        TEXT     NOT NULL,
    sources         JSONB    NOT NULL DEFAULT '[]',  -- [{chunk_id, score, text}]
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 向量检索索引（Week 3 Day 18 会详细讲，先建上）
-- HNSW 索引：查询快，适合生产
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
    ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- JSONB 索引：加速 metadata 字段过滤
CREATE INDEX IF NOT EXISTS idx_documents_metadata
    ON documents USING gin (metadata);
