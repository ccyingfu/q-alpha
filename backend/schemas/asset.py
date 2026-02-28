"""
资产 Schema
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AssetBase(BaseModel):
    """资产基础模型"""

    code: str = Field(..., description="资产代码")
    name: str = Field(..., description="资产名称")
    type: str = Field(..., description="资产类型")
    description: Optional[str] = Field(None, description="描述信息")


class AssetCreate(AssetBase):
    """创建资产请求"""

    pass


class AssetUpdate(BaseModel):
    """更新资产请求"""

    name: Optional[str] = None
    description: Optional[str] = None


class AssetResponse(AssetBase):
    """资产响应"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
