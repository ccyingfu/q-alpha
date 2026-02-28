"""
资产管理接口
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from database.repositories import AssetRepository
from database.models import Asset, AssetType
from backend.schemas import AssetCreate, AssetResponse, AssetUpdate

router = APIRouter()


@router.get("/", response_model=List[AssetResponse])
async def list_assets(
    asset_type: str = None,
    db: Session = Depends(get_db),
):
    """
    获取所有资产列表

    可选按类型过滤。
    """
    repo = AssetRepository(db)

    if asset_type:
        try:
            asset_type_enum = AssetType(asset_type)
            assets = repo.get_by_type(asset_type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid asset type: {asset_type}")
    else:
        assets = repo.get_all()

    return assets


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
):
    """根据 ID 获取资产"""
    repo = AssetRepository(db)
    asset = repo.get_by_id(asset_id)

    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

    return asset


@router.get("/code/{asset_code}", response_model=AssetResponse)
async def get_asset_by_code(
    asset_code: str,
    db: Session = Depends(get_db),
):
    """根据代码获取资产"""
    repo = AssetRepository(db)
    asset = repo.get_by_code(asset_code)

    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_code} not found")

    return asset


@router.post("/", response_model=AssetResponse)
async def create_asset(
    asset_data: AssetCreate,
    db: Session = Depends(get_db),
):
    """创建新资产"""
    repo = AssetRepository(db)

    # 检查代码是否已存在
    existing = repo.get_by_code(asset_data.code)
    if existing:
        raise HTTPException(status_code=400, detail=f"Asset code {asset_data.code} already exists")

    # 创建资产
    asset = Asset(
        code=asset_data.code,
        name=asset_data.name,
        type=asset_data.type,
        description=asset_data.description,
    )

    return repo.create(asset)


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    asset_data: AssetUpdate,
    db: Session = Depends(get_db),
):
    """更新资产信息"""
    repo = AssetRepository(db)
    asset = repo.get_by_id(asset_id)

    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

    # 更新字段
    if asset_data.name is not None:
        asset.name = asset_data.name
    if asset_data.description is not None:
        asset.description = asset_data.description

    return repo.update(asset)


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
):
    """删除资产"""
    repo = AssetRepository(db)
    asset = repo.get_by_id(asset_id)

    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

    repo.delete(asset)
    return {"message": f"Asset {asset_id} deleted successfully"}
