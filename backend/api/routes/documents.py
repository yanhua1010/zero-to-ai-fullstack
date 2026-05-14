"""
文档上传接口 —— 1 个：
    POST /api/documents   上传文件 → 触发 ETL → 数据落库

这个接口收的是 multipart/form-data（文件 + 表单字段），不是 JSON，
所以用 UploadFile / Form 而不是 Pydantic 请求体。
"""

import logging
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from backend.api.schemas import DocumentUploadOut
from backend.etl.pipeline import ETLPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

UPLOAD_DIR = Path("data/uploads")
SUPPORTED_SUFFIXES = {".pdf", ".md", ".txt"}


@router.post("", response_model=DocumentUploadOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="待入库的文档（pdf / md / txt）"),
    kb_name: str = Form(..., description="写入哪个知识库，不存在会自动创建"),
):
    """
    上传一个文档并同步跑完整条 ETL 管道。

    流程：存盘 → ETLPipeline.run() → 返回入库统计。
    注意 ETL 是同步阻塞的；生产环境文件大时应该改成后台任务（Week 6 的话题）。
    """
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"不支持的文件类型 '{suffix or '未知'}'，仅支持 {sorted(SUPPORTED_SUFFIXES)}",
        )

    # 1. 把上传的文件落到磁盘（ETLPipeline 接收的是文件路径）
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / Path(file.filename).name
    content = await file.read()
    dest.write_bytes(content)
    logger.info(f"[API] 收到上传文件: {dest}（{len(content)} 字节），目标知识库: {kb_name}")

    # 2. 跑 ETL
    try:
        pipeline = ETLPipeline(kb_name=kb_name)
        result = pipeline.run(str(dest))
    except Exception as exc:  # ETL 内部任何一层出错都兜到这里
        logger.exception("[API] ETL 处理失败")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ETL 处理失败: {exc}",
        )

    # result 的 key 正好是 file/documents/chunks/loaded/elapsed_s，再补上 kb_name
    return DocumentUploadOut(kb_name=kb_name, **result)
