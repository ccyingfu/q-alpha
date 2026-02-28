"""
缓存管理器

提供本地缓存功能，避免重复获取相同数据。
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
from pydantic import BaseModel


class CacheMetadata(BaseModel):
    """缓存元数据"""

    file_path: str
    created_at: datetime
    expires_at: datetime
    rows: int
    data_range: dict  # {"start": "2020-01-01", "end": "2024-01-01"}


class CacheManager:
    """
    缓存管理器

    使用本地文件系统缓存数据，支持增量更新。
    """

    def __init__(
        self,
        cache_dir: Path,
        expire_hours: int = 24,
    ):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录路径
            expire_hours: 缓存过期时间（小时）
        """
        self.cache_dir = Path(cache_dir)
        self.expire_hours = expire_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 元数据目录
        self.meta_dir = self.cache_dir / ".meta"
        self.meta_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, data_type: str, code: str) -> str:
        """
        生成缓存键

        Args:
            data_type: 数据类型 (index/etf/stock)
            code: 代码

        Returns:
            缓存键
        """
        return f"{data_type}_{code}"

    def _get_cache_path(self, cache_key: str) -> Path:
        """
        获取缓存文件路径

        Args:
            cache_key: 缓存键

        Returns:
            缓存文件路径
        """
        return self.cache_dir / f"{cache_key}.parquet"

    def _get_meta_path(self, cache_key: str) -> Path:
        """
        获取元数据文件路径

        Args:
            cache_key: 缓存键

        Returns:
            元数据文件路径
        """
        return self.meta_dir / f"{cache_key}.json"

    def get(self, data_type: str, code: str) -> Optional[pd.DataFrame]:
        """
        获取缓存数据

        Args:
            data_type: 数据类型
            code: 代码

        Returns:
            缓存的 DataFrame，如果缓存不存在或已过期返回 None
        """
        cache_key = self._get_cache_key(data_type, code)
        cache_path = self._get_cache_path(cache_key)
        meta_path = self._get_meta_path(cache_key)

        # 检查缓存文件是否存在
        if not cache_path.exists() or not meta_path.exists():
            return None

        # 读取元数据
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = CacheMetadata.model_validate_json(f.read())
        except Exception:
            return None

        # 检查是否过期
        if datetime.now() > meta.expires_at:
            return None

        # 读取缓存数据
        try:
            df = pd.read_parquet(cache_path)
            return df
        except Exception:
            return None

    def set(
        self,
        data_type: str,
        code: str,
        df: pd.DataFrame,
    ) -> None:
        """
        保存数据到缓存

        Args:
            data_type: 数据类型
            code: 代码
            df: 要缓存的数据
        """
        cache_key = self._get_cache_key(data_type, code)
        cache_path = self._get_cache_path(cache_key)
        meta_path = self._get_meta_path(cache_key)

        # 保存数据
        df.to_parquet(cache_path, index=False)

        # 保存元数据
        meta = CacheMetadata(
            file_path=str(cache_path),
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=self.expire_hours),
            rows=len(df),
            data_range={
                "start": df["date"].min().strftime("%Y-%m-%d"),
                "end": df["date"].max().strftime("%Y-%m-%d"),
            },
        )

        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(meta.model_dump_json(indent=2))

    def update(
        self,
        data_type: str,
        code: str,
        new_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        增量更新缓存

        合并已有数据和新数据，避免重复。

        Args:
            data_type: 数据类型
            code: 代码
            new_df: 新获取的数据

        Returns:
            合并后的完整数据
        """
        existing_df = self.get(data_type, code)

        if existing_df is None:
            # 没有缓存，直接保存新数据
            merged_df = new_df
        else:
            # 合并数据，去重
            merged_df = pd.concat([existing_df, new_df], ignore_index=True)
            merged_df = merged_df.drop_duplicates(subset=["date"]).sort_values("date")
            merged_df = merged_df.reset_index(drop=True)

        # 保存合并后的数据
        self.set(data_type, code, merged_df)

        return merged_df

    def clear(self, data_type: Optional[str] = None, code: Optional[str] = None) -> None:
        """
        清除缓存

        Args:
            data_type: 数据类型，None 表示清除所有
            code: 代码，None 表示清除指定类型的所有缓存
        """
        if data_type is None:
            # 清除所有缓存
            for file in self.cache_dir.glob("*.parquet"):
                file.unlink()
            for file in self.meta_dir.glob("*.json"):
                file.unlink()
        elif code is None:
            # 清除指定类型的所有缓存
            prefix = f"{data_type}_"
            for file in self.cache_dir.glob(f"{prefix}*.parquet"):
                file.unlink()
            for file in self.meta_dir.glob(f"{prefix}*.json"):
                file.unlink()
        else:
            # 清除指定缓存
            cache_key = self._get_cache_key(data_type, code)
            cache_path = self._get_cache_path(cache_key)
            meta_path = self._get_meta_path(cache_key)

            if cache_path.exists():
                cache_path.unlink()
            if meta_path.exists():
                meta_path.unlink()
