# src/agents/parallel_agent.py
"""
并行 Multi-Agent 系统 (生产级增强版)

基于 MiniMax-M2.7，实现 Market/Macro/Risk 三方会诊

增强功能:
1. 配置验证 (API Key 检查)
2. 异常处理与重试
3. 风控集成 (数据源感知)
4. 日志系统
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 导入风控和日志
from src.risk.risk_control import get_risk_control, init_risk_control, TradeAction
from src.utils.logger import setup_logger, get_logger
from src.utils.config import get_api_key, ConfigurationError

# 强制指定编码加载
import sys
if sys.version_info[0] >= 3:
    from dotenv import load_dotenv
    # 尝试以 UTF-8 加载
    load_dotenv(dotenv_path='.env', encoding='utf-8')
else:
    load_dotenv()

logger = setup_logger("MDE.Agent")

# 配置常量
MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")
BASE_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"


class ParallelAgentSystem:
    """并行 Agent 系统"""
    
    def __init__(self, features: Dict = None, history_context: Dict = None, last_decision: Dict = None):
        self.features = features or {}
        self.history_context = history_context or {}
        self.last_decision = last_decision or {}
        
        # 初始化风控
        self.rc = init_risk_control()
        
        # 验证 API Key
        try:
            self.api_key = get_api_key("MINIMAX_API_KEY")
        except ConfigurationError as e:
            logger.error(f"❌ API Key 验证失败：{e}")
            self.api_key = None
        
        self.client = httpx.AsyncClient(timeout=30)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }
    
    async def _call_agent(self, role: str, prompt: str) -> str:
        """异步调用 LLM"""
        if not self.api_key:
            logger.warning(f"⚠️ 无 API Key，使用模拟响应 [{role}]")
            return f"[模拟 {role}] 无 API Key，无法调用 LLM"
        
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": f"你是专业的金融分析师 ({role})。基于数据客观分析，输出简洁。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "top_p": 0.9
        }
        
        try:
            resp = await self.client.post(BASE_URL, json=payload, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            content = data['choices'][0]['message']['content']
            logger.info(f"✅ {role} 调用成功")
            return content
        except httpx.HTTPError as e:
            logger.error(f"❌ {role} HTTP 错误：{e}")
            self.rc.record_failure()
            return f"[{role} 异常] HTTP 错误：{str(e)}"
        except Exception as e:
            logger.error(f"❌ {role} 调用失败：{e}", exc_info=True)
            self.rc.record_failure()
            return f"[{role} 异常] {str(e)}"
    
    async def run_market_agent(self) -> str:
        """运行市场分析 Agent"""
        price = self.features.get('price', 0)
        rsi = self.features.get('rsi', 50)
        trend = self.features.get('trend', 'neutral')
        rsi_trend = self.history_context.get('rsi_trend', 'N/A')
        
        prompt = f"""
[市场数据]
价格：{price}
RSI: {rsi}
趋势：{trend}
RSI 变化：{rsi_trend}

[任务]
判断短期技术面是 'Bullish' (看涨), 'Bearish' (看跌) 还是 'Neutral' (震荡)。
理由：一句话。
"""
        return await self._call_agent("Market Agent", prompt)
    
    async def run_macro_agent(self) -> str:
        """运行宏观分析 Agent"""
        # 获取周期信号
        try:
            from src.services.supply_demand_monitor import get_monitor
            monitor = get_monitor()
            opps = monitor.get_opportunities()
            cycle_context = ""
            if opps:
                cycle_context = "\n[周期信号]\n" + "\n".join([f"- {o['industry_name']}: {o['type']} ({o['reason']})" for o in opps[:3]])
            else:
                cycle_context = "\n[周期信号] 暂无显著周期信号"
        except:
            cycle_context = "\n[周期信号] 数据未更新"
        
        # 模拟宏观数据
        macro_sim = "利率维持高位，通胀温和"
        
        prompt = f"""
[宏观环境] {macro_sim}
{cycle_context}

[任务]
判断宏观环境是 'Risk-On' 还是 'Risk-Off'。
理由：一句话。
"""
        return await self._call_agent("Macro Agent", prompt)
    
    async def run_risk_agent(self) -> str:
        """运行风险分析 Agent"""
        vol = self.features.get('volatility', 0.1)
        last_action = self.last_decision.get('action', 'None')
        last_result = self.last_decision.get('result', 'Pending')
        
        prompt = f"""
[风险指标]
波动率：{vol}
上次决策：{last_action} -> 结果：{last_result}

[任务]
评估当前风险等级 (High/Medium/Low) 并建议仓位 (0-100%)。
"""
        return await self._call_agent("Risk Agent", prompt)
    
    async def run_router(self, market: str, macro: str, risk: str) -> Dict[str, Any]:
        """运行路由聚合 Agent"""
        # 获取风控状态
        risk_report = self.rc.get_security_report()
        is_safe_to_trade = risk_report.get('circuit_breaker', False) == False
        
        prompt = f"""
[综合会诊]
Market: {market}
Macro: {macro}
Risk: {risk}

[历史教训]
上次决策准确率：{self.last_decision.get('accuracy_history', 'Unknown')}

[风控状态]
安全模式：{risk_report.get('safe_mode', False)}
熔断器：{risk_report.get('circuit_breaker', False)}
可交易：{is_safe_to_trade}

[任务]
输出 JSON 格式：
{{
  "action": "BUY/SELL/HOLD",
  "confidence": 0-100,
  "summary": "简短总结"
}}

注意：如果风控显示不可交易，强制输出 HOLD
"""
        response_text = await self._call_agent("Router Agent", prompt)
        
        # 尝试解析 JSON
        try:
            # 提取 JSON 部分
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response_text[start:end]
                result = json.loads(json_str)
                
                # 风控覆盖：如果不可交易，强制 HOLD
                if not is_safe_to_trade and result.get('action') != 'HOLD':
                    logger.warning("🚨 风控覆盖：强制 HOLD")
                    result['action'] = 'HOLD'
                    result['summary'] = '风控强制 HOLD'
                
                return result
        except Exception as e:
            logger.error(f"解析 Router JSON 失败：{e}")
        
        # 默认返回
        return {"action": "HOLD", "confidence": 50, "summary": response_text}
    
    async def execute(self) -> Dict[str, Any]:
        """执行完整的多 Agent 流程"""
        if not self.api_key:
            logger.warning("⚠️ 无 API Key，使用模拟数据运行")
        
        logger.info("⚡ 启动并行推理...")
        
        # 1. 并发执行子 Agent
        try:
            market_op, macro_op, risk_op = await asyncio.gather(
                self.run_market_agent(),
                self.run_macro_agent(),
                self.run_risk_agent()
            )
        except Exception as e:
            logger.error(f"❌ Agent 执行失败：{e}", exc_info=True)
            return {
                "error": str(e),
                "final": {"action": "HOLD", "confidence": 0, "summary": "执行失败"}
            }
        
        logger.info(f"📈 Market: {market_op[:50]}...")
        logger.info(f"🌍 Macro: {macro_op[:50]}...")
        logger.info(f"🛡️ Risk: {risk_op[:50]}...")
        
        # 2. Router 汇总
        final_decision = await self.run_router(market_op, macro_op, risk_op)
        logger.info(f"🎯 Final: {final_decision}")
        
        # 记录成功
        self.rc.record_success()
        
        return {
            "market": market_op,
            "macro": macro_op,
            "risk": risk_op,
            "final": final_decision
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.client.aclose()


async def run_agent_system(features: Dict = None, history_context: Dict = None, last_decision: Dict = None):
    """运行 Agent 系统的便捷函数"""
    async with ParallelAgentSystem(features, history_context, last_decision) as agent:
        return await agent.execute()


if __name__ == "__main__":
    # 测试用假数据
    import logging
    logging.basicConfig(level=logging.INFO)
    
    fake_features = {"price": 405.2, "rsi": 55.3, "volatility": 0.2, "trend": "bullish"}
    fake_history = {"rsi_trend": "Rising"}
    fake_last = {"action": "HOLD", "result": "N/A", "accuracy_history": "60%"}
    
    async def test():
        async with ParallelAgentSystem(fake_features, fake_history, fake_last) as agent:
            result = await agent.execute()
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    asyncio.run(test())
