"""
缓存管理器单元测试
"""

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from data_fetcher.cache_manager import CacheManager, CacheMetadata


@pytest.fixture
def temp_cache_dir(tmp_path):
    """创建临时缓存目录"""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


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


class TestCacheManager:
    """缓存管理器测试"""

    def test_init(self, temp_cache_dir):
        """测试初始化"""
        cache_mgr = CacheManager(cache_dir=temp_cache_dir, expire_hours=24)
        assert cache_mgr.cache_dir == temp_cache_dir
        assert cache_mgr.expire_hours == 24
        assert temp_cache_dir.exists()

    def test_set_and_get(self, temp_cache_dir, sample_df):
        """测试设置和获取缓存"""
        cache_mgr = CacheManager(cache_dir=temp_cache_dir, expire_hours=24)

        # 设置缓存
        cache_mgr.set("index", "000300", sample_df)

        # 获取缓存
        cached_df = cache_mgr.get("index", "000300")

        # 验证数据
        assert cached_df is not None
        assert len(cached_df) == len(sample_df)
        assert list(cached_df.columns) == list(sample_df.columns)

    def test_cache_expiry(self, temp_cache_dir, sample_df):
        """测试缓存过期"""
        # 创建已过期的缓存
        cache_mgr = CacheManager(cache_dir=temp_cache_dir, expire_hours=-1)

        # 设置缓存（立即过期）
        cache_mgr.set("index", "000300", sample_df)

        # 获取缓存应该返回 None
        cached_df = cache_mgr.get("index", "000300")
        assert cached_df is None

    def test_update_incremental(self, temp_cache_dir, sample_df):
        """测试增量更新"""
        cache_mgr = CacheManager(cache_dir=temp_cache_dir, expire_hours=24)

        # 初始数据（前3条）
        initial_df = sample_df.iloc[:3].copy()
        cache_mgr.set("index", "000300", initial_df)

        # 新增数据（后2条）
        new_df = sample_df.iloc[3:].copy()
        merged_df = cache_mgr.update("index", "000300", new_df)

        # 验证合并后的数据
        assert len(merged_df) == 5
        assert len(merged_df.drop_duplicates(subset=["date"])) == 5

    def test_clear_all(self, temp_cache_dir, sample_df):
        """测试清除所有缓存"""
        cache_mgr = CacheManager(cache_dir=temp_cache_dir, expire_hours=24)

        # 设置多个缓存
        cache_mgr.set("index", "000300", sample_df)
        cache_mgr.set("etf", "518880", sample_df)

        # 清除所有
        cache_mgr.clear()

        # 验证缓存已清除
        assert cache_mgr.get("index", "000300") is None
        assert cache_mgr.get("etf", "518880") is None

    def test_clear_by_type(self, temp_cache_dir, sample_df):
        """测试按类型清除缓存"""
        cache_mgr = CacheManager(cache_dir=temp_cache_dir, expire_hours=24)

        # 设置多个缓存
        cache_mgr.set("index", "000300", sample_df)
        cache_mgr.set("index", "000905", sample_df)
        cache_mgr.set("etf", "518880", sample_df)

        # 清除 index 类型
        cache_mgr.clear(data_type="index")

        # 验证 index 缓存已清除，etf 缓存还在
        assert cache_mgr.get("index", "000300") is None
        assert cache_mgr.get("index", "000905") is None
        assert cache_mgr.get("etf", "518880") is not None

    def test_clear_by_code(self, temp_cache_dir, sample_df):
        """测试按代码清除缓存"""
        cache_mgr = CacheManager(cache_dir=temp_cache_dir, expire_hours=24)

        # 设置缓存
        cache_mgr.set("index", "000300", sample_df)
        cache_mgr.set("index", "000905", sample_df)

        # 清除指定代码
        cache_mgr.clear(data_type="index", code="000300")

        # 验证只有指定的缓存被清除
        assert cache_mgr.get("index", "000300") is None
        assert cache_mgr.get("index", "000905") is not None
