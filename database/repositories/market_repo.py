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
        from sqlalchemy import and_, func, or_

        query = self.db.query(MarketDaily).filter(MarketDaily.asset_id == asset_id)

        # 安全提取日期部分（兼容 datetime 和 date 类型）
        def to_date_str(d):
            """将日期转换为 YYYY-MM-DD 格式的字符串"""
            if d is None:
                return None
            if isinstance(d, datetime):
                return d.strftime("%Y-%m-%d")
            return d.strftime("%Y-%m-%d")

        # SQLite 使用字符串比较 date 字段
        # date 字段存储格式为 "YYYY-MM-DD HH:MM:SS.ffffff"
        # 通过字符串前缀比较实现日期范围过滤
        if start_date:
            start_str = to_date_str(start_date)
            # 大于等于开始日期: date >= start_str
            query = query.filter(MarketDaily.date >= start_str)
        if end_date:
            end_str = to_date_str(end_date)
            # 小于等于结束日期: 需要特殊处理，因为字符串比较
            # 使用 date + 1 天的方式来包含当天的所有时间
            from datetime import timedelta
            end_dt = datetime.strptime(end_str, "%Y-%m-%d") + timedelta(days=1)
            end_next_str = end_dt.strftime("%Y-%m-%d")
            query = query.filter(MarketDaily.date < end_next_str)

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
