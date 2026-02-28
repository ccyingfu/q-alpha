"""
AKShare 数据获取器实现

使用 AKShare 库获取中国金融市场的历史数据。
"""

import logging
from datetime import date, datetime
from typing import Optional

import akshare as ak
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import DataFetcher
from .cache_manager import CacheManager
from .config import FetcherConfig

logger = logging.getLogger(__name__)


class AKShareFetcher(DataFetcher):
    """
    AKShare 数据获取器

    封装 AKShare 的接口，提供统一的金融数据获取能力。
    """

    def __init__(self, config: Optional[FetcherConfig] = None):
        """
        初始化 AKShare 获取器

        Args:
            config: 配置对象，None 则使用默认配置
        """
        self.config = config or FetcherConfig()

        # 初始化缓存管理器
        if self.config.enable_cache:
            self.cache = CacheManager(
                cache_dir=self.config.cache_dir,
                expire_hours=self.config.cache_expire_hours,
            )
        else:
            self.cache = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def fetch_index_daily(
        self,
        index_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """
        获取指数日线数据

        Args:
            index_code: 指数代码，如 "000300"（沪深300）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            标准化的 DataFrame
        """
        # 尝试从缓存获取
        if self.cache:
            cached_df = self.cache.get("index", index_code)
            if cached_df is not None:
                logger.info(f"从缓存获取指数数据: {index_code}")
                return self._filter_by_date(cached_df, start_date, end_date)

        # 从 AKShare 获取数据
        try:
            logger.info(f"从 AKShare 获取指数数据: {index_code}")

            # AKShare 的指数数据接口
            df = ak.stock_zh_index_daily(
                symbol=f"sh{index_code}" if index_code.startswith("0") else f"sz{index_code}"
            )

            # 标准化列名
            df = df.rename(
                columns={
                    "date": "date",
                    "open": "open",
                    "high": "high",
                    "low": "low",
                    "close": "close",
                    "volume": "volume",
                }
            )

            # 标准化格式
            df = self._standardize_dataframe(df)

            # 更新缓存
            if self.cache:
                self.cache.update("index", index_code, df)

            # 过滤日期范围
            return self._filter_by_date(df, start_date, end_date)

        except Exception as e:
            logger.error(f"获取指数数据失败: {index_code}, 错误: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def fetch_etf_daily(
        self,
        etf_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """
        获取 ETF 日线数据

        Args:
            etf_code: ETF 代码，如 "518880"（黄金ETF）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            标准化的 DataFrame
        """
        # 尝试从缓存获取
        if self.cache:
            cached_df = self.cache.get("etf", etf_code)
            if cached_df is not None:
                logger.info(f"从缓存获取 ETF 数据: {etf_code}")
                return self._filter_by_date(cached_df, start_date, end_date)

        # 从 AKShare 获取数据
        try:
            logger.info(f"从 AKShare 获取 ETF 数据: {etf_code}")

            # AKShare 的 ETF 数据接口
            df = ak.fund_etf_hist_em(
                symbol=etf_code,
                period="daily",
                adjust="qfq",
            )

            # 标准化列名
            df = df.rename(
                columns={
                    "交易日": "date",
                    "开盘": "open",
                    "最高": "high",
                    "最低": "low",
                    "收盘": "close",
                    "成交量": "volume",
                }
            )

            # 标准化格式
            df = self._standardize_dataframe(df)

            # 更新缓存
            if self.cache:
                self.cache.update("etf", etf_code, df)

            # 过滤日期范围
            return self._filter_by_date(df, start_date, end_date)

        except Exception as e:
            logger.error(f"获取 ETF 数据失败: {etf_code}, 错误: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def fetch_stock_daily(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """
        获取个股日线数据

        Args:
            stock_code: 股票代码，如 "002594"（比亚迪）
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权方式

        Returns:
            标准化的 DataFrame
        """
        # 尝试从缓存获取
        if self.cache:
            cached_df = self.cache.get("stock", stock_code)
            if cached_df is not None:
                logger.info(f"从缓存获取股票数据: {stock_code}")
                return self._filter_by_date(cached_df, start_date, end_date)

        # 从 AKShare 获取数据
        try:
            logger.info(f"从 AKShare 获取股票数据: {stock_code}")

            # 确定市场
            if stock_code.startswith("0") or stock_code.startswith("3"):
                symbol = f"sz{stock_code}"
            elif stock_code.startswith("6") or stock_code.startswith("88"):
                symbol = f"sh{stock_code}"
            else:
                raise ValueError(f"无法识别股票代码: {stock_code}")

            # AKShare 的股票数据接口
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.strftime("%Y%m%d") if start_date else "19900101",
                end_date=end_date.strftime("%Y%m%d") if end_date else "21000101",
                adjust=adjust or "",
            )

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "date",
                    "开盘": "open",
                    "最高": "high",
                    "最低": "low",
                    "收盘": "close",
                    "成交量": "volume",
                }
            )

            # 标准化格式
            df = self._standardize_dataframe(df)

            # 更新缓存
            if self.cache:
                self.cache.update("stock", stock_code, df)

            # 过滤日期范围
            return self._filter_by_date(df, start_date, end_date)

        except Exception as e:
            logger.error(f"获取股票数据失败: {stock_code}, 错误: {e}")
            raise

    def _filter_by_date(
        self,
        df: pd.DataFrame,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> pd.DataFrame:
        """
        按日期范围过滤数据

        Args:
            df: 原始数据
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            过滤后的 DataFrame
        """
        if start_date is not None:
            df = df[df["date"] >= pd.Timestamp(start_date)]

        if end_date is not None:
            df = df[df["date"] <= pd.Timestamp(end_date)]

        return df.reset_index(drop=True)
