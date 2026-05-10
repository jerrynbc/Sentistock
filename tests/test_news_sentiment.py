"""
真实新闻情绪测试 - AKShare 新闻抓取 + SnowNLP 情感分析

测试目标:
1. 验证 AKShare stock_news_em 接口可用性及数据量
2. 测试 SnowNLP 对财经新闻的情感分析效果
3. 探索新闻发布日期与交易日的对齐方式
"""

import akshare as ak
import pandas as pd
from snownlp import SnowNLP
from datetime import datetime
import jieba
import jieba.analyse

def fetch_news(symbol: str, limit: int = 50) -> pd.DataFrame:
    """获取东方财富个股新闻"""
    print(f"📰 正在获取 {symbol} 的新闻...")
    try:
        # stock_news_em 接口: symbol 通常是股票代码
        df = ak.stock_news_em(symbol=symbol)
        print(f"✅ 获取到 {len(df)} 条新闻")
        return df
    except Exception as e:
        print(f"❌ 获取失败：{e}")
        return pd.DataFrame()

def analyze_sentiment(text: str) -> dict:
    """分析文本情感"""
    if not text or pd.isna(text):
        return {'score': 0.5, 'label': 'neutral'}
        
    s = SnowNLP(text)
    score = s.sentiments
    
    # 简单分词提取关键词
    keywords = jieba.analyse.extract_tags(text, topK=5)
    
    if score > 0.6:
        label = 'positive'
    elif score < 0.4:
        label = 'negative'
    else:
        label = 'neutral'
        
    return {'score': score, 'label': label, 'keywords': keywords}

def test_news_analysis(symbol: str = '300454', limit: int = 20):
    """完整测试流程"""
    df = fetch_news(symbol, limit)
    if df.empty:
        return
        
    # 查看列名
    print(f"\n📊 新闻数据列：{df.columns.tolist()}")
    print(df.head(3))
    
    # 情感分析
    print(f"\n{'='*80}")
    print("情感分析结果")
    print(f"{'='*80}")
    
    sentiments = []
    for _, row in df.iterrows():
        content = row.get('新闻内容', '') or row.get('新闻标题', '')
        result = analyze_sentiment(content)
        sentiments.append(result)
        
    df['sentiment_score'] = [s['score'] for s in sentiments]
    df['sentiment_label'] = [s['label'] for s in sentiments]
    df['keywords'] = [', '.join(s['keywords']) for s in sentiments]
    
    # 打印部分结果
    for i, row in df.head(5).iterrows():
        print(f"\n日期：{row.get('发布时间', 'N/A')}")
        print(f"标题：{row.get('新闻标题', 'N/A')}")
        print(f"情感分数：{row['sentiment_score']:.3f} ({row['sentiment_label']})")
        print(f"关键词：{row['keywords']}")
        print("-" * 40)
        
    # 统计
    pos_count = len(df[df['sentiment_label'] == 'positive'])
    neg_count = len(df[df['sentiment_label'] == 'negative'])
    neu_count = len(df[df['sentiment_label'] == 'neutral'])
    
    print(f"\n{'='*80}")
    print("情感分布统计")
    print(f"{'='*80}")
    print(f"正面新闻：{pos_count} 条 ({pos_count/len(df)*100:.1f}%)")
    print(f"负面新闻：{neg_count} 条 ({neg_count/len(df)*100:.1f}%)")
    print(f"中性新闻：{neu_count} 条 ({neu_count/len(df)*100:.1f}%)")
    print(f"平均情感分数：{df['sentiment_score'].mean():.3f}")

if __name__ == "__main__":
    test_news_analysis('300454')  # 深信服
    # test_news_analysis('600519')  # 贵州茅台
