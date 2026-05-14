#!/bin/bash
# run_full_system.sh
# MDE v4.0 全流程启动脚本

set -e

echo "🚀 启动 MDE v4.0 全流程系统..."
echo "========================================"

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "⚠️  未找到虚拟环境，尝试使用系统 Python (可能报错)"
fi

# 1. 获取实时数据 & 更新特征
echo "1️⃣  获取实时数据并构建特征..."
python src/data/realtime_ingest.py
# 注意：build_features.py 需要适配新的数据结构，这里先简化处理或跳过
# 如果之前没有 build_features.py 的更新版，我们暂时跳过或使用旧版
if [ -f "src/features/build.py" ]; then
    python src/features/build.py
else
    echo "⚠️  未找到特征构建脚本，跳过。"
fi

# 2. 校准昨日决策 (A. 复盘)
echo -e "\n2️⃣  执行复盘校准..."
python src/services/review_service.py

# 3. 运行 Multi-Agent 决策
echo -e "\n3️⃣  运行 Multi-Agent 系统..."
python src/agents/parallel_agent.py

# 4. 启动看板 (B. 可视化)
echo -e "\n4️⃣  启动 Streamlit 看板..."
echo "💡 看板即将启动，请在浏览器访问提示地址 (默认 http://localhost:8501)"
echo "按 Ctrl+C 可停止看板服务"
echo "========================================"

# 启动 Streamlit (非阻塞方式或前台)
# 生产环境建议用 systemd 或 supervisor 管理
streamlit run src/dashboard/app.py --server.headless true --server.address 0.0.0.0

echo "✅ 系统已停止"
