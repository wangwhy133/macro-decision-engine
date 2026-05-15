#!/bin/bash
# setup.sh - MDE 一键安装脚本 (生产级)
# 功能：创建虚拟环境、安装依赖、初始化配置

set -e  # 遇到错误立即退出

echo "🚀 MDE 系统安装脚本 v4.1.2"
echo "========================================"

# 1. 检查 Python 版本
echo "1️⃣  检查 Python 版本..."
python3 --version || { echo "❌ Python3 未安装"; exit 1; }

# 2. 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "2️⃣  创建虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 3. 激活虚拟环境
echo "3️⃣  激活虚拟环境..."
source venv/bin/activate

# 4. 升级 pip
echo "4️⃣  升级 pip..."
pip install --upgrade pip

# 5. 安装依赖
echo "5️⃣  安装 Python 依赖..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ 依赖安装完成"
else
    echo "❌ requirements.txt 不存在"
    exit 1
fi

# 6. 创建必要目录
echo "6️⃣  创建必要目录..."
mkdir -p logs data/raw data/features

# 7. 初始化环境变量
echo "7️⃣  初始化环境变量..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️  请编辑 .env 文件，填入 MINIMAX_API_KEY"
        echo "   然后运行：bash run_full_system.sh"
    else
        echo "❌ .env.example 不存在"
        exit 1
    fi
else
    echo "✅ .env 已存在"
fi

# 8. 运行健康检查
echo "8️⃣  运行健康检查..."
python3 -m src.services.healthcheck || echo "⚠️  健康检查未通过，请检查配置"

echo ""
echo "========================================"
echo "✅ 安装完成！"
echo ""
echo "下一步:"
echo "  1. 编辑 .env 文件，填入 MINIMAX_API_KEY"
echo "  2. 运行：bash run_full_system.sh"
echo "========================================"
