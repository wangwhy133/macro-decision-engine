# src/data/crawlers/__init__.py
"""爬虫模块"""

from .base_crawler import BaseCrawler
from .pig_crawler import PigCrawler, fetch_pig_data
from .semiconductor_crawler import SemiconductorCrawler, fetch_semiconductor_data

__all__ = [
    'BaseCrawler',
    'PigCrawler', 'fetch_pig_data',
    'SemiconductorCrawler', 'fetch_semiconductor_data'
]
