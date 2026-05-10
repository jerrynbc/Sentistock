#!/usr/bin/env python3
"""
RSSHub新闻源集成模块
"""

import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict

class RSSHubNewsFetcher:
    """从RSSHub获取A股实时新闻"""
    
    def __init__(self):
        self.base_url = "https://rsshub.app/10jqka/realtimenews/A股"
        self.session = requests.Session()
        self.session.timeout = 10
        
    def fetch_news(self, symbol: str = None) -> List[Dict]:
        """
        获取A股实时新闻
        
        Args:
            symbol: 股票代码（可选，RSS返回所有A股新闻）
            
        Returns:
            新闻列表，包含标题、内容、时间等信息
        """
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            # 解析RSS
            feed = feedparser.parse(response.content)
            news_list = []
            
            for entry in feed.entries:
                # 过滤包含股票代码的新闻（如果指定了symbol）
                if symbol and symbol not in entry.title and symbol not in entry.summary:
                    continue
                    
                news_item = {
                    'title': entry.title,
                    'content': entry.summary,
                    'pub_date': datetime(*entry.published_parsed[:6]) if entry.published_parsed else datetime.now(),
                    'source': '同花顺',
                    'url': entry.link
                }
                news_list.append(news_item)
                
            return news_list
            
        except Exception as e:
            print(f"⚠️ RSSHub新闻获取失败: {e}")
            return []
            
    def get_latest_news(self, hours: int = 2) -> List[Dict]:
        """获取最近N小时的新闻"""
        all_news = self.fetch_news()
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_news = [n for n in all_news if n['pub_date'] >= cutoff_time]
        return recent_news

# 全局实例
rss_fetcher = RSSHubNewsFetcher()

def get_rss_news(symbol: str = None) -> List[Dict]:
    """便捷函数：获取RSS新闻"""
    return rss_fetcher.fetch_news(symbol)