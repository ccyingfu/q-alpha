"""
策略仓储
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from database.models.strategy import Strategy, RebalanceType


class StrategyRepository:
    """策略数据仓储"""

    def __init__(self, db: Session):
        """
        初始化仓储

        Args:
            db: 数据库会话
        """
        self.db = db

    def create(self, strategy: Strategy) -> Strategy:
        """
        创建策略

        Args:
            strategy: 策略对象

        Returns:
            创建的策略对象
        """
        self.db.add(strategy)
        self.db.commit()
        self.db.refresh(strategy)
        return strategy

    def get_by_id(self, strategy_id: int) -> Optional[Strategy]:
        """
        根据 ID 获取策略

        Args:
            strategy_id: 策略 ID

        Returns:
            策略对象或 None
        """
        return self.db.query(Strategy).filter(Strategy.id == strategy_id).first()

    def get_by_name(self, name: str) -> Optional[Strategy]:
        """
        根据名称获取策略

        Args:
            name: 策略名称

        Returns:
            策略对象或 None
        """
        return self.db.query(Strategy).filter(Strategy.name == name).first()

    def get_all(self) -> List[Strategy]:
        """
        获取所有策略

        Returns:
            策略列表
        """
        return self.db.query(Strategy).all()

    def update(self, strategy: Strategy) -> Strategy:
        """
        更新策略

        Args:
            strategy: 策略对象

        Returns:
            更新后的策略对象
        """
        self.db.commit()
        self.db.refresh(strategy)
        return strategy

    def delete(self, strategy: Strategy) -> None:
        """
        删除策略

        Args:
            strategy: 策略对象
        """
        self.db.delete(strategy)
        self.db.commit()
