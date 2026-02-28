# Database 模块

数据库模块，提供数据持久化、模型定义和数据访问层。

## 功能特性

- 💾 SQLite 数据库，零配置
- 🔄 SQLAlchemy 2.0 ORM，类型安全
- ⚡ 高效的批量操作
- 📊 完整的模型定义（资产、行情、策略、回测）
- 🔍 优化的索引设计

## 快速开始

### 初始化数据库

```python
from database import init_db

init_db()  # 创建所有表
```

### 使用仓储

```python
from database.connection import get_db_context
from database.repositories import AssetRepository
from database.models import Asset, AssetType

# 创建资产
with get_db_context() as db:
    repo = AssetRepository(db)

    asset = Asset(
        code="000300",
        name="沪深300",
        type=AssetType.INDEX,
        description="沪深300指数"
    )
    repo.create(asset)

    # 查询资产
    asset = repo.get_by_code("000300")
    print(asset.name)
```

### 插入行情数据

```python
from database.repositories import MarketDataRepository
import pandas as pd

# 从 DataFrame 批量插入
df = pd.DataFrame({
    "date": pd.date_range("2024-01-01", periods=5),
    "open": [10.0, 10.5, 11.0, 11.5, 12.0],
    "high": [10.5, 11.0, 11.5, 12.0, 12.5],
    "low": [9.5, 10.0, 10.5, 11.0, 11.5],
    "close": [10.5, 10.8, 11.2, 11.8, 12.2],
    "volume": [1000000, 1100000, 1200000, 1300000, 1400000],
})

with get_db_context() as db:
    repo = MarketDataRepository(db)
    repo.bulk_create_from_df(df, asset_id=1)
```

## 数据模型

### Asset - 资产模型

存储可投资资产的基本信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String(20) | 资产代码，唯一 |
| name | String(100) | 资产名称 |
| type | String(20) | 资产类型（index/etf/stock/bond/fund/commodity） |
| description | Text | 描述信息 |

### MarketDaily - 日线行情模型

存储历史日线行情数据。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| asset_id | Integer | 关联资产 ID |
| date | DateTime | 交易日期 |
| open | Float | 开盘价 |
| high | Float | 最高价 |
| low | Float | 最低价 |
| close | Float | 收盘价 |
| volume | Float | 成交量 |

### Strategy - 策略模型

定义投资组合的资产配置和再平衡策略。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String(100) | 策略名称，唯一 |
| description | Text | 描述信息 |
| allocation | JSON | 资产配置 {"code": weight} |
| rebalance_type | String(20) | 再平衡类型（monthly/quarterly/yearly/threshold） |
| rebalance_threshold | Float | 阈值（用于 threshold 类型） |

### BacktestResult - 回测结果模型

存储策略回测的完整结果。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| strategy_id | Integer | 关联策略 ID |
| start_date | DateTime | 回测开始日期 |
| end_date | DateTime | 回测结束日期 |
| initial_capital | Float | 初始资金 |
| total_return | Float | 总收益率 |
| annual_return | Float | 年化收益率 |
| max_drawdown | Float | 最大回撤 |
| sharpe_ratio | Float | 夏普比率 |
| sortino_ratio | Float | 索提诺比率 |
| calmar_ratio | Float | 卡玛比率 |
| volatility | Float | 波动率 |
| rebalance_count | Integer | 再平衡次数 |
| equity_curve | JSON | 净值序列 |
| drawdown_curve | JSON | 回撤序列 |

## 仓储接口

### AssetRepository

- `create(asset)` - 创建资产
- `get_by_id(asset_id)` - 根据 ID 获取
- `get_by_code(code)` - 根据代码获取
- `get_all()` - 获取所有资产
- `get_by_type(asset_type)` - 根据类型获取
- `update(asset)` - 更新资产
- `delete(asset)` - 删除资产
- `bulk_create(assets)` - 批量创建

### MarketDataRepository

- `create(data)` - 创建行情数据
- `bulk_create(data_list)` - 批量创建
- `bulk_create_from_df(df, asset_id)` - 从 DataFrame 批量创建
- `get_by_id(data_id)` - 根据 ID 获取
- `get_by_asset(asset_id, start_date, end_date)` - 根据资产获取
- `get_latest_date(asset_id)` - 获取最新日期
- `delete_by_asset(asset_id)` - 删除指定资产的所有数据

### StrategyRepository

- `create(strategy)` - 创建策略
- `get_by_id(strategy_id)` - 根据 ID 获取
- `get_by_name(name)` - 根据名称获取
- `get_all()` - 获取所有策略
- `update(strategy)` - 更新策略
- `delete(strategy)` - 删除策略

### BacktestRepository

- `create(result)` - 创建回测结果
- `get_by_id(result_id)` - 根据 ID 获取
- `get_by_strategy(strategy_id)` - 根据策略获取
- `get_latest_by_strategy(strategy_id)` - 获取最新结果
- `get_all()` - 获取所有结果
- `delete(result)` - 删除结果
- `delete_by_strategy(strategy_id)` - 删除策略的所有结果

## 初始数据

### 预设资产

- 沪深300 (000300)
- 中证500 (000905)
- 创业板指 (399006)
- 上证50 (000016)
- 黄金ETF (518880)
- 沪深300ETF (510300)
- 创业板ETF (159915)
- 中证500ETF (510500)

### 预设策略

- 保守型策略 - 以债券和大盘股为主
- 平衡型策略 - 股债平衡
- 激进型策略 - 以成长股为主
- 60/40 股债平衡 - 经典配置

## 数据库文件

默认情况下，数据库文件存储在项目根目录：`q_alpha.db`

## 注意事项

1. SQLite 不支持并发写入，使用单会话模式
2. 批量操作建议使用 `bulk_create_from_df`
3. JSON 字段存储为 TEXT，查询时注意性能
4. 日期时间统一使用 UTC 时区
