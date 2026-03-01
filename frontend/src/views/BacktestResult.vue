<template>
  <div class="backtest-result">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>回测结果</span>
          <div>
            <el-button
              type="danger"
              :disabled="selectedIds.length === 0"
              @click="handleBatchDelete"
            >
              批量删除 ({{ selectedIds.length }})
            </el-button>
            <el-button type="primary" @click="openRunDialog">执行回测</el-button>
          </div>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="filter-bar">
        <el-select
          v-model="filterStrategy"
          placeholder="按策略筛选"
          clearable
          style="width: 200px"
        >
          <el-option
            v-for="strategy in strategyStore.strategies"
            :key="strategy.id"
            :label="strategy.name"
            :value="strategy.id"
          />
        </el-select>

        <el-date-picker
          v-model="filterDateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width: 300px; margin-left: 16px"
        />

        <el-button
          v-if="filterStrategy || filterDateRange"
          link
          type="primary"
          @click="resetFilters"
          style="margin-left: 16px"
        >
          重置筛选
        </el-button>
      </div>

      <el-table
        :data="pagedResults"
        @sort-change="handleSortChange"
        @selection-change="handleSelectionChange"
        v-loading="backtestStore.loading"
        element-loading-text="加载中..."
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="strategy_name" label="策略" />
        <el-table-column label="时间范围">
          <template #default="{ row }">
            {{ formatDate(row.start_date) }} ~ {{ formatDate(row.end_date) }}
          </template>
        </el-table-column>
        <el-table-column label="回测时间" width="180" sortable="custom">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_return" label="总收益率" sortable>
          <template #default="{ row }">
            <span :class="getReturnClass(row.metrics.total_return)">
              {{ (row.metrics.total_return * 100).toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="annual_return" label="年化收益" sortable>
          <template #default="{ row }">
            <span :class="getReturnClass(row.metrics.annual_return)">
              {{ (row.metrics.annual_return * 100).toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="max_drawdown" label="最大回撤" sortable>
          <template #default="{ row }">
            {{ (row.metrics.max_drawdown * 100).toFixed(2) }}%
          </template>
        </el-table-column>
        <el-table-column prop="sharpe_ratio" label="夏普比率" sortable>
          <template #default="{ row }">
            {{ row.metrics.sharpe_ratio?.toFixed(2) || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="selectResult(row)">
              查看
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="pageSizes"
        :total="totalCount"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

    <!-- 详情区域：左右分栏布局 -->
    <el-card v-if="selectedResult" class="detail-card">
      <template #header>
        <div class="card-header">
          <span>详细结果 - {{ selectedResult.strategy_name }}</span>
        </div>
      </template>

      <!-- 指标统计 -->
      <el-row :gutter="20" class="metrics-row">
        <el-col :span="4.8">
          <div class="date-range-statistic">
            <div class="statistic-title">时间范围</div>
            <div class="statistic-value">{{ formatDotDate(selectedResult.start_date) }} 到 {{ formatDotDate(selectedResult.end_date) }}</div>
          </div>
        </el-col>
        <el-col :span="4.8">
          <el-statistic title="总收益率" :value="selectedResult.metrics.total_return * 100" :precision="2" suffix="%" />
        </el-col>
        <el-col :span="4.8">
          <el-statistic title="年化收益率" :value="selectedResult.metrics.annual_return * 100" :precision="2" suffix="%" />
        </el-col>
        <el-col :span="4.8">
          <el-statistic title="最大回撤" :value="selectedResult.metrics.max_drawdown * 100" :precision="2" suffix="%" />
        </el-col>
        <el-col :span="4.8">
          <el-statistic title="夏普比率" :value="selectedResult.metrics.sharpe_ratio" :precision="2" />
        </el-col>
      </el-row>

      <!-- 左右分栏 -->
      <el-row :gutter="20" class="content-row">
        <!-- 左侧：资产配置详情 -->
        <el-col :span="8" class="allocation-col">
          <div class="allocation-panel">
            <h4>资产配置比例</h4>
            <el-table :data="assetAllocationData" class="allocation-table" :row-class-name="getAllocationRowClass">
              <el-table-column prop="name" label="资产">
                <template #default="{ row }">
                  <span class="asset-dot" :style="{ backgroundColor: row.color }"></span>
                  {{ row.name }}
                </template>
              </el-table-column>
              <el-table-column prop="weight" label="权重">
                <template #default="{ row }">
                  {{ (row.weight * 100).toFixed(1) }}%
                </template>
              </el-table-column>
              <el-table-column prop="netValue" label="净值">
                <template #default="{ row }">
                  <span :class="row.netValue >= 1 ? 'text-danger' : 'text-success'">
                    {{ row.netValue.toFixed(4) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
            <div class="allocation-chart">
              <div
                v-for="item in assetAllocationData"
                :key="item.code"
                class="allocation-bar"
              >
                <div class="bar-label">
                  <span class="asset-dot" :style="{ backgroundColor: item.color }"></span>
                  {{ item.name }}
                </div>
                <div class="bar-track">
                  <div
                    class="bar-fill"
                    :style="{ width: (item.weight * 100) + '%', backgroundColor: item.color }"
                  ></div>
                </div>
                <div class="bar-value">{{ (item.weight * 100).toFixed(1) }}%</div>
              </div>
            </div>
          </div>
        </el-col>

        <!-- 右侧：净值曲线折线图 -->
        <el-col :span="16" class="chart-col">
          <div ref="chartRef" class="chart-container"></div>
        </el-col>
      </el-row>

      <!-- 曲线显示控制 -->
      <div class="chart-controls">
        <el-checkbox-group v-model="visibleCurves">
          <el-checkbox value="strategy" disabled>策略净值</el-checkbox>
          <el-checkbox value="sh" v-if="selectedResult.benchmark_curves?.sh">上证指数</el-checkbox>
          <el-checkbox value="hs300" v-if="selectedResult.benchmark_curves?.hs300">沪深300</el-checkbox>
        </el-checkbox-group>
      </div>
    </el-card>

    <!-- 执行回测对话框 -->
    <el-dialog v-model="showRunDialog" title="执行回测" width="450px">
      <el-alert
        v-if="backtestError"
        :title="backtestError"
        type="error"
        :closable="true"
        @close="backtestError = ''"
        style="margin-bottom: 16px"
      />
      <el-form :model="form" label-width="100px">
        <el-form-item label="策略">
          <el-select v-model="form.strategy_id" placeholder="请选择策略">
            <el-option
              v-for="strategy in strategyStore.strategies"
              :key="strategy.id"
              :label="strategy.name"
              :value="strategy.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="form.start_date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="form.end_date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="初始资金">
          <el-input-number v-model="form.initial_capital" :min="10000" :step="10000" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRunDialog = false">取消</el-button>
        <el-button type="primary" :loading="backtestStore.loading" @click="runBacktest">
          执行
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import { useBacktestStore } from '../stores/backtest'
import { useStrategyStore } from '../stores/strategy'
import { useAssetStore } from '../stores/asset'
import type { BacktestResponse } from '../types'

const route = useRoute()
const router = useRouter()
const backtestStore = useBacktestStore()
const strategyStore = useStrategyStore()
const assetStore = useAssetStore()

const selectedResult = ref<BacktestResponse | null>(null)
const showRunDialog = ref(false)
const backtestError = ref('')
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

// 当前高亮的数据点索引
const highlightedIndex = ref<number>(-1)

// 曲线显示控制
const visibleCurves = ref<string[]>(['sh', 'hs300'])

// 多选状态
const selectedIds = ref<number[]>([])

// 筛选状态
const filterStrategy = ref<number | undefined>()
const filterDateRange = ref<[string, string] | undefined>()

// 获取当前日期的 YYYY-MM-DD 格式
const getTodayDate = () => {
  const d = new Date()
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const form = ref({
  strategy_id: Number(route.query.strategy_id) || undefined,
  start_date: '2020-01-01',
  end_date: getTodayDate(),
  initial_capital: 100000,
})

// 排序状态
const sortField = ref('id')
const sortOrder = ref<'ascending' | 'descending'>('descending')

// 分页状态
const currentPage = ref(1)
const pageSize = ref(10)
const pageSizes = [10, 20, 50, 100]

// 资产颜色映射
const assetColors: Record<string, string> = {
  default: '#409eff',
  '510300.SH': '#f56c6c',
  '000300.SH': '#67c23a',
  '000001.SH': '#e6a23c',
  '399001.SZ': '#909399',
}

// 获取资产颜色
const getAssetColor = (code: string): string => {
  return assetColors[code] || `hsl(${Math.abs(code.charCodeAt(0) * 17) % 360}, 70%, 50%)`
}

// 资产配置数据（含动态净值）
const assetAllocationData = computed(() => {
  if (!selectedResult.value) return []

  // 找到对应的策略
  const strategy = strategyStore.strategies.find(s => s.id === selectedResult.value?.strategy_id)
  if (!strategy) return []

  const allocation = strategy.allocation

  // 获取当前组合净值
  const currentPortfolioValue = highlightedIndex.value >= 0 && selectedResult.value.equity_curve[highlightedIndex.value]
    ? selectedResult.value.equity_curve[highlightedIndex.value]!.value
    : selectedResult.value.equity_curve[selectedResult.value.equity_curve.length - 1]?.value || 1

  return Object.entries(allocation).map(([code, weight]) => {
    const asset = assetStore.assets.find(a => a.code === code)
    // 计算资产净值 = 组合净值 × 权重
    const netValue = currentPortfolioValue * weight

    return {
      code,
      name: asset?.name || code,
      weight,
      netValue,
      color: getAssetColor(code),
    }
  })
})

// 获取资产配置行样式
const getAllocationRowClass = () => {
  // 暂时不高亮行，因为已经有饼图联动了
  return ''
}

// 筛选后的数据
const filteredResults = computed(() => {
  let data = [...backtestStore.results]

  // 按策略筛选
  if (filterStrategy.value) {
    data = data.filter(r => r.strategy_id === filterStrategy.value)
  }

  // 按日期范围筛选
  if (filterDateRange.value) {
    const [start, end] = filterDateRange.value
    data = data.filter(r => {
      const dateStr = r.start_date?.split('T')[0]
      if (!dateStr) return false
      return dateStr >= start && dateStr <= end
    })
  }

  return data
})

// 排序后的数据
const sortedResults = computed(() => {
  const data = [...filteredResults.value]
  const order = sortOrder.value === 'ascending' ? 1 : -1

  return data.sort((a, b) => {
    let valueA: number
    let valueB: number

    switch (sortField.value) {
      case 'id':
        valueA = a.id
        valueB = b.id
        break
      case 'created_at':
        valueA = a.created_at ? new Date(a.created_at).getTime() : 0
        valueB = b.created_at ? new Date(b.created_at).getTime() : 0
        break
      case 'annual_return':
        valueA = a.metrics.annual_return
        valueB = b.metrics.annual_return
        break
      case 'max_drawdown':
        valueA = a.metrics.max_drawdown
        valueB = b.metrics.max_drawdown
        break
      case 'sharpe_ratio':
        valueA = a.metrics.sharpe_ratio ?? 0
        valueB = b.metrics.sharpe_ratio ?? 0
        break
      default:
        return 0
    }
    return (valueA - valueB) * order
  })
})

// 总条数
const totalCount = computed(() => sortedResults.value.length)

// 分页后的数据
const pagedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return sortedResults.value.slice(start, start + pageSize.value)
})

// 重置筛选
const resetFilters = () => {
  filterStrategy.value = undefined
  filterDateRange.value = undefined
  currentPage.value = 1
}

onMounted(async () => {
  await strategyStore.fetchStrategies()
  await assetStore.fetchAssets()
  await backtestStore.fetchResults()

  // 检查是否需要自动打开回测对话框
  const strategyId = Number(route.query.strategy_id)
  const autoRun = route.query.auto_run === 'true'

  if (strategyId && autoRun) {
    form.value.strategy_id = strategyId
    showRunDialog.value = true
    // 清除路由参数
    router.replace({ query: {} })
  } else if (backtestStore.results.length > 0) {
    selectResult(backtestStore.results[0]!)
  }
})

// 监听曲线显示变化，重新渲染图表
watch(visibleCurves, () => {
  if (selectedResult.value) {
    renderChart()
  }
})

const selectResult = (result: BacktestResponse) => {
  selectedResult.value = result
  highlightedIndex.value = -1
  nextTick(() => {
    renderChart()
  })
}

const openRunDialog = () => {
  backtestError.value = ''
  showRunDialog.value = true
}

// 防抖定时器
let debounceTimer: ReturnType<typeof setTimeout> | null = null

// 清除防抖
const clearDebounce = () => {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
}

const runBacktest = async () => {
  // 清除之前的错误
  backtestError.value = ''

  try {
    // 日期已经是 YYYY-MM-DD 格式，只需添加时间部分
    const formatDateTime = (dateStr: string) => {
      return `${dateStr}T00:00:00`
    }

    await backtestStore.runBacktest({
      strategy_id: form.value.strategy_id!,
      start_date: formatDateTime(form.value.start_date),
      end_date: formatDateTime(form.value.end_date),
      initial_capital: form.value.initial_capital,
    })

    ElMessage.success('回测执行成功')
    showRunDialog.value = false

    // 自动选中新结果并展示详情
    if (backtestStore.results.length > 0) {
      selectResult(backtestStore.results[0]!)
    }
  } catch (error: any) {
    // 提取更详细的错误信息
    let errorMsg = '回测执行失败，请稍后重试'

    if (error.response?.data?.detail) {
      const detail = error.response.data.detail
      // 后端已经返回了友好的中文错误信息
      errorMsg = detail
    } else if (error.message) {
      errorMsg = error.message
    }

    // 显示在对话框中
    backtestError.value = errorMsg
    // 同时显示 Toast 提示
    ElMessage.error(errorMsg)
  }
}

const renderChart = () => {
  if (!chartRef.value || !selectedResult.value) return

  if (chart) {
    chart.dispose()
  }

  chart = echarts.init(chartRef.value)

  const dates = selectedResult.value.equity_curve.map((e) => e.date)
  const values = selectedResult.value.equity_curve.map((e) => e.value)

  // 获取策略信息
  const strategy = strategyStore.strategies.find(s => s.id === selectedResult.value?.strategy_id)

  // 构建系列数据
  const series: any[] = [
    {
      name: '策略净值',
      type: 'line',
      data: values,
      smooth: true,
      lineStyle: { width: 3 },
      itemStyle: { color: '#f56c6c' },
    }
  ]

  // 添加上证指数
  if (visibleCurves.value.includes('sh') && selectedResult.value.benchmark_curves?.sh) {
    const shValues = selectedResult.value.benchmark_curves.sh.map((e) => e.value)
    series.push({
      name: '上证指数',
      type: 'line',
      data: shValues,
      smooth: true,
      lineStyle: { width: 2 },
      itemStyle: { color: '#409eff' },
    })
  }

  // 添加沪深300
  if (visibleCurves.value.includes('hs300') && selectedResult.value.benchmark_curves?.hs300) {
    const hs300Values = selectedResult.value.benchmark_curves.hs300.map((e) => e.value)
    series.push({
      name: '沪深300',
      type: 'line',
      data: hs300Values,
      smooth: true,
      lineStyle: { width: 2 },
      itemStyle: { color: '#67c23a' },
    })
  }

  const option = {
    title: {
      text: '净值曲线对比',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        if (!Array.isArray(params) || params.length === 0) return ''

        const dataIndex = params[0].dataIndex
        const date = dates[dataIndex]

        let tooltip = `<div style="margin-bottom: 8px; font-weight: bold;">${date}</div>`

        // 组合净值
        const portfolioValue = values[dataIndex] ?? 1
        tooltip += `<div style="margin-bottom: 8px;">
          <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: #f56c6c; margin-right: 8px;"></span>
          <strong>组合净值:</strong> ${portfolioValue.toFixed(4)}
        </div>`

        // 各资产净值
        if (strategy) {
          tooltip += `<div style="border-top: 1px solid #ddd; padding-top: 8px; margin-top: 8px; font-size: 12px; color: #666;">各资产净值</div>`

          Object.entries(strategy.allocation).forEach(([code, weight]) => {
            const asset = assetStore.assets.find(a => a.code === code)
            const assetName = asset?.name || code
            const assetValue = portfolioValue * weight
            const color = getAssetColor(code)

            tooltip += `<div style="margin: 4px 0;">
              <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: ${color}; margin-right: 8px;"></span>
              ${assetName} (${(weight * 100).toFixed(1)}%): ${assetValue.toFixed(4)}
            </div>`
          })
        }

        // 基准指数
        params.slice(1).forEach((param: any) => {
          tooltip += `<div style="margin: 4px 0;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: ${param.color}; margin-right: 8px;"></span>
            ${param.seriesName}: ${param.value.toFixed(4)}
          </div>`
        })

                        return tooltip
      },
    },
    legend: {
      data: series.map(s => s.name),
      bottom: 10,
    },
    xAxis: {
      type: 'category',
      data: dates,
    },
    yAxis: {
      type: 'value',
      name: '净值',
      min: 0,
    },
    series,
  }

  chart.setOption(option)

  // 监听 highlight 事件实现联动
  chart.off('highlight')
  chart.on('highlight', (params: any) => {
    clearDebounce()

    debounceTimer = setTimeout(() => {
      if (params.batch?.[0]?.dataIndex !== undefined) {
        highlightedIndex.value = params.batch[0].dataIndex
      }
    }, 100)
  })

  // 监听 mouseout 事件重置高亮
  chart.off('mouseout')
  chart.on('mouseout', () => {
    clearDebounce()
    highlightedIndex.value = -1
  })
}

const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  return dateStr.split('T')[0]
}

const formatDotDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  const parts = dateStr.split('T')[0]?.split('-')
  if (!parts || parts.length !== 3) return '-'
  return `${parts[0]}.${parts[1]}.${parts[2]}`
}

const formatDateTime = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}.${month}.${day} ${hours}:${minutes}:${seconds}`
}

const getReturnClass = (value: number) => {
  // 红色代表正值，绿色代表负值
  return value >= 0 ? 'text-danger' : 'text-success'
}

const handleSortChange = ({ prop, order }: { prop: string; order: string | null }) => {
  sortField.value = prop || 'id'
  sortOrder.value = order === 'ascending' ? 'ascending' : 'descending'
}

const handleSelectionChange = (selection: BacktestResponse[]) => {
  selectedIds.value = selection.map(item => item.id)
}

const handleDelete = async (result: BacktestResponse) => {
  try {
    await ElMessageBox.confirm(
      `确定删除回测结果「${result.strategy_name}」吗？`,
      '删除确认',
      { type: 'warning' }
    )

    await backtestStore.deleteResult(result.id)
    ElMessage.success('删除成功')

    // 如果当前页没有数据了，回到上一页
    if (pagedResults.value.length === 1 && currentPage.value > 1) {
      currentPage.value--
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleBatchDelete = async () => {
  if (selectedIds.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedIds.value.length} 条记录吗？`,
      '批量删除确认',
      { type: 'warning' }
    )

    await backtestStore.batchDelete(selectedIds.value)
    ElMessage.success('批量删除成功')
    selectedIds.value = []

    // 如果当前页没有数据了，回到上一页
    if (pagedResults.value.length === 0 && currentPage.value > 1) {
      currentPage.value--
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}
</script>

<style scoped>
.backtest-result {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.detail-card {
  margin-top: 20px;
}

.metrics-row {
  margin-bottom: 20px;
}

.content-row {
  margin-top: 16px;
}

.allocation-col {
  border-right: 1px solid #ebeef5;
  padding-right: 20px;
}

.allocation-panel {
  height: 100%;
}

.allocation-panel h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
}

.allocation-table {
  margin-bottom: 20px;
}

.asset-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 8px;
}

.allocation-chart {
  padding: 16px;
  background-color: #fafafa;
  border-radius: 8px;
}

.allocation-bar {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.bar-label {
  width: 120px;
  font-size: 14px;
  display: flex;
  align-items: center;
}

.bar-track {
  flex: 1;
  height: 20px;
  background-color: #e0e0e0;
  border-radius: 10px;
  overflow: hidden;
  margin: 0 12px;
}

.bar-fill {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 10px;
}

.bar-value {
  width: 50px;
  text-align: right;
  font-size: 14px;
  font-weight: 600;
}

.chart-col {
  padding-left: 10px;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.chart-controls {
  display: flex;
  align-items: center;
  margin-top: 16px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}

/* 时间范围样式 */
.date-range-statistic {
  text-align: center;
}

.statistic-title {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.statistic-value {
  font-size: 10px;
  font-weight: 500;
  color: #303133;
}

/* 高亮行样式 */
:deep(.el-table .highlight-row) {
  background-color: #f0f9ff !important;
}
</style>
