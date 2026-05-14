"""
pytest 全局配置。

两件事：
1. 把项目根目录加进 sys.path，让测试能 import backend 包
2. 提供 live_db fixture —— 需要数据库的测试依赖它，
   本地没起 Postgres（docker compose up -d）时自动跳过，不让整个套件变红
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import pytest


def _db_available() -> bool:
    """探测本地 Postgres 是否可连。连不上不抛错，返回 False。"""
    try:
        from sqlalchemy import create_engine, text

        from backend.api.deps import _build_db_url

        engine = create_engine(
            _build_db_url(), connect_args={"connect_timeout": 2}
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


# 收集测试时探测一次，避免每个测试都连一遍
DB_AVAILABLE = _db_available()


@pytest.fixture(scope="session")
def live_db():
    """
    需要数据库的测试把这个 fixture 加进参数列表即可。
    没连上数据库时调用 pytest.skip()，该测试被标记为 skipped 而非 failed。
    """
    if not DB_AVAILABLE:
        pytest.skip("本地 Postgres 未连接（docker compose up -d），跳过需要 DB 的集成测试")
