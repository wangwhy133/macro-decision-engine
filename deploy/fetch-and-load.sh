#!/bin/bash
# 一键获取真实数据并导入
# 用法：bash deploy/fetch-and-load.sh

set -e

echo "🚀 开始获取真实数据 (AKShare)..."

# 1. 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未检测到 Python3，请先安装 Python3"
    exit 1
fi

# 2. 检查并安装 pip 依赖
echo "📦 检查 Python 依赖..."
cd "$(dirname "$0")/../data_fetch"

if ! python3 -c "import akshare" 2>/dev/null; then
    echo "⚠️  未安装 AKShare，正在安装..."
    pip3 install -r requirements.txt
else
    echo "✅ AKShare 已安装"
fi

# 3. 运行抓取脚本
echo "📊 正在抓取数据..."
python3 ak_fetch.py

# 4. 导入数据库
echo "💾 导入数据库..."
cd ..
npm run load-csv

echo ""
echo "🎉 数据获取并导入完成！"
echo "📊 运行以下命令验证："
echo "   npm run decision"
