"""
回测情感集成模块

功能:
1. 抓取股票新闻并计算情感分数
2. 将不规则的新闻日期对齐到交易日
3. 与回测框架集成

对齐策略:
- 交易日有新闻：使用当日新闻平均分
- 交易日无新闻：
  - 策略 A：使用前值填充 (Forward Fill) - 假设情绪持续
  - 策略 B：使用技术指标模拟值作为 Fallback
"""

import sys
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from news.sources import fetch_news
from sentiment.lexicon_analyzer import get_analyzer


def generate_sentiment_series(
    trade_dates: List[str], 
    symbol: str,
    fallback_method: str = 'ffill'
) -> pd.Series:
    """
    生成与交易日对齐的情感分数序列
    
    Args:
        trade_dates: 交易日列表 (YYYY-MM-DD)
        symbol: 股票代码
        fallback_method: 缺失日期的填充策略 ('ffill' | None)
        
    Returns:
        pd.Series: index=trade_dates, value=sentiment_score (0~1)
    """
    # 1. 获取新闻
    news_list = fetch_news(symbol)
    if not news_list:
        return pd.Series(index=trade_dates, data=0.5)  # 默认中性
        
    # 2. 分析新闻情感
    daily_scores = {}
    analyzer = get_analyzer()
    
    for news in news_list:
        date_str = str(news.get('date', ''))[:10]  # YYYY-MM-DD
        text = (news.get('title', '') + ' ' + (news.get('content', '') or ''))
        
        res = analyzer.analyze(text)
        
        if date_str not in daily_scores:
            daily_scores[date_str] = []
        daily_scores[date_str].append(res['score'])
        
    # 计算每日平均分
    avg_daily = {d: sum(scores)/len(scores) for d, scores in daily_scores.items()}
    
    # 3. 对齐交易日
    sentiment_series = pd.Series(index=trade_dates, dtype=float)
    
    for date in trade_dates:
        if date in avg_daily:
            sentiment_series[date] = avg_daily[date]
        else:
            sentiment_series[date] = None
            
    # 4. 填充缺失值
    if fallback_method == 'ffill':
        sentiment_series = sentiment_series.ffill()
        sentiment_series.fillna(0.5, inplace=True)  # 头部缺失补中性
    else:
        sentiment_series.fillna(0.5, inplace=True)
        
    return sentiment_series


if __name__ == "__main__":
    # 测试：获取最近 10 个交易日
    import akshare as ak
    df = ak.stock_zh_a_hist(symbol="300454", period="daily", adjust="qfq")
    df['日期'] = df['日期'].astype(str)
    trade_dates = df['日期'].tolist()[-20:]  # 最近 20 天
    
    series = generate_sentiment_series(trade_dates, '300454')
    print(series.tail(10))
