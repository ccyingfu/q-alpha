"""
投资策略模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict

from sqlalchemy import DateTime, Float, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class RebalanceType(str, Enum):
    """再平衡类型"""

    MONTHLY = "monthly"  # 按月
    QUARTERLY = "quarterly"  # 按季度
    YEARLY = "yearly"  # 按年
    THRESHOLD = "threshold"  # 阈值触发


class Strategy(Base):
    """
    投资策略模型

    定义投资组合的资产配置和再平衡策略。
    """

    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 资产配置（JSON 格式）
    # 示例：{"000300": 0.6, "518880": 0.4}
    allocation: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # 再平衡配置
    rebalance_type: Mapped[RebalanceType] = mapped_column(
        String(20), default=RebalanceType.MONTHLY, nullable=False
    )
    rebalance_threshold: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # 阈值触发时使用，如 0.05 表示 5%

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系
    backtests: Mapped[list["BacktestResult"]] = relationship(
        "BacktestResult", back_populates="strategy", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Strategy(name={self.name}, rebalance_type={self.rebalance_type})>"

    def get_allocation_dict(self) -> Dict[str, float]:
        """
        获取资产配置字典

        Returns:
            资产代码到权重的映射
        """
        return self.allocation
