#!/usr/bin/env python3
"""
Macro System Dashboard
基于 Streamlit 的可视化看板
用法: streamlit run macro_system/dashboard.py
"""
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path

# 配置页面
st.set_page_config(
    page_title="Macro System Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入本地模块 (需设置 PYTHONPATH)
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(script_dir))

from macro_system.utils.cache_manager import get_cache
from macro_system.utils.heartbeat import get_status
from macro_system.config.settings import get_settings

# === 侧边栏 ===
st.sidebar.title("📊 Macro System")
st.sidebar.markdown("**生产环境看板**")
st.sidebar.markdown("---")

# 刷新按钮
if st.sidebar.button("🔄 刷新数据"):
    st.rerun()

# 系统状态
st.sidebar.subheader("系统状态")
status = get_status()
status_color = "🟢" if status.get("status") in ["RUNNING", "SUCCESS"] else "🔴"
st.sidebar.markdown(f"{status_color} **{status.get('status', 'UNKNOWN')}**")
st.sidebar.markdown(f"🕒 {status.get('timestamp', 'N/A')}")
if status.get("message"):
    st.sidebar.info(status["message"])

# === 主内容区 ===
st.title("📊 宏观决策系统看板")

# 1. 关键指标卡片
st.subheader("📌 关键指标 (最近一次运行)")

# 尝试读取最新报告
report_path = Path("/opt/macro-push/data/outputs/latest.json")
if report_path.exists():
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        regime = report.get("regime", "N/A")
        risk_level = report.get("risk_level", "N/A")
        data_quality = report.get("data_quality", "N/A")
        run_time = report.get("run_timestamp", "N/A")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("制度 (Regime)", regime)
        with col2:
            st.metric("风险评分", risk_level)
        with col3:
            st.metric("数据质量", data_quality)
        with col4:
            st.metric("运行时间", run_time.split("T")[0] if "T" in str(run_time) else run_time)
            
    except Exception as e:
        st.error(f"读取报告失败：{e}")
        regime = "N/A"
else:
    st.warning("未找到最新报告，请先运行一次主流程。")
    regime = "N/A"

st.markdown("---")

# 2. 历史运行记录
st.subheader("📜 历史运行记录")
db_path = get_settings().db_path
daily_runs_path = Path(db_path).parent / "daily_runs.db" # 假设路径

# 简单展示缓存统计
try:
    cache = get_cache()
    stats = cache.get_stats()
    st.markdown(f"**缓存统计**: 共 **{stats['total_entries']}** 条记录")
    
    if stats['by_source']:
        df_cache = pd.DataFrame(list(stats['by_source'].items()), columns=['数据源', '记录数'])
        st.bar_chart(df_cache.set_index('数据源'))
except Exception as e:
    st.warning(f"无法读取缓存统计：{e}")

st.markdown("---")

# 5. 历史趋势图
st.subheader("📈 历史趋势")
try:
    from macro_system.data.history import get_history_manager
    hist_mgr = get_history_manager()
    history = hist_mgr.get_history(limit=30)
    
    if history:
        df_hist = pd.DataFrame(history)
        df_hist['run_date'] = pd.to_datetime(df_hist['run_date'])
        df_hist = df_hist.sort_values('run_date')
        
        # 风险评分趋势
        if 'risk_level' in df_hist.columns and not df_hist['risk_level'].isna().all():
            st.markdown("**风险评分走势**")
            st.line_chart(df_hist.set_index('run_date')['risk_level'])
        
        # CPI 趋势
        if 'cpi' in df_hist.columns and not df_hist['cpi'].isna().all():
            st.markdown("**CPI 走势**")
            st.line_chart(df_hist.set_index('run_date')['cpi'])
            
    else:
        st.info("暂无历史数据，请先运行几次主流程。")
except Exception as e:
    st.warning(f"无法加载历史趋势：{e}")

st.markdown("---")

# 3. 数据源状态
st.subheader("🔌 数据源状态")
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("**中国宏观 (AkShare)**")
    # 简单测试
    try:
        from macro_system.data.providers.akshare_china import fetch_china_macro
        # 不真正抓取，仅检查模块
        st.success("✅ 模块可用")
    except Exception:
        st.error("❌ 模块加载失败")

with col_b:
    st.markdown("**美国宏观 (FRED)**")
    if os.getenv("FRED_API_KEY"):
        st.success("✅ 已配置 API Key")
    else:
        st.warning("⚠️ 未配置 API Key")

st.markdown("---")

# 4. 原始报告预览
st.subheader("📄 最新报告预览")
if report_path.exists():
    with st.expander("查看原始 JSON 报告"):
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                st.json(json.load(f))
        except Exception as e:
            st.error(f"读取失败：{e}")
else:
    st.info("暂无报告")

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <small>Macro System Dashboard v1.0 | Powered by Streamlit</small>
    </div>
    """,
    unsafe_allow_html=True
)
