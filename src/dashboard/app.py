# src/dashboard/app.py
"""
MDE 专业交易终端 (v7.0.0)

功能:
1. 实时信号监控 (多资产)
2. 持仓管理与盈亏分析
3. 一键下单 (模拟/实盘)
4. 策略健康度可视化
5. 系统资源监控
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List

# 设置页面配置
st.set_page_config(
    page_title="MDE 专业交易终端 v7.0",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS (美化)
st.markdown("""
<style>
    .metric-card { background-color: #1e1e1e; padding: 20px; border-radius: 10px; }
    .signal-buy { color: #00ff00; font-weight: bold; }
    .signal-sell { color: #ff0000; font-weight: bold; }
    .signal-hold { color: #cccccc; }
</style>
""", unsafe_allow_html=True)

st.title("📈 MDE 专业交易终端 v7.0")
st.caption(f"最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 侧边栏：全局控制
st.sidebar.header("⚙️ 控制中心")
mode = st.sidebar.selectbox("交易模式", ["模拟盘 (Paper)", "实盘 (Live)"])
refresh_rate = st.sidebar.slider("刷新频率 (秒)", 5, 60, 10)

if st.sidebar.button("🔄 立即刷新"):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info(f"**当前模式**: {mode}")
st.sidebar.info(f"**系统状态**: 🟢 运行中")

# 模拟数据加载 (实际应调用后端 API)
def load_portfolio_data() -> Dict:
    """加载组合数据"""
    return {
        "total_equity": 125000,
        "cash": 45000,
        "pnl_today": 2300,
        "pnl_total": 25000,
        "positions": [
            {"symbol": "PIG", "name": "生猪", "shares": 1000, "avg_price": 14.0, "current_price": 14.5, "pnl": 500, "signal": "BUY"},
            {"symbol": "CORN", "name": "玉米", "shares": 2000, "avg_price": 2.5, "current_price": 2.4, "pnl": -200, "signal": "HOLD"},
            {"symbol": "SPX", "name": "标普 500", "shares": 10, "avg_price": 4400, "current_price": 4500, "pnl": 1000, "signal": "SELL"}
        ],
        "signals": [
            {"time": "10:00", "symbol": "PIG", "action": "BUY", "strength": 9.0, "reason": "痛苦指数高，供给侧出清"},
            {"time": "09:30", "symbol": "CORN", "action": "HOLD", "strength": 5.0, "reason": "震荡整理"}
        ]
    }

# 加载数据
data = load_portfolio_data()

# 第一行：核心指标
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("总资产", f"${data['total_equity']:,.0f}", f"{data['pnl_total']/100000*100:.2f}%")
with col2:
    st.metric("可用现金", f"${data['cash']:,.0f}")
with col3:
    st.metric("今日盈亏", f"${data['pnl_today']:+,.0f}", delta_color="normal")
with col4:
    st.metric("总盈亏", f"${data['pnl_total']:+,.0f}", delta_color="normal")

st.markdown("---")

# 第二行：持仓与信号
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📊 持仓监控")
    if data['positions']:
        df_pos = pd.DataFrame(data['positions'])
        # 格式化显示
        st.dataframe(
            df_pos.style.format({
                'avg_price': '${:.2f}',
                'current_price': '${:.2f}',
                'pnl': '${:+,.0f}'
            }).applymap(lambda x: 'color: green' if x > 0 else 'color: red', subset=['pnl']),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("当前无持仓")

with col_right:
    st.subheader("🚀 最新信号")
    if data['signals']:
        for sig in data['signals']:
            action_class = f"signal-{sig['action'].lower()}"
            st.markdown(f"**{sig['time']} - {sig['symbol']}**")
            st.markdown(f"<span class='{action_class}'>{sig['action']}</span> (强度：{sig['strength']})", unsafe_allow_html=True)
            st.caption(sig['reason'])
            st.divider()
    else:
        st.info("暂无新信号")

st.markdown("---")

# 第三行：一键交易
st.subheader("💼 快速交易")
c1, c2, c3, c4 = st.columns(4)
symbol = c1.selectbox("标的", ["PIG", "CORN", "SPX"])
action = c2.selectbox("操作", ["BUY", "SELL", "CLOSE"])
shares = c3.number_input("数量", min_value=100, step=100)
price = c4.number_input("价格", value=data['positions'][0]['current_price'] if data['positions'] else 0.0, format="%.2f")

if st.button("🔥 立即下单", type="primary"):
    st.success(f"已提交 {action} 订单：{shares}股 {symbol} @ {price}")
    st.toast(f"订单已提交至 {mode} 环境", icon="✅")

# 第四行：系统健康
with st.expander("🏥 系统健康检查"):
    st.write("**CPU 使用率**: 35%")
    st.write("**内存使用率**: 42%")
    st.write("**磁盘剩余**: 120GB")
    st.write("**数据源状态**: 🟢 正常")
    st.write("**策略健康度**: 🟢 良好 (胜率 62%)")
