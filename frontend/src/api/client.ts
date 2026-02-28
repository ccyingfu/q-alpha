/**
 * API 客户端
 */

import axios from 'axios'
import type { Asset, ExternalAssetSearchResult, Strategy, BacktestRequest, BacktestResponse, MarketDataResponse } from '../types'

// API 基础 URL
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// 创建 axios 实例
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// 资产相关 API
export const assetApi = {
  // 外部搜索资产（从 akshare 等数据源）
  searchExternal: (query: string, type?: string, limit = 10) =>
    api.get<ExternalAssetSearchResult[]>('/api/assets/search-external', {
      params: { q: query, asset_type: type, limit },
    }),

  // 搜索资产（数据库）
  search: (query: string, type?: string, limit = 10) =>
    api.get<Asset[]>('/api/assets/search', { params: { q: query, asset_type: type, limit } }),

  // 获取所有资产
  list: (type?: string) =>
    api.get<Asset[]>('/api/assets/', { params: { asset_type: type } }),

  // 获取单个资产
  get: (id: number) => api.get<Asset>(`/api/assets/${id}`),

  // 根据代码获取资产
  getByCode: (code: string) => api.get<Asset>(`/api/assets/code/${code}`),

  // 创建资产
  create: (data: Partial<Asset>) => api.post<Asset>('/api/assets/', data),

  // 更新资产
  update: (id: number, data: Partial<Asset>) => api.put<Asset>(`/api/assets/${id}`, data),

  // 删除资产
  delete: (id: number) => api.delete(`/api/assets/${id}`),
}

// 策略相关 API
export const strategyApi = {
  // 获取所有策略
  list: () => api.get<Strategy[]>('/api/strategies/'),

  // 获取单个策略
  get: (id: number) => api.get<Strategy>(`/api/strategies/${id}`),

  // 根据名称获取策略
  getByName: (name: string) => api.get<Strategy>(`/api/strategies/name/${name}`),

  // 创建策略
  create: (data: Partial<Strategy>) => api.post<Strategy>('/api/strategies/', data),

  // 更新策略
  update: (id: number, data: Partial<Strategy>) => api.put<Strategy>(`/api/strategies/${id}`, data),

  // 删除策略
  delete: (id: number) => api.delete(`/api/strategies/${id}`),
}

// 回测相关 API
export const backtestApi = {
  // 执行回测
  run: (request: BacktestRequest) => api.post<BacktestResponse>('/api/backtest/run', request),

  // 获取回测结果列表
  listResults: (strategyId?: number) =>
    api.get<BacktestResponse[]>('/api/backtest/results', { params: { strategy_id: strategyId } }),

  // 获取单个回测结果
  getResult: (id: number) => api.get<BacktestResponse>(`/api/backtest/results/${id}`),

  // 删除回测结果
  deleteResult: (id: number) => api.delete(`/api/backtest/results/${id}`),

  // 批量删除回测结果
  batchDelete: (ids: number[]) => api.post('/api/backtest/batch-delete', { ids }),
}

// 市场数据相关 API
export const marketApi = {
  // 获取市场数据
  getDaily: (
    assetCode: string,
    startDate?: string,
    endDate?: string,
    refresh = false
  ) =>
    api.get<MarketDataResponse>(`/api/market/${assetCode}/daily`, {
      params: { start_date: startDate, end_date: endDate, refresh },
    }),
}

export default api
