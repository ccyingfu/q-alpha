#!/bin/bash
#
# Q-Alpha 一键启动脚本
#

set -e

echo "==================================="
echo "  Q-Alpha 量化策略回测系统"
echo "==================================="
echo ""

# 检查 Poetry
if ! command -v poetry &> /dev/null; then
    echo "错误: Poetry 未安装"
    echo "请访问 https://python-poetry.org/ 安装 Poetry"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "错误: Node.js 未安装"
    echo "请访问 https://nodejs.org/ 安装 Node.js"
    exit 1
fi

# 安装 Python 依赖
echo "安装 Python 依赖..."
poetry install

# 安装前端依赖
echo "安装前端依赖..."
cd frontend
npm install
cd ..

# 初始化数据库
echo "初始化数据库..."
poetry run python scripts/init_db.py

echo ""
echo "==================================="
echo "  初始化完成！"
echo "==================================="
echo ""
echo "启动服务："
echo ""
echo "  后端: poetry run uvicorn backend.main:app --reload"
echo "  前端: cd frontend && npm run dev"
echo ""
