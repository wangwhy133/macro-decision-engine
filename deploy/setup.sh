#!/bin/bash
# 宏观决策引擎 (MDE) 一键部署脚本
# 用法：bash deploy/setup.sh

set -e

echo "🚀 开始部署宏观决策引擎 (MDE)..."

# 1. 环境检查
echo "🔍 检查环境..."
if ! command -v node &> /dev/null; then
    echo "❌ 未检测到 Node.js，请先安装 Node.js >= 18"
    exit 1
fi

# 2. 安装依赖
echo "📦 安装依赖..."
npm install --production

# 3. 初始化数据库
echo "🗄️  初始化数据库..."
npm run quick-init

# 4. 创建日志目录
LOG_DIR="/var/log/mde"
if [ ! -d "$LOG_DIR" ]; then
    echo "📝 创建日志目录 $LOG_DIR"
    sudo mkdir -p $LOG_DIR
    sudo chmod 755 $LOG_DIR
fi

# 5. 配置 Cron (可选)
echo "⏰ 配置定时任务..."
read -p "是否添加每日 9:00 自动复盘任务？(y/n): " choice
if [ "$choice" == "y" ]; then
    CRON_CMD="0 9 * * * cd $(pwd) && $(which npx) tsx src/cli/daily-review.ts >> $LOG_DIR/daily.log 2>&1"
    (crontab -l | grep -v "daily-review" ; echo "$CRON_CMD") | crontab -
    echo "✅ Cron 任务已添加"
    crontab -l
else
    echo "⏭️  跳过 Cron 配置"
fi

# 6. 验证运行
echo "🧪 验证运行..."
npm run daily

echo ""
echo "🎉 部署完成！"
echo "📂 项目路径：$(pwd)"
echo "📊 数据库：$(pwd)/macro-decision.db"
echo "📝 日志目录：$LOG_DIR"
echo ""
echo "常用命令:"
echo "  npm run daily    - 每日复盘"
echo "  npm run backtest - 策略回测"
echo "  npm run decision - 生成决策报告"
echo "  crontab -r       - (可选) 删除定时任务"
