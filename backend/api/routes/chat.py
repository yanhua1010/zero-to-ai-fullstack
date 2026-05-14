"""
问答接口 —— 1 个：
    POST /api/chat   RAG 问答，SSE 流式返回

SSE（Server-Sent Events）：服务端用一个长连接，持续往客户端推 `data: ...\n\n`，
直到流结束。比起一次性返回，前端能"边生成边显示"，体验接近 ChatGPT。

这个接口里有一个和普通接口不一样的坑，见 _persist_conversation 的注释。
"""

import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.api.deps import engine
from backend.api.schemas import ChatRequest
from backend.models import Conversation, KnowledgeBase
from backend.rag.generation import RAGChain

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
def chat(payload: ChatRequest):
    """
    RAG 问答，流式返回。

    返回的事件流（每行一个 `data: {json}`）：
        {"type": "sources", "sources": [...]}    先把检索来源推过去
        {"type": "delta",   "text": "..."}       LLM 逐段吐的文本
        {"type": "done",    "answer": ..., ...}  收尾，带完整结果

    流结束后，把这轮问答写进 conversations 表。
    """
    chain = RAGChain(kb_name=payload.kb_name, top_k=payload.top_k)

    def event_stream():
        answer_parts: list[str] = []
        sources: list = []
        try:
            for event in chain.ask_stream(payload.question):
                if event["type"] == "sources":
                    sources = event["sources"]
                elif event["type"] == "delta":
                    answer_parts.append(event["text"])
                # 每个事件序列化成一行 SSE。ensure_ascii=False 让中文不被转义
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        finally:
            # 不管正常结束还是中途断开，都尝试把已生成的内容落库
            _persist_conversation(payload, "".join(answer_parts), sources)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _persist_conversation(payload: ChatRequest, answer: str, sources: list) -> None:
    """
    把一轮问答写进 conversations 表。

    为什么这里自己开 session、不用 Depends(get_db)：
    StreamingResponse 的生成器是在路由函数 return *之后* 才被消费的，
    那时候 get_db() 这种"请求级"依赖可能已经被框架清理掉了。
    所以流式接口里涉及 DB 的收尾动作，session 要自己管。
    """
    if not answer:
        return
    try:
        with Session(engine) as db:
            kb = db.query(KnowledgeBase).filter_by(name=payload.kb_name).first()
            db.add(Conversation(
                kb_id=kb.id if kb else None,
                query=payload.question,
                response=answer,
                sources=sources,
            ))
            db.commit()
    except Exception:
        # 落库失败不应该影响已经返回给用户的答案，记日志即可
        logger.exception("[API] 对话历史落库失败")
