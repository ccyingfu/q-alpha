"""
日期工具函数
"""

from datetime import datetime, timedelta
from typing import List


def get_trading_dates(start_date: datetime, end_date: datetime) -> List[datetime]:
    """
    获取交易日列表（简单版，不考虑节假日）

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        日期列表
    """
    dates = []
    current = start_date

    while current <= end_date:
        # 排除周末
        if current.weekday() < 5:
            dates.append(current)
        current += timedelta(days=1)

    return dates


def get_next_rebalance_date(
    current_date: datetime, rebalance_type: str
) -> datetime:
    """
    获取下一个再平衡日期

    Args:
        current_date: 当前日期
        rebalance_type: 再平衡类型 (monthly/quarterly/yearly)

    Returns:
        下一个再平衡日期
    """
    if rebalance_type == "monthly":
        # 下个月第一天
        if current_date.month == 12:
            next_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            next_date = current_date.replace(month=current_date.month + 1, day=1)

    elif rebalance_type == "quarterly":
        # 下个季度第一天
        current_quarter = (current_date.month - 1) // 3 + 1
        if current_quarter == 4:
            next_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            next_date = current_date.replace(month=current_quarter * 3 + 1, day=1)

    elif rebalance_type == "yearly":
        # 下一年第一天
        next_date = current_date.replace(year=current_date.year + 1, month=1, day=1)

    else:
        raise ValueError(f"Unknown rebalance type: {rebalance_type}")

    return next_date
