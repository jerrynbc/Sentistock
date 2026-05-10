"""
真实新闻情绪测试 - 词典情感分析 vs SnowNLP

测试目标:
1. 验证财经词典情感分析的准确度
2. 对比 SnowNLP 的效果
3. 查看多源新闻获取情况
"""

import sys
import os
# Add src to path
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
sys.path.insert(0, src_path)

from news.sources import fetch_news
from sentiment.lexicon_analyzer import get_analyzer
from snownlp import SnowNLP

def compare_sentiment(symbol: str = '300454'):
    """对比两种情感分析方法"""
    # 获取新闻
    news_list = fetch_news(symbol)
    if not news_list:
        print("❌ 未获取到新闻")
        return
        
    analyzer = get_analyzer()
    
    print(f"\n{'='*80}")
    print(f"情感分析对比 ({symbol})")
    print(f"{'='*80}")
    print(f"{'标题':<40} | {'词典法':<8} | {'SnowNLP':<8}")
    print("-" * 90)
    
    for news in news_list[:10]:
        text = news.get('title', '') + ' ' + (news.get('content', '') or '')[:50]
        
        # 词典法
        lex_res = analyzer.analyze(text)
        lex_score = f"{lex_res['score']:.2f} ({lex_res['label'][0]})"
        
        # SnowNLP
        snow_res = SnowNLP(text).sentiments
        snow_score = f"{snow_res:.2f} ({'P' if snow_res > 0.6 else 'N' if snow_res < 0.4 else 'M'})"
        
        print(f"{news['title'][:30]:<40} | {lex_score:<8} | {snow_score:<8}")
        
    print("\n词典法优势:")
    print("✅ 能识别财经关键词 (如：亏损=负面，回购=正面)")
    print("✅ 结合程度副词 (如：大幅下跌 > 下跌)")
    print("✅ 不受通用语料干扰")

if __name__ == "__main__":
    compare_sentiment('300454')
    compare_sentiment('600519')
