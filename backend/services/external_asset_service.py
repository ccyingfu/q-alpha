"""
外部资产搜索服务

使用 Baostock 从外部查询资产信息。
Baostock 是证券宝提供的免费数据接口，无需注册、无限制调用。
"""

import logging
import re
from typing import List, Optional

import baostock as bs
import pandas as pd

from backend.schemas.asset import ExternalAssetSearchResult

logger = logging.getLogger(__name__)


class ExternalAssetService:
    """外部资产搜索服务（基于 Baostock）"""

    # 类级别的登录状态管理
    _login_count = 0

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
        搜索股票信息（使用 Baostock）

        Args:
            query: 查询字符串（代码或名称）
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        try:
            ExternalAssetService._ensure_login()

            # 获取所有A股列表
            rs = bs.query_stock_basic()

            if rs.error_code != "0":
                logger.error(f"Baostock 查询股票列表失败: {rs.error_msg}")
                return []

            # 转换为 DataFrame
            data_list = []
            while (rs.error_code == "0") & rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 按代码或名称搜索
            query_upper = query.upper()
            if query.isdigit():
                # 纯数字，按代码搜索
                results = df[df["code"].str.contains(query, na=False)]
            else:
                # 按名称或代码搜索
                results = df[
                    df["code"].str.contains(query_upper, na=False) |
                    df["code_name"].str.contains(query, na=False)
                ]

            # 限制结果数量
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
        finally:
            ExternalAssetService._safe_logout()

    @staticmethod
    def search_indices(query: str, limit: int = 10) -> List[ExternalAssetSearchResult]:
        """
        搜索指数信息（使用 Baostock）

        Args:
            query: 查询字符串
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        try:
            ExternalAssetService._ensure_login()

            # Baostock 获取所有证券列表，然后过滤指数
            rs = bs.query_stock_basic()

            if rs.error_code != "0":
                logger.error(f"Baostock 查询指数列表失败: {rs.error_msg}")
                return []

            # 转换为 DataFrame
            data_list = []
            while (rs.error_code == "0") & rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 指数代码通常以 000, 399 开头
            index_df = df[df["code"].str.match(r"^(sh\.(000|88|98)|sz\.(399|99))", na=False)]

            # 按代码或名称搜索
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
        finally:
            ExternalAssetService._safe_logout()

    @staticmethod
    def search_etfs(query: str, limit: int = 10) -> List[ExternalAssetSearchResult]:
        """
        搜索 ETF 信息（使用 Baostock）

        Args:
            query: 查询字符串
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        try:
            ExternalAssetService._ensure_login()

            # Baostock 获取所有证券列表，然后过滤 ETF
            rs = bs.query_stock_basic()

            if rs.error_code != "0":
                logger.error(f"Baostock 查询ETF列表失败: {rs.error_msg}")
                return []

            # 转换为 DataFrame
            data_list = []
            while (rs.error_code == "0") & rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)

            # ETF 代码通常以 51, 52, 15, 16, 56, 159 开头
            etf_df = df[df["code"].str.match(r"^(sh\.(5[0-9])|sz\.(15|16|159|56))", na=False)]

            # 按代码或名称搜索
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
        finally:
            ExternalAssetService._safe_logout()

    @staticmethod
    def search(query: str, asset_type: Optional[str] = None, limit: int = 10) -> List[ExternalAssetSearchResult]:
        """
        综合搜索资产

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
        results: List[ExternalAssetSearchResult] = []

        # 根据类型过滤搜索
        if asset_type == "stock" or asset_type is None:
            results.extend(ExternalAssetService.search_stocks(query, limit))

        if asset_type == "index" or asset_type is None:
            results.extend(ExternalAssetService.search_indices(query, limit))

        if asset_type == "etf" or asset_type is None:
            results.extend(ExternalAssetService.search_etfs(query, limit))

        # 去重并限制数量
        seen = set()
        unique_results = []
        for r in results:
            if r.code not in seen:
                seen.add(r.code)
                unique_results.append(r)

        return unique_results[:limit]
