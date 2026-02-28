<template>
  <el-container class="layout">
    <el-aside width="200px">
      <div class="logo">
        <h2>Q-Alpha</h2>
        <p>量化策略回测</p>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#001529"
        text-color="#fff"
        active-text-color="#1890ff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/strategy">
          <el-icon><Setting /></el-icon>
          <span>策略配置</span>
        </el-menu-item>
        <el-menu-item index="/backtest">
          <el-icon><DataLine /></el-icon>
          <span>回测结果</span>
        </el-menu-item>
        <el-menu-item index="/data">
          <el-icon><FolderOpened /></el-icon>
          <span>数据管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header>
        <div class="header-title">{{ pageTitle }}</div>
      </el-header>

      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const activeMenu = computed(() => route.path)

const pageTitle = computed(() => {
  return route.meta.title as string || 'Q-Alpha'
})
</script>

<style scoped>
.layout {
  width: 100%;
  height: 100vh;
}

.logo {
  padding: 20px;
  text-align: center;
  color: #fff;
  background-color: #002140;
}

.logo h2 {
  margin: 0;
  font-size: 24px;
}

.logo p {
  margin: 5px 0 0;
  font-size: 12px;
  color: #aaa;
}

.el-aside {
  background-color: #001529;
}

.el-header {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
}

.header-title {
  font-size: 18px;
  font-weight: 500;
}

.el-main {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>
