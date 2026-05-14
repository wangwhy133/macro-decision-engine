# src/features/build.py
"""
构建 Feature Store (生产级增强版)
策略：
1. 严格缓存优先 (缓存有效期 24 小时)
2. 网络请求带指数退避重试 (应对限流)
3. 失败降级模拟数据
"""
import duckdb
import pandas as pd
import pandas_ta as ta
import json
import os
from datetime import datetime, timedelta
import yfinance as yf
import time
import random

# 引入新的通用加载器
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.universal_loader import get_complete_data

DB_PATH = "data/mde.duckdb"
FEATURES_DIR = "data/features"
# 不再需要 CACHE_FILE 常量，由 universal_loader 内部管理

def build_features(symbol: str = "SPY"):
    print("🏗️ 构建 Feature Store...")
    
    # 使用新的通用加载器 (自动处理增量更新和多源降级)
    df = get_complete_data(symbol)
    
    if df.empty:
        print("❌ 无法获取任何数据")
        return

    # 计算技术指标
    df['rsi_14'] = ta.rsi(df['Close'], length=14)
    try:
        macd_df = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        df['macd'] = macd_df['MACD_12_26_9']
    except Exception as e:
        print(f"⚠️ MACD 计算失败：{e}")
        df['macd'] = 0.0
        
    df['volatility'] = df['Close'].rolling(window=20).std() / df['Close'].rolling(window=20).mean()
    df['ma_50'] = df['Close'].rolling(window=50).mean()
    
    # 处理 NaN
    df = df.bfill().ffill()

    # 市场状态
    latest = df.iloc[-1]
    trend = 'bullish' if latest['Close'] > latest['ma_50'] else 'bearish'
    regime = 'risk_on' if latest['rsi_14'] < 70 else 'overbought'

    # 保存最新状态 (JSON)
    feature_snapshot = {
        "timestamp": str(latest.name),
        "symbol": symbol,
        "price": round(float(latest['Close']), 2),
        "rsi": round(float(latest['rsi_14']), 2),
        "macd": round(float(latest['macd']), 2),
        "volatility": round(float(latest['volatility']), 4),
        "trend": trend,
        "market_regime": regime
    }
    
    os.makedirs(FEATURES_DIR, exist_ok=True)
    with open(f"{FEATURES_DIR}/latest_state.json", 'w') as f:
        json.dump(feature_snapshot, f, indent=2)
    
    print(f"✅ Feature Store 已更新：{feature_snapshot}")

if __name__ == "__main__":
    build_features("SPY")