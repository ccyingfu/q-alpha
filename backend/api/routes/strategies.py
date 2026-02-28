"""
策略管理接口
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from database.repositories import StrategyRepository
from database.models import Strategy
from backend.schemas import StrategyCreate, StrategyResponse, StrategyUpdate

router = APIRouter()


@router.get("/", response_model=List[StrategyResponse])
async def list_strategies(
    db: Session = Depends(get_db),
):
    """获取所有策略列表"""
    repo = StrategyRepository(db)
    strategies = repo.get_all()
    return strategies


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
):
    """根据 ID 获取策略"""
    repo = StrategyRepository(db)
    strategy = repo.get_by_id(strategy_id)

    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    return strategy


@router.get("/name/{strategy_name}", response_model=StrategyResponse)
async def get_strategy_by_name(
    strategy_name: str,
    db: Session = Depends(get_db),
):
    """根据名称获取策略"""
    repo = StrategyRepository(db)
    strategy = repo.get_by_name(strategy_name)

    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_name} not found")

    return strategy


@router.post("/", response_model=StrategyResponse)
async def create_strategy(
    strategy_data: StrategyCreate,
    db: Session = Depends(get_db),
):
    """创建新策略"""
    repo = StrategyRepository(db)

    # 检查名称是否已存在
    existing = repo.get_by_name(strategy_data.name)
    if existing:
        raise HTTPException(
            status_code=400, detail=f"Strategy name {strategy_data.name} already exists"
        )

    # 验证配置总和为 1
    total_weight = sum(strategy_data.allocation.values())
    if abs(total_weight - 1.0) > 0.01:
        raise HTTPException(
            status_code=400, detail=f"Allocation weights must sum to 1.0, got {total_weight}"
        )

    # 创建策略
    strategy = Strategy(
        name=strategy_data.name,
        description=strategy_data.description,
        allocation=strategy_data.allocation,
        rebalance_type=strategy_data.rebalance_type,
        rebalance_threshold=strategy_data.rebalance_threshold,
    )

    return repo.create(strategy)


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    strategy_data: StrategyUpdate,
    db: Session = Depends(get_db),
):
    """更新策略"""
    repo = StrategyRepository(db)
    strategy = repo.get_by_id(strategy_id)

    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    # 更新字段
    if strategy_data.name is not None:
        strategy.name = strategy_data.name
    if strategy_data.description is not None:
        strategy.description = strategy_data.description
    if strategy_data.allocation is not None:
        # 验证配置总和
        total_weight = sum(strategy_data.allocation.values())
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400, detail=f"Allocation weights must sum to 1.0, got {total_weight}"
            )
        strategy.allocation = strategy_data.allocation
    if strategy_data.rebalance_type is not None:
        strategy.rebalance_type = strategy_data.rebalance_type
    if strategy_data.rebalance_threshold is not None:
        strategy.rebalance_threshold = strategy_data.rebalance_threshold

    return repo.update(strategy)


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
):
    """删除策略"""
    repo = StrategyRepository(db)
    strategy = repo.get_by_id(strategy_id)

    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

    repo.delete(strategy)
    return {"message": f"Strategy {strategy_id} deleted successfully"}
