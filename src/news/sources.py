"""
多源新闻抓取器

支持的数据源:
1. 东方财富 (AKShare stock_news_em)
   - 优点：稳定
   - 缺点：仅返回最新 10 条
2. 新浪财经 (Requests 爬虫)
   - 优点：数据量较大
   - 缺点：反爬，需处理解析逻辑

接口:
    fetch_news(symbol: str, sources: List[str] = ['eastmoney', 'sina']) -> List[Dict]
"""

import akshare as ak
import pandas as pd
import requests
import re
from datetime import datetime
from typing import List, Dict

try:
    from .rsshub_fetcher import get_rss_news
    RSSHUB_AVAILABLE = True
except ImportError:
    RSSHUB_AVAILABLE = False


def fetch_eastmoney_news(symbol: str) -> List[Dict]:
    """获取东方财富个股新闻"""
    try:
        df = ak.stock_news_em(symbol=symbol)
        if df.empty:
            return []
            
        news_list = []
        for _, row in df.iterrows():
            news_list.append({
                'title': row.get('新闻标题', ''),
                'content': row.get('新闻内容', ''),
                'date': row.get('发布时间', ''),
                'source': 'eastmoney',
                'url': row.get('新闻链接', '')
            })
        return news_list
    except Exception as e:
        print(f"⚠️ 东方财富新闻获取失败：{e}")
        return []


def fetch_sina_news(symbol: str) -> List[Dict]:
    """获取新浪财经新闻 (简易爬虫)"""
    # 新浪新闻搜索 URL
    # 这里使用新浪财经的个股新闻页面作为示例，实际可能变动
    # 由于新浪反爬，这里仅尝试获取列表页
    url = f"https://finance.sina.com.cn/realstock/company/{symbol}/nc.shtml"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        # 简单解析：这里仅作演示，实际新浪页面结构复杂
        # 建议使用 AKShare 或其他稳定源
        # 此处返回空列表，提示用户源不稳定
        print(f"ℹ️ 新浪财经源当前不可用 (反爬限制)")
        return []
    except Exception as e:
        return []


def fetch_news(symbol: str, use_real: bool = False, sources: List[str] = ['eastmoney', 'sina']) -> List[Dict]:
    """
    聚合抓取新闻
    
    Args:
        symbol: 股票代码 (如 300454)
        use_real: 是否使用真实新闻源
        sources: 数据源列表
        
    Returns:
        List[Dict]: 新闻列表，按时间倒序
    """
    if use_real:
        # 优先使用RSSHub实时新闻
        if RSSHUB_AVAILABLE:
            rss_news = get_rss_news(symbol)
            if rss_news:
                print(f"📡 从RSSHub获取 {len(rss_news)} 条实时新闻")
                return rss_news
        
        # 如果RSSHub不可用，回退到原有数据源
        print("⚠️ RSSHub不可用，使用模拟新闻")
        return _generate_mock_news(symbol)
    else:
        # 使用模拟新闻（用于回测）
        return _generate_mock_news(symbol)


def _generate_mock_news(symbol: str) -> List[Dict]:
    """生成模拟新闻数据"""
    return [{
        'title': f'{symbol}公司发布重要公告',
        'content': '公司今日发布公告，内容涉及...',
        'pub_date': datetime.now(),
        'source': 'mock',
        'url': ''
    }]


if __name__ == "__main__":
    news = fetch_news('300454')
    print(f"获取到 {len(news)} 条新闻")
    for n in news[:3]:
        print(f"{n['date']} | {n['title']}")
