"""
AkShare 中国宏观经济数据接口
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# 核心指标字段
CORE_FIELDS = ["CPI", "PPI", "PMI", "社融", "M2", "失业率"]

def fetch_china_macro(indicator: str = "all") -> Dict[str, Any]:
    """
    获取中国宏观数据
    
    Args:
        indicator: 指标名称，如 "CPI", "PPI", "PMI" 等
    
    Returns:
        数据字典
    """
    logger.info(f"获取中国宏观数据：{indicator}")
    
    # 演示模式：返回模拟数据
    return {
        "status": "simulated",
        "source": "AkShare",
        "data": {
            "CPI": {"value": 102.5, "yoy": 0.025, "date": "2026-04"},
            "PPI": {"value": 98.2, "yoy": -0.018, "date": "2026-04"},
            "PMI": {"value": 50.8, "date": "2026-04"},
            "社融": {"value": "3.5 万亿", "yoy": 0.05, "date": "2026-04"},
            "M2": {"value": "300 万亿", "yoy": 0.08, "date": "2026-04"},
            "失业率": {"value": 5.2, "date": "2026-04"}
        },
        "message": "演示模式：返回模拟数据"
    }
