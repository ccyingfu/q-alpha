/**
 * 回测状态管理
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { backtestApi } from '../api/client'
import type { BacktestRequest, BacktestResponse } from '../types'

export const useBacktestStore = defineStore('backtest', () => {
  const results = ref<BacktestResponse[]>([])
  const currentResult = ref<BacktestResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 执行回测
  const runBacktest = async (request: BacktestRequest) => {
    loading.value = true
    error.value = null
    try {
      currentResult.value = await backtestApi.run(request)
      results.value.unshift(currentResult.value)
      return currentResult.value
    } catch (e: any) {
      error.value = e.message || '执行回测失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  // 获取回测结果列表
  const fetchResults = async (strategyId?: number) => {
    loading.value = true
    error.value = null
    try {
      results.value = await backtestApi.listResults(strategyId)
    } catch (e: any) {
      error.value = e.message || '获取回测结果失败'
    } finally {
      loading.value = false
    }
  }

  // 获取单个回测结果
  const fetchResult = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      currentResult.value = await backtestApi.getResult(id)
      return currentResult.value
    } catch (e: any) {
      error.value = e.message || '获取回测结果失败'
    } finally {
      loading.value = false
    }
  }

  // 删除回测结果
  const deleteResult = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      await backtestApi.deleteResult(id)
      results.value = results.value.filter((r) => r.id !== id)
      if (currentResult.value?.id === id) {
        currentResult.value = null
      }
    } catch (e: any) {
      error.value = e.message || '删除回测结果失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  // 批量删除回测结果
  const batchDelete = async (ids: number[]) => {
    loading.value = true
    error.value = null
    try {
      await backtestApi.batchDelete(ids)
      results.value = results.value.filter((r) => !ids.includes(r.id))
      if (currentResult.value && ids.includes(currentResult.value.id)) {
        currentResult.value = null
      }
    } catch (e: any) {
      error.value = e.message || '批量删除失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    results,
    currentResult,
    loading,
    error,
    runBacktest,
    fetchResults,
    fetchResult,
    deleteResult,
    batchDelete,
  }
})
