"""
MDE 多源数据实现
- Mootdx (腾讯/同花顺底层)
- AkShare (财联社/个股新闻)
- iWenCai (同花顺热点)
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .sources import DataSource, NewsItem, HotTopic

class AkShareSource(DataSource):
    """
    AkShare 数据源
    - 财联社新闻
    - 个股新闻
    - 财经新闻
    """
    name = "AkShare"
    
    def get_news(self, symbol: Optional[str] = None, limit: int = 10) -> List[NewsItem]:
        items = []
        try:
            if symbol:
                # 个股新闻
                df = ak.stock_news_em(symbol=symbol)
                if df is not None and not df.empty:
                    for _, row in df.head(limit).iterrows():
                        items.append(NewsItem(
                            title=str(row.get('标题', '')),
                            content=str(row.get('内容', '')),
                            source='东方财富',
                            publish_time=pd.to_datetime(row.get('发布时间', datetime.now())).to_pydatetime(),
                            tags=['个股新闻'],
                            raw_id=str(row.get('id', ''))
                        ))
            else:
                # 财联社新闻 (7x24 快讯)
                df = ak.stock_info_global_cls(symbol="全部")
                if df is not None and not df.empty:
                    for _, row in df.head(limit).iterrows():
                        content = str(row.get('内容', ''))
                        items.append(NewsItem(
                            title=content[:50] + "..." if len(content) > 50 else content,
                            content=content,
                            source='财联社',
                            publish_time=pd.to_datetime(row.get('发布时间', datetime.now())).to_pydatetime(),
                            tags=['快讯', '财联社'],
                            raw_id=str(row.get('id', ''))
                        ))
        except Exception as e:
            print(f"AkShare 获取新闻失败：{e}")
        
        return items
    
    def get_hot_topics(self) -> List[HotTopic]:
        """获取同花顺/东方财富 热点板块"""
        topics = []
        try:
            # 东方财富行业板块
            df = ak.stock_board_industry_name_em()
            if df is not None and not df.empty:
                for _, row in df.head(20).iterrows():
                    topics.append(HotTopic(
                        name=str(row.get('板块名称', '')),
                        rank=int(row.get('排名', 0)),
                        change_rate=float(str(row.get('涨跌幅', '0')).replace('%', '')) if row.get('涨跌幅') else 0.0,
                        related_stocks=[]
                    ))
        except Exception as e:
            print(f"AkShare 获取热点失败：{e}")
        return topics
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """获取行情 (简化)"""
        try:
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                row = df[df['代码'] == symbol].iloc[0] if '代码' in df.columns else None
                if row is not None:
                    return {
                        'symbol': symbol,
                        'price': float(row.get('最新价', 0)),
                        'change': float(row.get('涨跌幅', 0)),
                        'volume': float(row.get('成交量', 0)),
                        'timestamp': datetime.now()
                    }
        except Exception as e:
            print(f"AkShare 获取行情失败：{e}")
        return {}

class MootdxSource(DataSource):
    """
    Mootdx 数据源 (腾讯/同花顺底层协议)
    需安装: pip install mootdx
    """
    name = "Mootdx"
    
    def __init__(self):
        self.client = None
        try:
            import mootdx
            self.client = mootdx.client()
        except:
            pass
    
    def get_news(self, symbol: Optional[str] = None, limit: int = 10) -> List[NewsItem]:
        # Mootdx 主要用于行情，新闻功能有限，此处返回空由其他源补充
        return []
    
    def get_hot_topics(self) -> List[HotTopic]:
        return []
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        if not self.client:
            return {}
        try:
            # 解析代码 (如 sh600000)
            market = 'sh' if symbol.startswith('6') else 'sz'
            code = symbol[2:] if len(symbol) > 2 else symbol
            data = self.client.quotes(market, [code])
            if data:
                d = data[0]
                return {
                    'symbol': symbol,
                    'price': d.get('price', 0),
                    'change': d.get('percent', 0),
                    'volume': d.get('vol', 0),
                    'timestamp': datetime.now()
                }
        except Exception as e:
            print(f"Mootdx 获取行情失败：{e}")
        return {}

class WenCaiSource(DataSource):
    """
    iWenCai (同花顺问财) 热点数据
    需安装: pip install akshare (通过 akshare 调用)
    """
    name = "WenCai"
    
    def get_news(self, symbol: Optional[str] = None, limit: int = 10) -> List[NewsItem]:
        return []
    
    def get_hot_topics(self) -> List[HotTopic]:
        """获取同花顺热点主题"""
        topics = []
        try:
            # 同花顺概念板块
            df = ak.stock_board_concept_name_em()
            if df is not None and not df.empty:
                for _, row in df.head(20).iterrows():
                    topics.append(HotTopic(
                        name=str(row.get('板块名称', '')),
                        rank=int(row.get('排名', 0)),
                        change_rate=float(str(row.get('涨跌幅', '0')).replace('%', '')) if row.get('涨跌幅') else 0.0,
                        related_stocks=[]
                    ))
        except Exception as e:
            print(f"WenCai 获取热点失败：{e}")
        return topics
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        return {}

# 工厂函数
def get_source(name: str) -> DataSource:
    if name == 'AkShare':
        return AkShareSource()
    elif name == 'Mootdx':
        return MootdxSource()
    elif name == 'WenCai':
        return WenCaiSource()
    raise ValueError(f"未知数据源：{name}")

__all__ = ['AkShareSource', 'MootdxSource', 'WenCaiSource', 'get_source']
