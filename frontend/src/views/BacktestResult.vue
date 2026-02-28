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
            <el-button type="primary" @click="showRunDialog = true">执行回测</el-button>
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
        :default-sort="{ prop: 'id', order: 'descending' }"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" sortable />
        <el-table-column prop="strategy_name" label="策略" />
        <el-table-column label="时间范围">
          <template #default="{ row }">
            {{ formatDate(row.start_date) }} ~ {{ formatDate(row.end_date) }}
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
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="selectResult(row)">
              查看
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

    <el-card v-if="selectedResult" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>详细结果 - {{ selectedResult.strategy_name }}</span>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="6">
          <el-statistic title="总收益率" :value="selectedResult.metrics.total_return * 100" :precision="2" suffix="%" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="年化收益率" :value="selectedResult.metrics.annual_return * 100" :precision="2" suffix="%" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="最大回撤" :value="selectedResult.metrics.max_drawdown * 100" :precision="2" suffix="%" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="夏普比率" :value="selectedResult.metrics.sharpe_ratio" :precision="2" />
        </el-col>
      </el-row>

      <div ref="chartRef" style="width: 100%; height: 400px; margin-top: 20px"></div>
    </el-card>

    <!-- 执行回测对话框 -->
    <el-dialog v-model="showRunDialog" title="执行回测" width="400px">
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
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import { useBacktestStore } from '../stores/backtest'
import { useStrategyStore } from '../stores/strategy'
import type { BacktestResponse } from '../types'

const route = useRoute()
const backtestStore = useBacktestStore()
const strategyStore = useStrategyStore()

const selectedResult = ref<BacktestResponse | null>(null)
const showRunDialog = ref(false)
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

// 多选状态
const selectedIds = ref<number[]>([])

// 筛选状态
const filterStrategy = ref<number | undefined>()
const filterDateRange = ref<[string, string] | undefined>()

const form = ref({
  strategy_id: Number(route.query.strategy_id) || undefined,
  start_date: '2020-01-01',
  end_date: '2024-12-31',
  initial_capital: 100000,
})

// 排序状态
const sortField = ref('id')
const sortOrder = ref<'ascending' | 'descending'>('descending')

// 分页状态
const currentPage = ref(1)
const pageSize = ref(10)
const pageSizes = [10, 20, 50, 100]

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
  await backtestStore.fetchResults()

  if (backtestStore.results.length > 0) {
    selectResult(backtestStore.results[0]!)
  }
})

const selectResult = (result: BacktestResponse) => {
  selectedResult.value = result
  nextTick(() => {
    renderChart()
  })
}

const runBacktest = async () => {
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
    if (backtestStore.results.length > 0) {
      selectResult(backtestStore.results[0]!)
    }
  } catch (error) {
    ElMessage.error('回测执行失败')
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

  chart.setOption({
    title: {
      text: '净值曲线',
    },
    tooltip: {
      trigger: 'axis',
    },
    xAxis: {
      type: 'category',
      data: dates,
    },
    yAxis: {
      type: 'value',
      name: '净值',
    },
    series: [
      {
        name: '净值',
        type: 'line',
        data: values,
        smooth: true,
      },
    ],
  })
}

const formatDate = (dateStr: string) => {
  return dateStr.split('T')[0]
}

const getReturnClass = (value: number) => {
  return value >= 0 ? 'text-success' : 'text-danger'
}

const handleSortChange = ({ prop, order }: { prop: string; order: string | null }) => {
  sortField.value = prop || 'id'
  sortOrder.value = order === 'ascending' ? 'ascending' : 'descending'
}

const handleSelectionChange = (selection: BacktestResponse[]) => {
  selectedIds.value = selection.map(item => item.id)
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

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}
</style>
