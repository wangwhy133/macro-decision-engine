"""
标准输出模块 - 构建和持久化标准决策输出
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def build_and_persist_standard_decision(
    data: Dict[str, Any],
    analysis: Optional[Dict[str, Any]] = None,
    decision: Optional[str] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    构建并持久化标准决策输出
    
    Args:
        data: 采集的原始数据
        analysis: AI 分析结果
        decision: 最终决策
        output_path: 输出路径 (可选)
    
    Returns:
        标准决策对象
    """
    timestamp = datetime.now().isoformat()
    
    decision_obj = {
        "timestamp": timestamp,
        "status": "success",
        "data": data,
        "analysis": analysis or {},
        "decision": decision,
        "metadata": {
            "version": "2.0",
            "generated_at": timestamp
        }
    }
    
    logger.info(f"标准决策构建完成：{timestamp}")
    
    # 如果指定了输出路径，则持久化
    if output_path:
        try:
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(decision_obj, f, indent=2, ensure_ascii=False)
            logger.info(f"决策已持久化到：{output_path}")
        except Exception as e:
            logger.error(f"持久化失败：{e}")
    
    return decision_obj
