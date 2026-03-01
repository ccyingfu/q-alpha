"""
迁移脚本：为 assets 表的 name 字段添加索引

运行方式：
    python -m backend.migrations.add_asset_name_index
"""

import logging

from sqlalchemy import text
from database.connection import engine

logger = logging.getLogger(__name__)


def upgrade():
    """添加索引"""
    with engine.connect() as conn:
        # 检查索引是否已存在
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='index' AND name='ix_assets_name'")
        ).fetchone()

        if result is None:
            logger.info("Adding index on assets.name...")
            conn.execute(text("CREATE INDEX ix_assets_name ON assets(name)"))
            conn.commit()
            logger.info("Index created successfully.")
        else:
            logger.info("Index already exists.")


def downgrade():
    """移除索引"""
    with engine.connect() as conn:
        logger.info("Dropping index on assets.name...")
        conn.execute(text("DROP INDEX IF EXISTS ix_assets_name"))
        conn.commit()
        logger.info("Index dropped successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    upgrade()
