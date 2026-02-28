"""
外部资产搜索服务

使用 akshare 等数据源从外部查询资产信息。
"""

import logging
import re
from typing import List, Optional

import akshare as ak

from backend.schemas.asset import ExternalAssetSearchResult

logger = logging.getLogger(__name__)


class ExternalAssetService:
    """外部资产搜索服务"""

    # A股代码前缀规则
    STOCK_CODE_PREFIXES = {
        "0": "stock",  # 深圳主板
        "2": "stock",  # 深圳B股
        "3": "stock",  # 创业板
        "6": "stock",  # 上海主板
        "8": "stock",  # 上海B股
    }

    # 指数代码规则
    INDEX_CODE_PREFIXES = {
        "000": "index",  # 深证指数
        "001": "index",  # 国证指数
        "399": "index",  # 深证指数
        "000300": "index",  # 沪深300
        "000905": "index",  # 中证500
    }

    # ETF代码规则
    ETF_CODE_PREFIXES = {
        "5": "etf",  # 上海ETF
        "15": "etf",  # 深圳ETF
        "56": "etf",  # 深圳ETF
        "159": "etf",  # 深圳ETF
    }

    @staticmethod
    def _guess_asset_type(code: str) -> str:
        """
        根据代码推测资产类型

        Args:
            code: 资产代码

        Returns:
            资产类型
        """
        code = code.strip().upper()

        # ETF 判断
        if code.startswith("5") or code.startswith("15") or code.startswith("56") or code.startswith("159"):
            return "etf"

        # 指数判断
        if code.startswith("000") or code.startswith("001") or code.startswith("399"):
            return "index"

        # 默认为股票
        return "stock"

    @staticmethod
    def search_stocks(query: str, limit: int = 10) -> List[ExternalAssetSearchResult]:
        """
        搜索股票信息

        Args:
            query: 查询字符串（代码或名称）
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        try:
            # 获取所有A股列表
            df = ak.stock_info_a_code_name()

            # 按代码或名称搜索
            if query.isdigit():
                # 纯数字，按代码搜索
                results = df[df["code"].str.contains(query, na=False)]
            else:
                # 按名称搜索
                results = df[df["name"].str.contains(query, na=False)]

            # 限制结果数量
            results = results.head(limit)

            return [
                ExternalAssetSearchResult(
                    code=row["code"],
                    name=row["name"],
                    type=ExternalAssetService._guess_asset_type(row["code"]),
                    source="akshare",
                )
                for _, row in results.iterrows()
            ]
        except Exception as e:
            logger.error(f"搜索股票失败: {query}, 错误: {e}")
            return []

    @staticmethod
    def search_indices(query: str, limit: int = 10) -> List[ExternalAssetSearchResult]:
        """
        搜索指数信息

        Args:
            query: 查询字符串
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        try:
            # 获取指数列表
            df = ak.index_stock_info()

            # 按代码或名称搜索
            if query.isdigit():
                results = df[df["index_code"].str.contains(query, na=False)]
            else:
                results = df[df["index_name"].str.contains(query, na=False)]

            results = results.head(limit)

            return [
                ExternalAssetSearchResult(
                    code=row["index_code"],
                    name=row["index_name"],
                    type="index",
                    source="akshare",
                )
                for _, row in results.iterrows()
            ]
        except Exception as e:
            logger.error(f"搜索指数失败: {query}, 错误: {e}")
            return []

    @staticmethod
    def search_etfs(query: str, limit: int = 10) -> List[ExternalAssetSearchResult]:
        """
        搜索 ETF 信息

        Args:
            query: 查询字符串
            limit: 返回结果数量限制

        Returns:
            搜索结果列表
        """
        try:
            # 获取ETF列表
            df = ak.fund_etf_category_sina(symbol="ETF基金")

            # 按代码或名称搜索
            if query.isdigit():
                results = df[df["代码"].str.contains(query, na=False)]
            else:
                results = df[df["名称"].str.contains(query, na=False)]

            results = results.head(limit)

            return [
                ExternalAssetSearchResult(
                    code=row["代码"],
                    name=row["名称"],
                    type="etf",
                    source="akshare",
                )
                for _, row in results.iterrows()
            ]
        except Exception as e:
            logger.error(f"搜索ETF失败: {query}, 错误: {e}")
            return []

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
