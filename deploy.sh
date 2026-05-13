#!/bin/bash
# 宏观经济数据监控系统 - 生产环境部署脚本
# 用法：bash deploy.sh

set -e

echo "🚀 宏观经济数据监控系统 - 生产环境部署"
echo "=========================================="

# 1. 创建虚拟环境
echo "📦 步骤 1/5: 创建 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 2. 安装依赖
echo "📦 步骤 2/5: 安装 Python 依赖..."
./venv/bin/pip install --upgrade pip -q
./venv/bin/pip install -r requirements.txt -q
echo "✅ 依赖安装完成"

# 3. 配置文件检查
echo "📝 步骤 3/5: 配置文件检查..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，从 .env.example 复制..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件填入必要的 API Keys"
fi

# 4. 运行环境检查
echo "🔍 步骤 4/5: 运行环境健康检查..."
./venv/bin/python -m macro_system check

# 5. 创建 systemd 服务 (可选)
echo "🔧 步骤 5/5: 创建 systemd 服务 (可选)..."
if [ "$1" == "--service" ]; then
    SERVICE_FILE="/etc/systemd/system/macro-system.service"
    echo "📄 创建 systemd 服务文件: $SERVICE_FILE"
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Macro Economic Data Monitoring System
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python -m macro_system run
Environment="PATH=$(pwd)/venv/bin"

[Install]
WantedBy=multi-user.target
EOF
    echo "✅ Systemd 服务文件创建完成"
    echo "📌 运行以下命令启用定时任务:"
    echo "   sudo systemctl enable macro-system.timer"
    echo "   sudo systemctl start macro-system.timer"
else
    echo "ℹ️  跳过 systemd 服务创建 (--service 参数启用)"
fi

echo ""
echo "=========================================="
echo "✅ 部署完成!"
echo ""
echo "📌 下一步操作:"
echo "1. 编辑 .env 文件，填入 FRED API Key 和其他配置"
echo "2. 运行测试：./venv/bin/python -m macro_system check"
echo "3. 执行采集：./venv/bin/python -m macro_system run"
echo "4. 启动看板：./venv/bin/streamlit run macro_system/dashboard.py"
echo ""
echo "📚 详细文档：README.md, QUICKSTART.md, WHITEPAPER.md"
