# src/dashboard/app.py
"""
B. Streamlit 看板
可视化 Agent 思维链、胜率曲线与资金曲线
"""
import streamlit as st
import duckdb
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="MDE 作战指挥室", layout="wide")
st.title("🛡️ MDE v4.0 作战指挥室")

DB_PATH = "../../data/mde.duckdb"
FEATURE_PATH = "../../data/features/latest_state.json"

# 侧边栏
st.sidebar.header("⚙️ 控制")
if st.sidebar.button("🔄 手动校准昨日决策"):
    st.sidebar.success("校准任务已触发 (模拟)")
    # 实际应调用 review_service.calibrate_pending_decisions()

# 1. 加载数据
try:
    conn = duckdb.connect(DB_PATH)
    df = conn.execute("SELECT * FROM decision_logs ORDER BY timestamp DESC").df()
    conn.close()
except Exception as e:
    st.error(f"数据库错误：{e}")
    df = pd.DataFrame()

features = {}
if os.path.exists(FEATURE_PATH):
    try:
        with open(FEATURE_PATH, 'r') as f:
            features = json.load(f)
    except:
        pass

# 2. 顶部指标卡
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("总决策次数", len(df))
with col2:
    if not df.empty:
        completed = df[df['status'] == 'COMPLETED']
        accuracy = completed['is_correct'].mean() * 100 if not completed.empty else 0
        st.metric("历史胜率", f"{accuracy:.1f}%")
    else:
        st.metric("历史胜率", "0%")
with col3:
    st.metric("当前价格", features.get('price', 'N/A'))
with col4:
    st.metric("当前趋势", features.get('trend', 'N/A'))

st.divider()

# 3. 资金曲线
if not df.empty and 'actual_return' in df.columns:
    st.subheader("📈 累计收益曲线")
    df_sorted = df.sort_values('timestamp')
    df_sorted['cumulative_return'] = df_sorted['actual_return'].fillna(0).cumsum()
    st.line_chart(df_sorted.set_index('timestamp')['cumulative_return'])

# 4. 决策历史明细
st.subheader("📜 决策历史明细")
if not df.empty:
    display_df = df.copy()
    display_df['timestamp'] = display_df['timestamp'].astype(str)
    display_df['signal'] = display_df['final_decision'].apply(
        lambda x: '🟢 BUY' if x == 'BUY' else ('🔴 SELL' if x == 'SELL' else '⚪ HOLD')
    )
    
    st.dataframe(
        display_df[['timestamp', 'signal', 'confidence', 'actual_return', 'is_correct', 'status']],
        hide_index=True
    )
else:
    st.info("暂无决策记录")

# 5. 最新 Agent 思维链
if not df.empty:
    st.subheader("🧠 最新 Agent 思维链")
    latest = df.iloc[0]
    try:
        opinions = json.loads(latest['agent_opinions'])
        col_m, col_mac, col_r = st.columns(3)
        with col_m:
            st.markdown(f"**📈 Market:**\n{opinions.get('market', 'N/A')}")
        with col_mac:
            st.markdown(f"**🌍 Macro:**\n{opinions.get('macro', 'N/A')}")
        with col_r:
            st.markdown(f"**🛡️ Risk:**\n{opinions.get('risk', 'N/A')}")
    except:
        st.warning("解析思维链失败")
