# src/dashboard/app.py
"""
MDE 作战指挥室 (v4.3.0 增强版)

功能:
1. 实时特征与信号监控
2. 周期指标仪表盘 (痛苦/疯狂指数)
3. 实盘/模拟盘交易记录
4. 数据源健康状态
5. 系统健康检查
"""

import streamlit as st
import duckdb
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="MDE 作战指挥室 v4.3", layout="wide")
st.title("🛡️ MDE v4.3 作战指挥室")

# 路径配置
DB_PATH = "data/mde.duckdb"
FEATURE_PATH = "data/features/latest_state.json"
SUPPLY_DEMAND_PATH = "data/supply_demand_state.json"
TRADE_LOG_PATH = "logs/trade_logs.json"

# ============ 侧边栏 ============
st.sidebar.header("⚙️ 控制中心")

if st.sidebar.button("🔄 刷新全部数据"):
    st.rerun()

if st.sidebar.button("📊 手动校准昨日决策"):
    from src.services.review_service import ReviewService
    with st.spinner("正在校准..."):
        svc = ReviewService()
        svc.calibrate_pending_decisions()
    st.sidebar.success("校准完成!")

st.sidebar.markdown("---")
st.sidebar.info("**系统状态**: 运行中 ✅")

# ============ 辅助函数 ============
def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

# ============ 1. 核心指标卡 ============
st.header("📊 核心指标")

features = load_json(FEATURE_PATH)
supply_demand = load_json(SUPPLY_DEMAND_PATH)

# 加载决策统计
try:
    conn = duckdb.connect(DB_PATH)
    df = conn.execute("SELECT * FROM decision_logs ORDER BY timestamp DESC").df()
    conn.close()
    total_decisions = len(df)
    if not df.empty:
        completed = df[df['status'] == 'COMPLETED']
        accuracy = completed['is_correct'].mean() * 100 if not completed.empty else 0
    else:
        accuracy = 0
except:
    total_decisions = 0
    accuracy = 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("总决策次数", total_decisions)
with col2:
    st.metric("历史胜率", f"{accuracy:.1f}%")
with col3:
    st.metric("当前价格", features.get('price', 'N/A'))
with col4:
    st.metric("市场趋势", features.get('trend', 'N/A'))

# ============ 2. 周期指标监控 ============
st.header("🔁 周期指标监控")

if supply_demand:
    # 转换为 DataFrame
    if isinstance(supply_demand, list):
        df_sd = pd.DataFrame(supply_demand)
    else:
        df_sd = pd.DataFrame([supply_demand])
    
    if not df_sd.empty:
        latest_sd = df_sd.iloc[-1] if len(df_sd) == 1 else df_sd[df_sd['industry'] == df_sd['industry'].iloc[0]].iloc[-1]
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("痛苦指数")
            pain = latest_sd.get('pain_index', 0)
            if pain > 70:
                st.error(f"🔴 {pain:.1f} (极度痛苦，关注抄底)")
            elif pain > 40:
                st.warning(f"🟡 {pain:.1f} (磨底期)")
            else:
                st.info(f"🟢 {pain:.1f} (正常)")
        
        with col_b:
            st.subheader("疯狂指数")
            mania = latest_sd.get('mania_index', 0)
            if mania > 70:
                st.error(f"🔴 {mania:.1f} (极度疯狂，关注逃顶)")
            elif mania > 40:
                st.warning(f"🟡 {mania:.1f} (扩张期)")
            else:
                st.info(f"🟢 {mania:.1f} (正常)")
else:
    st.info("暂无周期数据，请先运行供需监控器")

# ============ 3. 交易执行监控 ============
st.header("💼 交易执行监控")

trade_logs = load_json(TRADE_LOG_PATH)
if trade_logs:
    df_trades = pd.DataFrame(trade_logs)
    st.dataframe(
        df_trades[['timestamp', 'symbol', 'side', 'shares', 'price', 'status']].tail(10),
        use_container_width=True
    )
else:
    st.info("暂无交易记录")

# ============ 4. 数据源健康状态 ============
st.header("🔗 数据源健康状态")

data_sources = {
    "特征数据": os.path.exists(FEATURE_PATH),
    "供需数据": os.path.exists(SUPPLY_DEMAND_PATH),
    "决策日志": os.path.exists(DB_PATH),
    "交易日志": os.path.exists(TRADE_LOG_PATH)
}

for source, exists in data_sources.items():
    col_icon = "✅" if exists else "❌"
    st.write(f"{col_icon} {source}")

# ============ 5. 系统健康检查 ============
st.header("🏥 系统健康检查")

from src.services.healthcheck import get_health_check
hc = get_health_check()
status = hc.get_status()

st.write(f"**整体状态**: {'✅ ' + status['status'].upper() if status['status'] == 'healthy' else '⚠️ ' + status['status'].upper()}")
st.write(f"**运行时间**: {status['uptime_seconds']:.0f} 秒")
st.write(f"**健康度**: {status['health_percentage']:.0%}")

if status['issues']:
    st.warning("发现以下问题:")
    for issue in status['issues']:
        st.write(f"- {issue}")

# ============ Footer ============
st.markdown("---")
st.caption(f"最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | MDE v4.3.0")
