"""
MDE 数据源统一接口与模型
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import hashlib

@dataclass
class NewsItem:
    """统一新闻模型"""
    title: str
    content: str
    source: str  # 来源：财联社/同花顺/腾讯
    publish_time: datetime
    sentiment: float = 0.0  # -1.0 (利空) ~ 1.0 (利好)
    tags: List[str] = field(default_factory=list)
    raw_id: str = ""
    
    def __post_init__(self):
        if not self.raw_id:
            # 生成唯一 ID
            self.raw_id = hashlib.md5(f"{self.title}{self.publish_time}".encode()).hexdigest()

@dataclass
class HotTopic:
    """统一热点主题模型"""
    name: str
    rank: int
    change_rate: float = 0.0  # 涨幅
    heat_value: float = 0.0  # 热度值
    related_stocks: List[str] = field(default_factory=list)

class DataSource(ABC):
    """数据源基类"""
    
    name = "BaseSource"
    
    @abstractmethod
    def get_news(self, symbol: Optional[str] = None, limit: int = 10) -> List[NewsItem]:
        """获取新闻"""
        pass
    
    @abstractmethod
    def get_hot_topics(self) -> List[HotTopic]:
        """获取热点"""
        pass
    
    @abstractmethod
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """获取行情"""
        pass
