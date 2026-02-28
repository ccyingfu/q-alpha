/**
 * 策略状态管理
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { strategyApi } from '../api/client'
import type { Strategy } from '../types'

export const useStrategyStore = defineStore('strategy', () => {
  const strategies = ref<Strategy[]>([])
  const currentStrategy = ref<Strategy | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 获取所有策略
  const fetchStrategies = async () => {
    loading.value = true
    error.value = null
    try {
      strategies.value = await strategyApi.list()
    } catch (e: any) {
      error.value = e.message || '获取策略列表失败'
    } finally {
      loading.value = false
    }
  }

  // 获取单个策略
  const fetchStrategy = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      currentStrategy.value = await strategyApi.get(id)
      return currentStrategy.value
    } catch (e: any) {
      error.value = e.message || '获取策略失败'
    } finally {
      loading.value = false
    }
  }

  // 创建策略
  const createStrategy = async (data: Partial<Strategy>) => {
    loading.value = true
    error.value = null
    try {
      const newStrategy = await strategyApi.create(data)
      strategies.value.push(newStrategy)
      return newStrategy
    } catch (e: any) {
      error.value = e.message || '创建策略失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  // 更新策略
  const updateStrategy = async (id: number, data: Partial<Strategy>) => {
    loading.value = true
    error.value = null
    try {
      const updated = await strategyApi.update(id, data)
      const index = strategies.value.findIndex((s) => s.id === id)
      if (index !== -1) {
        strategies.value[index] = updated
      }
      if (currentStrategy.value?.id === id) {
        currentStrategy.value = updated
      }
      return updated
    } catch (e: any) {
      error.value = e.message || '更新策略失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  // 删除策略
  const deleteStrategy = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      await strategyApi.delete(id)
      strategies.value = strategies.value.filter((s) => s.id !== id)
      if (currentStrategy.value?.id === id) {
        currentStrategy.value = null
      }
    } catch (e: any) {
      error.value = e.message || '删除策略失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    strategies,
    currentStrategy,
    loading,
    error,
    fetchStrategies,
    fetchStrategy,
    createStrategy,
    updateStrategy,
    deleteStrategy,
  }
})
