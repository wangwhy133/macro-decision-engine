"""
JSON 工具类
解决 numpy 类型、datetime 等不可序列化问题
"""
import json
import datetime
import numpy as np
from typing import Any

class FlexibleEncoder(json.JSONEncoder):
    """
    宽容的 JSON 编码器
    自动处理 numpy 类型、datetime 等
    """
    def default(self, obj: Any) -> Any:
        # Numpy 类型
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        
        # 时间类型
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        
        # Pandas (可选，防止依赖)
        try:
            import pandas as pd
            if isinstance(obj, pd.Timestamp):
                return obj.isoformat()
        except ImportError:
            pass
        
        # 其他未知类型：转为字符串
        return str(obj)

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """安全的 JSON 序列化"""
    return json.dumps(obj, cls=FlexibleEncoder, **kwargs)

def safe_json_loads(s: str, **kwargs) -> Any:
    """安全的 JSON 反序列化"""
    return json.loads(s, **kwargs)

if __name__ == "__main__":
    # 测试
    import numpy as np
    data = {
        "int_val": np.int64(10),
        "float_val": np.float32(3.14),
        "time_val": datetime.datetime.now(),
        "normal": 100
    }
    print(safe_json_dumps(data))
