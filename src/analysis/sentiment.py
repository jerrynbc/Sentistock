"""
情感分析模块 - 详细解释版

输出详细的分析过程和原因
"""

from snownlp import SnowNLP
import pandas as pd
from datetime import datetime, timedelta
import jieba
import re


def explain_sentiment_score(text: str) -> dict:
    """
    详细解释情感得分的计算过程
    
    Args:
        text: 要分析的文本
    
    Returns:
        详细的分析结果
    """
    s = SnowNLP(text)
    score = s.sentiments
    
    # 分词
    words = list(s.words)
    
    # 情感分类
    if score > 0.6:
        sentiment = 'positive'
        sentiment_cn = '正面'
        reason = "得分>0.6，表达积极情感"
    elif score < 0.4:
        sentiment = 'negative'
        sentiment_cn = '负面'
        reason = "得分<0.4，表达消极情感"
    else:
        sentiment = 'neutral'
        sentiment_cn = '中性'
        reason = "得分在 0.4-0.6 之间，情感不明显"
    
    # 分析积极/消极词汇
    positive_words = []
    negative_words = []
    
    # 简单的情感词库
    positive_dict = ['利好', '增长', '突破', '机会', '发展', '信心', '上调', '买入', 
                     '优秀', '成功', '受益', '回暖', '复苏', '创新高', '超预期']
    negative_dict = ['风险', '下跌', '亏损', '下滑', '担忧', '减持', '暴跌', '崩盘',
                     '不及预期', '承压', '挑战', '困境', '恶化', '违约', '调查']
    
    for word in words:
        if word in positive_dict:
            positive_words.append(word)
        if word in negative_dict:
            negative_words.append(word)
    
    # 分析句子结构
    if '不' in text:
        reason += "；包含否定词'不'，可能影响情感"
    if '？' in text:
        reason += "；包含问号，表示疑问"
    if '!' in text:
        reason += "；包含感叹号，情感强烈"
    
    return {
        'score': round(score, 3),
        'sentiment': sentiment,
        'sentiment_cn': sentiment_cn,
        'reason': reason,
        'words': words,
        'positive_words': positive_words,
        'negative_words': negative_words,
        'keywords': s.keywords(3)
    }


def analyze_single_sentiment(text: str, explain: bool = True) -> dict:
    """
    分析单个文本的情感，可选择输出详细解释
    
    Args:
        text: 要分析的文本
        explain: 是否输出详细解释
    
    Returns:
        情感分析结果
    """
    s = SnowNLP(text)
    score = s.sentiments
    
    if score > 0.6:
        sentiment = 'positive'
        sentiment_cn = '正面'
    elif score < 0.4:
        sentiment = 'negative'
        sentiment_cn = '负面'
    else:
        sentiment = 'neutral'
        sentiment_cn = '中性'
    
    result = {
        'score': round(score, 3),
        'sentiment': sentiment,
        'sentiment_cn': sentiment_cn,
        'keywords': s.keywords(3)
    }
    
    if explain:
        explanation = explain_sentiment_score(text)
        result['explanation'] = explanation
    
    return result


def analyze_news_sentiment(news_list: list, show_explanation: bool = True) -> list:
    """
    批量分析新闻情感，输出详细解释
    
    Args:
        news_list: 新闻列表
        show_explanation: 是否显示详细解释
    
    Returns:
        添加了情感分析结果的新闻列表
    """
    print(f"\n{'='*60}")
    print("逐条新闻情感分析")
    print(f"{'='*60}\n")
    
    analyzed_news = []
    
    for i, news in enumerate(news_list, 1):
        result = analyze_single_sentiment(news['title'], explain=show_explanation)
        
        analyzed_news.append({
            **news,
            'sentiment_score': result['score'],
            'sentiment': result['sentiment'],
            'sentiment_cn': result['sentiment_cn'],
            'keywords': result['keywords']
        })
        
        if show_explanation:
            emoji = '🟢' if result['sentiment'] == 'positive' else ('🔴' if result['sentiment'] == 'negative' else '⚪')
            print(f"{i}. {emoji} 新闻标题：{news['title']}")
            print(f"   情感得分：{result['score']}")
            print(f"   情感分类：{result['sentiment_cn']}")
            
            if 'explanation' in result:
                exp = result['explanation']
                if exp['positive_words']:
                    print(f"   积极词汇：{', '.join(exp['positive_words'])} → 推高分数")
                if exp['negative_words']:
                    print(f"   消极词汇：{', '.join(exp['negative_words'])} → 拉低分数")
                print(f"   分析原因：{exp['reason']}")
            
            print()
        
        if i % 5 == 0:
            print(f"[进度] 已分析 {i}/{len(news_list)} 条\n")
    
    return analyzed_news


def explain_overall_sentiment(analyzed_news: list) -> str:
    """
    解释整体情绪指数的计算过程
    
    Args:
        analyzed_news: 已分析的新闻列表
    
    Returns:
        解释文本
    """
    if not analyzed_news:
        return "数据为空"
    
    total = len(analyzed_news)
    positive = sum(1 for n in analyzed_news if n['sentiment'] == 'positive')
    negative = sum(1 for n in analyzed_news if n['sentiment'] == 'negative')
    neutral = sum(1 for n in analyzed_news if n['sentiment'] == 'neutral')
    
    overall_score = sum(n['sentiment_score'] for n in analyzed_news) / total
    
    explanation = []
    explanation.append("【整体情绪指数计算过程】")
    explanation.append("")
    explanation.append(f"1️⃣ 统计数据:")
    explanation.append(f"   - 总新闻数：{total} 条")
    explanation.append(f"   - 正面新闻：{positive} 条 ({positive/total*100:.1f}%)")
    explanation.append(f"   - 中性新闻：{neutral} 条 ({neutral/total*100:.1f}%)")
    explanation.append(f"   - 负面新闻：{negative} 条 ({negative/total*100:.1f}%)")
    explanation.append("")
    
    explanation.append(f"2️⃣ 计算平均分:")
    explanation.append(f"   整体得分 = 所有新闻情感得分的总和 ÷ 新闻总数")
    explanation.append(f"   整体得分 = {sum(n['sentiment_score'] for n in analyzed_news):.3f} ÷ {total}")
    explanation.append(f"   整体得分 = {overall_score:.3f}")
    explanation.append("")
    
    if overall_score > 0.7:
        level = '非常乐观'
        reason = f"得分 {overall_score:.3f} > 0.7，说明绝大多数新闻都是正面的"
    elif overall_score > 0.55:
        level = '谨慎乐观'
        reason = f"得分 {overall_score:.3f} 在 0.55-0.7 之间，正面新闻多于负面新闻"
    elif overall_score > 0.45:
        level = '中性'
        reason = f"得分 {overall_score:.3f} 在 0.45-0.55 之间，正面和负面新闻相当"
    elif overall_score > 0.3:
        level = '谨慎悲观'
        reason = f"得分 {overall_score:.3f} 在 0.3-0.45 之间，负面新闻多于正面新闻"
    else:
        level = '非常悲观'
        reason = f"得分 {overall_score:.3f} < 0.3，说明绝大多数新闻都是负面的"
    
    explanation.append(f"3️⃣ 判断情绪等级:")
    explanation.append(f"   - {level}")
    explanation.append(f"   - 原因：{reason}")
    explanation.append("")
    
    # 判断趋势
    if positive > negative * 1.5:
        trend = '乐观'
        trend_reason = f"正面新闻 ({positive}) 远多于负面新闻 ({negative})"
    elif negative > positive * 1.5:
        trend = '悲观'
        trend_reason = f"负面新闻 ({negative}) 远多于正面新闻 ({positive})"
    else:
        trend = '平稳'
        trend_reason = f"正面 ({positive}) 和负面 ({negative}) 新闻数量相近"
    
    explanation.append(f"4️⃣ 判断情绪趋势:")
    explanation.append(f"   - {trend}")
    explanation.append(f"   - 原因：{trend_reason}")
    explanation.append("")
    
    explanation.append(f"5️⃣ 投资建议:")
    if level == '非常乐观':
        explanation.append(f"   ⚠️ 情绪过于乐观，可能是阶段性高点，注意风险")
    elif level == '谨慎乐观':
        explanation.append(f"   ✅ 情绪偏向积极，可以继续持有，但要注意止损")
    elif level == '中性':
        explanation.append(f"   ⚪ 情绪中性，方向不明，建议观望")
    elif level == '谨慎悲观':
        explanation.append(f"   ⚠️ 情绪偏向消极，考虑减仓或观望")
    else:  # 非常悲观
        explanation.append(f"   ✨ 情绪极度悲观，可能是买入机会 (别人恐惧我贪婪)")
    
    return "\n".join(explanation)


def calculate_sentiment_index(analyzed_news: list, explain: bool = True) -> dict:
    """
    计算情绪指数，可选择输出解释
    
    Args:
        analyzed_news: 已分析的新闻列表
        explain: 是否输出解释
    
    Returns:
        情绪指数字典
    """
    if not analyzed_news:
        return {
            'overall_score': 0.5,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'total_count': 0,
            'trend': 'stable',
            'level': 'neutral',
            'explanation': '数据为空'
        }
    
    positive_count = sum(1 for n in analyzed_news if n['sentiment'] == 'positive')
    negative_count = sum(1 for n in analyzed_news if n['sentiment'] == 'negative')
    neutral_count = sum(1 for n in analyzed_news if n['sentiment'] == 'neutral')
    total_count = len(analyzed_news)
    
    overall_score = sum(n['sentiment_score'] for n in analyzed_news) / total_count
    
    if overall_score > 0.7:
        level = 'very_positive'
        level_cn = '非常乐观'
    elif overall_score > 0.55:
        level = 'positive'
        level_cn = '谨慎乐观'
    elif overall_score > 0.45:
        level = 'neutral'
        level_cn = '中性'
    elif overall_score > 0.3:
        level = 'negative'
        level_cn = '谨慎悲观'
    else:
        level = 'very_negative'
        level_cn = '非常悲观'
    
    if positive_count > negative_count * 1.5:
        trend = 'bullish'
        trend_cn = '乐观'
    elif negative_count > positive_count * 1.5:
        trend = 'bearish'
        trend_cn = '悲观'
    else:
        trend = 'stable'
        trend_cn = '平稳'
    
    result = {
        'overall_score': round(overall_score, 3),
        'positive_count': positive_count,
        'negative_count': negative_count,
        'neutral_count': neutral_count,
        'total_count': total_count,
        'trend': trend,
        'trend_cn': trend_cn,
        'level': level,
        'level_cn': level_cn
    }
    
    if explain:
        result['explanation'] = explain_overall_sentiment(analyzed_news)
    
    return result


def full_sentiment_analysis(news_list: list, price_data: pd.DataFrame = None, 
                           show_explanation: bool = True) -> dict:
    """
    完整的情绪分析流程，输出详细解释
    
    Args:
        news_list: 新闻列表
        price_data: 价格数据
        show_explanation: 是否显示详细解释
    
    Returns:
        完整分析结果
    """
    print("\n" + "="*60)
    print("Phase 3: 情绪分析 - 详细版")
    print("="*60)
    
    # 逐条分析
    analyzed_news = analyze_news_sentiment(news_list, show_explanation=show_explanation)
    
    # 计算整体情绪指数
    sentiment_index = calculate_sentiment_index(analyzed_news, explain=show_explanation)
    
    if show_explanation:
        print("\n" + "="*60)
        print(sentiment_index['explanation'])
        print("="*60)
    
    # 关键词分析
    from collections import Counter
    all_keywords = []
    for news in analyzed_news:
        all_keywords.extend(news.get('keywords', []))
    keyword_counts = Counter(all_keywords)
    keywords = keyword_counts.most_common(10)
    
    # 时间线
    timeline = pd.DataFrame()  # 简化
    
    # 相关性分析
    correlation = {'correlation': 0, 'interpretation': '未提供价格数据'}
    
    # 生成报告
    report = []
    report.append("=" * 60)
    report.append("情绪分析报告 (详细版)")
    report.append("=" * 60)
    report.append("")
    report.append(f"统计范围：{sentiment_index['total_count']} 条新闻")
    report.append(f"整体情绪得分：{sentiment_index['overall_score']} (0-1, 越高越正面)")
    report.append(f"情绪等级：{sentiment_index['level_cn']}")
    report.append(f"情绪趋势：{sentiment_index['trend_cn']}")
    report.append("")
    report.append("情感分布:")
    report.append(f"  正面：{sentiment_index['positive_count']} 条 ({sentiment_index['positive_count']/sentiment_index['total_count']*100:.1f}%)")
    report.append(f"  中性：{sentiment_index['neutral_count']} 条 ({sentiment_index['neutral_count']/sentiment_index['total_count']*100:.1f}%)")
    report.append(f"  负面：{sentiment_index['negative_count']} 条 ({sentiment_index['negative_count']/sentiment_index['total_count']*100:.1f}%)")
    report.append("")
    
    if keywords:
        report.append("高频关键词:")
        for kw, count in keywords:
            report.append(f"  - {kw}: {count}次")
    
    report.append("\n" + "=" * 60)
    
    # 打印详细解释
    if show_explanation:
        print("\n" + "\n".join(report))
    
    return {
        'analyzed_news': analyzed_news,
        'sentiment_index': sentiment_index,
        'keywords': keywords,
        'timeline': timeline,
        'correlation': correlation,
        'report': "\n".join(report)
    }


if __name__ == "__main__":
    from src.analysis.news_crawler import generate_fake_news
    
    print("测试情感分析模块 (详细解释版)...\n")
    
    news = generate_fake_news("300454", "深信服")
    
    result = full_sentiment_analysis(news, show_explanation=True)
