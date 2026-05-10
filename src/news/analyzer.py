"""
新闻情感分析集成模块

功能:
1. 聚合多源新闻 (东方财富 + 新浪)
2. 使用财经词典进行情感分析
3. 生成时间序列情感分数

用法:
    from src.news.analyzer import NewsSentimentAnalyzer
    analyzer = NewsSentimentAnalyzer()
    results = analyzer.analyze_stock('300454')
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List

# 确保 src 目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news.sources import fetch_news
from sentiment.lexicon_analyzer import get_analyzer


class NewsSentimentAnalyzer:
    """新闻情感分析器"""
    
    def __init__(self):
        self.analyzer = get_analyzer()
        
    def analyze_stock(self, symbol: str, days: int = 30) -> List[Dict]:
        """
        分析股票近 N 天新闻情感
        
        Returns:
            List[Dict]: 每日情感汇总
            [
                {'date': '2025-01-01', 'score': 0.6, 'count': 5, 'label': 'positive', 'news': [...]},
                ...
            ]
        """
        # 1. 获取新闻
        print(f"📰 正在抓取 {symbol} 的新闻...")
        news_list = fetch_news(symbol)
        
        if not news_list:
            print("❌ 未获取到新闻数据")
            return []
            
        print(f"✅ 获取到 {len(news_list)} 条新闻")
        
        # 2. 逐条分析情感
        analyzed_news = []
        for news in news_list:
            text = (news.get('title', '') + ' ' + news.get('content', ''))
            result = self.analyzer.analyze(text)
            
            analyzed_news.append({
                'date': news.get('date', ''),
                'title': news.get('title', ''),
                'source': news.get('source', 'unknown'),
                'url': news.get('url', ''),
                'score': result['score'],
                'label': result['label'],
                'keywords': result['keywords'],
                'evidence': result['evidence']
            })
            
        # 3. 按日期聚合 (如果有日期信息)
        # 注意：东方财富的发布时间通常是字符串 "2025-05-10 12:00:00"
        daily_scores = {}
        
        for item in analyzed_news:
            # 提取日期部分
            date_str = str(item['date'])
            if len(date_str) >= 10:
                date_key = date_str[:10]  # YYYY-MM-DD
            else:
                date_key = date_str
                
            if date_key not in daily_scores:
                daily_scores[date_key] = {
                    'date': date_key,
                    'scores': [],
                    'labels': [],
                    'news': []
                }
                
            daily_scores[date_key]['scores'].append(item['score'])
            daily_scores[date_key]['labels'].append(item['label'])
            daily_scores[date_key]['news'].append(item)
            
        # 计算每日平均得分
        daily_results = []
        for date_key, data in sorted(daily_scores.items(), reverse=True):
            avg_score = sum(data['scores']) / len(data['scores'])
            # 多数投票决定标签
            pos = data['labels'].count('positive')
            neg = data['labels'].count('negative')
            neu = data['labels'].count('neutral')
            
            if pos > neg and pos > neu:
                daily_label = 'positive'
            elif neg > pos and neg > neu:
                daily_label = 'negative'
            else:
                daily_label = 'neutral'
                
            daily_results.append({
                'date': date_key,
                'score': round(avg_score, 4),
                'count': len(data['scores']),
                'label': daily_label,
                'news': data['news']
            })
            
        return daily_results


if __name__ == "__main__":
    analyzer = NewsSentimentAnalyzer()
    results = analyzer.analyze_stock('300454')
    
    for day in results[:5]:
        print(f"\n📅 {day['date']} | 分数：{day['score']:.3f} ({day['label']}) | 新闻数：{day['count']}")
        for n in day['news'][:2]:
            print(f"   - {n['title']}")
