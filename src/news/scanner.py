"""
实时舆情监控

功能:
1. 扫描关注股票的最新新闻情感
2. 生成今日信号 (买入/卖出/观望)
3. 异动预警 (连续负面新闻、突发利空)

用法:
    from src.news.scanner import SentimentScanner
    scanner = SentimentScanner()
    scanner.scan(['300454', '600519', '000001'])
"""

import sys
import os
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news.sources import fetch_news
from sentiment.lexicon_analyzer import get_analyzer


class SentimentScanner:
    """实时舆情监控器"""
    
    # 信号阈值
    BUY_THRESHOLD = 0.60    # 平均情感 > 0.60 → 买入信号
    SELL_THRESHOLD = 0.40   # 平均情感 < 0.40 → 卖出信号
    ALERT_NEGATIVE_COUNT = 3  # 连续 3 条负面新闻 → 预警
    
    def __init__(self, use_real_news: bool = False):
        self.analyzer = get_analyzer()
        self.use_real_news = use_real_news
        
    def scan_single(self, symbol: str) -> Dict:
        """扫描单只股票"""
        # 获取新闻
        news_list = fetch_news(symbol, use_real=self.use_real_news)
        if not news_list:
            return {
                'symbol': symbol,
                'status': 'no_news',
                'signal': '观望',
                'avg_score': 0.5,
                'news_count': 0,
                'alerts': [],
                'news': []
            }
            
        # 分析每条新闻
        analyzed = []
        for news in news_list:
            text = (news.get('title', '') + ' ' + (news.get('content', '') or ''))
            result = self.analyzer.analyze(text)
            
            analyzed.append({
                'title': news.get('title', ''),
                'date': news.get('date', ''),
                'source': news.get('source', 'unknown'),
                'score': result['score'],
                'label': result['label'],
                'evidence': result['evidence'],
                'url': news.get('url', '')
            })
            
        # 统计
        scores = [n['score'] for n in analyzed]
        avg_score = sum(scores) / len(scores)
        
        pos_count = sum(1 for n in analyzed if n['label'] == 'positive')
        neg_count = sum(1 for n in analyzed if n['label'] == 'negative')
        neu_count = sum(1 for n in analyzed if n['label'] == 'neutral')
        
        # 生成信号
        if avg_score >= self.BUY_THRESHOLD:
            signal = '买入'
        elif avg_score <= self.SELL_THRESHOLD:
            signal = '卖出'
        else:
            signal = '观望'
            
        # 预警检查
        alerts = []
        
        # 1. 负面新闻占比过高
        if neg_count > len(analyzed) * 0.6:
            alerts.append(f"⚠️ 负面新闻占比过高：{neg_count}/{len(analyzed)} ({neg_count/len(analyzed)*100:.0f}%)")
            
        # 2. 连续负面新闻 (按时间排序)
        sorted_news = sorted(analyzed, key=lambda x: x.get('date', ''), reverse=True)
        consecutive_neg = 0
        for n in sorted_news:
            if n['label'] == 'negative':
                consecutive_neg += 1
                if consecutive_neg >= self.ALERT_NEGATIVE_COUNT:
                    alerts.append(f"🚨 连续 {consecutive_neg} 条负面新闻，注意风险")
                    break
            else:
                consecutive_neg = 0
                
        # 3. 极端情感
        very_neg = [n for n in analyzed if n['score'] < 0.3]
        if very_neg:
            alerts.append(f"🔴 发现 {len(very_neg)} 条极度负面新闻")
            
        return {
            'symbol': symbol,
            'status': 'ok',
            'signal': signal,
            'avg_score': round(avg_score, 4),
            'news_count': len(analyzed),
            'pos_count': pos_count,
            'neg_count': neg_count,
            'neu_count': neu_count,
            'alerts': alerts,
            'news': analyzed
        }
        
    def scan(self, symbols: List[str]) -> List[Dict]:
        """批量扫描"""
        print(f"\n{'='*80}")
        print(f"📡 实时舆情扫描")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"股票数：{len(symbols)}")
        print(f"{'='*80}")
        
        results = []
        for symbol in symbols:
            print(f"\n📊 扫描 {symbol}...")
            result = self.scan_single(symbol)
            results.append(result)
            self._print_single_result(result)
            
        # 汇总
        self._print_summary(results)
        
        return results
        
    def _print_single_result(self, result: Dict):
        """打印单只结果"""
        symbol = result['symbol']
        signal = result['signal']
        score = result['avg_score']
        
        if signal == '买入':
            icon = '🟢'
        elif signal == '卖出':
            icon = '🔴'
        else:
            icon = '🟡'
            
        print(f"  {icon} 信号：{signal} | 情感分：{score:.3f} | 新闻数：{result['news_count']}")
        
        if result['pos_count'] > 0:
            print(f"     正面：{result['pos_count']} | 负面：{result['neg_count']} | 中性：{result['neu_count']}")
            
        for alert in result.get('alerts', []):
            print(f"     {alert}")
            
        # 打印最新 3 条新闻
        for n in result.get('news', [])[:3]:
            print(f"     - [{n['label']}] {n['title']}")
            
    def _print_summary(self, results: List[Dict]):
        """打印汇总"""
        buy_count = sum(1 for r in results if r['signal'] == '买入')
        sell_count = sum(1 for r in results if r['signal'] == '卖出')
        wait_count = sum(1 for r in results if r['signal'] == '观望')
        alert_count = sum(len(r.get('alerts', [])) for r in results)
        
        print(f"\n{'='*80}")
        print(f"📊 汇总统计")
        print(f"{'='*80}")
        print(f"🟢 买入信号：{buy_count} 只")
        print(f"🔴 卖出信号：{sell_count} 只")
        print(f"🟡 观望：{wait_count} 只")
        print(f"⚠️ 预警数：{alert_count}")
        
        # 高风险股票
        risky = [r for r in results if r.get('alerts')]
        if risky:
            print(f"\n⚠️ 需要关注的股票：")
            for r in risky:
                print(f"  {r['symbol']}：{len(r['alerts'])} 条预警")


if __name__ == "__main__":
    scanner = SentimentScanner()
    scanner.scan(['300454', '600519', '000001'])
