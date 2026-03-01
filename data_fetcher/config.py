"""
数据获取模块配置
"""

from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings


class FetcherConfig(BaseSettings):
    """数据获取器配置"""

    # 缓存配置
    cache_dir: Path = Field(default=Path("./data/cache"), description="缓存目录路径")
    cache_expire_hours: int = Field(default=24, description="缓存过期时间（小时）")
    enable_cache: bool = Field(default=True, description="是否启用缓存")

    # 网络请求配置
    timeout: int = Field(default=30, description="请求超时时间（秒）")
    max_retries: int = Field(default=3, description="最大重试次数")

    # 数据格式
    output_format: Literal["dataframe", "dict"] = Field(
        default="dataframe", description="输出格式"
    )

    class Config:
        env_prefix = "FETCHER_"
        env_file = ".env"
        extra = "ignore"  # 忽略额外的环境变量
