# src/services/healthcheck.py
"""
健康检查服务 (生产级)

功能:
1. 服务存活检查
2. 依赖服务状态检查
3. 性能指标采集
4. 告警通知

使用示例:
    from src.services.healthcheck import HealthCheckService
    
    hc = HealthCheckService()
    status = hc.get_status()
    
    if status['status'] == 'unhealthy':
        send_alert(status['issues'])
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.utils.logger import setup_logger
from src.risk.risk_control import get_risk_control

logger = setup_logger("MDE.HealthCheck")


class HealthCheckService:
    """健康检查服务"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.last_check_time = None
        self.check_count = 0
        self.consecutive_failures = 0
        self.max_failures = 3
        
        # 健康检查项
        self.checks = {
            'config': self._check_config,
            'data_dir': self._check_data_dir,
            'risk_control': self._check_risk_control,
            'api_key': self._check_api_key,
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取系统健康状态
        
        Returns:
            健康状态字典
        """
        self.last_check_time = datetime.now()
        self.check_count += 1
        
        results = {}
        issues = []
        
        # 执行所有检查
        for check_name, check_func in self.checks.items():
            try:
                result = check_func()
                results[check_name] = result
                if not result['healthy']:
                    issues.append(result.get('message', f'{check_name} 检查失败'))
            except Exception as e:
                logger.error(f"健康检查 {check_name} 异常：{e}")
                results[check_name] = {
                    'healthy': False,
                    'message': str(e)
                }
                issues.append(f'{check_name}: {str(e)}')
        
        # 计算总体状态
        healthy_count = sum(1 for r in results.values() if r.get('healthy', False))
        total_count = len(results)
        health_percentage = healthy_count / total_count if total_count > 0 else 0
        
        if health_percentage == 1.0:
            status = 'healthy'
        elif health_percentage >= 0.5:
            status = 'degraded'
        else:
            status = 'unhealthy'
        
        # 更新失败计数
        if status != 'healthy':
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
        
        return {
            'status': status,
            'timestamp': self.last_check_time.isoformat(),
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'check_count': self.check_count,
            'consecutive_failures': self.consecutive_failures,
            'health_percentage': health_percentage,
            'issues': issues,
            'checks': results
        }
    
    def _check_config(self) -> Dict[str, Any]:
        """检查配置文件"""
        config_file = '.env'
        if os.path.exists(config_file):
            return {
                'healthy': True,
                'message': f'配置文件存在：{config_file}'
            }
        else:
            return {
                'healthy': False,
                'message': f'配置文件缺失：{config_file}'
            }
    
    def _check_data_dir(self) -> Dict[str, Any]:
        """检查数据目录"""
        data_dirs = ['data/raw', 'data/features', 'logs']
        missing_dirs = []
        
        for dir_path in data_dirs:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except Exception as e:
                    missing_dirs.append(f'{dir_path} (创建失败：{e})')
        
        if missing_dirs:
            return {
                'healthy': False,
                'message': f'数据目录缺失：{", ".join(missing_dirs)}'
            }
        
        return {
            'healthy': True,
            'message': '数据目录正常'
        }
    
    def _check_risk_control(self) -> Dict[str, Any]:
        """检查风控系统"""
        try:
            rc = get_risk_control()
            report = rc.get_security_report()
            
            if report.get('circuit_breaker'):
                return {
                    'healthy': False,
                    'message': '风控熔断器已触发'
                }
            
            return {
                'healthy': True,
                'message': '风控系统正常',
                'details': report
            }
        except Exception as e:
            return {
                'healthy': False,
                'message': f'风控系统异常：{e}'
            }
    
    def _check_api_key(self) -> Dict[str, Any]:
        """检查 API Key"""
        api_key = os.getenv('MINIMAX_API_KEY')
        
        if not api_key:
            return {
                'healthy': False,
                'message': 'API Key 未配置'
            }
        
        if len(api_key) < 10:
            return {
                'healthy': False,
                'message': 'API Key 格式错误'
            }
        
        return {
            'healthy': True,
            'message': 'API Key 配置正常'
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标
        
        Returns:
            性能指标字典
        """
        return {
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'check_count': self.check_count,
            'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
            'consecutive_failures': self.consecutive_failures,
            'timestamp': datetime.now().isoformat()
        }
    
    def send_alert(self, message: str, level: str = 'WARNING'):
        """
        发送告警 (预留接口)
        
        Args:
            message: 告警内容
            level: 告警级别
        """
        logger.warning(f"🚨 告警 [{level}]: {message}")
        # TODO: 实现邮件/Telegram 告警


# 全局健康检查实例
_health_check_service = None


def get_health_check() -> HealthCheckService:
    """获取健康检查服务实例"""
    global _health_check_service
    if _health_check_service is None:
        _health_check_service = HealthCheckService()
    return _health_check_service


def health_check() -> Dict[str, Any]:
    """快捷健康检查"""
    hc = get_health_check()
    return hc.get_status()


if __name__ == "__main__":
    # 测试健康检查
    import logging
    logging.basicConfig(level=logging.INFO)
    
    hc = get_health_check()
    
    # 获取状态
    status = hc.get_status()
    print(f"系统状态：{status['status']}")
    print(f"健康度：{status['health_percentage']:.0%}")
    print(f"运行时间：{status['uptime_seconds']:.0f}秒")
    
    if status['issues']:
        print("\n问题列表:")
        for issue in status['issues']:
            print(f"  - {issue}")
    
    # 获取指标
    metrics = hc.get_metrics()
    print(f"\n性能指标：{metrics}")
