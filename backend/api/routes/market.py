"""
市场行情数据接口
"""

from datetime import date, datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from database.connection import get_db
from database.repositories import AssetRepository, MarketDataRepository
from database.models import Asset
from backend.schemas import MarketDataResponse, MarketDataPoint
from data_fetcher import BaostockFetcher

router = APIRouter()


# 全局更新状态
_update_status = {"is_updating": False, "current": "", "total": 0, "updated": 0, "errors": []}


@router.post("/update-all")
async def update_all_data(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    更新所有资产的市场数据（后台任务）
    """
    global _update_status

    if _update_status["is_updating"]:
        return {"message": "数据更新任务正在进行中", "status": "running"}

    # 获取所有资产
    asset_repo = AssetRepository(db)
    assets = asset_repo.get_all()

    if not assets:
        raise HTTPException(status_code=404, detail="没有找到任何资产")

    # 重置状态
    _update_status = {
        "is_updating": True,
        "current": "",
        "total": len(assets),
        "updated": 0,
        "errors": []
    }

    # 添加后台任务
    background_tasks.add_task(_update_all_assets_task, assets)

    return {
        "message": f"开始更新 {len(assets)} 个资产的数据",
        "status": "started",
        "total": len(assets)
    }


@router.get("/update-status")
async def get_update_status():
    """
    获取数据更新状态
    """
    return _update_status


async def _update_all_assets_task(assets: List[Asset]):
    """
    后台任务：更新所有资产数据
    """
    global _update_status
    fetcher = BaostockFetcher()

    from database.connection import SessionLocal
    db = SessionLocal()

    try:
        asset_repo = AssetRepository(db)
        market_repo = MarketDataRepository(db)

        for i, asset in enumerate(assets):
            try:
                _update_status["current"] = f"{asset.code} - {asset.name}"

                # 获取数据（使用默认日期范围获取全部历史数据）
                if asset.type == "index":
                    df = fetcher.fetch_index_daily(asset.code)
                elif asset.type == "etf":
                    df = fetcher.fetch_etf_daily(asset.code)
                elif asset.type == "stock":
                    df = fetcher.fetch_stock_daily(asset.code)
                else:
                    _update_status["errors"].append(f"{asset.code}: 不支持的资产类型 {asset.type}")
                    continue

                if not df.empty:
                    # 删除旧数据并插入新数据
                    market_repo.delete_by_asset(asset.id)
                    market_repo.bulk_create_from_df(df, asset.id)
                    _update_status["updated"] += 1

            except Exception as e:
                _update_status["errors"].append(f"{asset.code}: {str(e)}")

            _update_status["total"] = len(assets)

    finally:
        db.close()
        _update_status["is_updating"] = False


@router.get("/{asset_code}/daily", response_model=MarketDataResponse)
async def get_market_daily(
    asset_code: str,
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    refresh: bool = Query(False, description="强制刷新数据"),
    db: Session = Depends(get_db),
):
    """
    获取资产日线行情数据

    优先从数据库读取，如果数据不存在或 refresh=True，则从数据源获取。
    """
    # 获取资产信息
    asset_repo = AssetRepository(db)
    asset = asset_repo.get_by_code(asset_code)

    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_code} not found")

    # 尝试从数据库获取数据
    market_repo = MarketDataRepository(db)
    market_data = []

    if not refresh:
        # 从数据库获取
        db_data = market_repo.get_by_asset(asset.id, start_date, end_date)
        if db_data:
            market_data = [
                MarketDataPoint(
                    date=d.date,
                    open=d.open,
                    high=d.high,
                    low=d.low,
                    close=d.close,
                    volume=d.volume,
                )
                for d in db_data
            ]

    # 如果数据库没有数据或需要刷新，从数据源获取
    if not market_data or refresh:
        fetcher = BaostockFetcher()

        # 安全提取日期部分（兼容 datetime 和 date 类型）
        def to_date(d):
            if d is None:
                return None
            if isinstance(d, date) and not isinstance(d, datetime):
                return d
            return d.date()

        # 根据资产类型选择获取方法
        if asset.type == "index":
            df = fetcher.fetch_index_daily(asset_code, to_date(start_date), to_date(end_date))
        elif asset.type == "etf":
            df = fetcher.fetch_etf_daily(asset_code, to_date(start_date), to_date(end_date))
        elif asset.type == "stock":
            df = fetcher.fetch_stock_daily(asset_code, to_date(start_date), to_date(end_date))
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported asset type: {asset.type}")

        # 检查数据是否为空
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"未获取到 {asset_code}({asset.name}) 的市场数据，请检查资产代码或日期范围"
            )

        # 存储到数据库
        if not refresh:
            # 删除旧数据
            market_repo.delete_by_asset(asset.id)

        # 插入新数据
        market_repo.bulk_create_from_df(df, asset.id)

        # 转换为响应格式
        market_data = [
            MarketDataPoint(
                date=row["date"].to_pydatetime(),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
            for _, row in df.iterrows()
        ]

    # 计算日期范围
    data_start = min(d.date for d in market_data) if market_data else None
    data_end = max(d.date for d in market_data) if market_data else None

    return MarketDataResponse(
        asset_code=asset.code,
        asset_name=asset.name,
        data=market_data,
        start_date=data_start,
        end_date=data_end,
        count=len(market_data),
    )
