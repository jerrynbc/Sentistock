"""
舆情监控守护进程 (Monitor Daemon)

功能:
1. 定时扫描关注列表股票的新闻
2. 记录历史数据到 Memory
3. 计算舆情加速度，触发预警
4. 检查持仓状态，给出卖出建议

用法:
    python src/core/monitor.py --symbols 300454 600519 --interval 30
"""

print("🚀 Monitor module loaded!")
import sys
import os
import time
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from news.scanner import SentimentScanner
from db.memory import SentimentMemory


class MonitorDaemon:
    """舆情监控后台服务"""
    
    def __init__(self, symbols: list, interval_minutes: int = 30):
        self.symbols = symbols
        self.interval = interval_minutes * 60
        self.scanner = SentimentScanner(use_real_news=True) # 启用真实新闻
        self.memory = SentimentMemory()
        
        # 舆情熔断阈值
        self.KILL_SWITCH = 0.35
        self.RAPID_DECLINE_THRESHOLD = -0.2 # 2小时内下降0.2分
        
    def run(self):
        print(f"🤖 启动舆情监控守护进程...")
        print(f"监控列表：{', '.join(self.symbols)}")
        print(f"扫描间隔：{self.interval // 60} 分钟")
        print("-" * 60)
        
        try:
            while True:
                self._scan_cycle()
                print(f"\n💤 休眠 {self.interval // 60} 分钟，等待下一次扫描...")
                print(f"下次扫描时间：{datetime.now().strftime('%H:%M:%S')}")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\n🛑 监控已手动停止")
            
    def _scan_cycle(self):
        print(f"============================================================")
        print(f"📡 扫描开始：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"============================================================")
        for symbol in self.symbols:
            self._check_symbol(symbol)
        print("💤 等待下次扫描...")
            
    def _check_symbol(self, symbol: str):
        """检查单只股票"""
        # 1. 扫描新闻
        result = self.scanner.scan_single(symbol)
        
        if result['status'] == 'no_news':
            print(f"ℹ️ {symbol}: 无新闻更新")
            return
            
        # 2. 提取数据
        score = result['avg_score']
        goodness = score / 100.0 # 归一化到0-1
        news_count = result['news_count']
        # 提取最新的负面关键词
        neg_keywords = []
        for n in result.get('news', []):
            if n.get('label') == 'negative':
                # 简单分析提取关键词，这里复用 analyzer
                from sentiment.lexicon_analyzer import get_analyzer
                analyzer = get_analyzer()
                res = analyzer.analyze(n.get('title', '') + ' ' + (n.get('content', '') or ''))
                neg_keywords.extend([e['word'] for e in res.get('evidence', []) if e.get('polarity') == 'negative'])
        
        # 3. 记录到 Memory
        self.memory.record(
            symbol=symbol, 
            score=goodness, # 存储归一化后的分数
            news_count=news_count, 
            negative_keywords=list(set(neg_keywords)), # 去重
            signal=result['signal']
        )
        
        # 4. 检查舆情加速度 (2小时)
        velocity = self.memory.get_velocity(symbol, window_hours=2)
        
        print(f"📊 {symbol} ({result['name'] if 'name' in result else ''}):")
        print(f"   得分：{score:.3f} | 信号：{result['signal']}")
        print(f"   负面词：{', '.join(neg_keywords[:3]) if neg_keywords else '无'}")
        
        if velocity is not None:
            arrow = "📈" if velocity > 0 else "📉"
            print(f"   舆情加速度 (2h)：{velocity:+.3f} {arrow}")
            
            # 触发预警
            if velocity < self.RAPID_DECLINE_THRESHOLD:
                print(f"   🚨 严重预警：舆情急剧恶化！")
                self._alert(symbol, "舆情急剧恶化，建议立即减仓或清仓！")
                
        # 5. 检查绝对分数 (熔断)
        if score < self.KILL_SWITCH:
            print(f"   🔴 熔断预警：得分低于 {self.KILL_SWITCH}！")
            self._alert(symbol, f"舆情得分极低 ({score:.2f})，建议清仓规避风险！")
            
    def _alert(self, symbol: str, message: str):
        """输出报警信息 (可扩展为发送邮件/微信)"""
        print(f"\n🚨🚨🚨 报警：{symbol}")
        print(f"   原因：{message}")
        print(f"🚨🚨🚨\n")


def main():
    print("🔍 Monitor main() started")
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbols', nargs='+', required=True, help='股票代码列表')
    parser.add_argument('--interval', type=int, default=30, help='扫描间隔 (分钟)')
    args = parser.parse_args()
    
    daemon = MonitorDaemon(args.symbols, args.interval)
    daemon.run()

if __name__ == "__main__":
    main()
