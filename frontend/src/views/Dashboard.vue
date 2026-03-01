<template>
  <div class="dashboard" v-loading="isLoading" element-loading-text="加载中...">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon blue"><Wallet /></el-icon>
            <div class="stat-text">
              <p class="stat-label">总策略数</p>
              <p class="stat-value">{{ strategyCount }}</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon green"><DataLine /></el-icon>
            <div class="stat-text">
              <p class="stat-label">回测次数</p>
              <p class="stat-value">{{ backtestCount }}</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon orange"><FolderOpened /></el-icon>
            <div class="stat-text">
              <p class="stat-label">资产数量</p>
              <p class="stat-value">{{ assetCount }}</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon purple"><TrendCharts /></el-icon>
            <div class="stat-text">
              <p class="stat-label">数据更新</p>
              <p class="stat-value">今日</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>欢迎使用 Q-Alpha 量化策略回测系统</span>
            </div>
          </template>
          <div class="welcome-content">
            <h3>功能特性</h3>
            <ul>
              <li>📊 <strong>多资产数据获取</strong>：支持指数、ETF、个股等金融数据，基于 Baostock 免费数据源</li>
              <li>💾 <strong>智能缓存机制</strong>：Parquet 格式本地缓存，支持增量更新</li>
              <li>🔄 <strong>策略回测引擎</strong>：支持定期再平衡、阈值触发等多种策略，自动获取缺失数据</li>
              <li>📈 <strong>绩效指标计算</strong>：年化收益率、最大回撤、夏普比率、索提诺比率、卡玛比率等专业指标</li>
              <li>🎨 <strong>可视化界面</strong>：基于 ECharts 的交互式图表，净值曲线对比、回撤分析</li>
              <li>⚖️ <strong>基准对比</strong>：支持上证指数、沪深300 等基准收益对比</li>
            </ul>

            <h3>快速开始</h3>
            <ol>
              <li>前往 <strong>数据管理</strong> 页面，查看可用资产和历史行情数据</li>
              <li>在 <strong>策略配置</strong> 页面，创建您的投资组合策略，设置资产权重</li>
              <li>点击 <strong>执行回测</strong>，选择日期范围和初始资金，系统自动获取缺失数据</li>
              <li>在 <strong>回测结果</strong> 页面，查看净值曲线、绩效指标，对比基准收益</li>
            </ol>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useStrategyStore } from '../stores/strategy'
import { useBacktestStore } from '../stores/backtest'
import { useAssetStore } from '../stores/asset'

const strategyStore = useStrategyStore()
const backtestStore = useBacktestStore()
const assetStore = useAssetStore()

const strategyCount = ref(0)
const backtestCount = ref(0)
const assetCount = ref(0)
const isLoading = ref(true)

onMounted(async () => {
  try {
    // 并行加载统计数据
    await Promise.all([
      strategyStore.fetchStrategies(),
      backtestStore.fetchResults(),
      assetStore.fetchAssets(),
    ])

    strategyCount.value = strategyStore.strategies.length
    backtestCount.value = backtestStore.results.length
    assetCount.value = assetStore.assets.length
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.dashboard {
  width: 100%;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  font-size: 48px;
  margin-right: 20px;
}

.stat-icon.blue {
  color: #409eff;
}

.stat-icon.green {
  color: #67c23a;
}

.stat-icon.orange {
  color: #e6a23c;
}

.stat-icon.purple {
  color: #909399;
}

.stat-text {
  flex: 1;
}

.stat-label {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.stat-value {
  margin: 10px 0 0;
  font-size: 28px;
  font-weight: bold;
}

.card-header {
  font-size: 16px;
  font-weight: 500;
}

.welcome-content {
  line-height: 1.8;
}

.welcome-content h3 {
  margin-top: 20px;
  margin-bottom: 10px;
}

.welcome-content ul,
.welcome-content ol {
  padding-left: 20px;
}

.welcome-content li {
  margin-bottom: 8px;
}
</style>
