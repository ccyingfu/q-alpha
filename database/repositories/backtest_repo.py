"""
回测结果仓储
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from database.models.backtest import BacktestResult


class BacktestRepository:
    """回测结果仓储"""

    def __init__(self, db: Session):
        """
        初始化仓储

        Args:
            db: 数据库会话
        """
        self.db = db

    def create(self, result: BacktestResult) -> BacktestResult:
        """
        创建回测结果

        Args:
            result: 回测结果对象

        Returns:
            创建的回测结果对象
        """
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result

    def get_by_id(self, result_id: int) -> Optional[BacktestResult]:
        """
        根据 ID 获取回测结果

        Args:
            result_id: 回测结果 ID

        Returns:
            回测结果对象或 None
        """
        return self.db.query(BacktestResult).filter(BacktestResult.id == result_id).first()

    def get_by_strategy(self, strategy_id: int) -> List[BacktestResult]:
        """
        根据策略 ID 获取回测结果

        Args:
            strategy_id: 策略 ID

        Returns:
            回测结果列表
        """
        return (
            self.db.query(BacktestResult)
            .filter(BacktestResult.strategy_id == strategy_id)
            .order_by(BacktestResult.created_at.desc())
            .all()
        )

    def get_latest_by_strategy(self, strategy_id: int) -> Optional[BacktestResult]:
        """
        获取指定策略的最新回测结果

        Args:
            strategy_id: 策略 ID

        Returns:
            最新的回测结果对象或 None
        """
        return (
            self.db.query(BacktestResult)
            .filter(BacktestResult.strategy_id == strategy_id)
            .order_by(BacktestResult.created_at.desc())
            .first()
        )

    def get_all(self) -> List[BacktestResult]:
        """
        获取所有回测结果

        Returns:
            回测结果列表
        """
        return self.db.query(BacktestResult).order_by(BacktestResult.created_at.desc()).all()

    def delete(self, result: BacktestResult) -> None:
        """
        删除回测结果

        Args:
            result: 回测结果对象
        """
        self.db.delete(result)
        self.db.commit()

    def delete_by_strategy(self, strategy_id: int) -> int:
        """
        删除指定策略的所有回测结果

        Args:
            strategy_id: 策略 ID

        Returns:
            删除的记录数
        """
        count = (
            self.db.query(BacktestResult)
            .filter(BacktestResult.strategy_id == strategy_id)
            .delete()
        )
        self.db.commit()
        return count
