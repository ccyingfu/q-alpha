"""
数据获取器单元测试
"""

from datetime import date
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from data_fetcher import AKShareFetcher, FetcherConfig


@pytest.fixture
def sample_df():
    """创建示例数据"""
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=5),
            "open": [10.0, 10.5, 11.0, 11.5, 12.0],
            "high": [10.5, 11.0, 11.5, 12.0, 12.5],
            "low": [9.5, 10.0, 10.5, 11.0, 11.5],
            "close": [10.5, 10.8, 11.2, 11.8, 12.2],
            "volume": [1000000, 1100000, 1200000, 1300000, 1400000],
        }
    )


@pytest.fixture
def fetcher_config():
    """创建测试配置"""
    return FetcherConfig(
        enable_cache=False,  # 测试时禁用缓存
        timeout=10,
    )


class TestAKShareFetcher:
    """AKShare 获取器测试"""

    def test_init_default_config(self):
        """测试默认配置初始化"""
        fetcher = AKShareFetcher()
        assert fetcher.config is not None
        assert fetcher.config.source == "akshare"

    def test_init_custom_config(self, fetcher_config):
        """测试自定义配置初始化"""
        fetcher = AKShareFetcher(config=fetcher_config)
        assert fetcher.config == fetcher_config

    @patch("data_fetcher.akshare_fetcher.ak.stock_zh_index_daily")
    def test_fetch_index_daily(self, mock_ak_index, sample_df):
        """测试获取指数数据"""
        # Mock AKShare 返回数据
        mock_df = sample_df.copy()
        mock_ak_index.return_value = mock_df

        fetcher = AKShareFetcher()
        result = fetcher.fetch_index_daily("000300")

        # 验证结果
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        assert list(result.columns) == ["date", "open", "high", "low", "close", "volume"]
        assert mock_ak_index.called

    @patch("data_fetcher.akshare_fetcher.ak.fund_etf_hist_em")
    def test_fetch_etf_daily(self, mock_ak_etf, sample_df):
        """测试获取 ETF 数据"""
        # Mock AKShare 返回数据
        mock_df = sample_df.copy()
        mock_ak_etf.return_value = mock_df

        fetcher = AKShareFetcher()
        result = fetcher.fetch_etf_daily("518880")

        # 验证结果
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        assert mock_ak_etf.called

    @patch("data_fetcher.akshare_fetcher.ak.stock_zh_a_hist")
    def test_fetch_stock_daily(self, mock_ak_stock, sample_df):
        """测试获取股票数据"""
        # Mock AKShare 返回数据
        mock_df = sample_df.copy()
        mock_ak_stock.return_value = mock_df

        fetcher = AKShareFetcher()
        result = fetcher.fetch_stock_daily("002594")

        # 验证结果
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        assert mock_ak_stock.called

    def test_standardize_dataframe(self, sample_df):
        """测试 DataFrame 标准化"""
        fetcher = AKShareFetcher()
        result = fetcher._standardize_dataframe(sample_df)

        # 验证日期类型
        assert pd.api.types.is_datetime64_any_dtype(result["date"])

        # 验证数值类型
        for col in ["open", "high", "low", "close", "volume"]:
            assert pd.api.types.is_numeric_dtype(result[col])

    def test_filter_by_date(self, sample_df):
        """测试日期过滤"""
        fetcher = AKShareFetcher()

        # 过滤后的数据
        result = fetcher._filter_by_date(
            sample_df,
            start_date=date(2024, 1, 2),
            end_date=date(2024, 1, 4),
        )

        # 应该只有3条数据
        assert len(result) == 3
