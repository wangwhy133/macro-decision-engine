#!/bin/bash
# 宏观经济数据监控系统 - 一键启动脚本
# 用法：bash start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 宏观经济数据监控系统 - 启动脚本"
echo "======================================"
echo ""

# 1. 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
    
    echo "📦 安装依赖..."
    ./venv/bin/pip install --upgrade pip -q
    ./venv/bin/pip install -r requirements.txt -q
    echo "✅ 依赖安装完成"
else
    echo "✅ 虚拟环境已存在"
fi

# 2. 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，正在创建..."
    cp .env.example .env 2>/dev/null || echo "# 请编辑 .env 文件填入 API Keys" > .env
    echo "⚠️  请编辑 .env 文件填入必要的 API Keys"
    echo "   运行：nano .env"
    echo ""
fi

# 3. 运行健康检查
echo ""
echo "🔍 运行健康检查..."
./venv/bin/python -m macro_system check

if [ $? -ne 0 ]; then
    echo "❌ 健康检查失败，请检查配置"
    exit 1
fi

echo ""
echo "======================================"
echo "✅ 系统就绪！"
echo ""
echo "📋 可用命令:"
echo "  1. 运行数据采集:  ./venv/bin/python -m macro_system run"
echo "  2. 启动可视化看板: ./venv/bin/streamlit run macro_system/dashboard.py"
echo "  3. 查看帮助:      ./venv/bin/python -m macro_system --help"
echo ""
echo "💡 提示：配置 API Keys 后运行数据采集"
echo "   编辑：nano .env"
echo ""
