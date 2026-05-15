# src/data/crawlers/base_crawler.py
"""
通用爬虫基类 (Base Crawler)

功能:
1. 统一接口 (fetch, parse, save)
2. 自动重试与降级
3. 数据校验与缓存
4. 异常处理与日志
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

from src.utils.retry import retry_with_fallback
from src.utils.logger import setup_logger

logger = setup_logger("MDE.Crawler")

class BaseCrawler(ABC):
    """爬虫基类"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.name = self.__class__.__name__
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """数据源名称 (如 'pig_gov', 'sia')"""
        pass
    
    @abstractmethod
    def fetch_raw(self) -> Any:
        """获取原始数据 (子类实现)"""
        pass
    
    @abstractmethod
    def parse(self, raw_data: Any) -> Dict[str, Any]:
        """解析数据 (子类实现)"""
        pass
    
    def fetch(self) -> Optional[Dict[str, Any]]:
        """
        获取并解析数据 (带重试和缓存)
        
        Returns:
            解析后的数据字典，失败返回 None
        """
        cache_file = os.path.join(self.cache_dir, f"{self.source_name}_cache.json")
        
        # 1. 尝试读取缓存 (1 小时内有效)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached = json.load(f)
                cache_time = datetime.fromisoformat(cached['timestamp'])
                if (datetime.now() - cache_time).total_seconds() < 3600:
                    logger.info(f"[{self.name}] 使用缓存数据")
                    return cached['data']
            except Exception as e:
                logger.warning(f"[{self.name}] 读取缓存失败：{e}")
        
        # 2. 抓取新数据
        @retry_with_fallback(max_retries=3, fallback=lambda: None)
        def _fetch_with_retry():
            raw = self.fetch_raw()
            return self.parse(raw)
        
        try:
            logger.info(f"[{self.name}] 正在抓取新数据...")
            data = _fetch_with_retry()
            
            if data:
                # 保存缓存
                cache_data = {
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }
                with open(cache_file, 'w') as f:
                    json.dump(cache_data, f, indent=2)
                logger.info(f"[{self.name}] 抓取成功，已缓存")
                return data
            else:
                logger.error(f"[{self.name}] 抓取失败，无数据")
                return None
        except Exception as e:
            logger.error(f"[{self.name}] 抓取异常：{e}")
            return None
    
    def save_to_db(self, data: Dict[str, Any], db_path: str = "data/supply_demand_db.json"):
        """保存到数据库 (简化为 JSON 文件)"""
        if not os.path.exists(db_path):
            db = []
        else:
            with open(db_path, 'r') as f:
                db = json.load(f)
        
        # 添加时间戳并追加
        record = {
            'source': self.source_name,
            'fetch_time': datetime.now().isoformat(),
            **data
        }
        db.append(record)
        
        with open(db_path, 'w') as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[{self.name}] 数据已入库：{db_path}")
