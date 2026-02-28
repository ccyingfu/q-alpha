"""
回测 Schema
"""

from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class PerformanceMetrics(BaseModel):
    """绩效指标"""

    total_return: float = Field(..., description="总收益率")
    annual_return: float = Field(..., description="年化收益率")
    max_drawdown: float = Field(..., description="最大回撤")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    sortino_ratio: Optional[float] = Field(None, description="索提诺比率")
    calmar_ratio: Optional[float] = Field(None, description="卡玛比率")
    volatility: float = Field(..., description="波动率")
    rebalance_count: int = Field(..., description="再平衡次数")


class BacktestRequest(BaseModel):
    """回测请求"""

    strategy_id: int = Field(..., description="策略 ID")
    start_date: datetime = Field(..., description="回测开始日期")
    end_date: datetime = Field(..., description="回测结束日期")
    initial_capital: float = Field(default=100000.0, description="初始资金")


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""

    ids: List[int] = Field(..., description="要删除的结果ID列表")


class DataPoint(BaseModel):
    """数据点"""
    date: str
    value: float


class BacktestResponse(BaseModel):
    """回测响应"""

    id: int
    strategy_id: int
    strategy_name: str

    # 回测配置
    start_date: datetime
    end_date: datetime
    initial_capital: float

    # 绩效指标
    metrics: PerformanceMetrics

    # 数据序列
    equity_curve: List[Dict[str, Union[str, float]]] = Field(..., description="净值序列")
    drawdown_curve: List[Dict[str, Union[str, float]]] = Field(..., description="回撤序列")
    benchmark_curves: Optional[Dict[str, List[Dict[str, Union[str, float]]]]] = Field(
        None, description="基准指数序列 (sh=上证指数, hs300=沪深300)"
    )

    # 时间戳
    created_at: datetime

    class Config:
        from_attributes = True
