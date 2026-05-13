"""
数据突变检测器
检测宏观数据的异常跳变，防止"幽灵数据"误导
"""
from typing import Dict, Any, Optional, List
from datetime import datetime

class AnomalyDetector:
    """检测数据突变"""
    
    # 合理波动范围 (倍数)
    # 例如：CPI 环比变化不应超过 3 倍标准差，或绝对值不超过 2%
    THRESHOLDS = {
        "cpi": {"max_change": 2.0},       # CPI 单月变化不超过 2%
        "ppi": {"max_change": 3.0},       # PPI 单月变化不超过 3%
        "pmi_mfg": {"max_change": 5.0},   # PMI 变化不超过 5 点
        "unemployment_rate": {"max_change": 1.0},
    }
    
    def __init__(self):
        self.history: Dict[str, List[float]] = {}
    
    def check(self, field: str, current_value: Optional[float]) -> Dict[str, Any]:
        """
        检查单个字段是否异常
        :return: {"is_anomaly": bool, "reason": str, "severity": str}
        """
        if current_value is None:
            return {"is_anomaly": False, "reason": "无数据", "severity": "info"}
        
        if field not in self.THRESHOLDS:
            return {"is_anomaly": False, "reason": "无阈值定义", "severity": "info"}
        
        threshold = self.THRESHOLDS[field]
        max_change = threshold.get("max_change", 999)
        
        # 简单规则：如果历史数据存在，检查变化率
        if field in self.history and len(self.history[field]) > 0:
            last_value = self.history[field][-1]
            change = abs(current_value - last_value)
            
            if change > max_change:
                return {
                    "is_anomaly": True,
                    "reason": f"变化幅度过大：{change:.2f} > {max_change}",
                    "severity": "high"
                }
        
        # 记录历史
        if field not in self.history:
            self.history[field] = []
        self.history[field].append(current_value)
        # 只保留最近 10 条
        if len(self.history[field]) > 10:
            self.history[field] = self.history[field][-10:]
        
        return {"is_anomaly": False, "reason": "正常", "severity": "low"}
    
    def check_batch(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        批量检查数据
        :return: {"has_anomaly": bool, "anomalies": List[str], "warnings": List[str]}
        """
        anomalies = []
        warnings = []
        
        for field in self.THRESHOLDS.keys():
            value = data.get(field)
            if value is not None:
                result = self.check(field, float(value))
                if result["is_anomaly"]:
                    anomalies.append(f"{field}: {result['reason']}")
                    if result["severity"] == "high":
                        warnings.append(f"高危：{field} 数据异常")
        
        return {
            "has_anomaly": len(anomalies) > 0,
            "anomalies": anomalies,
            "warnings": warnings
        }

# 全局单例
_detector = AnomalyDetector()

def get_detector() -> AnomalyDetector:
    return _detector

if __name__ == "__main__":
    detector = get_detector()
    
    # 测试
    data1 = {"cpi": 2.5, "ppi": 1.0}
    data2 = {"cpi": 2.6, "ppi": 1.1}  # 正常
    data3 = {"cpi": 10.0, "ppi": 1.2} # 异常
    
    print("测试 1 (正常):", detector.check_batch(data1))
    print("测试 2 (正常):", detector.check_batch(data2))
    print("测试 3 (异常):", detector.check_batch(data3))
