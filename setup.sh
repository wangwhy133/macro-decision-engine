#!/bin/bash
# Macro System 一键安装脚本 (生产环境)
# 用法: bash setup.sh

set -e

echo "=========================================="
echo "Macro System 安装脚本 (P1.5)"
echo "=========================================="

# 1. 检查 Python 版本
echo -n "检查 Python 版本... "
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 python3，请安装 Python 3.10+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python $PYTHON_VERSION"

# 2. 创建目录结构
DATA_DIR="/opt/macro-push/data"
echo -n "创建数据目录 $DATA_DIR... "
sudo mkdir -p "$DATA_DIR"
sudo chown -R $(whoami):$(whoami) "$DATA_DIR"
echo "✓ 完成"

# 3. 安装依赖
echo "安装 Python 依赖..."
pip3 install -r requirements.txt
echo "✓ 依赖安装完成"

# 4. 配置文件
CONFIG_FILE="$HOME/.macro_config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -n "创建配置文件模板... "
    cp config.example.json "$CONFIG_FILE"
    echo "✓ 完成 ($CONFIG_FILE)"
    echo "⚠️  请编辑 $CONFIG_FILE 填入 API Keys"
else
    echo "✓ 配置文件已存在 ($CONFIG_FILE)"
fi

# 5. 环境变量
if [ ! -f ".env" ]; then
    echo -n "创建 .env 文件... "
    cp .env.example .env
    echo "✓ 完成 (.env)"
    echo "⚠️  请编辑 .env 填入敏感信息"
else
    echo "✓ .env 文件已存在"
fi

# 6. 验证安装
echo "运行安装后验证..."
python3 -m macro_system.config.config_validator

echo ""
echo "=========================================="
echo "✅ 安装完成!"
echo "=========================================="
echo "下一步:"
echo "1. 编辑 ~/.macro_config.json 填入 API Keys"
echo "2. 运行: python3 -m macro_system.core.orchestrator --dry-run"
echo "3. 配置定时任务: sudo systemctl enable macro-push.timer"
echo "=========================================="
