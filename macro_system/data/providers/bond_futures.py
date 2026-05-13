"""美债收益率和外盘期货数据抓取（免费源）"""
from typing import Dict, Any, List
import sys

def fetch_us_bond() -> Dict[str, Any]:
    """
    抓取美债收益率（10Y, 2Y, 30Y, 期限利差）
    使用 FRED API 或 Yahoo Finance
    """
    from datetime import datetime
    
    result = {
        "us10y": None, "us2y": None, "us30y": None,
        "us10y_2y_spread": None, "us30y_10y_spread": None,
        "_source": "mixed", "_timestamp": datetime.now().isoformat(),
        "_quality": {"coverage": 0, "core_fields": [], "freshness": "unknown"}
    }
    
    # 尝试 FRED
    api_key = os.getenv("FRED_API_KEY", "")
    if api_key:
        try:
            from fredapi import Fred
            fred = Fred(api_key=api_key)
            
            # 10Y
            try:
                dgs10 = fred.get_series("DGS10")
                if len(dgs10) > 0:
                    result["us10y"] = round(dgs10.iloc[-1], 3)
                    result["_quality"]["core_fields"].append("us10y")
            except: pass
            
            # 2Y
            try:
                dgs2 = fred.get_series("DGS2")
                if len(dgs2) > 0:
                    result["us2y"] = round(dgs2.iloc[-1], 3)
                    result["_quality"]["core_fields"].append("us2y")
            except: pass
            
            # 30Y
            try:
                dgs30 = fred.get_series("DGS30")
                if len(dgs30) > 0:
                    result["us30y"] = round(dgs30.iloc[-1], 3)
                    result["_quality"]["core_fields"].append("us30y")
            except: pass
            
            # 计算利差
            if result["us10y"] and result["us2y"]:
                result["us10y_2y_spread"] = round(result["us10y"] - result["us2y"], 3)
            if result["us30y"] and result["us10y"]:
                result["us30y_10y_spread"] = round(result["us30y"] - result["us10y"], 3)
            
        except ImportError:
            pass
    
    core_count = len(result["_quality"]["core_fields"])
    result["_quality"]["coverage"] = f"{core_count}/5"
    result["_quality"]["freshness"] = "fresh" if core_count >= 2 else "stale"
    
    return result

def fetch_futures() -> List[Dict[str, Any]]:
    """
    抓取外盘期货（原油、黄金、铜等）
    使用 AkShare 免费接口
    """
    from datetime import datetime
    
    futures_list = []
    
    try:
        import akshare as ak
        
        # 黄金 (COMEX)
        try:
            df = ak.futures_zh_spot(symbol="GC")
            if df is not None and not df.empty and "最新价" in df.columns:
                futures_list.append({
                    "symbol": "GC", "name": "黄金",
                    "price": float(df.iloc[-1]["最新价"]),
                    "change_pct": float(df.iloc[-1]["涨跌幅"]) if "涨跌幅" in df.columns else None
                })
        except: pass
        
        # 原油 (WTI)
        try:
            df = ak.futures_zh_spot(symbol="CL")
            if df is not None and not df.empty and "最新价" in df.columns:
                futures_list.append({
                    "symbol": "CL", "name": "原油",
                    "price": float(df.iloc[-1]["最新价"]),
                    "change_pct": float(df.iloc[-1]["涨跌幅"]) if "涨跌幅" in df.columns else None
                })
        except: pass
        
        # 铜
        try:
            df = ak.futures_zh_spot(symbol="HG")
            if df is not None and not df.empty and "最新价" in df.columns:
                futures_list.append({
                    "symbol": "HG", "name": "铜",
                    "price": float(df.iloc[-1]["最新价"]),
                    "change_pct": float(df.iloc[-1]["涨跌幅"]) if "涨跌幅" in df.columns else None
                })
        except: pass
        
    except ImportError:
        pass
    
    return futures_list

if __name__ == "__main__":
    import json
    import os
    print("美债:", json.dumps(fetch_us_bond(), indent=2, ensure_ascii=False))
    print("期货:", json.dumps(fetch_futures(), indent=2, ensure_ascii=False))
