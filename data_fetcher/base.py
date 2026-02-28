"""
数据获取器抽象基类
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

import pandas as pd


class DataFetcher(ABC):
    """
    数据获取器抽象基类

    定义统一的接口用于获取金融数据，支持多种数据源实现。
    """

    @abstractmethod
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
            start_date: 开始日期，None 表示从有数据开始
            end_date: 结束日期，None 表示到最新数据

        Returns:
            DataFrame 包含以下列:
                - date: 交易日期
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量
        """
        pass

    @abstractmethod
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
            DataFrame 格式同 fetch_index_daily
        """
        pass

    @abstractmethod
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
            DataFrame 格式同 fetch_index_daily
        """
        pass

    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化 DataFrame 格式

        确保列名和数据类型符合规范。

        Args:
            df: 原始数据

        Returns:
            标准化后的 DataFrame
        """
        # 标准列名映射
        column_mapping = {
            "date": "date",
            "日期": "date",
            "open": "open",
            "开盘": "open",
            "high": "high",
            "最高": "high",
            "low": "low",
            "最低": "low",
            "close": "close",
            "收盘": "close",
            "volume": "volume",
            "成交量": "volume",
        }

        df = df.rename(columns=column_mapping)

        # 确保必需列存在
        required_columns = ["date", "open", "high", "low", "close", "volume"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        # 转换日期类型
        df["date"] = pd.to_datetime(df["date"])

        # 确保数值列类型正确
        numeric_columns = ["open", "high", "low", "close", "volume"]
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # 按日期排序
        df = df.sort_values("date").reset_index(drop=True)

        return df
