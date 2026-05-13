"""
心跳与状态管理
记录系统运行状态，便于监控
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, Any

STATUS_FILE = "/opt/macro-push/data/.status.json"

def update_status(status: str, message: str = "", extra: Dict[str, Any] = None):
    """
    更新运行状态
    :param status: RUNNING, SUCCESS, FAILED, DEAD
    :param message: 状态描述
    """
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    
    data = {
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "unix_time": time.time(),
        "pid": os.getpid(),
        **(extra or {})
    }
    
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_status() -> Dict[str, Any]:
    """获取当前状态"""
    if not os.path.exists(STATUS_FILE):
        return {"status": "UNKNOWN", "message": "无状态文件"}
    
    try:
        with open(STATUS_FILE) as f:
            data = json.load(f)
        
        # 检查是否超时 (假设 2 小时无更新视为 DEAD)
        if time.time() - data.get("unix_time", 0) > 7200:
            data["status"] = "DEAD"
            data["message"] = "状态超时，可能已挂死"
        
        return data
    except:
        return {"status": "UNKNOWN", "message": "读取状态失败"}

def is_alive(timeout_seconds: int = 7200) -> bool:
    """检查系统是否存活"""
    status = get_status()
    if status.get("status") in ["RUNNING", "SUCCESS"]:
        return True
    return False

if __name__ == "__main__":
    # 测试
    update_status("RUNNING", "系统运行中")
    print("当前状态:", get_status())
