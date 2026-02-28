<template>
  <div class="strategy-config">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>策略列表</span>
              <el-button type="primary" @click="showCreateDialog = true">
                新建策略
              </el-button>
            </div>
          </template>

          <el-table :data="strategyStore.strategies" @row-click="selectStrategy" stripe>
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="rebalance_type" label="再平衡" width="100">
              <template #default="{ row }">
                {{ formatRebalanceType(row.rebalance_type) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card v-if="selectedStrategy">
          <template #header>
            <div class="card-header">
              <span>{{ selectedStrategy.name }}</span>
              <div>
                <el-button @click="runBacktest">执行回测</el-button>
                <el-button type="danger" @click="deleteStrategy">删除</el-button>
              </div>
            </div>
          </template>

          <el-descriptions :column="2" border>
            <el-descriptions-item label="策略名称">
              {{ selectedStrategy.name }}
            </el-descriptions-item>
            <el-descriptions-item label="再平衡方式">
              {{ formatRebalanceType(selectedStrategy.rebalance_type) }}
            </el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">
              {{ selectedStrategy.description || '-' }}
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
        </el-card>

        <el-empty v-else description="请选择一个策略" />
      </el-col>
    </el-row>

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

const selectedStrategy = ref<Strategy | null>(null)
const showCreateDialog = ref(false)

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

const allocationData = computed(() => {
  if (!selectedStrategy.value) return []
  return Object.entries(selectedStrategy.value.allocation).map(([code, weight]) => {
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
  if (strategyStore.strategies.length > 0) {
    selectedStrategy.value = strategyStore.strategies[0]
  }
})

const selectStrategy = (strategy: Strategy) => {
  selectedStrategy.value = strategy
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
  if (asset) {
    form.value.allocations[index].code = asset.code
    form.value.allocations[index].name = asset.name
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
      rebalance_type: form.value.rebalance_type,
      allocation,
    })

    ElMessage.success('策略创建成功')
    showCreateDialog.value = false
    resetForm()
  } catch (error) {
    ElMessage.error('策略创建失败')
  }
}

const deleteStrategy = async () => {
  if (!selectedStrategy.value) return

  try {
    await ElMessageBox.confirm('确定删除该策略吗？', '提示', {
      type: 'warning',
    })

    await strategyStore.deleteStrategy(selectedStrategy.value.id)
    ElMessage.success('策略删除成功')
    selectedStrategy.value = null
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('策略删除失败')
    }
  }
}

const runBacktest = () => {
  if (!selectedStrategy.value) return
  router.push({ name: 'Backtest', query: { strategy_id: selectedStrategy.value.id } })
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
