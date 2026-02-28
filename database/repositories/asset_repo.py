"""
资产仓储
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from database.models.asset import Asset, AssetType


class AssetRepository:
    """资产数据仓储"""

    def __init__(self, db: Session):
        """
        初始化仓储

        Args:
            db: 数据库会话
        """
        self.db = db

    def create(self, asset: Asset) -> Asset:
        """
        创建资产

        Args:
            asset: 资产对象

        Returns:
            创建的资产对象
        """
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def get_by_id(self, asset_id: int) -> Optional[Asset]:
        """
        根据 ID 获取资产

        Args:
            asset_id: 资产 ID

        Returns:
            资产对象或 None
        """
        return self.db.query(Asset).filter(Asset.id == asset_id).first()

    def get_by_code(self, code: str) -> Optional[Asset]:
        """
        根据代码获取资产

        Args:
            code: 资产代码

        Returns:
            资产对象或 None
        """
        return self.db.query(Asset).filter(Asset.code == code).first()

    def get_all(self) -> List[Asset]:
        """
        获取所有资产

        Returns:
            资产列表
        """
        return self.db.query(Asset).all()

    def get_by_type(self, asset_type: AssetType) -> List[Asset]:
        """
        根据类型获取资产

        Args:
            asset_type: 资产类型

        Returns:
            资产列表
        """
        return self.db.query(Asset).filter(Asset.type == asset_type).all()

    def update(self, asset: Asset) -> Asset:
        """
        更新资产

        Args:
            asset: 资产对象

        Returns:
            更新后的资产对象
        """
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def delete(self, asset: Asset) -> None:
        """
        删除资产

        Args:
            asset: 资产对象
        """
        self.db.delete(asset)
        self.db.commit()

    def bulk_create(self, assets: List[Asset]) -> List[Asset]:
        """
        批量创建资产

        Args:
            assets: 资产对象列表

        Returns:
            创建的资产对象列表
        """
        self.db.bulk_save_objects(assets)
        self.db.commit()
        return assets
