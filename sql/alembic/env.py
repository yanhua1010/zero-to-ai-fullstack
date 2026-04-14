"""Alembic 迁移环境配置

对照 Java 的 Flyway/Liquibase：
  Flyway:   resources/db/migration/V1__init.sql
  Alembic:  sql/alembic/versions/xxxx_init.py（Python 生成，也可以写 SQL）

关键差异：Alembic 支持"自动生成"迁移文件——
  alembic revision --autogenerate -m "add table"
  它会对比 ORM 模型和数据库当前状态，自动生成 ALTER TABLE 等语句。
"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 从环境变量拼接连接串，覆盖 alembic.ini 里的静态配置
db_url = (
    f"postgresql+psycopg2://"
    f"{os.getenv('POSTGRES_USER', 'postgres')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'knowledge_base')}"
)
config.set_main_option("sqlalchemy.url", db_url)

# 把 ORM 模型的 metadata 注册进来，autogenerate 才能感知模型变化
from backend.models import Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
