#!/bin/bash
#
# Q-Alpha 一键启动脚本
# 同时启动后端和前端服务
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# PID 文件
BACKEND_PID_FILE="$PROJECT_ROOT/.backend.pid"
FRONTEND_PID_FILE="$PROJECT_ROOT/.frontend.pid"

echo ""
echo "==================================="
echo "  Q-Alpha 量化策略回测系统"
echo "==================================="
echo ""

# 检查虚拟环境
VENV_PATH="$PROJECT_ROOT/.venv"

if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}警告: 虚拟环境不存在${NC}"
    echo "请先运行 ./scripts/run_all.sh 初始化项目"
    exit 1
fi

# 检查前端依赖
if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    echo -e "${YELLOW}警告: 前端依赖未安装${NC}"
    echo "请先运行 ./scripts/run_all.sh 初始化项目"
    exit 1
fi

# 检查是否已有服务在运行
if [ -f "$BACKEND_PID_FILE" ]; then
    BACKEND_PID=$(cat "$BACKEND_PID_FILE")
    if ps -p "$BACKEND_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}警告: 后端服务已在运行 (PID: $BACKEND_PID)${NC}"
        echo "请先运行 ./stop.sh 关闭服务"
        exit 1
    else
        rm -f "$BACKEND_PID_FILE"
    fi
fi

if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
    if ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}警告: 前端服务已在运行 (PID: $FRONTEND_PID)${NC}"
        echo "请先运行 ./stop.sh 关闭服务"
        exit 1
    else
        rm -f "$FRONTEND_PID_FILE"
    fi
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source "$VENV_PATH/bin/activate"

# 启动后端服务
echo ""
echo -e "${BLUE}[1/2]${NC} 启动后端服务..."
cd "$PROJECT_ROOT"
nohup python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$BACKEND_PID_FILE"

# 等待后端启动
sleep 3

# 检查后端是否成功启动
if ps -p "$BACKEND_PID" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 后端服务启动成功 (PID: $BACKEND_PID)"
else
    echo -e "${RED}✗${NC} 后端服务启动失败"
    echo "查看日志: cat logs/backend.log"
    exit 1
fi

# 启动前端服务
echo ""
echo -e "${BLUE}[2/2]${NC} 启动前端服务..."
cd "$PROJECT_ROOT/frontend"
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$FRONTEND_PID_FILE"

# 等待前端启动
sleep 3

# 检查前端是否成功启动
if ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 前端服务启动成功 (PID: $FRONTEND_PID)"
else
    echo -e "${RED}✗${NC} 前端服务启动失败"
    echo "查看日志: cat logs/frontend.log"
    exit 1
fi

echo ""
echo "==================================="
echo -e "${GREEN}  所有服务启动成功！${NC}"
echo "==================================="
echo ""
echo -e "后端 API: ${BLUE}http://localhost:8000${NC}"
echo -e "API 文档: ${BLUE}http://localhost:8000/docs${NC}"
echo -e "前端界面: ${BLUE}http://localhost:5173${NC}"
echo ""
echo "日志文件:"
echo "  - 后端: logs/backend.log"
echo "  - 前端: logs/frontend.log"
echo ""
echo -e "${YELLOW}提示: 使用 ./stop.sh 关闭所有服务${NC}"
echo ""
