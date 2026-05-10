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
from analysis.backtest_optimized import OptimizedBacktester, TradingStrategy
from analysis.advanced_strategy import AdvancedTradingStrategy
from analysis.portfolio_backtest import PortfolioStrategy, prepare_portfolio_data
from analysis.stock_scorer import StockScorer, score_stocks_batch, print_score_summary
from news.scanner import SentimentScanner
from news.daily_report import DailyReportGenerator


class SentistockEngine:
    """Sentistock 核心引擎"""
    
    def __init__(self):
        self.backtester = OptimizedBacktester()
        self.scanner = SentimentScanner()
        self.reporter = DailyReportGenerator()
        
    def login(self, user: str = None, password: str = None) -> bool:
        return self.backtester.login(user, password)
        
    def get_stock_data(self, symbols: List[str], start: str = '2025-01-01', end: str = '2025-12-31') -> Dict[str, pd.DataFrame]:
        """获取股票数据 (优先缓存)"""
        data = {}
        for symbol in symbols:
            if self.backtester.cache.is_cached(symbol, start, end):
                data[symbol] = self.backtester.cache.load_price(symbol, start, end)
            else:
                if not self.backtester.authenticated:
                    print(f"⚠️ 未登录，跳过 {symbol}")
                    continue
                price_df = self.backtester.fetch_price_data(symbol, start, end, use_cache=True)
                if not price_df.empty:
                    data[symbol] = price_df
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
        """单股回测"""
        # 获取数据 (如果外部没传 data，这里尝试从缓存获取)
        if 'data' in kwargs:
            data = kwargs.pop('data')
        else:
            data = self.get_stock_data([symbol])
            
        if symbol not in data:
            return {}
            
        df = prepare_portfolio_data(data[symbol], symbol=symbol, use_real_news=use_real_news)
        
        # 选择策略
        if use_advanced:
            strategy = AdvancedTradingStrategy(**kwargs)
        else:
            strategy = TradingStrategy(**kwargs)
            
        return strategy.run(df)
        
    def run_portfolio(self, symbols: List[str], weight_type: str = 'equal', use_advanced: bool = False, **kwargs) -> Dict:
        """组合回测"""
        data = self.get_stock_data(symbols)
        prepared = {s: prepare_portfolio_data(df, symbol=s) for s, df in data.items()}
        
        # 计算权重
        if weight_type == 'score':
            scorer = StockScorer()
            scores = score_stocks_batch(scorer, data)
            total = sum(scores[s]['scores']['sentiment_suitability'] for s in prepared)
            weights = {s: scores[s]['scores']['sentiment_suitability'] / total for s in prepared}
        else:
            weights = {s: 1.0 / len(prepared) for s in prepared}
            
        if use_advanced:
            from analysis.portfolio_backtest import AdvancedPortfolioStrategy # 需要实现或者复用
            # 这里暂时只支持单股 Advanced，组合回测逻辑比较复杂，暂用普通策略
            # 实际上 Advanced 主要是 Exit 逻辑，Portfolio 也需要支持。
            # 为了简化，暂时先不做 Portfolio 的 Advanced。
            
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
