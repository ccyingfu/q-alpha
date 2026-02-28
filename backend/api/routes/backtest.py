"""
回测执行接口
"""

from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from database.repositories import (
    AssetRepository,
    BacktestRepository,
    MarketDataRepository,
    StrategyRepository,
)
from backend.schemas import BacktestRequest, BacktestResponse, BatchDeleteRequest
from backend.services.backtest_engine import BacktestEngine
from data_fetcher import BaostockFetcher

router = APIRouter()


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db),
):
    """
    执行策略回测

    根据策略配置和历史数据执行回测，返回绩效指标和净值曲线。
    会自动获取缺失的市场数据。
    """
    # 获取策略
    strategy_repo = StrategyRepository(db)
    strategy = strategy_repo.get_by_id(request.strategy_id)

    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy {request.strategy_id} not found")

    # 确保所有资产的市场数据已加载
    asset_repo = AssetRepository(db)
    market_repo = MarketDataRepository(db)
    fetcher = BaostockFetcher()

    for asset_code in strategy.allocation.keys():
        asset = asset_repo.get_by_code(asset_code)

        if not asset:
            raise HTTPException(
                status_code=404, detail=f"Asset {asset_code} not found in database"
            )

        # 检查数据库中是否有该资产的数据，并检查数据是否完整
        existing_data = market_repo.get_by_asset(
            asset.id, request.start_date, request.end_date
        )

        # 检查数据是否需要刷新
        need_refresh = False
        if not existing_data:
            need_refresh = True
        else:
            # 检查数据的最新日期是否覆盖请求的结束日期
            # 允许一定的容忍度（考虑到数据源可能有1-2天的延迟）
            from datetime import timedelta
            latest_date = max(d.date for d in existing_data)
            # 确保 latest_date 是 date 类型
            if isinstance(latest_date, datetime):
                latest_date = latest_date.date()
            # 安全提取 date 类型
            request_end = request.end_date if isinstance(request.end_date, date) and not isinstance(request.end_date, datetime) else request.end_date.date()
            # 如果最新数据早于请求结束日期超过7天，需要刷新
            if (request_end - latest_date) > timedelta(days=7):
                need_refresh = True

        # 如果没有数据或数据不完整，自动获取
        if need_refresh:
            try:
                # 根据资产类型选择获取方法
                # 安全提取日期部分
                start = request.start_date if isinstance(request.start_date, date) and not isinstance(request.start_date, datetime) else request.start_date.date()
                end = request.end_date if isinstance(request.end_date, date) and not isinstance(request.end_date, datetime) else request.end_date.date()

                if asset.type == "index":
                    df = fetcher.fetch_index_daily(asset_code, start, end)
                elif asset.type == "etf":
                    df = fetcher.fetch_etf_daily(asset_code, start, end)
                elif asset.type == "stock":
                    df = fetcher.fetch_stock_daily(asset_code, start, end)
                else:
                    raise HTTPException(
                        status_code=400, detail=f"Unsupported asset type: {asset.type}"
                    )

                # 检查数据是否为空
                if df.empty:
                    raise HTTPException(
                        status_code=404,
                        detail=f"未获取到 {asset_code}({asset.name}) 的市场数据，请检查资产代码或日期范围"
                    )

                # 删除旧数据再存储新数据（避免重复）
                market_repo.delete_by_asset(asset.id)
                market_repo.bulk_create_from_df(df, asset.id)

            except HTTPException:
                raise
            except Exception as e:
                # 提取更友好的错误信息
                error_msg = str(e)
                if "ConnectionError" in error_msg or "ProxyError" in error_msg or "RemoteDisconnected" in error_msg:
                    raise HTTPException(
                        status_code=503,
                        detail=f"无法获取 {asset_code}({asset.name}) 的市场数据，请检查网络连接或稍后重试",
                    )
                elif "RetryError" in error_msg:
                    raise HTTPException(
                        status_code=503,
                        detail=f"获取 {asset_code}({asset.name}) 数据超时，请检查网络连接或稍后重试",
                    )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"获取 {asset_code}({asset.name}) 数据失败: {error_msg}",
                    )

    # 执行回测
    engine = BacktestEngine(db)
    result = engine.run(
        strategy=strategy,
        start_date=request.start_date,
        end_date=request.end_date,
        initial_capital=request.initial_capital,
    )

    # 保存回测结果
    backtest_repo = BacktestRepository(db)
    saved_result = backtest_repo.create(result)

    # 转换为响应格式
    return BacktestResponse(
        id=saved_result.id,
        strategy_id=saved_result.strategy_id,
        strategy_name=strategy.name,
        start_date=saved_result.start_date,
        end_date=saved_result.end_date,
        initial_capital=saved_result.initial_capital,
        metrics={
            "total_return": saved_result.total_return,
            "annual_return": saved_result.annual_return,
            "max_drawdown": saved_result.max_drawdown,
            "sharpe_ratio": saved_result.sharpe_ratio,
            "sortino_ratio": saved_result.sortino_ratio,
            "calmar_ratio": saved_result.calmar_ratio,
            "volatility": saved_result.volatility,
            "rebalance_count": saved_result.rebalance_count,
        },
        equity_curve=saved_result.equity_curve,
        drawdown_curve=saved_result.drawdown_curve,
        benchmark_curves=saved_result.benchmark_curves,
        created_at=saved_result.created_at,
    )


@router.get("/results", response_model=List[BacktestResponse])
async def list_backtests(
    strategy_id: int = None,
    db: Session = Depends(get_db),
):
    """
    获取回测结果列表

    可选按策略过滤。
    """
    repo = BacktestRepository(db)

    if strategy_id:
        results = repo.get_by_strategy(strategy_id)
    else:
        results = repo.get_all()

    # 转换为响应格式
    responses = []
    for result in results:
        strategy_repo = StrategyRepository(db)
        strategy = strategy_repo.get_by_id(result.strategy_id)

        responses.append(
            BacktestResponse(
                id=result.id,
                strategy_id=result.strategy_id,
                strategy_name=strategy.name if strategy else "Unknown",
                start_date=result.start_date,
                end_date=result.end_date,
                initial_capital=result.initial_capital,
                metrics={
                    "total_return": result.total_return,
                    "annual_return": result.annual_return,
                    "max_drawdown": result.max_drawdown,
                    "sharpe_ratio": result.sharpe_ratio,
                    "sortino_ratio": result.sortino_ratio,
                    "calmar_ratio": result.calmar_ratio,
                    "volatility": result.volatility,
                    "rebalance_count": result.rebalance_count,
                },
                equity_curve=result.equity_curve,
                drawdown_curve=result.drawdown_curve,
                benchmark_curves=result.benchmark_curves,
                created_at=result.created_at,
            )
        )

    return responses


@router.get("/results/{result_id}", response_model=BacktestResponse)
async def get_backtest_result(
    result_id: int,
    db: Session = Depends(get_db),
):
    """获取单个回测结果"""
    backtest_repo = BacktestRepository(db)
    result = backtest_repo.get_by_id(result_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"Backtest result {result_id} not found")

    # 获取策略信息
    strategy_repo = StrategyRepository(db)
    strategy = strategy_repo.get_by_id(result.strategy_id)

    return BacktestResponse(
        id=result.id,
        strategy_id=result.strategy_id,
        strategy_name=strategy.name if strategy else "Unknown",
        start_date=result.start_date,
        end_date=result.end_date,
        initial_capital=result.initial_capital,
        metrics={
            "total_return": result.total_return,
            "annual_return": result.annual_return,
            "max_drawdown": result.max_drawdown,
            "sharpe_ratio": result.sharpe_ratio,
            "sortino_ratio": result.sortino_ratio,
            "calmar_ratio": result.calmar_ratio,
            "volatility": result.volatility,
            "rebalance_count": result.rebalance_count,
        },
        equity_curve=result.equity_curve,
        drawdown_curve=result.drawdown_curve,
        benchmark_curves=result.benchmark_curves,
        created_at=result.created_at,
    )


@router.delete("/results/{result_id}")
async def delete_backtest_result(
    result_id: int,
    db: Session = Depends(get_db),
):
    """删除回测结果"""
    repo = BacktestRepository(db)
    result = repo.get_by_id(result_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"Backtest result {result_id} not found")

    repo.delete(result)
    return {"message": f"Backtest result {result_id} deleted successfully"}


@router.post("/batch-delete")
async def batch_delete_results(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db),
):
    """
    批量删除回测结果
    """
    repo = BacktestRepository(db)
    deleted_count = 0

    for result_id in request.ids:
        result = repo.get_by_id(result_id)
        if result:
            repo.delete(result)
            deleted_count += 1

    return {"message": f"Deleted {deleted_count} results", "deleted_count": deleted_count}
