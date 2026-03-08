"""
AKShare ETF 数据获取器

专门用于获取 ETF 数据，弥补 Baostock 不支持 ETF 的缺陷。
使用重试机制应对 AKShare 连接不稳定的问题。
"""

import logging
import time
from datetime import date, datetime
from typing import Optional

import akshare as ak
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base import DataFetcher
from .cache_manager import CacheManager
from .config import FetcherConfig

logger = logging.getLogger(__name__)


class AKShareETFFetcher(DataFetcher):
    """
    AKShare ETF 数据获取器

    专门用于获取 ETF 日线数据，使用重试机制应对连接不稳定问题。
    """

    def __init__(self, config: Optional[FetcherConfig] = None):
        """
        初始化 AKShare ETF 获取器

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

    def _format_date(self, d: Optional[date]) -> str:
        """格式化日期"""
        if d is None:
            return ""
        return d.strftime("%Y-%m-%d")

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        retry=retry_if_exception_type((ConnectionError, Exception)),
        before_sleep=lambda retry_state: logger.warning(
            f"AKShare 请求失败，第 {retry_state.attempt_number} 次重试，等待 {retry_state.next_action.sleep} 秒..."
        ),
    )
    def _fetch_with_retry(self, etf_code: str) -> pd.DataFrame:
        """
        带重试机制的 ETF 数据获取

        Args:
            etf_code: ETF 代码

        Returns:
            原始 DataFrame
        """
        logger.info(f"从 AKShare 获取 ETF 数据: {etf_code}")
        
        # 添加随机延迟，避免被限流
        import random
        time.sleep(random.uniform(1, 3))
        
        df = ak.fund_etf_hist_em(
            symbol=etf_code,
            period="daily",
            adjust="qfq"
        )
        
        if df is None or df.empty:
            raise ConnectionError(f"AKShare 返回空数据: {etf_code}")
        
        return df

    def fetch_index_daily(
        self,
        index_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """
        获取指数数据（AKShare ETF 获取器不支持指数）

        Raises:
            NotImplementedError: 此获取器仅支持 ETF
        """
        raise NotImplementedError("AKShareETFFetcher 仅支持 ETF 数据，请使用 BaostockFetcher 获取指数数据")

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
            if cached_df is not None and self._is_cache_sufficient(cached_df, start_date, end_date):
                logger.info(f"从缓存获取 ETF 数据: {etf_code}")
                return self._filter_by_date(cached_df, start_date, end_date)

        # 从 AKShare 获取数据（带重试）
        try:
            df = self._fetch_with_retry(etf_code)

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

    def fetch_stock_daily(
        self,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """
        获取股票数据（AKShare ETF 获取器不支持股票）

        Raises:
            NotImplementedError: 此获取器仅支持 ETF
        """
        raise NotImplementedError("AKShareETFFetcher 仅支持 ETF 数据，请使用 BaostockFetcher 获取股票数据")

    def _filter_by_date(
        self,
        df: pd.DataFrame,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> pd.DataFrame:
        """按日期范围过滤数据"""
        if start_date is not None:
            df = df[df["date"] >= pd.Timestamp(start_date)]

        if end_date is not None:
            df = df[df["date"] <= pd.Timestamp(end_date)]

        return df.reset_index(drop=True)

    def _is_cache_sufficient(
        self,
        cached_df: pd.DataFrame,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> bool:
        """检查缓存数据是否覆盖请求的日期范围"""
        if cached_df is None or cached_df.empty:
            return False

        if cached_df["date"].isna().all():
            return False

        cached_start = cached_df["date"].min()
        cached_end = cached_df["date"].max()

        if pd.isna(cached_start) or pd.isna(cached_end):
            return False

        if start_date is not None and pd.Timestamp(start_date) < cached_start:
            return False
        if end_date is not None and pd.Timestamp(end_date) > cached_end:
            return False

        return True
