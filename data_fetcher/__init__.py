"""
Q-Alpha 数据获取模块

提供从 AKShare、Baostock 等数据源获取金融数据的能力。
"""

from .base import DataFetcher
from .akshare_fetcher import AKShareFetcher
from .baostock_fetcher import BaostockFetcher
from .cache_manager import CacheManager
from .config import FetcherConfig

__all__ = [
    "DataFetcher",
    "BaostockFetcher",  # 主要数据源
    "AKShareFetcher",   # 备用数据源
    "CacheManager",
    "FetcherConfig",
]
