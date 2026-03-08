"""
Q-Alpha 数据获取模块

混合数据源策略：
- 股票/指数：Baostock（稳定、无需注册）
- ETF：AKShare（支持 ETF，带重试机制和缓存）
"""

from .base import DataFetcher
from .baostock_fetcher import BaostockFetcher
from .akshare_etf_fetcher import AKShareETFFetcher
from .cache_manager import CacheManager
from .config import FetcherConfig

__all__ = [
    "DataFetcher",
    "BaostockFetcher",
    "AKShareETFFetcher",
    "CacheManager",
    "FetcherConfig",
]
