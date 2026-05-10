"""
Stock Analyzer - Phase 3: 情绪分析

运行示例:
    python src/main.py 000001
"""

import sys
from src.data.collector import get_stock_history, get_stock_info
from src.visual.charts import plot_price_with_volume
from src.analysis.indicators import calculate_all_indicators, generate_signals
from src.visual.indicator_charts import plot_all_indicators
from src.analysis.news_crawler import fetch_all_news, generate_fake_news
from src.analysis.sentiment import full_sentiment_analysis
from src.visual.sentiment_charts import plot_all_sentiment_charts


def print_signals(df):
    """打印最近的买卖信号"""
    signals = df[df['signal'] != 0].tail(5)
    
    if len(signals) == 0:
        print("\n最近没有买卖信号")
        return
    
    print("\n" + "=" * 60)
    print("最近买卖信号")
    print("=" * 60)
    
    for idx, row in signals.iterrows():
        signal_type = '买入' if row['signal'] == 1 else '卖出'
        print(f"{row['日期']} | {signal_type} | {row['signal_type']} | 价格：{row['收盘']:.2f}")


def main():
    if len(sys.argv) < 2:
        print("用法：python src/main.py <股票代码>")
        print("示例：python src/main.py 000001  (平安银行)")
        sys.exit(1)
    
    symbol = sys.argv[1]
    
    print("=" * 60)
    print(f"股票分析器 - Phase 3: 情绪分析")
    print("=" * 60)
    print(f"\n正在分析股票：{symbol}")
    
    df = get_stock_history(symbol)
    
    if df.empty:
        print("获取数据失败，请检查股票代码是否正确")
        sys.exit(1)
    
    info = get_stock_info(symbol)
    
    if info:
        print("\n" + "=" * 60)
        print("股票基本信息")
        print("=" * 60)
        for key, value in info.items():
            print(f"{key}: {value}")
    
    print("\n" + "=" * 60)
    print("计算技术指标...")
    print("=" * 60)
    
    df = calculate_all_indicators(df)
    
    print("指标计算完成:")
    print("  - MA5, MA10, MA20 (移动平均线)")
    print("  - MACD (DIF, DEA, Histogram)")
    print("  - RSI (相对强弱指标)")
    print("  - Bollinger Bands (布林带)")
    print("  - 买卖信号")
    
    # Phase 3: 情绪分析
    print("\n" + "=" * 60)
    print("Phase 3: 情绪分析")
    print("=" * 60)
    
    stock_name = info.get('股票简称', symbol)
    
    # 获取新闻 (返回新闻列表和证据链)
    print("\n获取新闻...")
    news, evidence = fetch_all_news(symbol, stock_name, use_fake=True)
    
    if not news:
        print("未能获取新闻，使用模拟新闻...")
        news = generate_fake_news(symbol, stock_name)
        evidence = {
            'sources': [{'name': '模拟数据', 'count': len(news), 'url': 'N/A'}],
            'total_crawled': len(news),
            'fake_used': True
        }
    
    # 打印证据链
    print("\n" + "="*60)
    print("新闻证据链")
    print("="*60)
    print(f"\n采集时间：{evidence.get('crawl_time', 'N/A')}")
    print(f"\n数据来源:")
    for source in evidence['sources']:
        print(f"  • {source['name']}: {source['count']} 条")
        print(f"    网址：{source['url']}")
        if source.get('warning'):
            print(f"    ⚠️ {source['warning']}")
    
    print(f"\n总新闻数：{evidence.get('unique_count', len(news))} 条")
    print(f"\n完整新闻列表:")
    print("-"*60)
    for i, n in enumerate(news, 1):
        print(f"{i}. {n['title']}")
        print(f"   来源：{n['source']} | 时间：{n['time']}")
        if n.get('url') and n['url'] != '#':
            print(f"   链接：{n['url']}")
    print("-"*60)
    
    # 情感分析
    print("\n进行情感分析...")
    sentiment_result = full_sentiment_analysis(news, df)
    
    # 打印情绪报告
    print("\n" + sentiment_result['report'])
    
    # 显示前 10 条新闻
    print("\n" + "=" * 60)
    print("前 10 条新闻情感分析")
    print("=" * 60)
    for i, n in enumerate(sentiment_result['analyzed_news'][:10], 1):
        emoji = '🟢' if n['sentiment'] == 'positive' else ('🔴' if n['sentiment'] == 'negative' else '⚪')
        print(f"{i}. {emoji} {n['title']}")
        print(f"   情感得分：{n['sentiment_score']} | 分类：{n['sentiment_cn']}")
        print(f"   关键词：{', '.join(n.get('keywords', []))}")
        if 'explanation' in n:
            exp = n['explanation']
            if exp.get('positive_words'):
                print(f"   积极词汇：{', '.join(exp['positive_words'])} → 推高分数")
            if exp.get('negative_words'):
                print(f"   消极词汇：{', '.join(exp['negative_words'])} → 拉低分数")
            print(f"   原因：{exp.get('reason', '')}")
    
    print("\n" + "=" * 60)
    print("最近 5 个交易日数据")
    print("=" * 60)
    print(df[['日期', '收盘', 'DIF', 'DEA', 'RSI', 'BB_upper', 'BB_lower']].tail())
    
    latest_price = df['收盘'].iloc[-1]
    latest_macd = df['DIF'].iloc[-1]
    latest_dea = df['DEA'].iloc[-1]
    latest_rsi = df['RSI'].iloc[-1]
    
    print(f"\n最新收盘价：{latest_price:.2f}")
    print(f"MACD: {latest_macd:.4f}")
    print(f"DEA: {latest_dea:.4f}")
    print(f"RSI: {latest_rsi:.2f}")
    
    if latest_rsi > 70:
        print("⚠️ RSI > 70 - 超买区 (可能回调)")
    elif latest_rsi < 30:
        print("⚠️ RSI < 30 - 超卖区 (可能反弹)")
    else:
        print(f"RSI 位于正常区域")
    
    if latest_macd > latest_dea:
        print("MACD: 多头 (DIF > DEA)")
    else:
        print("MACD: 空头 (DIF < DEA)")
    
    print_signals(df)
    
    print("\n" + "=" * 60)
    print("正在绘制技术指标图表...")
    print("=" * 60)
    
    stock_name = info.get('股票简称', symbol)
    plot_all_indicators(
        df,
        title=f"{stock_name} ({symbol}) - 技术指标分析",
        save_path=f"{symbol}_indicators.png"
    )
    
    print("\n" + "=" * 60)
    print("正在绘制情绪分析图表...")
    print("=" * 60)
    
    plot_all_sentiment_charts(
        sentiment_result['timeline'],
        sentiment_result['analyzed_news'],
        sentiment_result['keywords'],
        df,
        title=f"{stock_name} ({symbol}) - 情绪分析",
        save_path=f"{symbol}_sentiment.png"
    )
    
    print(f"\n分析完成!")
    print(f"技术指标图表：{symbol}_indicators.png")
    print(f"情绪分析图表：{symbol}_sentiment.png")
    print("=" * 60)
    
    # 保存完整证据链到文件
    print("\n" + "=" * 60)
    print("保存分析报告...")
    print("=" * 60)
    
    from datetime import datetime
    report_content = []
    report_content.append("=" * 80)
    report_content.append(f"股票分析报告 - {stock_name} ({symbol})")
    report_content.append(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_content.append("=" * 80)
    report_content.append("")
    
    # 股票基本信息
    report_content.append("【一、股票基本信息】")
    report_content.append("-" * 80)
    for key, value in info.items():
        report_content.append(f"{key}: {value}")
    report_content.append("")
    
    # 技术指标摘要
    report_content.append("【二、技术指标摘要】")
    report_content.append("-" * 80)
    report_content.append(f"最新收盘价：{latest_price:.2f}")
    report_content.append(f"MACD: DIF={latest_macd:.4f}, DEA={latest_dea:.4f} → {'多头' if latest_macd > latest_dea else '空头'}")
    report_content.append(f"RSI: {latest_rsi:.2f} → {'超买' if latest_rsi > 70 else ('超卖' if latest_rsi < 30 else '正常')}")
    report_content.append("")
    
    # 完整新闻证据链
    report_content.append("【三、完整新闻证据链】")
    report_content.append("-" * 80)
    report_content.append(f"数据来源：{', '.join([s['name'] for s in evidence['sources']])}")
    report_content.append(f"总新闻数：{evidence.get('unique_count', len(news))} 条")
    report_content.append("")
    report_content.append("完整新闻列表:")
    for i, n in enumerate(news, 1):
        report_content.append(f"\n{i}. 标题：{n['title']}")
        report_content.append(f"   来源：{n['source']}")
        report_content.append(f"   时间：{n['time']}")
        report_content.append(f"   链接：{n.get('url', 'N/A')}")
    report_content.append("")
    
    # 情感分析详情
    report_content.append("【四、情感分析详情】")
    report_content.append("-" * 80)
    report_content.append(sentiment_result['report'])
    report_content.append("")
    
    # 各新闻情感得分
    report_content.append("【五、各条新闻情感得分详情】")
    report_content.append("-" * 80)
    for i, n in enumerate(sentiment_result['analyzed_news'], 1):
        report_content.append(f"\n{i}. {n['title']}")
        report_content.append(f"   情感得分：{n['sentiment_score']}")
        report_content.append(f"   情感分类：{n['sentiment_cn']}")
        if 'explanation' in n:
            exp = n['explanation']
            if exp.get('positive_words'):
                report_content.append(f"   积极词汇：{', '.join(exp['positive_words'])}")
            if exp.get('negative_words'):
                report_content.append(f"   消极词汇：{', '.join(exp['negative_words'])}")
            report_content.append(f"   分析原因：{exp.get('reason', '')}")
    report_content.append("")
    
    # 综合结论
    report_content.append("【六、综合结论】")
    report_content.append("-" * 80)
    sentiment_index = sentiment_result['sentiment_index']
    report_content.append(f"情绪指数：{sentiment_index['overall_score']} ({sentiment_index['level_cn']})")
    report_content.append(f"情绪趋势：{sentiment_index['trend_cn']}")
    report_content.append("")
    report_content.append("综合判断:")
    report_content.append(f"  - 技术面：{'🟢 多头' if latest_macd > latest_dea else '🔴 空头'}")
    report_content.append(f"  - 情绪面：{'🟢' if sentiment_index['overall_score'] > 0.6 else ('🔴' if sentiment_index['overall_score'] < 0.4 else '🟡')} {sentiment_index['level_cn']}")
    report_content.append("")
    report_content.append("⚠️ 免责声明：本报告仅供参考，不构成投资建议。股市有风险，投资需谨慎。")
    report_content.append("")
    report_content.append("=" * 80)
    
    # 写入文件
    report_filename = f"{stock_name}_{symbol}_分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_content))
    
    print(f"分析报告已保存到：{report_filename}")
    print("=" * 60)


if __name__ == "__main__":
    main()
