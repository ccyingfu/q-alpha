"""
市场行情数据仓储
"""

from datetime import date, datetime
from typing import List, Optional

from pandas import DataFrame
from sqlalchemy import and_
from sqlalchemy.orm import Session

from database.models.market_data import MarketDaily


class MarketDataRepository:
    """市场行情数据仓储"""

    def __init__(self, db: Session):
        """
        初始化仓储

        Args:
            db: 数据库会话
        """
        self.db = db

    def create(self, data: MarketDaily) -> MarketDaily:
        """
        创建行情数据

        Args:
            data: 行情数据对象

        Returns:
            创建的行情数据对象
        """
        self.db.add(data)
        self.db.commit()
        self.db.refresh(data)
        return data

    def bulk_create(self, data_list: List[MarketDaily]) -> List[MarketDaily]:
        """
        批量创建行情数据

        Args:
            data_list: 行情数据对象列表

        Returns:
            创建的行情数据对象列表
        """
        self.db.bulk_save_objects(data_list)
        self.db.commit()
        return data_list

    def bulk_create_from_df(
        self, df: DataFrame, asset_id: int
    ) -> List[MarketDaily]:
        """
        从 DataFrame 批量创建行情数据

        Args:
            df: 包含行情数据的 DataFrame
            asset_id: 资产 ID

        Returns:
            创建的行情数据对象列表
        """
        data_list = []
        for _, row in df.iterrows():
            # 确保日期只包含日期部分，没有时间部分
            date_val = row["date"]
            if hasattr(date_val, 'date'):
                # pandas Timestamp 或 datetime，提取日期部分
                date_val = date_val.date() if hasattr(date_val, 'date') else date_val
            
            data = MarketDaily(
                asset_id=asset_id,
                date=date_val,
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
            )
            data_list.append(data)

        return self.bulk_create(data_list)

    def get_by_id(self, data_id: int) -> Optional[MarketDaily]:
        """
        根据 ID 获取行情数据

        Args:
            data_id: 数据 ID

        Returns:
            行情数据对象或 None
        """
        return self.db.query(MarketDaily).filter(MarketDaily.id == data_id).first()

    def get_by_asset(
        self,
        asset_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[MarketDaily]:
        """
        根据资产 ID 获取行情数据

        Args:
            asset_id: 资产 ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            行情数据列表
        """
        from sqlalchemy import func
        
        query = self.db.query(MarketDaily).filter(MarketDaily.asset_id == asset_id)

        # 使用日期部分进行比较，避免时间部分的影响
        # 安全提取日期部分（兼容 datetime 和 date 类型）
        def to_date(d):
            if d is None:
                return None
            if isinstance(d, date) and not isinstance(d, datetime):
                return d
            return d.date()

        if start_date:
            query = query.filter(func.date(MarketDaily.date) >= to_date(start_date))
        if end_date:
            query = query.filter(func.date(MarketDaily.date) <= to_date(end_date))

        return query.order_by(MarketDaily.date).all()

    def get_latest_date(self, asset_id: int) -> Optional[datetime]:
        """
        获取指定资产的最新数据日期

        Args:
            asset_id: 资产 ID

        Returns:
            最新日期或 None
        """
        result = (
            self.db.query(MarketDaily.date)
            .filter(MarketDaily.asset_id == asset_id)
            .order_by(MarketDaily.date.desc())
            .first()
        )
        return result[0] if result else None

    def delete_by_asset(self, asset_id: int) -> int:
        """
        删除指定资产的所有行情数据

        Args:
            asset_id: 资产 ID

        Returns:
            删除的记录数
        """
        count = (
            self.db.query(MarketDaily)
            .filter(MarketDaily.asset_id == asset_id)
            .delete()
        )
        self.db.commit()
        return count
