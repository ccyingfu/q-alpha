"""
回测引擎

执行投资组合策略回测。
"""

import math
from datetime import datetime
from typing import List, Optional

import pandas as pd
from sqlalchemy.orm import Session

from database.models import Strategy
from database.repositories import AssetRepository, MarketDataRepository
from .metrics_calculator import MetricsCalculator
from ..config import settings


def _sanitize_metric(value: Optional[float]) -> Optional[float]:
    """
    清理指标值，将 NaN 转换为 None

    Args:
        value: 原始指标值

    Returns:
        清理后的值（NaN -> None）
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return value


class BacktestEngine:
    """
    回测引擎

    根据策略配置和历史数据执行回测。
    """

    def __init__(self, db: Session):
        """
        初始化回测引擎

        Args:
            db: 数据库会话
        """
        self.db = db
        self.metrics_calculator = MetricsCalculator(
            risk_free_rate=settings.risk_free_rate,
            trading_days_per_year=settings.trading_days_per_year,
        )

    def run(
        self,
        strategy: Strategy,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000.0,
    ) -> "BacktestResult":
        """
        执行回测

        Args:
            strategy: 策略对象
            start_date: 回测开始日期
            end_date: 回测结束日期
            initial_capital: 初始资金

        Returns:
            回测结果对象
        """
        # 1. 获取资产数据
        asset_codes = list(strategy.allocation.keys())
        asset_weights = strategy.allocation

        asset_repo = AssetRepository(self.db)
        market_repo = MarketDataRepository(self.db)

        # 获取所有资产的行情数据
        asset_data = {}
        for code in asset_codes:
            asset = asset_repo.get_by_code(code)
            if not asset:
                raise ValueError(f"Asset {code} not found in database")

            data = market_repo.get_by_asset(asset.id, start_date, end_date)
            if not data:
                raise ValueError(f"No market data for asset {code}")

            # 转换为 DataFrame
            df = pd.DataFrame(
                [
                    {
                        "date": d.date,
                        "open": d.open,
                        "high": d.high,
                        "low": d.low,
                        "close": d.close,
                        "volume": d.volume,
                    }
                    for d in data
                ]
            )
            df.set_index("date", inplace=True)
            asset_data[code] = df

        # 2. 对齐日期并过滤到请求的日期范围
        all_dates = sorted(set().union(*[df.index for df in asset_data.values()]))
        # 确保日期在请求的范围内
        all_dates = [d for d in all_dates if d >= start_date and d <= end_date]

        # 3. 计算组合净值
        equity_curve = []
        cash = initial_capital  # 初始现金
        holdings = {code: 0.0 for code in asset_codes}  # 持仓数量
        rebalance_count = 0
        first_day = True

        # 按日期遍历
        for i, date in enumerate(all_dates):
            # 第一天：按配置权重买入资产
            if first_day:
                for code in asset_codes:
                    if date in asset_data[code].index:
                        weight = asset_weights[code]
                        price = asset_data[code].loc[date, "close"]
                        # 计算应买入的金额
                        amount_to_invest = cash * weight
                        # 计算买入数量（按收盘价）
                        shares = amount_to_invest / price
                        holdings[code] = shares
                # 现金已全部投资
                cash = 0
                first_day = False

            # 计算当前持仓总价值
            total_value = cash  # 初始为剩余现金
            for code in asset_codes:
                if date in asset_data[code].index and holdings[code] > 0:
                    price = asset_data[code].loc[date, "close"]
                    value = holdings[code] * price
                    total_value += value

            # 记录净值
            equity_curve.append({"date": date.strftime("%Y-%m-%d"), "value": total_value})

        # 4. 计算绩效指标
        equity_series = pd.Series([e["value"] for e in equity_curve])
        metrics = self.metrics_calculator.calculate_all_metrics(
            equity_series, start_date, end_date
        )

        # 5. 计算回撤曲线（传入日期列表）
        drawdown_curve = self.metrics_calculator.calculate_drawdown_curve(
            equity_series, all_dates
        )

        # 6. 创建回测结果对象
        from database.models import BacktestResult

        # 清理指标值中的 NaN
        result = BacktestResult(
            strategy_id=strategy.id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            total_return=_sanitize_metric(metrics["total_return"]) or 0.0,
            annual_return=_sanitize_metric(metrics["annual_return"]) or 0.0,
            max_drawdown=_sanitize_metric(metrics["max_drawdown"]) or 0.0,
            sharpe_ratio=_sanitize_metric(metrics["sharpe_ratio"]),
            sortino_ratio=_sanitize_metric(metrics["sortino_ratio"]),
            calmar_ratio=_sanitize_metric(metrics["calmar_ratio"]),
            volatility=_sanitize_metric(metrics["volatility"]) or 0.0,
            rebalance_count=rebalance_count,
            equity_curve=equity_curve,
            drawdown_curve=drawdown_curve,
        )

        return result
