"""
市场行情 Schema
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class MarketDataPoint(BaseModel):
    """单个行情数据点"""

    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketDataResponse(BaseModel):
    """行情数据响应"""

    asset_code: str
    asset_name: str
    data: List[MarketDataPoint]

    start_date: datetime
    end_date: datetime
    count: int
