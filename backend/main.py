"""
Q-Alpha 后端 API 服务

基于 FastAPI 的回测引擎和 API 服务。
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import assets, backtest, market, strategies
from backend.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    应用生命周期管理

    启动时初始化数据库，关闭时清理资源。
    """
    # 启动
    logger.info("Starting Q-Alpha backend...")

    # 初始化数据库
    from database import init_db

    init_db()
    logger.info("Database initialized.")

    yield

    # 关闭
    logger.info("Shutting down Q-Alpha backend...")


# 创建 FastAPI 应用
app = FastAPI(
    title="Q-Alpha API",
    description="量化投资策略回测系统 API",
    version="0.1.0",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)},
    )


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "version": "0.1.0"}


# 注册路由
app.include_router(market.router, prefix="/api/market", tags=["Market Data"])
app.include_router(assets.router, prefix="/api/assets", tags=["Assets"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["Backtest"])


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to Q-Alpha API",
        "docs": "/docs",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
