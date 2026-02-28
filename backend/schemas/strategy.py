"""
策略 Schema
"""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class StrategyBase(BaseModel):
    """策略基础模型"""

    name: str = Field(..., description="策略名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="描述信息")
    allocation: Dict[str, float] = Field(..., description="资产配置 {code: weight}")
    rebalance_type: str = Field(default="monthly", description="再平衡类型")
    rebalance_threshold: Optional[float] = Field(None, description="再平衡阈值")


class StrategyCreate(StrategyBase):
    """创建策略请求"""

    pass


class StrategyUpdate(BaseModel):
    """更新策略请求"""

    name: Optional[str] = None
    description: Optional[str] = None
    allocation: Optional[Dict[str, float]] = None
    rebalance_type: Optional[str] = None
    rebalance_threshold: Optional[float] = None


class StrategyResponse(StrategyBase):
    """策略响应"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
