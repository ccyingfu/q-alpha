"""
回测引擎

执行投资组合策略回测。
"""

import math
from datetime import date, datetime
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
        # 确保日期在请求的范围内（将 Timestamp/datetime/date 统一转换为 date 类型进行比较）
        start_date_only = start_date.date() if isinstance(start_date, datetime) else start_date
        end_date_only = end_date.date() if isinstance(end_date, datetime) else end_date

        def to_date_value(d):
            """将各种日期类型统一转换为 date 对象"""
            if isinstance(d, date) and not isinstance(d, datetime):
                return d  # 已经是 date 对象
            return d.date()  # datetime 或 pandas Timestamp

        all_dates = [
            d for d in all_dates
            if to_date_value(d) >= start_date_only and to_date_value(d) <= end_date_only
        ]

        # 3. 计算组合净值
        equity_curve = []
        cash = initial_capital  # 初始现金
        holdings = {code: 0.0 for code in asset_codes}  # 持仓数量
        rebalance_count = 0
        first_day = True
        pending_cash = initial_capital  # 待分配的现金（用于处理部分资产无数据的情况）

        # 按日期遍历
        for i, dt in enumerate(all_dates):
            # 第一天：按配置权重买入资产
            if first_day:
                # 找出第一天有数据的资产及其权重
                available_weights = {}
                total_available_weight = 0.0
                for code in asset_codes:
                    if dt in asset_data[code].index:
                        available_weights[code] = asset_weights[code]
                        total_available_weight += asset_weights[code]

                # 如果有可投资资产，按权重归一化后投资
                if total_available_weight > 0:
                    for code, weight in available_weights.items():
                        price = asset_data[code].loc[dt, "close"]
                        # 按归一化后的权重投资（确保有数据的资产分配到全部资金）
                        normalized_weight = weight / total_available_weight
                        amount_to_invest = cash * normalized_weight
                        shares = amount_to_invest / price
                        holdings[code] = shares

                # 现金已全部投资（归一化确保全部资金被分配到有数据的资产）
                cash = 0
                first_day = False

            # 计算当前持仓总价值
            total_value = cash  # 初始为剩余现金
            has_data = False  # 标记当天是否有任何资产数据
            for code in asset_codes:
                if dt in asset_data[code].index and holdings[code] > 0:
                    has_data = True
                    price = asset_data[code].loc[dt, "close"]
                    value = holdings[code] * price
                    total_value += value

            # 只有当天有数据时才记录净值，否则使用前一天的净值
            if has_data or len(equity_curve) == 0:
                equity_curve.append({"date": dt.strftime("%Y-%m-%d"), "value": total_value})
            else:
                # 当天没有任何资产数据，使用前一天的净值
                previous_value = equity_curve[-1]["value"] if equity_curve else initial_capital
                equity_curve.append({"date": dt.strftime("%Y-%m-%d"), "value": previous_value})

        # 4. 计算绩效指标（统一使用 date 类型）
        equity_series = pd.Series([e["value"] for e in equity_curve])
        metrics = self.metrics_calculator.calculate_all_metrics(
            equity_series, start_date_only, end_date_only
        )

        # 5. 计算回撤曲线（传入日期列表）
        drawdown_curve = self.metrics_calculator.calculate_drawdown_curve(
            equity_series, all_dates
        )

        # 6. 计算基准指数曲线
        benchmark_curves = self._calculate_benchmark_curves(
            asset_repo, market_repo, start_date_only, end_date_only, all_dates, initial_capital
        )

        # 7. 创建回测结果对象
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
            benchmark_curves=benchmark_curves,
        )

        return result

    def _calculate_benchmark_curves(
        self,
        asset_repo: AssetRepository,
        market_repo: MarketDataRepository,
        start_date,
        end_date,
        all_dates: List,
        initial_capital: float,
    ) -> dict:
        """
        计算基准指数收益率曲线

        Args:
            asset_repo: 资产仓储
            market_repo: 行情数据仓储
            start_date: 开始日期
            end_date: 结束日期
            all_dates: 所有交易日期
            initial_capital: 初始资金

        Returns:
            基准指数曲线字典 {"sh": [...], "hs300": [...]}
        """
        benchmarks = {
            "sh": "000001",  # 上证指数
            "hs300": "000300",  # 沪深300
        }
        benchmark_curves = {}

        for key, code in benchmarks.items():
            asset = asset_repo.get_by_code(code)
            if not asset:
                continue

            data = market_repo.get_by_asset(asset.id, start_date, end_date)
            if not data:
                continue

            # 转换为字典方便查找，统一使用 date 类型
            price_dict = {}
            for d in data:
                # 确保 d.date 是 date 类型，使用 try-except 处理各种类型
                try:
                    # 尝试提取 date 部分（适用于 datetime 和 Timestamp）
                    date_key = d.date.date()
                except (AttributeError, TypeError):
                    # 已经是 date 对象或其他类型，直接使用
                    date_key = d.date
                price_dict[date_key] = d.close

            # 计算基准收益率曲线
            curve = []
            first_price = None

            for dt in all_dates:
                # 提取日期部分（支持 Timestamp, datetime, date 类型）
                if isinstance(dt, datetime):
                    date_only = dt.date()
                    date_str = dt.strftime("%Y-%m-%d")
                elif hasattr(dt, 'date'):  # pandas Timestamp
                    date_only = dt.date()
                    date_str = dt.strftime("%Y-%m-%d")
                elif isinstance(dt, date):
                    date_only = dt
                    date_str = dt.strftime("%Y-%m-%d")
                else:
                    # 其他情况，跳过
                    continue

                if date_only in price_dict:
                    price = price_dict[date_only]
                    if first_price is None:
                        first_price = price
                        # 第一天，收益率为0，净值为初始资金
                        curve.append({
                            "date": date_str,
                            "value": initial_capital
                        })
                    else:
                        # 计算累计收益率
                        total_return = (price - first_price) / first_price
                        value = initial_capital * (1 + total_return)
                        curve.append({
                            "date": date_str,
                            "value": value
                        })
                elif curve:
                    # 当天没有数据，使用前一天的值
                    curve.append({
                        "date": date_str,
                        "value": curve[-1]["value"]
                    })

            benchmark_curves[key] = curve

        return benchmark_curves
