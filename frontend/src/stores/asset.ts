/**
 * 资产状态管理
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { assetApi } from '../api/client'
import type { Asset, ExternalAssetSearchResult } from '../types'

export const useAssetStore = defineStore('asset', () => {
  const assets = ref<Asset[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 获取所有资产
  const fetchAssets = async (type?: string) => {
    loading.value = true
    error.value = null
    try {
      assets.value = await assetApi.list(type)
    } catch (e: any) {
      error.value = e.message || '获取资产列表失败'
    } finally {
      loading.value = false
    }
  }

  // 获取单个资产
  const fetchAsset = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      return await assetApi.get(id)
    } catch (e: any) {
      error.value = e.message || '获取资产失败'
    } finally {
      loading.value = false
    }
  }

  // 创建资产
  const createAsset = async (data: Partial<Asset>) => {
    loading.value = true
    error.value = null
    try {
      const newAsset = await assetApi.create(data)
      assets.value.push(newAsset)
      return newAsset
    } catch (e: any) {
      error.value = e.message || '创建资产失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  // 搜索资产
  const searchAssets = async (query: string, type?: string) => {
    loading.value = true
    error.value = null
    try {
      return await assetApi.search(query, type)
    } catch (e: any) {
      error.value = e.message || '搜索资产失败'
      return []
    } finally {
      loading.value = false
    }
  }

  // 外部搜索资产（从 akshare 等数据源）
  const searchAssetsExternal = async (query: string, type?: string) => {
    loading.value = true
    error.value = null
    try {
      return await assetApi.searchExternal(query, type)
    } catch (e: any) {
      error.value = e.message || '外部搜索资产失败'
      return []
    } finally {
      loading.value = false
    }
  }

  // 更新资产
  const updateAsset = async (id: number, data: Partial<Asset>) => {
    loading.value = true
    error.value = null
    try {
      const updated = await assetApi.update(id, data)
      const index = assets.value.findIndex((a) => a.id === id)
      if (index !== -1) {
        assets.value[index] = updated
      }
      return updated
    } catch (e: any) {
      error.value = e.message || '更新资产失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  // 删除资产
  const deleteAsset = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      await assetApi.delete(id)
      assets.value = assets.value.filter((a) => a.id !== id)
    } catch (e: any) {
      error.value = e.message || '删除资产失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    assets,
    loading,
    error,
    fetchAssets,
    fetchAsset,
    createAsset,
    updateAsset,
    deleteAsset,
    searchAssets,
    searchAssetsExternal,
  }
})
