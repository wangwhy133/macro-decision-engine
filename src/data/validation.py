# src/data/validation.py
"""
数据验证模块 (生产级)

功能:
1. 数据完整性检查
2. 异常值检测
3. 时间序列连续性验证
4. 技术指标合理性检查

使用示例:
    from src.data.validation import validate_data
    
    df = load_data()
    is_valid, issues = validate_data(df)
    
    if not is_valid:
        print(f"数据问题：{issues}")
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any
from src.utils.logger import setup_logger

logger = setup_logger("MDE.DataValidation")


def validate_data(df: pd.DataFrame, symbol: str = "SPY") -> Tuple[bool, List[str]]:
    """
    数据验证主函数
    
    Args:
        df: 数据 DataFrame
        symbol: 交易标的
    
    Returns:
        (是否有效，问题列表)
    """
    issues = []
    
    # 1. 基础检查
    if df.empty:
        issues.append("数据为空")
        return False, issues
    
    # 2. 必需列检查
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        issues.append(f"缺少必需列：{missing_cols}")
        return False, issues
    
    # 3. 空值检查
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        null_info = null_counts[null_counts > 0].to_dict()
        issues.append(f"存在空值：{null_info}")
    
    # 4. 价格有效性检查
    price_cols = ['Open', 'High', 'Low', 'Close']
    for col in price_cols:
        if col in df.columns:
            # 检查非正值
            if (df[col] <= 0).any():
                invalid_count = (df[col] <= 0).sum()
                issues.append(f"{col} 列存在 {invalid_count} 个非正值")
            
            # 检查异常值 (超过 3 个标准差)
            mean = df[col].mean()
            std = df[col].std()
            outliers = df[(df[col] < mean - 3*std) | (df[col] > mean + 3*std)]
            if len(outliers) > 0:
                issues.append(f"{col} 列存在 {len(outliers)} 个异常值")
    
    # 5. 价格逻辑检查
    if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
        # High 应该 >= Low
        if (df['High'] < df['Low']).any():
            issues.append("存在最高价低于最低价的数据")
        
        # High 应该 >= Open 和 Close
        if (df['High'] < df[['Open', 'Close']].max(axis=1)).any():
            issues.append("存在最高价低于开盘价或收盘价的数据")
        
        # Low 应该 <= Open 和 Close
        if (df['Low'] > df[['Open', 'Close']].min(axis=1)).any():
            issues.append("存在最低价高于开盘价或收盘价的数据")
    
    # 6. 成交量检查
    if 'Volume' in df.columns:
        if (df['Volume'] < 0).any():
            issues.append("存在负成交量")
        
        # 检查异常成交量
        vol_mean = df['Volume'].mean()
        vol_std = df['Volume'].std()
        vol_outliers = df[df['Volume'] > vol_mean + 5*vol_std]
        if len(vol_outliers) > 0:
            issues.append(f"存在 {len(vol_outliers)} 个异常成交量")
    
    # 7. 时间序列连续性检查
    if isinstance(df.index, pd.DatetimeIndex):
        if not df.index.is_monotonic_increasing:
            issues.append("时间序列非单调递增")
        
        # 检查时间间隔
        if len(df) > 1:
            time_diffs = df.index.to_series().diff()
            median_diff = time_diffs.median()
            large_gaps = time_diffs[time_diffs > median_diff * 2]
            if len(large_gaps) > 0:
                issues.append(f"存在 {len(large_gaps)} 个时间间隔异常")
    
    # 8. 数据量检查
    if len(df) < 30:
        issues.append(f"数据量过少 ({len(df)}条)，可能影响技术指标计算")
    
    is_valid = len(issues) == 0
    
    if not is_valid:
        logger.warning(f"数据验证失败 ({symbol}): {issues}")
    else:
        logger.info(f"数据验证通过 ({symbol})")
    
    return is_valid, issues


def validate_features(features: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    特征验证
    
    Args:
        features: 特征字典
    
    Returns:
        (是否有效，问题列表)
    """
    issues = []
    
    # 检查必需字段
    required_fields = ['price', 'rsi', 'macd', 'volatility', 'trend']
    missing_fields = [f for f in required_fields if f not in features]
    
    if missing_fields:
        issues.append(f"缺少必需特征：{missing_fields}")
        return False, issues
    
    # 检查 RSI 范围 (0-100)
    rsi = features.get('rsi', 0)
    if rsi < 0 or rsi > 100:
        issues.append(f"RSI 超出范围：{rsi}")
    
    # 检查价格有效性
    if features.get('price', 0) <= 0:
        issues.append("价格为非正值")
    
    # 检查波动率
    vol = features.get('volatility', 0)
    if vol < 0:
        issues.append("波动率为负值")
    
    is_valid = len(issues) == 0
    
    if not is_valid:
        logger.warning(f"特征验证失败：{issues}")
    
    return is_valid, issues


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    数据清洗
    
    Args:
        df: 原始数据
    
    Returns:
        清洗后的数据
    """
    cleaned = df.copy()
    
    # 删除完全空的行
    cleaned = cleaned.dropna(how='all')
    
    # 填充数值型空值 (向前填充)
    numeric_cols = cleaned.select_dtypes(include=[np.number]).columns
    cleaned[numeric_cols] = cleaned[numeric_cols].ffill()
    
    # 如果仍有空值，用 0 填充
    cleaned = cleaned.fillna(0)
    
    # 删除异常价格行
    for col in ['Open', 'High', 'Low', 'Close']:
        if col in cleaned.columns:
            cleaned = cleaned[cleaned[col] > 0]
    
    logger.info(f"数据清洗完成：{len(df)} -> {len(cleaned)} 条")
    
    return cleaned


if __name__ == "__main__":
    # 测试数据验证
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 创建测试数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    test_data = pd.DataFrame({
        'Open': np.random.rand(100) * 100 + 400,
        'High': np.random.rand(100) * 100 + 400,
        'Low': np.random.rand(100) * 100 + 400,
        'Close': np.random.rand(100) * 100 + 400,
        'Volume': np.random.randint(100000, 200000, 100)
    }, index=dates)
    
    # 验证
    is_valid, issues = validate_data(test_data, "TEST")
    print(f"验证结果：{'通过' if is_valid else '失败'}")
    if not is_valid:
        print(f"问题：{issues}")
