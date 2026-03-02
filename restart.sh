#!/bin/bash
#
# Q-Alpha 一键重启脚本
# 重启后端和前端服务
#

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 关闭服务
./stop.sh

# 等待进程完全结束
sleep 2

# 启动服务
./start.sh
