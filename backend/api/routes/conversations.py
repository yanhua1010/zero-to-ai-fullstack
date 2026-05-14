"""
历史对话接口 —— 1 个：
    GET /api/conversations   查历史问答，可按知识库过滤
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.api.schemas import ConversationOut
from backend.models import Conversation, KnowledgeBase

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
def list_conversations(
    kb_name: str | None = Query(default=None, description="按知识库名过滤，不传则返回全部"),
    limit: int = Query(default=20, ge=1, le=100, description="最多返回多少条"),
    db: Session = Depends(get_db),
):
    """按时间倒序返回历史对话。"""
    stmt = (
        select(Conversation)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
    )
    if kb_name:
        stmt = stmt.join(
            KnowledgeBase, KnowledgeBase.id == Conversation.kb_id
        ).where(KnowledgeBase.name == kb_name)

    return db.execute(stmt).scalars().all()
