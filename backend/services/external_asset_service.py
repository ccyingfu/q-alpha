"""
外部资产搜索服务

使用 Baostock 从外部查询资产信息。
Baostock 是证券宝提供的免费数据接口，无需注册、无限制调用。
"""

import logging
import re
import threading
import time
from typing import List, Optional

import baostock as bs
import pandas as pd

from backend.schemas.asset import ExternalAssetSearchResult

logger = logging.getLogger(__name__)


class ExternalAssetService:
    """外部资产搜索服务（基于 Baostock）"""

    # 类级别的登录状态管理
    _login_count = 0

    # 缓存相关
    _cache_lock = threading.RLock()
    _stock_df_cache: Optional[pd.DataFrame] = None
    _cache_time: float = 0
    _cache_ttl = 3600  # 缓存1小时

    @classmethod
    def _ensure_login(cls):
        """确保已登录 Baostock"""
        if cls._login_count == 0:
            lg = bs.login()
            if lg.error_code != "0":
                raise RuntimeError(f"Baostock 登录失败: {lg.error_msg}")
            logger.info("Baostock 登录成功（搜索服务）")
        cls._login_count += 1

    @classmethod
    def _safe_logout(cls):
        """安全登出 Baostock"""
        if cls._login_count > 0:
            cls._login_count -= 1
            if cls._login_count == 0:
                try:
                    bs.logout()
                    logger.info("Baostock 登出成功（搜索服务）")
                except Exception as e:
                    logger.warning(f"Baostock 登出时出现警告: {e}")

    @classmethod
    def _get_stock_df(cls) -> Optional[pd.DataFrame]:
        """
        获取股票数据 DataFrame（带缓存）

        Returns:
            股票数据的 DataFrame，如果获取失败则返回 None
        """
        current_time = time.time()

        # 检查缓存是否有效
        with cls._cache_lock:
            if cls._stock_df_cache is not None and (current_time - cls._cache_time) < cls._cache_ttl:
                return cls._stock_df_cache

        # 缓存过期或不存在，重新获取
        try:
            cls._ensure_login()

            rs = bs.query_stock_basic()
            if rs.error_code != "0":
                logger.error(f"Baostock 查询股票列表失败: {rs.error_msg}")
                return None

            data_list = []
            while (rs.error_code == "0") & rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 更新缓存
            with cls._cache_lock:
                cls._stock_df_cache = df
                cls._cache_time = current_time
                logger.info(f"Baostock 股票列表缓存已更新，共 {len(df)} 条记录")

            return df

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return None
        finally:
            cls._safe_logout()

    @classmethod
    def clear_cache(cls):
        """清除缓存"""
        with cls._cache_lock:
            cls._stock_df_cache = None
            cls._cache_time = 0

    @staticmethod
    def _guess_asset_type(code: str) -> str:
        """
        根据代码推测资产类型

        Args:
            code: 资产代码

        Returns:
            资产类型
        """
        code = code.strip()

        # ETF 判断
        if code.startswith("5") or code.startswith("15") or code.startswith("56") or code.startswith("159"):
            return "etf"

        # 指数判断
        if code.startswith("000") or code.startswith("001") or code.startswith("399"):
            return "index"

        # 默认为股票
        return "stock"

    @staticmethod
    def _normalize_code(code: str) -> str:
        """
        规范化资产代码，去除市场前缀

        Args:
            code: 原始代码（如 sh.600745 或 sh600745）

        Returns:
            规范化后的纯数字代码（如 600745）
        """
        code = code.strip()
        
        # 去除带点号的市场前缀（如 sh.600745 -> 600745）
        dot_prefixes = ["sh.", "sz.", "bj.", "SH.", "SZ.", "BJ."]
        for prefix in dot_prefixes:
            if code.upper().startswith(prefix.upper()):
                code = code[len(prefix):]
                return code
        
        # 去除不带点号的市场前缀（如 sh600745 -> 600745）
        prefixes = ["sh", "sz", "bj", "SH", "SZ", "BJ"]
        for prefix in prefixes:
            if code.lower().startswith(prefix.lower()):
                code = code[len(prefix):]
                break
        
        return code

    @staticmethod
    def search_stocks(query: str, limit: int = 10) -> List[ExternalAssetSearchResult]:
        """
        搜索股票信息（使用缓存的 Baostock 数据）

        Args:
            query: 查询字符串（代码或名称）
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        df = ExternalAssetService._get_stock_df()
        if df is None:
            return []

        try:
            # 按代码或名称搜索
            query_upper = query.upper()
            if query.isdigit():
                results = df[df["code"].str.contains(query, na=False)]
            else:
                results = df[
                    df["code"].str.contains(query_upper, na=False) |
                    df["code_name"].str.contains(query, na=False)
                ]

            results = results.head(limit)

            return [
                ExternalAssetSearchResult(
                    code=ExternalAssetService._normalize_code(row["code"]),
                    name=row["code_name"],
                    type=ExternalAssetService._guess_asset_type(row["code"]),
                    source="baostock",
                )
                for _, row in results.iterrows()
            ]
        except Exception as e:
            logger.error(f"搜索股票失败: {query}, 错误: {e}")
            return []

    @staticmethod
    def search_indices(query: str, limit: int = 10) -> List[ExternalAssetSearchResult]:
        """
        搜索指数信息（使用缓存的 Baostock 数据）

        Args:
            query: 查询字符串
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        df = ExternalAssetService._get_stock_df()
        if df is None:
            return []

        try:
            # 指数代码通常以 000, 399 开头
            index_df = df[df["code"].str.match(r"^(sh\.(000|88|98)|sz\.(399|99))", na=False)]

            if query.isdigit():
                results = index_df[index_df["code"].str.contains(query, na=False)]
            else:
                results = index_df[
                    index_df["code"].str.contains(query.upper(), na=False) |
                    index_df["code_name"].str.contains(query, na=False)
                ]

            results = results.head(limit)

            return [
                ExternalAssetSearchResult(
                    code=ExternalAssetService._normalize_code(row["code"]),
                    name=row["code_name"],
                    type="index",
                    source="baostock",
                )
                for _, row in results.iterrows()
            ]
        except Exception as e:
            logger.error(f"搜索指数失败: {query}, 错误: {e}")
            return []

    @staticmethod
    def search_etfs(query: str, limit: int = 10) -> List[ExternalAssetSearchResult]:
        """
        搜索 ETF 信息（使用缓存的 Baostock 数据）

        Args:
            query: 查询字符串
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        df = ExternalAssetService._get_stock_df()
        if df is None:
            return []

        try:
            # ETF 代码通常以 51, 52, 15, 16, 56, 159 开头
            etf_df = df[df["code"].str.match(r"^(sh\.(5[0-9])|sz\.(15|16|159|56))", na=False)]

            if query.isdigit():
                results = etf_df[etf_df["code"].str.contains(query, na=False)]
            else:
                results = etf_df[
                    etf_df["code"].str.contains(query.upper(), na=False) |
                    etf_df["code_name"].str.contains(query, na=False)
                ]

            results = results.head(limit)

            return [
                ExternalAssetSearchResult(
                    code=ExternalAssetService._normalize_code(row["code"]),
                    name=row["code_name"],
                    type="etf",
                    source="baostock",
                )
                for _, row in results.iterrows()
            ]
        except Exception as e:
            logger.error(f"搜索ETF失败: {query}, 错误: {e}")
            return []

    @staticmethod
    def search(query: str, asset_type: Optional[str] = None, limit: int = 10) -> List[ExternalAssetSearchResult]:
        """
        综合搜索资产（优化版本：一次性从缓存获取并过滤）

        Args:
            query: 查询字符串
            asset_type: 资产类型过滤
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        if not query or not query.strip():
            return []

        query = query.strip()

        # 获取缓存的数据
        df = ExternalAssetService._get_stock_df()
        if df is None:
            return []

        try:
            # 根据类型过滤
            if asset_type == "stock":
                # 股票：排除指数和ETF
                filtered_df = df[
                    ~df["code"].str.match(r"^(sh\.(000|88|98)|sz\.(399|99))", na=False) &
                    ~df["code"].str.match(r"^(sh\.(5[0-9])|sz\.(15|16|159|56))", na=False)
                ]
            elif asset_type == "index":
                # 指数
                filtered_df = df[df["code"].str.match(r"^(sh\.(000|88|98)|sz\.(399|99))", na=False)]
            elif asset_type == "etf":
                # ETF
                filtered_df = df[df["code"].str.match(r"^(sh\.(5[0-9])|sz\.(15|16|159|56))", na=False)]
            else:
                # 不过滤类型，返回全部
                filtered_df = df

            # 按代码或名称搜索
            query_upper = query.upper()
            if query.isdigit():
                results = filtered_df[filtered_df["code"].str.contains(query, na=False)]
            else:
                results = filtered_df[
                    filtered_df["code"].str.contains(query_upper, na=False) |
                    filtered_df["code_name"].str.contains(query, na=False)
                ]

            results = results.head(limit)

            return [
                ExternalAssetSearchResult(
                    code=ExternalAssetService._normalize_code(row["code"]),
                    name=row["code_name"],
                    type=asset_type if asset_type else ExternalAssetService._guess_asset_type(row["code"]),
                    source="baostock",
                )
                for _, row in results.iterrows()
            ]
        except Exception as e:
            logger.error(f"搜索失败: {query}, 错误: {e}")
            return []
