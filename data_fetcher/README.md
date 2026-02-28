# Data Fetcher 模块

数据获取模块，负责从 AKShare 等数据源获取金融数据。

## 功能特性

- 📡 支持指数、ETF、股份数据获取
- 💾 本地缓存机制，避免重复请求
- 🔄 增量更新，只获取新数据
- 🔁 自动重试，提高稳定性
- 📊 统一的 DataFrame 输出格式

## 快速开始

### 基本使用

```python
from data_fetcher import AKShareFetcher, FetcherConfig
from datetime import date

# 创建获取器实例
fetcher = AKShareFetcher()

# 获取沪深300指数数据
df = fetcher.fetch_index_daily(
    index_code="000300",
    start_date=date(2020, 1, 1),
    end_date=date(2024, 12, 31),
)

print(df.head())
```

### 自定义配置

```python
config = FetcherConfig(
    cache_dir=Path("./my_cache"),
    cache_expire_hours=48,
    enable_cache=True,
)

fetcher = AKShareFetcher(config=config)
```

### 禁用缓存

```python
config = FetcherConfig(enable_cache=False)
fetcher = AKShareFetcher(config=config)
```

## API 文档

### DataFetcher 基类

#### `fetch_index_daily(index_code, start_date, end_date)`

获取指数日线数据。

**参数**：
- `index_code` (str): 指数代码，如 "000300"（沪深300）
- `start_date` (date, optional): 开始日期
- `end_date` (date, optional): 结束日期

**返回**：DataFrame

**示例**：
```python
df = fetcher.fetch_index_daily("000300")
```

#### `fetch_etf_daily(etf_code, start_date, end_date)`

获取 ETF 日线数据。

**参数**：
- `etf_code` (str): ETF 代码，如 "518880"（黄金ETF）
- `start_date` (date, optional): 开始日期
- `end_date` (date, optional): 结束日期

**返回**：DataFrame

**示例**：
```python
df = fetcher.fetch_etf_daily("518880")
```

#### `fetch_stock_daily(stock_code, start_date, end_date, adjust)`

获取个股日线数据。

**参数**：
- `stock_code` (str): 股票代码，如 "002594"（比亚迪）
- `start_date` (date, optional): 开始日期
- `end_date` (date, optional): 结束日期
- `adjust` (str): 复权方式，""/"qfq"/"hfq"

**返回**：DataFrame

**示例**：
```python
df = fetcher.fetch_stock_daily("002594", adjust="qfq")
```

### CacheManager

#### `get(data_type, code)`

获取缓存数据。

#### `set(data_type, code, df)`

保存数据到缓存。

#### `update(data_type, code, new_df)`

增量更新缓存。

#### `clear(data_type, code)`

清除缓存。

## 数据格式

所有返回的 DataFrame 都包含以下列：

| 列名 | 类型 | 说明 |
|------|------|------|
| date | datetime | 交易日期 |
| open | float | 开盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| close | float | 收盘价 |
| volume | float | 成交量 |

## 常用代码

### 指数

| 代码 | 名称 |
|------|------|
| 000300 | 沪深300 |
| 000905 | 中证500 |
| 399006 | 创业板指 |
| 000016 | 上证50 |

### ETF

| 代码 | 名称 |
|------|------|
| 518880 | 黄金ETF |
| 510300 | 沪深300ETF |
| 159915 | 创业板ETF |

## 测试

```bash
cd data_fetcher
pytest tests/
```

## 注意事项

1. AKShare 接口可能不稳定，已内置重试机制
2. 缓存默认存储在 `./data/cache` 目录
3. 首次获取数据较慢，建议启用缓存
