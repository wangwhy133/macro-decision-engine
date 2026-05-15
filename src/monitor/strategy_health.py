# src/monitor/strategy_health.py
"""
策略健康度监控 (Strategy Health Monitor)

功能:
1. 实时监控策略表现 (胜率、盈亏比、最大回撤)
2. 检测策略失效 (连续亏损、偏离预期)
3. 自动熔断 (暂停交易) 防止进一步亏损
4. 生成健康报告

监控指标:
- 滚动胜率 (Rolling Win Rate)
- 滚动盈亏比 (Rolling Profit/Loss Ratio)
- 最大连续亏损 (Max Consecutive Losses)
- 实时回撤 (Drawdown)
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from src.utils.logger import setup_logger
from src.services.watchdog import get_watchdog

logger = setup_logger("MDE.HealthMonitor")

@dataclass
class HealthMetrics:
    """健康指标"""
    win_rate: float  # 胜率
    profit_loss_ratio: float  # 盈亏比
    consecutive_losses: int  # 连续亏损次数
    max_consecutive_losses: int  # 最大连续亏损
    drawdown: float  # 当前回撤
    total_pnl: float  # 总盈亏
    trade_count: int  # 交易次数

class StrategyHealthMonitor:
    """策略健康度监控器"""
    
    def __init__(
        self,
        expected_win_rate: float = 0.55,
        max_consecutive_losses: int = 5,  # 连续 5 次亏损熔断
        max_drawdown: float = 0.15,  # 最大回撤 15% 熔断
        min_trades_for_check: int = 10  # 至少 10 笔交易后开始检查
    ):
        self.expected_win_rate = expected_win_rate
        self.max_consecutive_losses = max_consecutive_losses
        self.max_drawdown = max_drawdown
        self.min_trades_for_check = min_trades_for_check
        
        self.is_paused = False
        self.pause_reason = ""
        self.trade_log: List[Dict] = []
        self.peak_capital = 0.0
        self.current_capital = 0.0
    
    def record_trade(self, pnl: float, pnl_pct: float, is_win: bool):
        """记录一笔交易"""
        self.trade_log.append({
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'is_win': is_win,
            'timestamp': datetime.now()
        })
        
        # 更新资本曲线
        self.current_capital += pnl
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        
        # 检查健康度
        self._check_health()
    
    def _check_health(self):
        """检查策略健康度"""
        if len(self.trade_log) < self.min_trades_for_check:
            return
        
        metrics = self.calculate_metrics()
        
        # 1. 检查连续亏损
        if metrics.consecutive_losses >= self.max_consecutive_losses:
            self._trigger_pause(f"连续亏损 {metrics.consecutive_losses} 次")
            return
        
        # 2. 检查最大回撤
        if self.peak_capital > 0:
            current_dd = (self.peak_capital - self.current_capital) / self.peak_capital
            if current_dd > self.max_drawdown:
                self._trigger_pause(f"回撤 {current_dd:.1%} 超过阈值 {self.max_drawdown:.1%}")
                return
        
        # 3. 检查胜率严重偏离
        if metrics.win_rate < self.expected_win_rate * 0.5:  # 胜率低于预期一半
            self._trigger_pause(f"胜率 {metrics.win_rate:.1%} 严重低于预期 {self.expected_win_rate:.1%}")
    
    def _trigger_pause(self, reason: str):
        """触发熔断"""
        if not self.is_paused:
            self.is_paused = True
            self.pause_reason = reason
            logger.error(f"🚨 策略熔断：{reason}")
            # TODO: 发送告警
    
    def resume(self):
        """手动恢复"""
        self.is_paused = False
        self.pause_reason = ""
        logger.info("✅ 策略已手动恢复")
    
    def calculate_metrics(self) -> HealthMetrics:
        """计算健康指标"""
        if not self.trade_log:
            return HealthMetrics(0, 0, 0, 0, 0, 0, 0)
        
        wins = [t for t in self.trade_log if t['is_win']]
        losses = [t for t in self.trade_log if not t['is_win']]
        
        win_rate = len(wins) / len(self.trade_log)
        
        avg_win = sum(t['pnl_pct'] for t in wins) / len(wins) if wins else 0
        avg_loss = abs(sum(t['pnl_pct'] for t in losses) / len(losses)) if losses else 0
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        # 计算连续亏损
        consec = 0
        max_consec = 0
        curr_consec = 0
        for t in reversed(self.trade_log):
            if not t['is_win']:
                curr_consec += 1
                max_consec = max(max_consec, curr_consec)
            else:
                curr_consec = 0
        consec = curr_consec  # 当前连续亏损
        
        # 回撤
        dd = (self.peak_capital - self.current_capital) / self.peak_capital if self.peak_capital > 0 else 0
        
        total_pnl = sum(t['pnl'] for t in self.trade_log)
        
        return HealthMetrics(
            win_rate=win_rate,
            profit_loss_ratio=profit_loss_ratio,
            consecutive_losses=consec,
            max_consecutive_losses=max_consec,
            drawdown=dd,
            total_pnl=total_pnl,
            trade_count=len(self.trade_log)
        )
    
    def get_status_report(self) -> Dict:
        """获取状态报告"""
        metrics = self.calculate_metrics()
        return {
            'status': 'PAUSED' if self.is_paused else 'RUNNING',
            'pause_reason': self.pause_reason,
            'metrics': {
                'win_rate': metrics.win_rate,
                'profit_loss_ratio': metrics.profit_loss_ratio,
                'consecutive_losses': metrics.consecutive_losses,
                'max_consecutive_losses': metrics.max_consecutive_losses,
                'drawdown': metrics.drawdown,
                'total_pnl': metrics.total_pnl,
                'trade_count': metrics.trade_count
            }
        }

# 全局单例
_monitor = None

def get_health_monitor() -> StrategyHealthMonitor:
    global _monitor
    if _monitor is None:
        _monitor = StrategyHealthMonitor()
    return _monitor

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    monitor = get_health_monitor()
    
    # 模拟交易
    for i in range(15):
        is_win = i % 3 == 0  # 模拟 3 笔中 1 笔赢
        pnl = 0.05 if is_win else -0.03
        monitor.record_trade(pnl*1000, pnl, is_win)
        
        status = monitor.get_status_report()
        print(f"交易 {i+1}: 状态={status['status']}, 胜率={status['metrics']['win_rate']:.1%}")
        
        if status['status'] == 'PAUSED':
            print(f"熔断原因：{status['pause_reason']}")
            break
