# Backend 模块

后端 API 模块，提供回测引擎和 RESTful API 服务。

## 功能特性

- 🚀 FastAPI 高性能 API 框架
- 📊 完整的回测引擎
- 📈 绩效指标计算（夏普比率、最大回撤等）
- 🔄 策略管理接口
- 📡 行情数据接口

## 快速开始

### 安装依赖

```bash
cd backend
poetry install
```

### 启动服务

```bash
poetry run uvicorn backend.main:app --reload
```

服务将在 http://localhost:8000 启动。

### API 文档

访问 http://localhost:8000/docs 查看 Swagger 文档。

## API 接口

### 健康检查

```
GET /health
```

### 市场行情数据

```
GET /api/market/{asset_code}/daily?start_date=xxx&end_date=xxx&refresh=false
```

获取资产日线行情数据。

### 资产管理

```
GET    /api/assets/          # 获取资产列表
GET    /api/assets/{id}      # 获取单个资产
POST   /api/assets/          # 创建资产
PUT    /api/assets/{id}      # 更新资产
DELETE /api/assets/{id}      # 删除资产
```

### 策略管理

```
GET    /api/strategies/      # 获取策略列表
GET    /api/strategies/{id}  # 获取单个策略
POST   /api/strategies/      # 创建策略
PUT    /api/strategies/{id}  # 更新策略
DELETE /api/strategies/{id}  # 删除策略
```

### 回测执行

```
POST /api/backtest/run
```

执行策略回测。

请求体：
```json
{
  "strategy_id": 1,
  "start_date": "2020-01-01T00:00:00",
  "end_date": "2024-12-31T00:00:00",
  "initial_capital": 100000.0
}
```

```
GET /api/backtest/results           # 获取回测结果列表
GET /api/backtest/results/{id}      # 获取单个结果
DELETE /api/backtest/results/{id}   # 删除结果
```

## 回测引擎

### BacktestEngine

核心回测引擎，负责执行策略回测。

**主要方法**：
- `run(strategy, start_date, end_date, initial_capital)` - 执行回测

**流程**：
1. 获取策略配置的资产列表
2. 从数据库获取历史行情数据
3. 对齐所有资产的日期
4. 按日期计算组合净值
5. 计算绩效指标
6. 返回回测结果

### MetricsCalculator

绩效指标计算器。

**计算的指标**：
- 总收益率 (Total Return)
- 年化收益率 (CAGR)
- 最大回撤 (Max Drawdown)
- 波动率 (Volatility)
- 夏普比率 (Sharpe Ratio)
- 索提诺比率 (Sortino Ratio)
- 卡玛比率 (Calmar Ratio)

## 配置

环境变量（.env 文件）：

```env
# API 配置
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True

# CORS 配置
CORS_ORIGINS=["http://localhost:5173"]

# 数据库
DATABASE_URL=sqlite:///q_alpha.db

# 回测配置
RISK_FREE_RATE=0.03
TRADING_DAYS_PER_YEAR=252

# 数据获取
CACHE_DIR=./data/cache
ENABLE_CACHE=True
```

## 开发指南

### 添加新的 API 端点

1. 在 `backend/schemas/` 中定义请求/响应模型
2. 在 `backend/api/routes/` 中创建路由
3. 在 `backend/main.py` 中注册路由

### 添加新的绩效指标

在 `backend/services/metrics_calculator.py` 中添加计算方法。

## 测试

```bash
cd backend
pytest tests/
```

## 注意事项

1. 首次启动会自动创建数据库表
2. 数据获取依赖 AKShare，可能需要等待
3. 回测计算量大时可能较慢
4. 生产环境建议关闭 API_RELOAD
