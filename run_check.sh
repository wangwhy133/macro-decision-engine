#!/bin/bash
# Macro System 健康检查与快速运行脚本
# 用法：bash run_check.sh [--dry-run]

set -e

# 设置 PYTHONPATH (退到 workspace 层级)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
export PYTHONPATH="$PARENT_DIR:$PYTHONPATH"
cd "$PARENT_DIR"

echo "=========================================="
echo "Macro System 健康检查"
echo "工作目录：$PARENT_DIR"
echo "=========================================="

# 1. 配置校验
echo "[1/4] 配置校验..."
python3 -m macro_system.config.config_validator || echo "⚠️  配置校验未通过"

# 2. 依赖检查
echo -e "\n[2/4] 依赖检查..."
python3 -c "import akshare; print('✓ AkShare:', akshare.__version__)" || echo "⚠️  AkShare 未安装"

# 3. 数据源测试 (快速)
echo -e "\n[3/4] 数据源快速测试..."
timeout 15 python3 -c "
from macro_system.data.providers.akshare_china import fetch_china_macro
data = fetch_china_macro()
if data.get('_error'):
    print('⚠️  AkShare 异常:', data.get('_error'))
else:
    fields = data.get('_quality', {}).get('core_fields', [])
    print(f'✓ AkShare 正常：获取到 {len(fields)} 个核心字段')
" || echo "⚠️  数据源测试超时或失败"

# 4. 缓存状态
echo -e "\n[4/4] 缓存状态..."
python3 -c "from macro_system.utils.cache_manager import get_cache; print(get_cache().get_stats())"

# 5. 可选：Dry Run
if [ "$1" == "--dry-run" ]; then
    echo -e "\n=========================================="
    echo "执行 Dry Run 测试..."
    echo "=========================================="
    python3 -m macro_system.core.orchestrator --dry-run
fi

echo -e "\n=========================================="
echo "✅ 健康检查完成"
echo "=========================================="
