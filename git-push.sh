#!/bin/bash
# Macro System Git Push Script
# 用于将 P0->P2 全阶段成果推送到 GitHub

set -e

REPO_URL="https://github.com/YOUR_USERNAME/macro-system.git"
REMOTE_NAME="origin"
BRANCH_NAME="master"

echo "🚀 Macro System Git 推送脚本"
echo "================================"

# 1. 检查 Git 状态
if ! command -v git &> /dev/null; then
    echo "❌ 错误: 未找到 git 命令，请先安装 git"
    exit 1
fi

# 2. 检查远程仓库配置
if ! git remote get-url $REMOTE_NAME &> /dev/null; then
    echo "⚠️  未配置远程仓库，尝试添加..."
    git remote add $REMOTE_NAME $REPO_URL
else
    echo "✓ 远程仓库已配置: $(git remote get-url $REMOTE_NAME)"
fi

# 3. 推送
echo "📡 正在推送到 $REMOTE_NAME/$BRANCH_NAME ..."
git push $REMOTE_NAME $BRANCH_NAME

if [ $? -eq 0 ]; then
    echo "✅ 推送成功!"
    echo "🔗 请前往 GitHub 查看: https://github.com/YOUR_USERNAME/macro-system"
else
    echo "❌ 推送失败，请检查网络连接和凭证配置"
    echo "💡 提示: 如果使用 HTTPS，请确保已配置 git credential helper"
    echo "💡 提示: 或者使用 SSH: git remote set-url origin git@github.com:YOUR_USERNAME/macro-system.git"
    exit 1
fi
