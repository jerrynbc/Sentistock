"""
核心引擎

提供统一的 API 供 CLI 和 Web 界面调用。
"""

import os
import sys
import pandas as pd
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
# 延迟导入聚宽相关模块，避免在无SDK环境下报错
try:
    from analysis.backtest_optimized import OptimizedBacktester, TradingStrategy
    from analysis.advanced_strategy import AdvancedTradingStrategy
    from analysis.portfolio_backtest import PortfolioStrategy, prepare_portfolio_data
except ImportError:
    # 在无聚宽SDK环境下，只导入不依赖SDK的模块
    from analysis.stock_scorer import StockScorer, score_stocks_batch, print_score_summary
    OptimizedBacktester = None
    TradingStrategy = None
    AdvancedTradingStrategy = None
    PortfolioStrategy = None
    prepare_portfolio_data = None

from analysis.stock_scorer import StockScorer, score_stocks_batch, print_score_summary
from news.scanner import SentimentScanner
from news.daily_report import DailyReportGenerator


class SentistockEngine:
    """Sentistock 核心引擎"""
    
    def __init__(self):
        if OptimizedBacktester is not None:
            self.backtester = OptimizedBacktester()
        else:
            self.backtester = None
        self.scanner = SentimentScanner()
        self.reporter = DailyReportGenerator()
        
    def login(self, user: str = None, password: str = None) -> bool:
        if self.backtester is not None:
            return self.backtester.login(user, password)
        return False
        
    def get_stock_data(self, symbols: List[str], start: str = '2025-01-01', end: str = '2025-12-31') -> Dict[str, pd.DataFrame]:
        """获取股票数据 (优先缓存)"""
        data = {}
        for symbol in symbols:
            cache_file = f"data/cache/{symbol}_{start}_{end}_price.csv"
            if os.path.exists(cache_file):
                data[symbol] = pd.read_csv(cache_file, index_col=0)
            else:
                print(f"⚠️ 缓存文件不存在: {cache_file}")
        return data
        
    def analyze_sentiment(self, symbols: List[str]) -> List[Dict]:
        """舆情扫描"""
        return self.scanner.scan(symbols)
        
    def generate_report(self, symbols: List[str]) -> str:
        """生成日报"""
        return self.reporter.generate(symbols, save=True)
        
    def score_stocks(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """股票评分"""
        scorer = StockScorer()
        return score_stocks_batch(scorer, data)
        
    def run_backtest(self, symbol: str, use_real_news: bool = False, use_advanced: bool = False, **kwargs) -> Dict:
        """单股回测 - 在无SDK环境下返回空结果"""
        if self.backtester is None:
            return {}
            
        # 获取数据 (如果外部没传 data，这里尝试从缓存获取)
        if 'data' in kwargs:
            data = kwargs.pop('data')
        else:
            data = self.get_stock_data([symbol])
            
        if symbol not in data:
            return {}
            
        df = prepare_portfolio_data(data[symbol], symbol=symbol, use_real_news=use_real_news) if prepare_portfolio_data else data[symbol]
        
        # 选择策略
        if use_advanced:
            strategy = AdvancedTradingStrategy(**kwargs)
        else:
            strategy = TradingStrategy(**kwargs)
            
        return strategy.run(df)
        
    def run_portfolio(self, symbols: List[str], weight_type: str = 'equal', use_advanced: bool = False, **kwargs) -> Dict:
        """组合回测 - 在无SDK环境下返回空结果"""
        if self.backtester is None:
            return {}
            
        data = self.get_stock_data(symbols)
        if not data or prepare_portfolio_data is None:
            return {}
            
        prepared = {s: prepare_portfolio_data(df, symbol=s) for s, df in data.items()}
        
        # 计算权重
        if weight_type == 'score':
            scorer = StockScorer()
            scores = score_stocks_batch(scorer, data)
            total = sum(scores[s]['scores']['sentiment_suitability'] for s in prepared)
            weights = {s: scores[s]['scores']['sentiment_suitability'] / total for s in prepared}
        else:
            weights = {s: 1.0 / len(prepared) for s in prepared}
            
        strategy = PortfolioStrategy(
            symbols=list(prepared.keys()),
            weights=weights,
            **kwargs
        )
        return strategy.run(prepared)


# 单例
_engine = None

def get_engine() -> SentistockEngine:
    global _engine
    if _engine is None:
        _engine = SentistockEngine()
    return _engine
