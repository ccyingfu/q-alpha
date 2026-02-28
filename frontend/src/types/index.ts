/**
 * 类型定义
 */

// 资产类型
export type AssetType = 'index' | 'etf' | 'stock' | 'bond' | 'fund' | 'commodity'

// 资产接口
export interface Asset {
  id: number
  code: string
  name: string
  type: AssetType
  description?: string
  created_at: string
  updated_at: string
}

// 再平衡类型
export type RebalanceType = 'monthly' | 'quarterly' | 'yearly' | 'threshold'

// 策略接口
export interface Strategy {
  id: number
  name: string
  description?: string
  allocation: Record<string, number>
  rebalance_type: RebalanceType
  rebalance_threshold?: number
  created_at: string
  updated_at: string
}

// 市场数据点
export interface MarketDataPoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

// 市场数据响应
export interface MarketDataResponse {
  asset_code: string
  asset_name: string
  data: MarketDataPoint[]
  start_date: string
  end_date: string
  count: number
}

// 绩效指标
export interface PerformanceMetrics {
  total_return: number
  annual_return: number
  max_drawdown: number
  sharpe_ratio?: number
  sortino_ratio?: number
  calmar_ratio?: number
  volatility: number
  rebalance_count: number
}

// 回测请求
export interface BacktestRequest {
  strategy_id: number
  start_date: string
  end_date: string
  initial_capital: number
}

// 回测响应
export interface BacktestResponse {
  id: number
  strategy_id: number
  strategy_name: string
  start_date: string
  end_date: string
  initial_capital: number
  metrics: PerformanceMetrics
  equity_curve: Array<{ date: string; value: number }>
  drawdown_curve: Array<{ date: string; value: number }>
  created_at: string
}
