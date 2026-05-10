"""
Phase 4.3: 能源与科技板块参数优化

目标：
1. 针对 9 只能源+科技股，寻找适用于组合的最优回测参数
2. 对比优化前后的收益、回撤、夏普比率

用法:
    python tests/test_params_optimization.py
"""

import sys
import os
import pandas as pd
import numpy as np
from itertools import product
from typing import Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from analysis.stock_scorer import StockScorer, score_stocks_batch
from analysis.portfolio_backtest import PortfolioStrategy, prepare_portfolio_data, DataCache

# 缓存目录和目标股票
CACHE_DIR = 'data/cache'
START_DATE = '2025-01-01'
END_DATE = '2025-12-31'

TARGET_STOCKS = [
    '601857', '600938', # 石油
    '600900', '600011', # 电力
    '688981', '002371', '603501', # 半导体
    '002230', '002415'  # AI
]

def load_data():
    """加载缓存数据"""
    data = {}
    cache = DataCache(CACHE_DIR)
    for symbol in TARGET_STOCKS:
        if cache.is_cached(symbol, START_DATE, END_DATE):
            data[symbol] = cache.load_price(symbol, START_DATE, END_DATE)
    return data

def optimize_portfolio_params(data: Dict[str, pd.DataFrame]):
    """网格搜索最优组合参数"""
    
    print(f"\n{'='*80}")
    print("🚀 开始参数优化 (能源 + 科技板块)")
    print(f"{'='*80}")
    
    # 准备数据
    prepared_data = {}
    for s, df in data.items():
        prepared_data[s] = prepare_portfolio_data(df, symbol=s, use_real_news=False)
        
    # 计算评分权重 (用于评估)
    scorer = StockScorer()
    score_results = score_stocks_batch(scorer, data)
    total_score = sum(score_results[s]['scores']['sentiment_suitability'] for s in prepared_data)
    weights = {s: score_results[s]['scores']['sentiment_suitability'] / total_score for s in prepared_data}
    
    # 参数网格
    buy_thresholds = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    take_profits = [0.15, 0.20, 0.25, 0.30, 0.40]
    stop_losses = [-0.05, -0.08, -0.10, -0.12, -0.15]
    max_holds = [15, 20, 30, 45, 60]
    
    best_sharpe = -999
    best_params = {}
    best_result = {}
    count = 0
    total = len(buy_thresholds) * len(take_profits) * len(stop_losses) * len(max_holds)
    
    print(f"搜索空间大小：{total} 组参数...\n")
    
    for bt, tp, sl, mh in product(buy_thresholds, take_profits, stop_losses, max_holds):
        count += 1
        if count % 200 == 0:
            print(f"  已测试 {count}/{total}...")
            
        # 运行组合回测
        strategy = PortfolioStrategy(
            symbols=list(prepared_data.keys()),
            weights=weights,
            initial_capital=1_000_000,
            buy_threshold=bt,
            take_profit_pct=tp,
            stop_loss_pct=sl,
            max_hold_days=mh,
            trend_filter=True,
        )
        
        res = strategy.run(prepared_data)
        
        # 评分：夏普比率优先，辅以总收益
        score = res['sharpe_ratio'] * 0.6 + (res['total_return'] / 100) * 0.4
        
        if score > best_sharpe and res['total_return'] > 0:
            best_sharpe = score
            best_params = {
                'buy_threshold': bt,
                'take_profit_pct': tp,
                'stop_loss_pct': sl,
                'max_hold_days': mh,
            }
            best_result = res
            
    print(f"\n{'='*80}")
    print("🏆 最优参数组合")
    print(f"{'='*80}")
    print(f"买入阈值：{best_params['buy_threshold']}")
    print(f"止盈目标：{best_params['take_profit_pct']*100:.0f}%")
    print(f"止损阈值：{best_params['stop_loss_pct']*100:.0f}%")
    print(f"最大持仓：{best_params['max_hold_days']} 天")
    print(f"综合得分：{best_sharpe:.3f}")
    print(f"累计收益：{best_result['total_return']:+.2f}%")
    print(f"最大回撤：{best_result['max_drawdown']:.2f}%")
    print(f"夏普比率：{best_result['sharpe_ratio']:.2f}")
    
    return best_params, best_result

def main():
    data = load_data()
    if not data:
        print("❌ 未找到缓存数据，请先运行 `tests/test_multi_industry.py` 获取数据")
        return
        
    # 1. 基准测试 (默认参数)
    print(f"\n{'='*80}")
    print("📊 1. 基准测试 (默认参数)")
    print(f"{'='*80}")
    
    prepared_data = {s: prepare_portfolio_data(df, symbol=s) for s, df in data.items()}
    scorer = StockScorer()
    score_results = score_stocks_batch(scorer, data)
    total_score = sum(score_results[s]['scores']['sentiment_suitability'] for s in prepared_data)
    weights = {s: score_results[s]['scores']['sentiment_suitability'] / total_score for s in prepared_data}
    
    baseline_strategy = PortfolioStrategy(
        symbols=list(prepared_data.keys()),
        weights=weights,
        initial_capital=1_000_000,
    )
    baseline_res = baseline_strategy.run(prepared_data)
    print(f"累计收益：{baseline_res['total_return']:+.2f}% | 回撤：{baseline_res['max_drawdown']:.2f}% | 夏普：{baseline_res['sharpe_ratio']:.2f}")
    
    # 2. 优化
    best_params, best_res = optimize_portfolio_params(data)
    
    # 3. 对比总结
    print(f"\n{'='*80}")
    print("📊 优化前后对比")
    print(f"{'='*80}")
    print(f"{'指标':<10} | {'基准':<10} | {'优化后':<10}")
    print("-" * 40)
    
    base_ret = f"{baseline_res['total_return']:+.2f}%"
    opt_ret = f"{best_res['total_return']:+.2f}%"
    base_dd = f"{baseline_res['max_drawdown']:.2f}%"
    opt_dd = f"{best_res['max_drawdown']:.2f}%"
    base_sh = f"{baseline_res['sharpe_ratio']:.2f}"
    opt_sh = f"{best_res['sharpe_ratio']:.2f}"
    
    print(f"{'累计收益':<10} | {base_ret:<10} | {opt_ret:<10}")
    print(f"{'最大回撤':<10} | {base_dd:<10} | {opt_dd:<10}")
    print(f"{'夏普比率':<10} | {base_sh:<10} | {opt_sh:<10}")
    
    print(f"\n✅ 优化完成！")

if __name__ == "__main__":
    main()
