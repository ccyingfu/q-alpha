<template>
  <div class="dashboard">
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
              <li>📊 多资产数据获取：支持指数、ETF、个股等金融数据</li>
              <li>💾 本地数据存储：基于 SQLite 的数据持久化</li>
              <li>🔄 策略回测引擎：支持定期再平衡、阈值触发等多种策略</li>
              <li>📈 绩效指标计算：夏普比率、最大回撤、卡玛比率等专业指标</li>
              <li>🎨 可视化界面：基于 ECharts 的交互式数据展示</li>
            </ul>

            <h3>快速开始</h3>
            <ol>
              <li>前往 <strong>数据管理</strong> 页面，更新资产数据</li>
              <li>在 <strong>策略配置</strong> 页面，创建您的投资策略</li>
              <li>点击 <strong>执行回测</strong>，查看策略表现</li>
              <li>在 <strong>回测结果</strong> 页面，分析绩效指标</li>
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

onMounted(async () => {
  // 加载统计数据
  await strategyStore.fetchStrategies()
  await backtestStore.fetchResults()
  await assetStore.fetchAssets()

  strategyCount.value = strategyStore.strategies.length
  backtestCount.value = backtestStore.results.length
  assetCount.value = assetStore.assets.length
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
