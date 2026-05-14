# src/agents/parallel_agent.py
"""
并行 Multi-Agent 系统
基于 MiniMax-M2.7，实现 Market/Macro/Risk 三方会诊
"""
import asyncio
import httpx
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# 强制指定编码加载
import sys
if sys.version_info[0] >= 3:
    from dotenv import load_dotenv
    # 尝试以 UTF-8 加载
    load_dotenv(dotenv_path='.env', encoding='utf-8')
else:
    load_dotenv()

API_KEY = os.getenv("MINIMAX_API_KEY", "")
MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")
BASE_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

class ParallelAgentSystem:
    def __init__(self, features, history_context=None, last_decision=None):
        self.features = features or {}
        self.history_context = history_context or {}
        self.last_decision = last_decision or {}
        self.client = httpx.AsyncClient(timeout=30)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

    async def _call_agent(self, role: str, prompt: str):
        """异步调用 LLM"""
        if not API_KEY:
            return f"[模拟 {role}] 无 API Key，无法调用"
        
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
            return data['choices'][0]['message']['content']
        except Exception as e:
            return f"API Error: {str(e)}"

    async def run_market_agent(self):
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

    async def run_macro_agent(self):
        # 模拟宏观数据 (实际应从数据库读取)
        macro_sim = "利率维持高位，通胀温和"
        prompt = f"""
[宏观环境]
{macro_sim}

[任务]
判断宏观环境是 'Risk-On' 还是 'Risk-Off'。
理由：一句话。
"""
        return await self._call_agent("Macro Agent", prompt)

    async def run_risk_agent(self):
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

    async def run_router(self, market, macro, risk):
        prompt = f"""
[综合会诊]
Market: {market}
Macro: {macro}
Risk: {risk}

[历史教训]
上次决策准确率：{self.last_decision.get('accuracy_history', 'Unknown')}

[任务]
输出 JSON 格式：
{{
 "action": "BUY/SELL/HOLD",
 "confidence": 0-100,
 "summary": "简短总结"
}}
"""
        response = await self._call_agent("Router Agent", prompt)
        # 尝试解析 JSON
        try:
            # 提取 JSON 部分
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response[start:end]
                return json.loads(json_str)
        except:
            pass
        return {"action": "HOLD", "confidence": 50, "summary": response}

    async def execute(self):
        print("⚡ 启动并行推理...")
        
        # 1. 并发执行子 Agent
        market_op, macro_op, risk_op = await asyncio.gather(
            self.run_market_agent(),
            self.run_macro_agent(),
            self.run_risk_agent()
        )
        
        print(f"📈 Market: {market_op[:50]}...")
        print(f"🌍 Macro: {macro_op[:550]}...")
        print(f"🛡️ Risk: {risk_op[:50]}...")

        # 2. Router 汇总
        final_decision = await self.run_router(market_op, macro_op, risk_op)
        print(f"🎯 Final: {final_decision}")
        
        return {
            "market": market_op,
            "macro": macro_op,
            "risk": risk_op,
            "final": final_decision
        }

if __name__ == "__main__":
    # 测试用假数据
    fake_features = {"price": 405.2, "rsi": 55.3, "volatility": 0.2, "trend": "bullish"}
    fake_history = {"rsi_trend": "Rising"}
    fake_last = {"action": "HOLD", "result": "N/A", "accuracy_history": "60%"}
    
    agent = ParallelAgentSystem(fake_features, fake_history, fake_last)
    result = asyncio.run(agent.execute())
    print(json.dumps(result, indent=2))
