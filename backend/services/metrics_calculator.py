"""
绩效计算服务

计算各种投资绩效指标。
"""

from datetime import datetime, date
from typing import List, Optional, Union

import numpy as np
import pandas as pd


class MetricsCalculator:
    """
    绩效计算器

    计算各种投资组合绩效指标。
    """

    def __init__(self, risk_free_rate: float = 0.03, trading_days_per_year: int = 252):
        """
        初始化计算器

        Args:
            risk_free_rate: 无风险利率（年化）
            trading_days_per_year: 每年交易日数
        """
        self.risk_free_rate = risk_free_rate
        self.trading_days_per_year = trading_days_per_year

    def calculate_total_return(self, equity_curve: pd.Series) -> float:
        """
        计算总收益率

        Args:
            equity_curve: 净值序列

        Returns:
            总收益率
        """
        if len(equity_curve) < 2:
            return 0.0

        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        return total_return

    def calculate_annual_return(
        self, equity_curve: pd.Series, start_date: Union[datetime, date], end_date: Union[datetime, date]
    ) -> float:
        """
        计算年化收益率 (CAGR)

        Args:
            equity_curve: 净值序列
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            年化收益率
        """
        if len(equity_curve) < 2:
            return 0.0

        # 计算总收益率
        total_return = self.calculate_total_return(equity_curve)

        # 统一转换为 date 类型
        if isinstance(start_date, datetime):
            start_date_only = start_date.date()
        else:
            start_date_only = start_date
        if isinstance(end_date, datetime):
            end_date_only = end_date.date()
        else:
            end_date_only = end_date

        days = (end_date_only - start_date_only).days
        years = days / 365.25

        if years <= 0:
            return 0.0

        # CAGR = (1 + total_return)^(1/years) - 1
        annual_return = (1 + total_return) ** (1 / years) - 1
        return annual_return

    def calculate_max_drawdown(self, equity_curve: pd.Series) -> float:
        """
        计算最大回撤

        Args:
            equity_curve: 净值序列

        Returns:
            最大回撤
        """
        if len(equity_curve) < 2:
            return 0.0

        # 计算累计最大值
        cumulative_max = equity_curve.cummax()

        # 计算回撤
        drawdown = (equity_curve - cumulative_max) / cumulative_max

        # 最大回撤
        max_drawdown = drawdown.min()
        return max_drawdown

    def calculate_drawdown_curve(
        self, equity_curve: pd.Series, dates: Optional[List[Union[datetime, date]]] = None
    ) -> List[dict]:
        """
        计算回撤曲线

        Args:
            equity_curve: 净值序列
            dates: 日期列表（可选），如果为空则使用整数索引

        Returns:
            回撤曲线数据
        """
        if len(equity_curve) < 2:
            return []

        # 计算累计最大值
        cumulative_max = equity_curve.cummax()

        # 计算回撤
        drawdown = (equity_curve - cumulative_max) / cumulative_max

        # 转换为输出格式
        if dates is not None:
            # 使用提供的日期列表，兼容 datetime 和 date 类型
            return [
                {"date": d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d), "value": float(drawdown.iloc[i])}
                for i, d in enumerate(dates)
            ]

        # 使用整数索引转换为字符串
        return [
            {"date": str(i), "value": float(dd)} for i, dd in drawdown.items()
        ]

    def calculate_volatility(self, returns: pd.Series) -> float:
        """
        计算波动率（年化）

        Args:
            returns: 日收益率序列

        Returns:
            年化波动率
        """
        if len(returns) < 2:
            return 0.0

        # 日波动率
        daily_vol = returns.std()

        # 如果标准差为 NaN（所有值相同），返回 0
        if pd.isna(daily_vol) or daily_vol == 0:
            return 0.0

        # 年化波动率
        annual_vol = daily_vol * np.sqrt(self.trading_days_per_year)
        return annual_vol

    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        annual_return: float,
    ) -> Optional[float]:
        """
        计算夏普比率

        Sharpe Ratio = (年化收益率 - 无风险利率) / 年化波动率

        Args:
            returns: 日收益率序列
            annual_return: 年化收益率

        Returns:
            夏普比率
        """
        if len(returns) == 0:
            return None

        volatility = self.calculate_volatility(returns)
        if volatility == 0:
            return None

        sharpe = (annual_return - self.risk_free_rate) / volatility
        return sharpe

    def calculate_sortino_ratio(
        self,
        returns: pd.Series,
        annual_return: float,
    ) -> Optional[float]:
        """
        计算索提诺比率

        Sortino Ratio = (年化收益率 - 无风险利率) / 下行波动率

        Args:
            returns: 日收益率序列
            annual_return: 年化收益率

        Returns:
            索提诺比率
        """
        if len(returns) == 0:
            return None

        # 计算下行收益率（负收益）
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0:
            return None

        # 下行波动率
        downside_vol = downside_returns.std() * np.sqrt(self.trading_days_per_year)

        if downside_vol == 0:
            return None

        sortino = (annual_return - self.risk_free_rate) / downside_vol
        return sortino

    def calculate_calmar_ratio(
        self,
        annual_return: float,
        max_drawdown: float,
    ) -> Optional[float]:
        """
        计算卡玛比率

        Calmar Ratio = 年化收益率 / |最大回撤|

        Args:
            annual_return: 年化收益率
            max_drawdown: 最大回撤

        Returns:
            卡玛比率
        """
        if max_drawdown == 0:
            return None

        calmar = annual_return / abs(max_drawdown)
        return calmar

    def calculate_all_metrics(
        self,
        equity_curve: pd.Series,
        start_date: Union[datetime, date],
        end_date: Union[datetime, date],
    ) -> dict:
        """
        计算所有绩效指标

        Args:
            equity_curve: 净值序列
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            包含所有指标的字典
        """
        # 计算收益率
        returns = equity_curve.pct_change().dropna()

        # 计算各项指标
        total_return = self.calculate_total_return(equity_curve)
        annual_return = self.calculate_annual_return(equity_curve, start_date, end_date)
        max_drawdown = self.calculate_max_drawdown(equity_curve)
        volatility = self.calculate_volatility(returns)
        sharpe_ratio = self.calculate_sharpe_ratio(returns, annual_return)
        sortino_ratio = self.calculate_sortino_ratio(returns, annual_return)
        calmar_ratio = self.calculate_calmar_ratio(annual_return, max_drawdown)

        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "max_drawdown": max_drawdown,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "calmar_ratio": calmar_ratio,
        }
