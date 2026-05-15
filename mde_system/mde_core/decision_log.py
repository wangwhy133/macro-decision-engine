"""
MDE 策略决策日志与透明化
记录每一笔交易的决策理由
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

@dataclass
class DecisionLog:
    """决策日志"""
    timestamp: str
    strategy_name: str
    symbol: str
    action: str  # BUY/SELL/HOLD
    reason: str  # 决策理由
    data_context: Dict[str, Any]  # 数据上下文 (如新闻情感、指标值)
    confidence: float  # 置信度
    trace_id: str  # 链路 ID

class DecisionLogger:
    """决策日志记录器"""
    
    def __init__(self, log_dir: str = "logs/decisions"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_date: Optional[str] = None
        self.log_file: Optional[any] = None
    
    def log(self, decision: DecisionLog):
        """记录决策"""
        today = decision.timestamp[:10]
        
        # 按天分割日志
        if self.current_date != today:
            if self.log_file:
                self.log_file.close()
            self.current_date = today
            log_path = self.log_dir / f"decisions_{today}.jsonl"
            self.log_file = open(log_path, 'a', encoding='utf-8')
        
        # 写入 JSONL
        self.log_file.write(json.dumps(asdict(decision), ensure_ascii=False) + '\n')
        self.log_file.flush()
    
    def get_today_logs(self) -> List[DecisionLog]:
        """获取今日日志"""
        today = datetime.now().strftime('%Y-%m-%d')
        log_path = self.log_dir / f"decisions_{today}.jsonl"
        if not log_path.exists():
            return []
        
        logs = []
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                logs.append(DecisionLog(**data))
        return logs
    
    def visualize(self, logs: List[DecisionLog]) -> str:
        """简单可视化 (文本版)"""
        if not logs:
            return "无日志"
        
        lines = ["### 决策可视化 ###"]
        for log in logs:
            lines.append(f"[{log.timestamp}] {log.strategy_name} {log.action} {log.symbol}")
            lines.append(f"  理由：{log.reason}")
            lines.append(f"  置信度：{log.confidence:.2f}")
            lines.append(f"  上下文：{json.dumps(log.data_context, ensure_ascii=False)}")
            lines.append("-" * 40)
        return "\n".join(lines)

# 全局实例
decision_logger = DecisionLogger()

__all__ = ['DecisionLog', 'DecisionLogger', 'decision_logger']
