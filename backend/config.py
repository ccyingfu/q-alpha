"""
后端配置

从环境变量或默认值加载配置。
"""

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用设置"""

    # API 配置
    api_host: str = Field(default="0.0.0.0", description="API 主机")
    api_port: int = Field(default=8000, description="API 端口")
    api_reload: bool = Field(default=True, description="自动重载")

    # CORS 配置
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="允许的 CORS 源",
    )

    # 数据库配置
    database_url: str = Field(default="sqlite:///q_alpha.db", description="数据库 URL")

    # 回测配置
    risk_free_rate: float = Field(default=0.03, description="无风险利率")
    trading_days_per_year: int = Field(default=252, description="每年交易日数")

    # 数据获取配置
    cache_dir: str = Field(default="./data/cache", description="缓存目录")
    enable_cache: bool = Field(default=True, description="启用缓存")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略额外的环境变量


# 创建全局设置实例
settings = Settings()
