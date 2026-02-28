"""
数据库连接配置

提供 SQLite 异步连接、会话管理和数据库初始化。
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

# 数据库 URL
DATABASE_URL = "sqlite:///q_alpha.db"

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 特定配置
    echo=False,  # 设置为 True 可查看 SQL 日志
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话

    用于 FastAPI 依赖注入。

    Yields:
        数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    获取数据库会话的上下文管理器

    用于脚本或非 FastAPI 场景。

    Yields:
        数据库会话
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    初始化数据库

    创建所有表。
    """
    from .models import asset, backtest, market_data, strategy  # noqa

    logger.info("Creating database tables...")
    from .models.base import Base

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")


def drop_db() -> None:
    """
    删除所有表

    警告：此操作不可逆！
    """
    from .models.base import Base

    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("All database tables dropped.")
