<template>
  <div class="strategy-config">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>策略配置</span>
          <el-button type="primary" @click="showCreateDialog = true">
            新建策略
          </el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="filter-bar">
        <el-select
          v-model="filterRebalanceType"
          placeholder="按再平衡方式筛选"
          clearable
          style="width: 200px"
        >
          <el-option label="按月" value="monthly" />
          <el-option label="按季度" value="quarterly" />
          <el-option label="按年" value="yearly" />
          <el-option label="阈值触发" value="threshold" />
        </el-select>

        <el-button
          v-if="filterRebalanceType"
          link
          type="primary"
          @click="resetFilters"
          style="margin-left: 16px"
        >
          重置筛选
        </el-button>
      </div>

      <el-table
        :data="pagedStrategies"
        @sort-change="handleSortChange"
        stripe
        v-loading="strategyStore.loading"
        element-loading-text="加载中..."
      >
        <el-table-column prop="name" label="名称" sortable="custom">
          <template #default="{ row }">
            <strong>{{ row.name }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="rebalance_type" label="再平衡方式" width="120">
          <template #default="{ row }">
            {{ formatRebalanceType(row.rebalance_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="{ row }">
            <span :title="row.description" class="description-text">
              {{ row.description || '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" sortable="custom">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row)">
              查看
            </el-button>
            <el-button link type="primary" @click="runBacktest(row)">
              回测
            </el-button>
            <el-button link type="danger" @click="deleteStrategy(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="totalCount"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

    <!-- 策略详情弹窗 -->
    <el-dialog v-model="showDetailDialog" title="策略详情" width="700px">
      <div v-if="currentStrategy">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="策略名称">
            {{ currentStrategy.name }}
          </el-descriptions-item>
          <el-descriptions-item label="再平衡方式">
            {{ formatRebalanceType(currentStrategy.rebalance_type) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentStrategy.description || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <h4 style="margin-top: 20px">资产配置</h4>
        <el-table :data="allocationData">
          <el-table-column prop="name" label="资产">
            <template #default="{ row }">
              {{ row.name }} ({{ row.code }})
            </template>
          </el-table-column>
          <el-table-column prop="weight" label="权重">
            <template #default="{ row }">
              {{ (row.weight * 100).toFixed(1) }}%
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="primary" @click="runBacktestFromDetail">执行回测</el-button>
        <el-button type="danger" @click="deleteStrategyFromDetail">删除</el-button>
      </template>
    </el-dialog>

    <!-- 创建策略对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建策略" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="策略名称" required>
          <el-input v-model="form.name" placeholder="请输入策略名称" />
        </el-form-item>

        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" placeholder="请输入策略描述" />
        </el-form-item>

        <el-form-item label="再平衡方式">
          <el-select v-model="form.rebalance_type" style="width: 100%">
            <el-option label="按月" value="monthly" />
            <el-option label="按季度" value="quarterly" />
            <el-option label="按年" value="yearly" />
            <el-option label="阈值触发" value="threshold" />
          </el-select>
        </el-form-item>

        <el-form-item label="资产配置">
          <div class="allocation-list">
            <div v-for="(item, index) in form.allocations" :key="index" class="allocation-item">
              <el-select
                v-model="item.code"
                placeholder="选择资产"
                filterable
                style="width: 200px"
                @change="onAssetChange(index, $event)"
              >
                <el-option
                  v-for="asset in assetStore.assets"
                  :key="asset.code"
                  :label="`${asset.name} (${asset.code})`"
                  :value="asset.code"
                />
              </el-select>

              <el-input-number
                v-model="item.weight"
                :min="0"
                :max="100"
                :precision="1"
                style="width: 120px; margin-left: 12px"
              />
              <span style="margin-left: 4px">%</span>

              <el-button
                type="danger"
                :icon="Delete"
                circle
                size="small"
                style="margin-left: 12px"
                @click="removeAllocation(index)"
              />
            </div>

            <el-button type="primary" link @click="addAllocation">
              + 添加资产
            </el-button>

            <div class="weight-summary" :class="{ error: !isWeightValid }">
              权重合计: {{ totalWeight.toFixed(1) }}%
              <span v-if="!isWeightValid" class="warning">（需等于100%）</span>
            </div>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!isWeightValid" @click="createStrategy">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { useStrategyStore } from '../stores/strategy'
import { useAssetStore } from '../stores/asset'
import type { Strategy } from '../types'

interface AllocationItem {
  code: string
  name: string
  weight: number
}

const router = useRouter()
const strategyStore = useStrategyStore()
const assetStore = useAssetStore()

const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const currentStrategy = ref<Strategy | null>(null)

// 再平衡类型映射
const rebalanceTypeMap: Record<string, string> = {
  monthly: '按月',
  quarterly: '按季度',
  yearly: '按年',
  threshold: '阈值触发',
}

const formatRebalanceType = (type: string) => {
  return rebalanceTypeMap[type] || type
}

// 格式化日期时间
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

const form = ref({
  name: '',
  description: '',
  rebalance_type: 'monthly',
  allocations: [] as AllocationItem[],
})

// 权重总和计算
const totalWeight = computed(() =>
  form.value.allocations.reduce((sum, item) => sum + item.weight, 0)
)

// 权重是否有效
const isWeightValid = computed(() =>
  Math.abs(totalWeight.value - 100) < 0.01
)

// 筛选状态
const filterRebalanceType = ref<string | undefined>()

// 排序状态
const sortField = ref<'name' | 'created_at'>('created_at')
const sortOrder = ref<'ascending' | 'descending'>('descending')

// 分页状态
const currentPage = ref(1)
const pageSize = ref(10)

// 筛选后的数据
const filteredStrategies = computed(() => {
  let data = [...strategyStore.strategies]

  if (filterRebalanceType.value) {
    data = data.filter(s => s.rebalance_type === filterRebalanceType.value)
  }

  return data
})

// 排序后的数据
const sortedStrategies = computed(() => {
  const data = [...filteredStrategies.value]
  const order = sortOrder.value === 'ascending' ? 1 : -1

  return data.sort((a, b) => {
    if (sortField.value === 'name') {
      return a.name.localeCompare(b.name) * order
    } else {
      const dateA = a.created_at ? new Date(a.created_at).getTime() : 0
      const dateB = b.created_at ? new Date(b.created_at).getTime() : 0
      return (dateA - dateB) * order
    }
  })
})

// 总条数
const totalCount = computed(() => sortedStrategies.value.length)

// 分页后的数据
const pagedStrategies = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return sortedStrategies.value.slice(start, start + pageSize.value)
})

// 资产配置数据
const allocationData = computed(() => {
  if (!currentStrategy.value) return []
  return Object.entries(currentStrategy.value.allocation).map(([code, weight]) => {
    const asset = assetStore.assets.find(a => a.code === code)
    return {
      code,
      name: asset?.name || code,
      weight,
    }
  })
})

onMounted(async () => {
  await assetStore.fetchAssets()
  await strategyStore.fetchStrategies()
})

// 排序变化
const handleSortChange = ({ prop, order }: { prop: string; order: string | null }) => {
  sortField.value = (prop === 'name' || prop === 'created_at') ? prop : 'created_at'
  sortOrder.value = order === 'ascending' ? 'ascending' : 'descending'
}

// 重置筛选
const resetFilters = () => {
  filterRebalanceType.value = undefined
  currentPage.value = 1
}

// 查看详情
const viewDetail = (strategy: Strategy) => {
  currentStrategy.value = strategy
  showDetailDialog.value = true
}

// 从列表执行回测
const runBacktest = (strategy: Strategy) => {
  router.push({
    name: 'Backtest',
    query: { strategy_id: strategy.id, auto_run: 'true' }
  })
}

// 从详情弹窗执行回测
const runBacktestFromDetail = () => {
  if (currentStrategy.value) {
    showDetailDialog.value = false
    runBacktest(currentStrategy.value)
  }
}

// 删除策略
const deleteStrategy = async (strategy: Strategy) => {
  try {
    await ElMessageBox.confirm(`确定删除策略「${strategy.name}」吗？`, '提示', {
      type: 'warning',
    })

    await strategyStore.deleteStrategy(strategy.id)
    ElMessage.success('策略删除成功')

    // 如果当前页没有数据了，回到上一页
    if (pagedStrategies.value.length === 1 && currentPage.value > 1) {
      currentPage.value--
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('策略删除失败')
    }
  }
}

// 从详情弹窗删除策略
const deleteStrategyFromDetail = () => {
  if (currentStrategy.value) {
    showDetailDialog.value = false
    deleteStrategy(currentStrategy.value)
  }
}

const addAllocation = () => {
  form.value.allocations.push({
    code: '',
    name: '',
    weight: 0,
  })
}

const removeAllocation = (index: number) => {
  form.value.allocations.splice(index, 1)
}

const onAssetChange = (index: number, code: string) => {
  const asset = assetStore.assets.find(a => a.code === code)
  if (asset && form.value.allocations[index]) {
    form.value.allocations[index]!.code = asset.code
    form.value.allocations[index]!.name = asset.name
  }
}

const resetForm = () => {
  form.value = {
    name: '',
    description: '',
    rebalance_type: 'monthly',
    allocations: [],
  }
}

const createStrategy = async () => {
  if (!isWeightValid.value) {
    ElMessage.warning('资产权重合计必须等于100%')
    return
  }

  try {
    const allocation: Record<string, number> = {}
    form.value.allocations.forEach(item => {
      allocation[item.code] = item.weight / 100
    })

    await strategyStore.createStrategy({
      name: form.value.name,
      description: form.value.description,
      rebalance_type: form.value.rebalance_type as 'monthly' | 'quarterly' | 'yearly' | 'threshold',
      allocation,
    })

    ElMessage.success('策略创建成功')
    showCreateDialog.value = false
    resetForm()
  } catch (error) {
    ElMessage.error('策略创建失败')
  }
}
</script>

<style scoped>
.strategy-config {
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

.description-text {
  display: inline-block;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.allocation-list {
  width: 100%;
}

.allocation-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.weight-summary {
  margin-top: 12px;
  font-size: 14px;
  color: #67c23a;
}

.weight-summary.error {
  color: #f56c6c;
}

.weight-summary .warning {
  font-size: 12px;
}
</style>
