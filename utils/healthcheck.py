"""系统健康检查工具"""
import os
import sys
import json
from typing import Dict, Any, List
from datetime import datetime

def check_python_env() -> Dict[str, Any]:
    """检查 Python 环境"""
    result = {"status": "ok", "issues": []}
    
    # Python 版本
    import sys
    result["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # 关键依赖
    required = ["akshare", "pandas", "sqlite3"]
    missing = []
    for pkg in required:
        try:
            if pkg == "sqlite3":
                __import__(pkg)
            else:
                __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        result["status"] = "warning"
        result["issues"].append(f"缺少依赖：{', '.join(missing)}")
    
    return result

def check_data_sources() -> Dict[str, Any]:
    """检查数据源连通性"""
    result = {"status": "ok", "sources": {}}
    
    # AkShare
    try:
        import akshare as ak
        # 快速测试（抓取 CPI，应 < 5 秒）
        start = datetime.now()
        df = ak.macro_china_cpi()
        latency = (datetime.now() - start).total_seconds()
        result["sources"]["akshare"] = {
            "status": "ok" if df is not None else "error",
            "latency_ms": int(latency * 1000)
        }
    except Exception as e:
        result["sources"]["akshare"] = {"status": "error", "message": str(e)}
        result["status"] = "warning"
    
    # FRED
    api_key = os.getenv("FRED_API_KEY", "")
    if api_key:
        try:
            from fredapi import Fred
            fred = Fred(api_key=api_key)
            start = datetime.now()
            _ = fred.get_series("DGS10")
            latency = (datetime.now() - start).total_seconds()
            result["sources"]["fred"] = {"status": "ok", "latency_ms": int(latency * 1000)}
        except Exception as e:
            result["sources"]["fred"] = {"status": "error", "message": str(e)}
    else:
        result["sources"]["fred"] = {"status": "skipped", "message": "API Key 未配置"}
    
    return result

def check_database(db_path: str = "/opt/macro-push/data/macro.db") -> Dict[str, Any]:
    """检查数据库状态"""
    result = {"status": "ok"}
    
    if not os.path.exists(db_path):
        result["status"] = "warning"
        result["message"] = f"数据库不存在：{db_path}"
        return result
    
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查关键表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        result["tables"] = tables
        
        # 检查最近运行记录
        if "daily_runs" in tables:
            cursor.execute("SELECT COUNT(*) FROM daily_runs")
            run_count = cursor.fetchone()[0]
            result["daily_runs_count"] = run_count
        
        conn.close()
        result["db_size_kb"] = int(os.path.getsize(db_path) / 1024)
        
    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
    
    return result

def check_config() -> Dict[str, Any]:
    """检查配置文件"""
    result = {"status": "ok", "issues": []}
    
    # 检查环境变量
    env_vars = ["MACRO_DB_PATH"]
    missing = []
    for var in env_vars:
        if var not in os.environ:
            missing.append(var)
    
    if missing:
        result["status"] = "warning"
        result["issues"].append(f"环境变量缺失：{', '.join(missing)}")
    
    # 检查配置文件
    config_paths = [
        "/root/.macro_config.json",
        os.path.expanduser("~/.config/macro/config.json"),
        "config.yaml"
    ]
    
    found = []
    for path in config_paths:
        if os.path.exists(path):
            found.append(path)
    
    if found:
        result["config_files"] = found
    else:
        result["status"] = "info"
        result["issues"].append("未找到配置文件（可选）")
    
    return result

def run_healthcheck() -> Dict[str, Any]:
    """运行完整健康检查"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "ok",
        "checks": {}
    }
    
    # Python 环境
    report["checks"]["python_env"] = check_python_env()
    
    # 数据源
    report["checks"]["data_sources"] = check_data_sources()
    
    # 数据库
    report["checks"]["database"] = check_database()
    
    # 配置
    report["checks"]["config"] = check_config()
    
    # 汇总状态
    for check_name, check_result in report["checks"].items():
        if check_result.get("status") in ["error", "warning"]:
            report["overall_status"] = "warning"
            break
        if check_result.get("status") == "error":
            report["overall_status"] = "error"
            break
    
    return report

if __name__ == "__main__":
    report = run_healthcheck()
    print(json.dumps(report, indent=2, ensure_ascii=False))
