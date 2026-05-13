"""
FRED 美国宏观数据抓取 (免费 API Key)
包含严格的数据校验 (Sanity Check)
"""
from typing import Dict, Any, Tuple
import os
import sys
from datetime import datetime

# 数据合理性阈值
SANITY_BOUNDS = {
    "cpi": (50.0, 350.0),       # CPI 指数值 (非同比)
    "core_cpi": (50.0, 350.0),
    "unemployment_rate": (0.0, 25.0),  # 失业率 %
    "gdp": (10000.0, 300000.0),  # GDP 十亿美元
    "vix": (5.0, 100.0),        # VIX 指数
    "ism_mfg": (20.0, 80.0),    # ISM 制造业 PMI
}

def _sanity_check(key: str, value: Any) -> Tuple[bool, str]:
    if value is None:
        return True, "None"
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

def fetch_us_macro() -> Dict[str, Any]:
    """
    抓取美国宏观数据，包含严格校验
    """
    timestamp = datetime.now().isoformat()
    base_result = {
        "cpi": None, "core_cpi": None, "pce": None,
        "nonfarm": None, "unemployment_rate": None, "job_openings": None,
        "gdp": None, "ism_mfg": None, "ism_services": None, "vix": None,
        "_source": "fred", "_timestamp": timestamp,
        "_quality": {"coverage": 0, "core_fields": [], "freshness": "unknown", "warnings": []}
    }
    
    api_key = os.getenv("FRED_API_KEY", "")
    if not api_key:
        # 尝试从配置文件读取
        config_path = os.path.expanduser("~/.macro_config.json")
        if os.path.exists(config_path):
            try:
                import json
                with open(config_path) as f:
                    cfg = json.load(f)
                    api_key = cfg.get("fred_api_key", "")
            except:
                pass
    
    if not api_key:
        base_result["_error"] = "FRED_API_KEY 未配置"
        base_result["_quality"]["warnings"].append("FRED API Key 缺失")
        return base_result
    
    try:
        from fredapi import Fred
        fred = Fred(api_key=api_key)
        
        # 1. CPI
        try:
            cpi = fred.get_series("CPIAUCNS")
            if len(cpi) > 0:
                val = cpi.iloc[-1]
                ok, msg = _sanity_check("cpi", val)
                if ok:
                    base_result["cpi"] = round(val, 2)
                    base_result["_quality"]["core_fields"].append("cpi")
                else:
                    base_result["_quality"]["warnings"].append(f"CPI 异常：{msg}")
        except Exception as e:
            base_result["_quality"]["warnings"].append(f"CPI 抓取失败：{str(e)[:50]}")
        
        # 2. Core CPI
        try:
            core = fred.get_series("CORECPI")
            if len(core) > 0:
                val = core.iloc[-1]
                ok, msg = _sanity_check("core_cpi", val)
                if ok:
                    base_result["core_cpi"] = round(val, 2)
                    base_result["_quality"]["core_fields"].append("core_cpi")
        except Exception as e:
            pass
        
        # 3. 失业率
        try:
            unemp = fred.get_series("UNRATE")
            if len(unemp) > 0:
                val = unemp.iloc[-1]
                ok, msg = _sanity_check("unemployment_rate", val)
                if ok:
                    base_result["unemployment_rate"] = round(val, 2)
                    base_result["_quality"]["core_fields"].append("unemployment_rate")
        except Exception as e:
            pass
        
        # 4. GDP
        try:
            gdp = fred.get_series("GDP")
            if len(gdp) > 0:
                val = gdp.iloc[-1]
                ok, msg = _sanity_check("gdp", val)
                if ok:
                    base_result["gdp"] = round(val, 2)
                    base_result["_quality"]["core_fields"].append("gdp")
        except Exception as e:
            pass
        
        # 5. ISM 制造业
        try:
            ism = fred.get_series("MANISM")
            if len(ism) > 0:
                val = ism.iloc[-1]
                ok, msg = _sanity_check("ism_mfg", val)
                if ok:
                    base_result["ism_mfg"] = round(val, 2)
                    base_result["_quality"]["core_fields"].append("ism_mfg")
        except Exception as e:
            pass
        
        # 6. VIX
        try:
            vix = fred.get_series("VIXCLS")
            if len(vix) > 0:
                val = vix.iloc[-1]
                ok, msg = _sanity_check("vix", val)
                if ok:
                    base_result["vix"] = round(val, 2)
                    base_result["_quality"]["core_fields"].append("vix")
        except Exception as e:
            pass
        
        # 统计
        core_count = len(base_result["_quality"]["core_fields"])
        base_result["_quality"]["coverage"] = f"{core_count}/6"
        base_result["_quality"]["freshness"] = "fresh" if core_count >= 3 else "stale"
        
        return base_result
        
    except ImportError:
        return {"_error": "fredapi_not_installed", "_timestamp": timestamp}
    except Exception as e:
        return {"_error": f"FRED 异常：{str(e)[:100]}", "_timestamp": timestamp}

if __name__ == "__main__":
    import json
    print(json.dumps(fetch_us_macro(), indent=2, ensure_ascii=False))
