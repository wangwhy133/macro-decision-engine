# src/data/realtime_ingest.py
"""
C. 真实实时流接入
使用 Finnhub (或降级为 yfinance) 获取实时行情
"""
import os
import yfinance as yf
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 尝试导入 finnhub，如果没有则降级
try:
    import finnhub
    FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
    HAS_FINNHUB = bool(FINNHUB_API_KEY)
except ImportError:
    HAS_FINNHUB = False

def get_realtime_data(symbol: str = "SPY"):
    """获取实时行情数据"""
    
    # 1. 尝试 Finnhub (更快，实时)
    if HAS_FINNHUB:
        try:
            finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)
            quote = finnhub_client.quote(symbol)
            # quote: [currentPrice, change, changePercent, openPrice, highPrice, lowPrice, prevClose, timestamp]
            if quote and quote[0]:
                return {
                    "price": quote[0],
                    "change": quote[1],
                    "change_percent": quote[2],
                    "high": quote[4],
                    "low": quote[5],
                    "source": "finnhub"
                }
        except Exception as e:
            print(f"⚠️ Finnhub 失败，降级至 yfinance: {e}")

    # 2. 降级方案：yfinance (延迟低，但非实时)
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if hist.empty:
            return None
        
        current_price = float(hist['Close'].iloc[-1])
        return {
            "price": current_price,
            "change": float(hist['Close'].iloc[-1] - hist['Open'].iloc[-1]),
            "change_percent": 0.0,
            "high": float(hist['High'].iloc[-1]),
            "low": float(hist['Low'].iloc[-1]),
            "source": "yfinance"
        }
    except Exception as e:
        print(f"❌ yfinance 也失败：{e}")
        return None

if __name__ == "__main__":
    data = get_realtime_data("SPY")
    if data:
        print(f"📊 实时数据 ({data['source']}): {data}")
    else:
        print("❌ 获取数据失败")
