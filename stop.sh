#!/bin/bash
#
# Q-Alpha 一键关闭脚本
# 关闭后端和前端服务
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
echo "  Q-Alpha 服务关闭"
echo "==================================="
echo ""

SERVICES_STOPPED=0

# 关闭后端服务
if [ -f "$BACKEND_PID_FILE" ]; then
    BACKEND_PID=$(cat "$BACKEND_PID_FILE")
    if ps -p "$BACKEND_PID" > /dev/null 2>&1; then
        echo -e "${BLUE}正在关闭后端服务...${NC} (PID: $BACKEND_PID)"
        kill "$BACKEND_PID"
        sleep 1
        # 如果进程还在，强制关闭
        if ps -p "$BACKEND_PID" > /dev/null 2>&1; then
            kill -9 "$BACKEND_PID"
        fi
        echo -e "${GREEN}✓${NC} 后端服务已关闭"
        SERVICES_STOPPED=1
    else
        echo -e "${YELLOW}后端服务未运行${NC}"
    fi
    rm -f "$BACKEND_PID_FILE"
else
    # 尝试通过进程名查找
    BACKEND_PIDS=$(pgrep -f "uvicorn backend.main:app" || true)
    if [ -n "$BACKEND_PIDS" ]; then
        echo -e "${BLUE}正在关闭后端服务...${NC}"
        echo "$BACKEND_PIDS" | xargs kill 2>/dev/null || true
        sleep 1
        echo -e "${GREEN}✓${NC} 后端服务已关闭"
        SERVICES_STOPPED=1
    fi
fi

# 关闭前端服务
if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
    if ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
        echo -e "${BLUE}正在关闭前端服务...${NC} (PID: $FRONTEND_PID)"
        kill "$FRONTEND_PID"
        sleep 1
        # 如果进程还在，强制关闭
        if ps -p "$FRONTEND_PID" > /dev/null 2>&1; then
            kill -9 "$FRONTEND_PID"
        fi
        echo -e "${GREEN}✓${NC} 前端服务已关闭"
        SERVICES_STOPPED=1
    else
        echo -e "${YELLOW}前端服务未运行${NC}"
    fi
    rm -f "$FRONTEND_PID_FILE"
else
    # 尝试通过进程名查找
    FRONTEND_PIDS=$(pgrep -f "vite.*q-alpha" || true)
    if [ -n "$FRONTEND_PIDS" ]; then
        echo -e "${BLUE}正在关闭前端服务...${NC}"
        echo "$FRONTEND_PIDS" | xargs kill 2>/dev/null || true
        sleep 1
        echo -e "${GREEN}✓${NC} 前端服务已关闭"
        SERVICES_STOPPED=1
    fi
fi

# 清理可能遗留的 npm/node 进程
NODE_PIDS=$(pgrep -f "npm.*dev.*q-alpha" || true)
if [ -n "$NODE_PIDS" ]; then
    echo "$NODE_PIDS" | xargs kill 2>/dev/null || true
fi

echo ""
if [ $SERVICES_STOPPED -eq 1 ]; then
    echo -e "${GREEN}==================================="
    echo "  所有服务已关闭"
    echo "===================================${NC}"
else
    echo -e "${YELLOW}没有发现运行中的服务${NC}"
fi
echo ""
