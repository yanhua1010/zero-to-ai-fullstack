"""
FastAPI 依赖（dependencies）—— 目前只有数据库 session。

对照 Spring：
- engine / SessionLocal  相当于 DataSource + EntityManagerFactory（应用启动时建一次）
- get_db()               相当于把 EntityManager 注入进 Controller，
                         请求开始时拿、请求结束时还，事务边界交给框架

注意：create_engine 是惰性的，导入这个模块不会真的去连数据库，
第一次执行 SQL 时才建立连接。所以没起数据库也能 import 整个 api 包。
"""

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def _build_db_url() -> str:
    """从环境变量拼数据库连接串（和 loaders.py / retriever.py 保持一致）。"""
    return (
        f"postgresql+psycopg2://"
        f"{os.getenv('POSTGRES_USER', 'postgres')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'knowledge_base')}"
    )


# 应用级单例：整个进程共用一个连接池
engine = create_engine(_build_db_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """
    每个请求一个 session，请求结束自动关闭。

    这是 FastAPI 里最经典的 "yield 依赖"：yield 之前是"请求开始"的逻辑，
    yield 之后（finally）是"请求结束"的清理。框架保证 finally 一定会跑。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
