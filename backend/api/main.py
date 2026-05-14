"""
FastAPI 应用入口。

启动方式：
    docker compose up -d                              # 先起数据库
    uv run uvicorn backend.api.main:app --reload      # 起 API
    打开 http://localhost:8000/docs                    # 自带的交互式 API 文档

对照 Java：这个文件相当于 Spring Boot 的 Application 主类 + WebConfig，
负责创建应用、装中间件、把各个 @RestController（router）挂上去。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import chat, conversations, documents, knowledge_bases

app = FastAPI(
    title="zero-to-ai-fullstack API",
    description="RAG 知识库问答系统后端",
    version="0.1.0",
)

# CORS：开发阶段放开所有来源，方便前端联调。
# 注意 allow_origins=["*"] 不能和 allow_credentials=True 同时用（浏览器会拒绝），
# 生产环境应把 allow_origins 收紧到具体的前端域名。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 5 个业务接口所在的 router
app.include_router(knowledge_bases.router)  # GET/POST /api/knowledge-bases
app.include_router(documents.router)        # POST     /api/documents
app.include_router(chat.router)             # POST     /api/chat
app.include_router(conversations.router)    # GET      /api/conversations


@app.get("/", tags=["health"])
def health():
    """健康检查：用来确认服务起没起来。"""
    return {"status": "ok", "service": "zero-to-ai-fullstack API"}
