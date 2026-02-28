"""
数据获取器单元测试
"""

from datetime import date
import contextlib

import pandas as pd
import pytest

from data_fetcher import BaostockFetcher, FetcherConfig, AKShareFetcher


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


class TestBaostockFetcher:
    """Baostock 获取器测试"""

    def test_init_default_config(self):
        """测试默认配置初始化"""
        fetcher = BaostockFetcher()
        assert fetcher.config is not None

    def test_init_custom_config(self, fetcher_config):
        """测试自定义配置初始化"""
        fetcher = BaostockFetcher(config=fetcher_config)
        assert fetcher.config == fetcher_config

    def test_convert_index_code(self):
        """测试指数代码转换"""
        fetcher = BaostockFetcher()

        # 测试沪深300
        assert fetcher._convert_index_code("000300") == "sh.000300"

        # 测试上证50
        assert fetcher._convert_index_code("000016") == "sh.000016"

        # 测试深证成指
        assert fetcher._convert_index_code("399001") == "sz.399001"

        # 测试已经是 Baostock 格式
        assert fetcher._convert_index_code("sh.000300") == "sh.000300"

    def test_convert_etf_code(self):
        """测试 ETF 代码转换"""
        fetcher = BaostockFetcher()

        # 测试 ETF 代码转换
        assert fetcher._convert_etf_code("518880") == "sh.518880"

        # 测试已经是 Baostock 格式
        assert fetcher._convert_etf_code("sh.518880") == "sh.518880"

    def test_convert_stock_code(self):
        """测试股票代码转换"""
        fetcher = BaostockFetcher()

        # 测试上海交易所股票
        assert fetcher._convert_stock_code("600000") == "sh.600000"

        # 测试深圳交易所主板
        assert fetcher._convert_stock_code("002594") == "sz.002594"

        # 测试深圳交易所创业板
        assert fetcher._convert_stock_code("300001") == "sz.300001"

        # 测试已经是 Baostock 格式
        assert fetcher._convert_stock_code("sz.002594") == "sz.002594"

    def test_format_date(self):
        """测试日期格式化"""
        fetcher = BaostockFetcher()

        assert fetcher._format_date(date(2024, 1, 1)) == "2024-01-01"
        assert fetcher._format_date(None) == ""

    def test_standardize_dataframe(self, sample_df):
        """测试 DataFrame 标准化"""
        fetcher = BaostockFetcher()
        result = fetcher._standardize_dataframe(sample_df)

        # 验证日期类型
        assert pd.api.types.is_datetime64_any_dtype(result["date"])

        # 验证数值类型
        for col in ["open", "high", "low", "close", "volume"]:
            assert pd.api.types.is_numeric_dtype(result[col])

    def test_filter_by_date(self, sample_df):
        """测试日期过滤"""
        fetcher = BaostockFetcher()

        # 过滤后的数据
        result = fetcher._filter_by_date(
            sample_df,
            start_date=date(2024, 1, 2),
            end_date=date(2024, 1, 4),
        )

        # 应该只有3条数据
        assert len(result) == 3

    def test_login_logout(self):
        """测试登录登出功能"""
        fetcher = BaostockFetcher()

        # 测试登录（类级别）
        initial_count = BaostockFetcher._login_count
        fetcher._ensure_login()
        assert BaostockFetcher._login_count > initial_count

        # 测试登出（类级别）
        fetcher._safe_logout()
        assert BaostockFetcher._login_count == initial_count

    def test_multi_instance_login(self):
        """测试多实例登录管理"""
        # 重置登录计数
        BaostockFetcher._login_count = 0

        fetcher1 = BaostockFetcher()
        fetcher2 = BaostockFetcher()

        # 两个实例都调用 _ensure_login
        fetcher1._ensure_login()
        count1 = BaostockFetcher._login_count

        fetcher2._ensure_login()
        count2 = BaostockFetcher._login_count

        # 登录计数应该增加
        assert count2 >= count1

        # 清理
        while BaostockFetcher._login_count > 0:
            BaostockFetcher._safe_logout()


class TestAKShareFetcher:
    """AKShare 获取器测试（保留作为备用）"""

    def test_init_default_config(self):
        """测试默认配置初始化"""
        fetcher = AKShareFetcher()
        assert fetcher.config is not None
        assert fetcher.config.source == "akshare"

    def test_init_custom_config(self, fetcher_config):
        """测试自定义配置初始化"""
        fetcher = AKShareFetcher(config=fetcher_config)
        assert fetcher.config == fetcher_config
