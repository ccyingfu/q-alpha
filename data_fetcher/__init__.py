"""
Q-Alpha 数据获取模块

提供从 AKShare 等数据源获取金融数据的能力。
"""

from .base import DataFetcher
from .akshare_fetcher import AKShareFetcher
from .cache_manager import CacheManager
from .config import FetcherConfig

__all__ = [
    "DataFetcher",
    "AKShareFetcher",
    "CacheManager",
    "FetcherConfig",
]
