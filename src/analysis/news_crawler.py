"""
新闻爬虫模块

爬取股票相关新闻和舆情数据
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import random


def fetch_news_from_sina(symbol: str, max_pages: int = 3) -> list:
    """
    从新浪财经爬取股票新闻
    
    Args:
        symbol: 股票代码
        max_pages: 最大爬取页数
    
    Returns:
        新闻列表，每条新闻包含标题、时间、链接
    """
    news_list = []
    
    # 新浪财经新闻 API
    base_url = "https://finance.sina.com.cn/stock/relnews/"
    
    # 构造搜索 URL (简化版，实际需要根据股票代码找对应页面)
    search_url = f"https://search.sina.com.cn/?q={symbol}&range=title&c=stock&num=20&page=1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.encoding = 'gbk'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_items = soup.find_all('div', class_='result-list')
        
        for item in news_items:
            title_elem = item.find('h2')
            time_elem = item.find('span', class_='time')
            link_elem = item.find('a')
            
            if title_elem and link_elem:
                news = {
                    'title': title_elem.get_text(strip=True),
                    'time': time_elem.get_text(strip=True) if time_elem else '',
                    'url': link_elem.get('href', ''),
                    'source': '新浪'
                }
                news_list.append(news)
        
        print(f"从新浪获取到 {len(news_list)} 条新闻")
        
    except Exception as e:
        print(f"新浪新闻爬取失败：{e}")
    
    return news_list


def fetch_news_from_eastmoney(symbol: str, max_count: int = 20) -> list:
    """
    从东方财富网爬取股票新闻
    
    Args:
        symbol: 股票代码
        max_count: 最大爬取条数
    
    Returns:
        新闻列表
    """
    news_list = []
    
    # 东方财富个股新闻 API
    url = f"https://newsapi.eastmoney.com/kuaixun/v1/ news/list?stock_code={symbol}&page_size={max_count}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': f'https://quote.eastmoney.com/{symbol}.html'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if 'data' in data and 'content' in data['data']:
            for item in data['data']['content']:
                news = {
                    'title': item.get('Title', ''),
                    'time': item.get('ShowTime', ''),
                    'url': item.get('Url', ''),
                    'source': '东方财富'
                }
                news_list.append(news)
        
        print(f"从东方财富获取到 {len(news_list)} 条新闻")
        
    except Exception as e:
        print(f"东方财富新闻爬取失败：{e}")
        # 尝试备用方案
        news_list = fetch_news_from_eastmoney_web(symbol, max_count)
    
    return news_list


def fetch_news_from_eastmoney_web(symbol: str, max_count: int = 20) -> list:
    """
    从东方财富网网页版爬取新闻 (备用方案)
    """
    news_list = []
    
    url = f"https://quote.eastmoney.com/{symbol}.html"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找新闻链接
        news_links = soup.find_all('a', href=True)
        
        for link in news_links[:max_count * 2]:
            href = link.get('href', '')
            if 'news' in href or 'article' in href:
                title = link.get_text(strip=True)
                if len(title) > 10 and len(title) < 100:
                    news = {
                        'title': title,
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'url': href if href.startswith('http') else f"https://quote.eastmoney.com{href}",
                        'source': '东方财富'
                    }
                    news_list.append(news)
                    
                    if len(news_list) >= max_count:
                        break
        
        print(f"从东方财富网页版获取到 {len(news_list)} 条新闻")
        
    except Exception as e:
        print(f"东方财富网页版爬取失败：{e}")
    
    return news_list


def fetch_news_from_xueqiu() -> list:
    """
    从雪球爬取讨论 (简化版)
    
    Returns:
        讨论列表
    """
    news_list = []
    
    # 雪球热门讨论 (示例)
    url = "https://xueqiu.com/hots/topic/hot"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        if 'list' in data:
            for item in data['list'][:10]:
                news = {
                    'title': item.get('title', ''),
                    'time': item.get('created_at', ''),
                    'url': f"https://xueqiu.com{item.get('target', '')}",
                    'source': '雪球'
                }
                news_list.append(news)
        
        print(f"从雪球获取到 {len(news_list)} 条讨论")
        
    except Exception as e:
        print(f"雪球爬取失败：{e}")
    
    return news_list


def generate_fake_news(symbol: str, stock_name: str = "股票") -> list:
    """
    生成模拟新闻 (用于测试，当爬虫不可用时)
    
    Args:
        symbol: 股票代码
        stock_name: 股票名称
    
    Returns:
        模拟新闻列表
    """
    import random
    
    positive_templates = [
        f"{stock_name}发布重大利好消息，业绩大幅增长",
        f"{stock_name}新产品获得市场认可，订单爆满",
        f"分析师上调{stock_name}目标价，看好长期发展",
        f"{stock_name}签订大额合同，预计增收数亿",
        f"政策利好，{stock_name}所在行业迎来发展机遇",
        f"{stock_name}技术突破，竞争优势明显",
        f"机构调研{stock_name},给予买入评级",
        f"{stock_name}回购股份，彰显发展信心"
    ]
    
    negative_templates = [
        f"{stock_name}业绩不及预期，股价承压",
        f"行业监管加强，{stock_name}面临挑战",
        f"{stock_name}大股东减持，市场担忧",
        f"原材料涨价，{stock_name}利润空间受挤压",
        f"{stock_name}产品出现质量问题，被监管部门约谈",
        f"竞争加剧，{stock_name}市场份额下滑",
        f"{stock_name}高管离职，引发市场猜测",
        f"经济下行压力,{stock_name}订单减少"
    ]
    
    neutral_templates = [
        f"{stock_name}发布季度报告，业绩符合预期",
        f"{stock_name}召开股东大会，审议多项议案",
        f"行业分析师调研{stock_name},了解经营情况",
        f"{stock_name}正常生产经营，无重大事项",
        f"市场波动，{stock_name}股价小幅震荡"
    ]
    
    news_list = []
    
    # 生成 3-5 条正面新闻
    for _ in range(random.randint(3, 5)):
        news_list.append({
            'title': random.choice(positive_templates),
            'time': (datetime.now() - timedelta(days=random.randint(0, 7))).strftime('%Y-%m-%d %H:%M'),
            'url': '#',
            'source': '模拟',
            'sentiment': 'positive'
        })
    
    # 生成 2-4 条负面新闻
    for _ in range(random.randint(2, 4)):
        news_list.append({
            'title': random.choice(negative_templates),
            'time': (datetime.now() - timedelta(days=random.randint(0, 7))).strftime('%Y-%m-%d %H:%M'),
            'url': '#',
            'source': '模拟',
            'sentiment': 'negative'
        })
    
    # 生成 2-3 条中性新闻
    for _ in range(random.randint(2, 3)):
        news_list.append({
            'title': random.choice(neutral_templates),
            'time': (datetime.now() - timedelta(days=random.randint(0, 7))).strftime('%Y-%m-%d %H:%M'),
            'url': '#',
            'source': '模拟',
            'sentiment': 'neutral'
        })
    
    print(f"生成 {len(news_list)} 条模拟新闻")
    
    return news_list


def fetch_all_news(symbol: str, stock_name: str = "股票", use_fake: bool = True) -> tuple:
    """
    获取所有来源的新闻
    
    Args:
        symbol: 股票代码
        stock_name: 股票名称
        use_fake: 是否使用模拟新闻 (爬虫失败时)
    
    Returns:
        (新闻列表，证据链字典)
    """
    all_news = []
    evidence = {
        'sources': [],
        'total_crawled': 0,
        'fake_used': False,
        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    print(f"\n正在获取 {symbol} 的新闻...")
    
    # 尝试从各源获取
    print("\n数据来源:")
    print("-" * 60)
    
    sina_news = fetch_news_from_sina(symbol)
    if sina_news:
        evidence['sources'].append({
            'name': '新浪财经',
            'count': len(sina_news),
            'url': 'https://finance.sina.com.cn/'
        })
        all_news.extend(sina_news)
        print(f"✅ 新浪财经：{len(sina_news)} 条")
    
    eastmoney_news = fetch_news_from_eastmoney(symbol)
    if eastmoney_news:
        evidence['sources'].append({
            'name': '东方财富网',
            'count': len(eastmoney_news),
            'url': 'https://quote.eastmoney.com/'
        })
        all_news.extend(eastmoney_news)
        print(f"✅ 东方财富网：{len(eastmoney_news)} 条")
    
    xueqiu_news = fetch_news_from_xueqiu()
    if xueqiu_news:
        evidence['sources'].append({
            'name': '雪球',
            'count': len(xueqiu_news),
            'url': 'https://xueqiu.com/'
        })
        all_news.extend(xueqiu_news)
        print(f"✅ 雪球：{len(xueqiu_news)} 条")
    
    # 如果爬虫失败，使用模拟新闻
    if len(all_news) < 5 and use_fake:
        print(f"✅ 模拟新闻：使用模拟数据 (真实新闻获取不足)")
        fake_news = generate_fake_news(symbol, stock_name)
        all_news.extend(fake_news)
        evidence['sources'].append({
            'name': '模拟数据',
            'count': len(fake_news),
            'url': 'N/A (仅用于测试)',
            'warning': '模拟新闻非真实数据，仅供参考'
        })
        evidence['fake_used'] = True
    
    evidence['total_crawled'] = len(all_news)
    
    # 去重 (按标题)
    seen = set()
    unique_news = []
    for news in all_news:
        if news['title'] not in seen:
            seen.add(news['title'])
            unique_news.append(news)
    
    evidence['unique_count'] = len(unique_news)
    
    print("-" * 60)
    print(f"共获取到 {len(unique_news)} 条不重复新闻")
    
    return unique_news, evidence


if __name__ == "__main__":
    print("测试新闻爬虫...")
    
    news = fetch_all_news("300454", "深信服")
    
    print("\n前 10 条新闻:")
    for i, n in enumerate(news[:10], 1):
        print(f"{i}. [{n['source']}] {n['title']} ({n['time']})")
