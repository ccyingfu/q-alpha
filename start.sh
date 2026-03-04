#!/bin/bash
#
# Q-Alpha 一键启动脚本
# 同时启动后端和前端服务
# 支持自动初始化项目
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

# 初始化项目函数
init_project() {
    echo ""
    echo -e "${YELLOW}检测到项目未初始化，开始自动初始化...${NC}"
    echo ""

    # 创建日志目录
    mkdir -p "$PROJECT_ROOT/logs"

    # 初始化后端
    if [ ! -d "$PROJECT_ROOT/.venv" ]; then
        echo -e "${BLUE}[1/2]${NC} 初始化后端环境..."
        cd "$PROJECT_ROOT"

        # 检查 Python 是否安装
        if ! command -v python3 &> /dev/null; then
            echo -e "${RED}错误: 未找到 Python3${NC}"
            exit 1
        fi

        # 创建虚拟环境
        echo "创建虚拟环境..."
        python3 -m venv .venv

        # 激活虚拟环境并安装依赖
        echo "安装后端依赖..."
        source .venv/bin/activate
        pip install --upgrade pip -q
        pip install -r requirements.txt -q

        echo -e "${GREEN}✓${NC} 后端环境初始化完成"
    else
        echo -e "${GREEN}✓${NC} 后端环境已存在"
    fi

    # 初始化前端
    if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
        echo ""
        echo -e "${BLUE}[2/2]${NC} 初始化前端环境..."
        cd "$PROJECT_ROOT/frontend"

        # 检查 Node.js 是否安装
        if ! command -v node &> /dev/null; then
            echo -e "${RED}错误: 未找到 Node.js${NC}"
            exit 1
        fi

        # 安装前端依赖
        echo "安装前端依赖..."
        npm install -q

        echo -e "${GREEN}✓${NC} 前端环境初始化完成"
    else
        echo -e "${GREEN}✓${NC} 前端环境已存在"
    fi

    echo ""
    echo -e "${GREEN}项目初始化完成！${NC}"
    echo ""
}

# 检查是否需要初始化
NEED_INIT=false

# 检查虚拟环境
VENV_PATH="$PROJECT_ROOT/.venv"

if [ ! -d "$VENV_PATH" ]; then
    NEED_INIT=true
fi

# 检查前端依赖
if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    NEED_INIT=true
fi

# 如果需要初始化，执行初始化
if [ "$NEED_INIT" = true ]; then
    init_project
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
echo -e "前端界面: ${BLUE}http://localhost:8001${NC}"
echo ""
echo "日志文件:"
echo "  - 后端: logs/backend.log"
echo "  - 前端: logs/frontend.log"
echo ""
echo -e "${YELLOW}提示: 使用 ./stop.sh 关闭所有服务${NC}"
echo ""
