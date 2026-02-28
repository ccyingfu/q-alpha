<template>
  <div class="data-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>资产列表</span>
          <div class="header-actions">
            <el-button type="success" @click="handleAdd" :icon="Plus">添加资产</el-button>
            <el-button type="primary" @click="refreshData">刷新数据</el-button>
          </div>
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

    <!-- 添加资产对话框 -->
    <el-dialog v-model="showAddDialog" title="添加资产" width="500px" @close="handleClose">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="80px"
        :disabled="isQuerying"
      >
        <el-form-item label="资产代码" prop="code">
          <el-input
            v-model="formData.code"
            placeholder="请输入资产代码"
            maxlength="20"
            show-word-limit
            @blur="handleCodeBlur"
          >
            <template #suffix>
              <el-icon v-if="isQuerying" class="is-loading"><Loading /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="资产名称" prop="name">
          <el-input
            v-model="formData.name"
            placeholder="请输入资产名称"
            maxlength="100"
            show-word-limit
            @blur="handleNameBlur"
          >
            <template #suffix>
              <el-icon v-if="isQuerying" class="is-loading"><Loading /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="资产类型" prop="type">
          <el-select v-model="formData.type" placeholder="请选择资产类型" style="width: 100%">
            <el-option label="指数" value="index" />
            <el-option label="ETF" value="etf" />
            <el-option label="股票" value="stock" />
            <el-option label="债券" value="bond" />
            <el-option label="基金" value="fund" />
            <el-option label="商品" value="commodity" />
          </el-select>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showAddDialog = false" :disabled="isQuerying">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="isSubmitting">确定</el-button>
      </template>
    </el-dialog>

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
import { Plus, Loading } from '@element-plus/icons-vue'
import { useAssetStore } from '../stores/asset'
import { marketApi } from '../api/client'
import type { Asset, MarketDataPoint } from '../types'
import type { FormInstance, FormRules } from 'element-plus'

const assetStore = useAssetStore()

// 数据详情对话框相关
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

// 添加资产对话框相关
const showAddDialog = ref(false)
const formRef = ref<FormInstance>()
const isSubmitting = ref(false)
const isQuerying = ref(false)

// 表单数据
const formData = ref({
  code: '',
  name: '',
  type: '' as any,
  description: '',
})

// 表单验证规则
const formRules: FormRules = {
  code: [
    { required: true, message: '请输入资产代码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value && value.trim() === '') {
          callback(new Error('资产代码不能为空格'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  name: [
    { required: true, message: '请输入资产名称', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value && value.trim() === '') {
          callback(new Error('资产名称不能为空格'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  type: [{ required: true, message: '请选择资产类型', trigger: 'change' }],
}

// 防抖函数
function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null
  return (...args: Parameters<T>) => {
    if (timeoutId) clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}

// 代码失焦时查询名称
const handleCodeBlur = debounce(async () => {
  const code = formData.value.code.trim()
  if (!code || formData.value.name) {
    return
  }

  isQuerying.value = true
  try {
    // 先搜索内部数据库
    let results = await assetStore.searchAssets(code)

    // 如果内部没有结果，从外部数据源搜索
    if (results.length === 0) {
      results = await assetStore.searchAssetsExternal(code)
    }

    if (results.length > 0) {
      formData.value.name = results[0].name
      if (!formData.value.type) {
        formData.value.type = results[0].type
      }
      ElMessage.success('已自动填充资产名称')
    }
  } catch (error) {
    // 查询失败不影响用户手动输入
    console.error('查询资产名称失败:', error)
  } finally {
    isQuerying.value = false
  }
}, 300)

// 名称失焦时查询代码
const handleNameBlur = debounce(async () => {
  const name = formData.value.name.trim()
  if (!name || formData.value.code) {
    return
  }

  isQuerying.value = true
  try {
    // 先搜索内部数据库
    let results = await assetStore.searchAssets(name)

    // 如果内部没有结果，从外部数据源搜索
    if (results.length === 0) {
      results = await assetStore.searchAssetsExternal(name)
    }

    if (results.length > 0) {
      formData.value.code = results[0].code
      if (!formData.value.type) {
        formData.value.type = results[0].type
      }
      ElMessage.success('已自动填充资产代码')
    }
  } catch (error) {
    // 查询失败不影响用户手动输入
    console.error('查询资产代码失败:', error)
  } finally {
    isQuerying.value = false
  }
}, 300)

// 打开添加对话框
const handleAdd = () => {
  showAddDialog.value = true
}

// 关闭对话框并重置表单
const handleClose = () => {
  formRef.value?.resetFields()
  formData.value = {
    code: '',
    name: '',
    type: '',
    description: '',
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  isSubmitting.value = true
  try {
    await assetStore.createAsset({
      code: formData.value.code.trim(),
      name: formData.value.name.trim(),
      type: formData.value.type,
      description: formData.value.description?.trim() || null,
    })

    ElMessage.success('资产添加成功')
    showAddDialog.value = false
    handleClose()
    await assetStore.fetchAssets()
  } catch (error: any) {
    const message = error.response?.data?.detail || error.message || '添加资产失败'
    ElMessage.error(message)
  } finally {
    isSubmitting.value = false
  }
}

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

.header-actions {
  display: flex;
  gap: 8px;
}

.data-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
