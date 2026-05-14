"""
知识库接口 —— 2 个：
    GET  /api/knowledge-bases   列表（带文档数）
    POST /api/knowledge-bases   创建

对照 Java：APIRouter ≈ @RestController + @RequestMapping("/api/knowledge-bases")
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.api.schemas import KnowledgeBaseCreate, KnowledgeBaseOut
from backend.models import Document, KnowledgeBase

router = APIRouter(prefix="/api/knowledge-bases", tags=["knowledge-bases"])


@router.get("", response_model=list[KnowledgeBaseOut])
def list_knowledge_bases(db: Session = Depends(get_db)):
    """所有知识库，外加每个库里的文档数。"""
    # LEFT JOIN + GROUP BY 一次查出 KB 和它的文档数，避免 N+1 查询
    rows = db.execute(
        select(KnowledgeBase, func.count(Document.id))
        .outerjoin(Document, Document.kb_id == KnowledgeBase.id)
        .group_by(KnowledgeBase.id)
        .order_by(KnowledgeBase.id)
    ).all()

    result = []
    for kb, doc_count in rows:
        item = KnowledgeBaseOut.model_validate(kb)
        item.document_count = doc_count
        result.append(item)
    return result


@router.post("", response_model=KnowledgeBaseOut, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(payload: KnowledgeBaseCreate, db: Session = Depends(get_db)):
    """创建知识库。名称重复返回 409。"""
    exists = db.query(KnowledgeBase).filter_by(name=payload.name).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"知识库 '{payload.name}' 已存在",
        )

    kb = KnowledgeBase(name=payload.name, description=payload.description)
    db.add(kb)
    db.commit()
    db.refresh(kb)  # 拿回数据库生成的 id / created_at
    return kb
