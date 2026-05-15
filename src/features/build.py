# src/features/build.py
"""
构建 Feature Store (生产级增强版)

策略:
1. 严格缓存优先 (缓存有效期 24 小时)
2. 网络请求带指数退避重试 (应对限流)
3. 失败降级模拟数据
4. 风控集成：自动标记模拟数据
5. 并发控制：文件锁防止数据损坏
6. 数据验证：确保数据质量
"""

import duckdb
import pandas as pd
import pandas_ta as ta
import json
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, Any

# 导入风控和日志
from src.risk.risk_control import get_risk_control, init_risk_control, TradeAction
from src.utils.logger import setup_logger
from src.utils.filelock import file_lock
from src.data.universal_loader import get_complete_data, DATA_SOURCE_SIMULATION
from src.data.validation import validate_data, validate_features, clean_data

logger = setup_logger("MDE.Features")

DB_PATH = "data/mde.duckdb"
FEATURES_DIR = "data/features"


def build_features(symbol: str = "SPY") -> Dict[str, Any]:
    """
    构建特征并返回
    
    Returns:
        特征字典 (包含风控标记)
    """
    logger.info("🏗️ 构建 Feature Store...")
    
    # 初始化风控
    rc = init_risk_control()
    
    # 使用新的通用加载器 (自动处理增量更新和多源降级)
    df = get_complete_data(symbol)
    
    if df.empty:
        logger.error("❌ 无法获取任何数据")
        return {}
    
    # 数据验证
    is_valid, issues = validate_data(df, symbol)
    if not is_valid:
        logger.warning(f"⚠️ 数据验证发现问题：{issues}")
        # 尝试清洗数据
        df = clean_data(df)
        # 再次验证
        is_valid, issues = validate_data(df, symbol)
        if not is_valid:
            logger.error(f"❌ 数据清洗后仍有问题：{issues}")
    
    # 计算技术指标
    try:
        df['rsi_14'] = ta.rsi(df['Close'], length=14)
    except Exception as e:
        logger.warning(f"⚠️ RSI 计算失败：{e}")
        df['rsi_14'] = 50.0  # 中性值
    
    try:
        macd_df = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        df['macd'] = macd_df['MACD_12_26_9']
    except Exception as e:
        logger.warning(f"⚠️ MACD 计算失败：{e}")
        df['macd'] = 0.0
    
    df['volatility'] = df['Close'].rolling(window=20).std() / df['Close'].rolling(window=20).mean()
    df['ma_50'] = df['Close'].rolling(window=50).mean()
    
    # 处理 NaN
    df = df.bfill().ffill()
    
    # 获取最新数据
    latest = df.iloc[-1]
    
    # 判断市场状态
    trend = 'bullish' if latest['Close'] > latest['ma_50'] else 'bearish'
    regime = 'risk_on' if latest['rsi_14'] < 70 else 'overbought'
    
    # 检查数据源 (风控关键步骤)
    data_source = DATA_SOURCE_SIMULATION if rc.simulation_signatures else "real"
    signature = rc.generate_data_signature(df)
    is_simulated = signature in rc.simulation_signatures
    
    # 风控检查
    action, reason = rc.check_trade_permission(
        data_source=data_source,
        features={"is_simulated": is_simulated},
        decision={},
        data_signature=signature
    )
    
    if action == TradeAction.BLOCK:
        logger.warning(f"🚨 风控阻断：{reason}")
    
    # 保存最新状态 (JSON) - 包含风控标记
    feature_snapshot = {
        "timestamp": str(latest.name),
        "symbol": symbol,
        "price": round(float(latest['Close']), 2),
        "rsi": round(float(latest['rsi_14']), 2),
        "macd": round(float(latest['macd']), 4),
        "volatility": round(float(latest['volatility']), 4),
        "trend": trend,
        "market_regime": regime,
        # 风控标记 (关键!)
        "is_simulated": is_simulated,
        "is_safe_to_trade": action == TradeAction.ALLOW,
        "data_source": data_source,
        "data_signature": signature[:16] + "..." if signature else None,
        "risk_control_status": action.value,
        "risk_control_reason": reason
    }
    
    os.makedirs(FEATURES_DIR, exist_ok=True)
    
    # 使用文件锁写入，防止并发冲突
    feature_file = f"{FEATURES_DIR}/latest_state.json"
    with file_lock(feature_file, timeout=10):
        with open(feature_file, 'w', encoding='utf-8') as f:
            json.dump(feature_snapshot, f, indent=2)
    
    if is_simulated:
        logger.warning(f"⚠️ 特征数据标记为 SIMULATED，交易已禁用")
    else:
        logger.info(f"✅ Feature Store 已更新：{feature_snapshot}")
    
    return feature_snapshot


if __name__ == "__main__":
    # 测试特征构建
    import logging
    logging.basicConfig(level=logging.INFO)
    
    features = build_features("SPY")
    print(f"\n📊 特征数据：{json.dumps(features, indent=2)}")
