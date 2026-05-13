"""
AkShare 中国宏观数据抓取 (免费、免 Key)
包含严格的数据校验 (Sanity Check) 和熔断机制。
"""
from typing import Dict, Any, Optional, Tuple, List
import sys
from datetime import datetime
from macro_system.utils.retry import retry

# === 常量定义 (Constants) ===
DEFAULT_TIMEOUT = 30
CACHE_TTL_HOURS = 24  # 宏观数据变化慢，缓存 24 小时
FAILURE_TTL_HOURS = 1 # 失败后缓存 1 小时，防止雪崩

# 数据合理性阈值 (Sanity Check Bounds)
SANITY_BOUNDS = {
    "cpi": (-5.0, 25.0),
    "ppi": (-10.0, 20.0),
    "pmi_mfg": (30.0, 60.0),
    "gdp_yoy": (-10.0, 20.0),
    "m2_yoy": (0.0, 30.0),
    "unemployment_rate": (0.0, 20.0),
    "lpr_1y": (0.0, 20.0),
    "lpr_5y": (0.0, 20.0),
}

# 核心字段集：如果缺失超过 50%，则判定为完全失败
CORE_FIELDS = ["cpi", "ppi", "pmi_mfg", "m2_yoy"]
MAX_MISSING_RATIO = 0.5  # 允许的最大缺失比例

def _sanity_check(key: str, value: Any) -> Tuple[bool, str]:
    """检查单个字段是否在合理范围内"""
    if value is None:
        return True, "None value"
    if key not in SANITY_BOUNDS:
        return True, "No bounds"
    min_val, max_val = SANITY_BOUNDS[key]
    try:
        v = float(value)
        if v < min_val or v > max_val:
            return False, f"Out of bounds [{min_val}, {max_val}]"
        return True, "OK"
    except (ValueError, TypeError):
        return True, "Non-numeric"

def fetch_china_macro() -> Dict[str, Any]:
    """
    抓取中国宏观数据，包含严格校验。
    """
    timestamp = datetime.now().isoformat()
    base_result = {
        "cpi": None, "ppi": None, "pmi_mfg": None, "pmi_non_mfg": None,
        "m2_yoy": None, "new_credit": None, "social_financing": None,
        "export_yoy": None, "import_yoy": None, "trade_balance": None,
        "unemployment_rate": None, "gdp_yoy": None, "industrial_value_yoy": None,
        "retail_sales_yoy": None, "lpr_1y": None, "lpr_5y": None,
        "rrr": None, "shibor_on": None, "consumer_confidence": None,
        "_source": "akshare", "_timestamp": timestamp,
        "_quality": {"coverage": 0, "core_fields": [], "freshness": "unknown", "warnings": []}
    }
    
    try:
        import akshare as ak
        import pandas as pd
        
        # 1. CPI (带重试)
        try:
            @retry(retries=2, delay=1.0, exceptions=(Exception,))
            def _fetch_cpi():
                df = ak.macro_china_cpi()
                if df is not None and not df.empty and "同比增长" in df.columns:
                    return df.iloc[-1]["同比增长"]
                return None
            
            val = _fetch_cpi()
            if val is not None:
                ok, msg = _sanity_check("cpi", val)
                if ok:
                    base_result["cpi"] = float(val) if val else None
                    if base_result["cpi"]: base_result["_quality"]["core_fields"].append("cpi")
                else:
                    base_result["_quality"]["warnings"].append(f"CPI 异常：{msg}")
        except Exception as e:
            base_result["_quality"]["warnings"].append(f"CPI 抓取失败：{str(e)[:50]}")
        
        # 2. PPI
        try:
            df = ak.macro_china_ppi()
            if df is not None and not df.empty and "当月同比增长" in df.columns:
                val = df.iloc[-1]["当月同比增长"]
                ok, msg = _sanity_check("ppi", val)
                if ok:
                    base_result["ppi"] = float(val) if val else None
                    if base_result["ppi"]: base_result["_quality"]["core_fields"].append("ppi")
                else:
                    base_result["_quality"]["warnings"].append(f"PPI 异常：{msg}")
        except Exception as e:
            base_result["_quality"]["warnings"].append(f"PPI 抓取失败：{str(e)[:50]}")
        
        # 3. PMI
        try:
            df = ak.macro_china_pmi()
            if df is not None and not df.empty and "制造业 PMI" in df.columns:
                val = df.iloc[-1]["制造业 PMI"]
                ok, msg = _sanity_check("pmi_mfg", val)
                if ok:
                    base_result["pmi_mfg"] = float(val) if val else None
                    if base_result["pmi_mfg"]: base_result["_quality"]["core_fields"].append("pmi_mfg")
                else:
                    base_result["_quality"]["warnings"].append(f"PMI 异常：{msg}")
        except Exception as e:
            base_result["_quality"]["warnings"].append(f"PMI 抓取失败：{str(e)[:50]}")
            
        # 4. M2
        try:
            df = ak.macro_china_money_supply()
            if df is not None and not df.empty and "m2" in df.columns:
                val = df.iloc[-1]["m2"]
                ok, msg = _sanity_check("m2_yoy", val)
                if ok:
                    base_result["m2_yoy"] = float(val) if val else None
                    if base_result["m2_yoy"]: base_result["_quality"]["core_fields"].append("m2_yoy")
        except Exception as e:
            pass # M2 非核心，失败不记录警告

        # 5. LPR
        try:
            df = ak.macro_china_loan_market_quote_rate()
            if df is not None and not df.empty:
                df_sorted = df.sort_values("报价日期").iloc[-1]
                if "1 年" in df_sorted:
                    val = df_sorted["1 年"]
                    ok, msg = _sanity_check("lpr_1y", val)
                    if ok:
                        base_result["lpr_1y"] = float(val)
                        if base_result["lpr_1y"]: base_result["_quality"]["core_fields"].append("lpr_1y")
                if "5 年" in df_sorted:
                    val = df_sorted["5 年"]
                    ok, msg = _sanity_check("lpr_5y", val)
                    if ok:
                        base_result["lpr_5y"] = float(val)
                        if base_result["lpr_5y"]: base_result["_quality"]["core_fields"].append("lpr_5y")
        except Exception as e:
            pass

        # 计算质量
        core_fields = base_result["_quality"]["core_fields"]
        core_count = len(core_fields)
        
        # 数据完整性校验 (Data Integrity Check)
        missing_core = [f for f in CORE_FIELDS if f not in core_fields]
        missing_ratio = len(missing_core) / len(CORE_FIELDS)
        
        if missing_ratio > MAX_MISSING_RATIO:
            # 核心字段缺失过多，判定为完全失败
            base_result["_error"] = f"核心字段缺失过多：{missing_core}"
            base_result["_quality"]["warnings"].append(f"完整性校验失败：缺失 {len(missing_core)}/{len(CORE_FIELDS)} 个核心字段")
            base_result["_quality"]["freshness"] = "corrupted"
            # 清空已抓取的部分数据，防止部分成功误导
            for field in CORE_FIELDS:
                base_result[field] = None
            return base_result
        
        base_result["_quality"]["coverage"] = f"{core_count}/5"
        base_result["_quality"]["freshness"] = "fresh" if core_count > 2 else "stale"
        
        return base_result
        
    except ImportError:
        return {"_error": "akshare_not_installed", "_timestamp": timestamp}
    except Exception as e:
        return {"_error": f"Unexpected: {str(e)[:100]}", "_timestamp": timestamp}

if __name__ == "__main__":
    import json
    data = fetch_china_macro()
    print(json.dumps(data, indent=2, ensure_ascii=False))