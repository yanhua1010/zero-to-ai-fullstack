"""
Pydantic 模型 —— API 的请求体 / 响应体定义。

对照 Java：这就是 DTO 层。和 SQLAlchemy 的 ORM Model（backend/models）分开，
原因和 Java 里 Entity 与 DTO 要分开一样：
- ORM Model 贴着数据库表结构
- Schema 贴着 API 契约，可以裁剪字段、改名、加校验

ConfigDict(from_attributes=True) = 允许直接拿 ORM 对象来构造（类似 MapStruct 的作用）。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── 知识库 ─────────────────────────────────────────────────────────────────────
class KnowledgeBaseCreate(BaseModel):
    """POST /api/knowledge-bases 的请求体。"""
    name: str = Field(..., min_length=1, max_length=255, description="知识库名称，唯一")
    description: str | None = Field(default=None, description="可选描述")


class KnowledgeBaseOut(BaseModel):
    """知识库的响应体。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    created_at: datetime
    document_count: int = 0  # 该知识库下的文档数，由 list 接口聚合填充


# ── 文档上传 ───────────────────────────────────────────────────────────────────
class DocumentUploadOut(BaseModel):
    """POST /api/documents 的响应体（ETL 跑完的结果）。"""
    kb_name: str
    file: str
    documents: int      # 提取出的原始文档数
    chunks: int         # 分块数
    loaded: int         # 成功写入 DB 的 chunk 数
    elapsed_s: float


# ── 问答 ───────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    """POST /api/chat 的请求体。"""
    kb_name: str = Field(..., description="在哪个知识库里问")
    question: str = Field(..., min_length=1, description="用户问题")
    top_k: int = Field(default=3, ge=1, le=20, description="检索取多少个 chunk")


# ── 历史对话 ───────────────────────────────────────────────────────────────────
class ConversationOut(BaseModel):
    """GET /api/conversations 的响应体。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    kb_id: int | None = None
    query: str
    response: str
    sources: list[Any] = []
    created_at: datetime
