"""
资产信息模型
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class AssetType(str, Enum):
    """资产类型枚举"""

    INDEX = "index"  # 指数
    ETF = "etf"  # ETF
    STOCK = "stock"  # 股票
    BOND = "bond"  # 债券
    FUND = "fund"  # 基金
    COMMODITY = "commodity"  # 商品


class Asset(Base):
    """
    资产信息模型

    存储各种可投资资产的基本信息。
    """

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 基本信息
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    type: Mapped[AssetType] = mapped_column(String(20), nullable=False, index=True)

    # 描述信息
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系
    market_data: Mapped[list["MarketDaily"]] = relationship(
        "MarketDaily", back_populates="asset", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Asset(code={self.code}, name={self.name}, type={self.type})>"
