<template>
  <div class="data-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>资产列表</span>
          <el-button type="primary" @click="refreshData">刷新数据</el-button>
        </div>
      </template>

      <el-table :data="assetStore.assets" stripe>
        <el-table-column prop="code" label="代码" width="120" />
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewData(row)">查看数据</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 数据详情对话框 -->
    <el-dialog v-model="showDataDialog" :title="`${currentAsset?.name} - 历史数据`" width="80%">
      <!-- 工具栏 -->
      <div class="data-toolbar">
        <el-radio-group v-model="dataGranularity" size="small">
          <el-radio-button value="year">年</el-radio-button>
          <el-radio-button value="month">月</el-radio-button>
          <el-radio-button value="day">日</el-radio-button>
        </el-radio-group>

        <el-input
          v-model="searchDate"
          placeholder="搜索日期..."
          clearable
          style="width: 200px"
        />
      </div>

      <!-- 数据表格 -->
      <el-table :data="pagedData" max-height="400" stripe>
        <el-table-column prop="date" label="日期" width="120" sortable />
        <el-table-column prop="open" label="开盘" width="100" sortable />
        <el-table-column prop="high" label="最高" width="100" sortable />
        <el-table-column prop="low" label="最低" width="100" sortable />
        <el-table-column prop="close" label="收盘" width="100" sortable />
        <el-table-column prop="volume" label="成交量" sortable />
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="pageSizes"
        :total="totalCount"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAssetStore } from '../stores/asset'
import { marketApi } from '../api/client'
import type { Asset, MarketDataPoint } from '../types'

const assetStore = useAssetStore()

const showDataDialog = ref(false)
const currentAsset = ref<Asset | null>(null)
const marketData = ref<MarketDataPoint[]>([])

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const pageSizes = [10, 20, 50, 100]

// 数据粒度
const dataGranularity = ref<'year' | 'month' | 'day'>('day')

// 搜索
const searchDate = ref('')

// 按粒度聚合数据
const aggregatedData = computed(() => {
  if (!marketData.value.length) return []

  if (dataGranularity.value === 'day') {
    return marketData.value
  }

  // 年/月聚合逻辑
  const grouped = new Map<string, MarketDataPoint[]>()
  marketData.value.forEach(item => {
    const key = dataGranularity.value === 'year'
      ? item.date.substring(0, 4)
      : item.date.substring(0, 7)
    if (!grouped.has(key)) grouped.set(key, [])
    grouped.get(key)!.push(item)
  })

  return Array.from(grouped.entries()).map(([period, items]) => ({
    date: period,
    open: items[0].open,
    high: Math.max(...items.map(i => i.high)),
    low: Math.min(...items.map(i => i.low)),
    close: items[items.length - 1].close,
    volume: items.reduce((sum, i) => sum + i.volume, 0),
  }))
})

// 搜索过滤
const filteredData = computed(() => {
  if (!searchDate.value) return aggregatedData.value
  return aggregatedData.value.filter(item =>
    item.date.includes(searchDate.value)
  )
})

// 分页数据
const pagedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredData.value.slice(start, start + pageSize.value)
})

const totalCount = computed(() => filteredData.value.length)

onMounted(async () => {
  await assetStore.fetchAssets()
})

const refreshData = async () => {
  try {
    ElMessage.success('数据刷新成功')
    await assetStore.fetchAssets()
  } catch (error) {
    ElMessage.error('数据刷新失败')
  }
}

const viewData = async (asset: Asset) => {
  currentAsset.value = asset

  try {
    const response = await marketApi.getDaily(asset.code)
    marketData.value = response.data
    showDataDialog.value = true
    // 重置分页
    currentPage.value = 1
  } catch (error) {
    ElMessage.error('获取数据失败')
  }
}
</script>

<style scoped>
.data-manage {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.data-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
