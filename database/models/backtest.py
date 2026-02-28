"""
回测结果模型
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class BacktestResult(Base):
    """
    回测结果模型

    存储策略回测的完整结果，包括配置、指标和净值序列。
    """

    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 关联策略
    strategy_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("strategies.id"), nullable=False, index=True
    )

    # 回测配置
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    initial_capital: Mapped[float] = mapped_column(Float, default=100000.0, nullable=False)

    # 绩效指标
    total_return: Mapped[float] = mapped_column(Float, nullable=False)
    annual_return: Mapped[float] = mapped_column(Float, nullable=False)
    max_drawdown: Mapped[float] = mapped_column(Float, nullable=False)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    sortino_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    calmar_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 波动率指标
    volatility: Mapped[float] = mapped_column(Float, nullable=False)

    # 交易统计
    rebalance_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 净值序列（JSON 格式）
    # 示例：[{"date": "2020-01-01", "value": 100000.0}, ...]
    equity_curve: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # 回撤序列（JSON 格式）
    drawdown_curve: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # 关系
    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="backtests")

    def __repr__(self) -> str:
        return f"<BacktestResult(id={self.id}, strategy_id={self.strategy_id}, annual_return={self.annual_return})>"
