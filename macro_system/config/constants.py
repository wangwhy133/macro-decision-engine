"""
全局常量定义
避免魔法字符串，提高可维护性
"""
from enum import Enum
from typing import Dict, Any

# === 数据源常量 ===
class DataSource(Enum):
    AKSHARE = "akshare"
    FRED = "fred"
    YAHOO = "yahoo"
    WIND = "wind"

# === 数据字段常量 ===
class MacroField(Enum):
    # 中国宏观
    CHINA_CPI = "cpi"
    CHINA_PPI = "ppi"
    CHINA_PMI_MFG = "pmi_mfg"
    CHINA_PMI_NON_MFG = "pmi_non_mfg"
    CHINA_M2_YOY = "m2_yoy"
    CHINA_GDP_YOY = "gdp_yoy"
    CHINA_NEW_CREDIT = "new_credit"
    CHINA_SOCIAL_FINANCING = "social_financing"
    CHINA_LPR_1Y = "lpr_1y"
    CHINA_LPR_5Y = "lpr_5y"
    
    # 美国宏观
    US_CPI = "us_cpi"
    US_CORE_CPI = "us_core_cpi"
    US_UNEMPLOYMENT = "unemployment_rate"
    US_NONFARM = "nonfarm"
    US_GDP = "us_gdp"
    US_VIX = "vix"
    
    # 债券
    US_10Y = "us10y"
    US_2Y = "us2y"
    US_30Y = "us30y"
    US_10Y_2Y_SPREAD = "us10y_2y_spread"

# === 缓存配置 ===
class CacheConfig:
    DEFAULT_TTL_HOURS = 24
    FAILURE_TTL_HOURS = 1
    MACRO_TTL_HOURS = 24  # 宏观数据变化慢
    FUTURES_TTL_HOURS = 1  # 期货变化快
    BOND_TTL_HOURS = 4     # 债券利率变化中等

# === 路径常量 ===
class Paths:
    DEFAULT_DATA_DIR = "/opt/macro-push/data"
    DEFAULT_DB_PATH = f"{DEFAULT_DATA_DIR}/macro.db"
    DEFAULT_CACHE_PATH = f"{DEFAULT_DATA_DIR}/cache.db"

# === 质量阈值 ===
class QualityThresholds:
    MIN_CORE_FIELDS = 3  # 核心字段至少 3 个
    MIN_COVERAGE_RATIO = 0.5  # 覆盖率至少 50%
    MAX_WARNINGS = 2  # 最多允许 2 个警告

# === 辅助函数 ===
def get_all_macro_fields() -> list[str]:
    """获取所有中国宏观字段名"""
    return [
        MacroField.CHINA_CPI.value,
        MacroField.CHINA_PPI.value,
        MacroField.CHINA_PMI_MFG.value,
        MacroField.CHINA_M2_YOY.value,
        MacroField.CHINA_GDP_YOY.value,
    ]

def get_all_us_fields() -> list[str]:
    """获取所有美国宏观字段名"""
    return [
        MacroField.US_CPI.value,
        MacroField.US_UNEMPLOYMENT.value,
        MacroField.US_NONFARM.value,
        MacroField.US_VIX.value,
    ]
