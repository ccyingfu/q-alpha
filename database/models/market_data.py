"""
市场行情数据模型
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class MarketDaily(Base):
    """
    日线行情数据模型

    存储指数、ETF、股仾的历史日线行情数据。
    """

    __tablename__ = "market_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assets.id"), nullable=False, index=True
    )

    # 交易日期
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    # OHLCV 数据
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # 关系
    asset: Mapped["Asset"] = relationship("Asset", back_populates="market_data")

    # 索引
    __table_args__ = (
        Index("idx_asset_date", "asset_id", "date"),
        Index("idx_date", "date"),
    )

    def __repr__(self) -> str:
        return f"<MarketDaily(asset_id={self.asset_id}, date={self.date}, close={self.close})>"
