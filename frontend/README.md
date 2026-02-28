# Frontend 模块

前端界面模块，基于 Vue 3 + TypeScript + Element Plus。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **语言**: TypeScript
- **构建工具**: Vite
- **UI 组件**: Element Plus
- **图表库**: ECharts
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP 客户端**: Axios

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

## 项目结构

```
src/
├── api/              # API 客户端
├── components/       # 组件
├── router/           # 路由配置
├── stores/           # Pinia 状态管理
├── styles/           # 全局样式
├── types/            # TypeScript 类型定义
└── views/            # 页面视图
```

## 页面说明

- **Dashboard** - 仪表盘，显示系统概览
- **StrategyConfig** - 策略配置与管理
- **BacktestResult** - 回测结果展示
- **DataManage** - 资产数据管理

