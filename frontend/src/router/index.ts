/**
 * 路由配置
 */

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Layout',
    component: () => import('../components/layout/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '仪表盘' },
      },
      {
        path: '/strategy',
        name: 'Strategy',
        component: () => import('../views/StrategyConfig.vue'),
        meta: { title: '策略配置' },
      },
      {
        path: '/backtest',
        name: 'Backtest',
        component: () => import('../views/BacktestResult.vue'),
        meta: { title: '回测结果' },
      },
      {
        path: '/data',
        name: 'Data',
        component: () => import('../views/DataManage.vue'),
        meta: { title: '数据管理' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
