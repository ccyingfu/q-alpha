"""
Baostock 数据获取器实现

使用 Baostock 库获取中国金融市场的历史数据。
Baostock 是证券宝提供的免费数据接口，无需注册、无限制调用。
"""

import logging
from datetime import date, datetime
from typing import Optional

import baostock as bs
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import DataFetcher
from .cache_manager import CacheManager
from .config import FetcherConfig

logger = logging.getLogger(__name__)


class BaostockFetcher(DataFetcher):
    """
    Baostock 数据获取器

    封装 Baostock 的接口，提供统一的金融数据获取能力。
    使用类级别的登录状态管理，确保多实例场景下正常工作。
    """

    # 类级别的登录状态管理
    _login_count = 0  # 引用计数
    _login_lock = False  # 简单的锁标志

    # 代码市场前缀映射
    INDEX_PREFIX = {
        # 上海交易所指数
        "000001": "sh",  # 上证指数
        "000300": "sh",  # 沪深300
        "000905": "sh",  # 中证500
        "000016": "sh",  # 上证50
        # 深圳交易所指数
        "399001": "sz",  # 深证成指
        "399006": "sz",  # 创业板指
        "399673": "sz",  # 创业板50
    }

    # ETF 市场前缀（ETF默认在上海交易所）
    ETF_DEFAULT_PREFIX = "sh"

    # 股票市场前缀
    STOCK_PREFIX = {
        "6": "sh",  # 上海交易所
        "0": "sz",  # 深圳交易所主板
        "3": "sz",  # 深圳交易所创业板
        "8": "bj",  # 北京交易所
    }

    # 复权方式映射
    ADJUST_FLAG = {
        "": "",       # 不复权
        "qfq": "2",   # 前复权
        "hfq": "3",   # 后复权
    }

    def __init__(self, config: Optional[FetcherConfig] = None):
        """
        初始化 Baostock 获取器

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

    @classmethod
    def _ensure_login(cls):
        """确保已登录 Baostock（类级别）"""
        if cls._login_count == 0:
            lg = bs.login()
            if lg.error_code != "0":
                raise RuntimeError(f"Baostock 登录失败: {lg.error_msg}")
            logger.info("Baostock 登录成功")
        cls._login_count += 1

    @classmethod
    def _safe_logout(cls):
        """安全登出 Baostock（类级别）"""
        if cls._login_count > 0:
            cls._login_count -= 1
            if cls._login_count == 0:
                try:
                    bs.logout()
                    logger.info("Baostock 登出成功")
                except Exception as e:
                    logger.warning(f"Baostock 登出时出现警告: {e}")

    def _convert_index_code(self, index_code: str) -> str:
        """
        转换指数代码为 Baostock 格式

        Args:
            index_code: 原始指数代码，如 "000300"

        Returns:
            Baostock 格式代码，如 "sh.000300"
        """
        # 检查是否已经是 Baostock 格式
        if "." in index_code:
            return index_code

        # 根据代码前缀判断市场
        prefix = self.INDEX_PREFIX.get(index_code, "sh")
        return f"{prefix}.{index_code}"

    def _convert_etf_code(self, etf_code: str) -> str:
        """
        转换 ETF 代码为 Baostock 格式

        Args:
            etf_code: 原始 ETF 代码，如 "518880"

        Returns:
            Baostock 格式代码，如 "sh.518880"
        """
        # 检查是否已经是 Baostock 格式
        if "." in etf_code:
            return etf_code

        # ETF 默认在上海交易所
        return f"{self.ETF_DEFAULT_PREFIX}.{etf_code}"

    def _convert_stock_code(self, stock_code: str) -> str:
        """
        转换股票代码为 Baostock 格式

        Args:
            stock_code: 原始股票代码，如 "002594"

        Returns:
            Baostock 格式代码，如 "sz.002594"
        """
        # 检查是否已经是 Baostock 格式
        if "." in stock_code:
            return stock_code

        # 根据首位数字判断市场
        first_char = stock_code[0]
        prefix = self.STOCK_PREFIX.get(first_char, "sh")
        return f"{prefix}.{stock_code}"

    def _format_date(self, d: Optional[date]) -> str:
        """
        格式化日期为 Baostock 要求的格式

        Args:
            d: 日期对象

        Returns:
            格式化后的日期字符串，如 "2024-01-01"
        """
        if d is None:
            return ""
        return d.strftime("%Y-%m-%d")

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
        # 尝试从缓存获取，但需要检查缓存数据是否覆盖请求的日期范围
        if self.cache:
            cached_df = self.cache.get("index", index_code)
            if cached_df is not None and self._is_cache_sufficient(cached_df, start_date, end_date):
                logger.info(f"从缓存获取指数数据: {index_code}")
                return self._filter_by_date(cached_df, start_date, end_date)

        # 从 Baostock 获取数据
        try:
            self._ensure_login()
            logger.info(f"从 Baostock 获取指数数据: {index_code}")

            # 转换代码格式
            bs_code = self._convert_index_code(index_code)

            # 设置默认日期范围
            end = self._format_date(end_date) or datetime.now().strftime("%Y-%m-%d")
            start = self._format_date(start_date) or "1990-12-19"

            # 查询数据
            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,volume",
                start_date=start,
                end_date=end,
                frequency="d",
                adjustflag="2"  # 指数使用前复权
            )

            if rs.error_code != "0":
                raise RuntimeError(f"Baostock 查询失败: {rs.error_msg}")

            # 转换为 DataFrame
            data_list = []
            while (rs.error_code == "0") & rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)

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
        # 尝试从缓存获取，但需要检查缓存数据是否覆盖请求的日期范围
        if self.cache:
            cached_df = self.cache.get("etf", etf_code)
            if cached_df is not None and self._is_cache_sufficient(cached_df, start_date, end_date):
                logger.info(f"从缓存获取 ETF 数据: {etf_code}")
                return self._filter_by_date(cached_df, start_date, end_date)

        # 从 Baostock 获取数据
        try:
            self._ensure_login()
            logger.info(f"从 Baostock 获取 ETF 数据: {etf_code}")

            # 转换代码格式
            bs_code = self._convert_etf_code(etf_code)

            # 设置默认日期范围
            end = self._format_date(end_date) or datetime.now().strftime("%Y-%m-%d")
            start = self._format_date(start_date) or "2000-01-01"

            # 查询数据
            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,volume",
                start_date=start,
                end_date=end,
                frequency="d",
                adjustflag="2"  # ETF 使用前复权
            )

            if rs.error_code != "0":
                raise RuntimeError(f"Baostock 查询失败: {rs.error_msg}")

            # 转换为 DataFrame
            data_list = []
            while (rs.error_code == "0") & rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)

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
                - "": 不复权
                - "qfq": 前复权（默认）
                - "hfq": 后复权

        Returns:
            标准化的 DataFrame
        """
        # 尝试从缓存获取，但需要检查缓存数据是否覆盖请求的日期范围
        cache_key = f"{stock_code}_{adjust}"
        if self.cache:
            cached_df = self.cache.get("stock", cache_key)
            if cached_df is not None and self._is_cache_sufficient(cached_df, start_date, end_date):
                logger.info(f"从缓存获取股票数据: {stock_code}")
                return self._filter_by_date(cached_df, start_date, end_date)

        # 从 Baostock 获取数据
        try:
            self._ensure_login()
            logger.info(f"从 Baostock 获取股票数据: {stock_code}")

            # 转换代码格式
            bs_code = self._convert_stock_code(stock_code)

            # 设置默认日期范围
            end = self._format_date(end_date) or datetime.now().strftime("%Y-%m-%d")
            start = self._format_date(start_date) or "1990-12-19"

            # 转换复权方式
            adjust_flag = self.ADJUST_FLAG.get(adjust, "2")

            # 查询数据
            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,volume",
                start_date=start,
                end_date=end,
                frequency="d",
                adjustflag=adjust_flag
            )

            if rs.error_code != "0":
                raise RuntimeError(f"Baostock 查询失败: {rs.error_msg}")

            # 转换为 DataFrame
            data_list = []
            while (rs.error_code == "0") & rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 标准化格式
            df = self._standardize_dataframe(df)

            # 更新缓存
            if self.cache:
                self.cache.update("stock", cache_key, df)

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

    def _is_cache_sufficient(
        self,
        cached_df: pd.DataFrame,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> bool:
        """
        检查缓存数据是否覆盖请求的日期范围

        Args:
            cached_df: 缓存的数据
            start_date: 请求的开始日期
            end_date: 请求的结束日期

        Returns:
            True 如果缓存数据覆盖请求的范围，False 否则
        """
        if cached_df is None or cached_df.empty:
            return False

        cached_start = cached_df["date"].min()
        cached_end = cached_df["date"].max()

        # 检查请求的日期范围是否在缓存范围内
        if start_date is not None and pd.Timestamp(start_date) < cached_start:
            return False
        if end_date is not None and pd.Timestamp(end_date) > cached_end:
            return False

        return True
