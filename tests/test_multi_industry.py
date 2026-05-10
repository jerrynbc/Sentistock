"""
Phase 4.3: 多行业评分验证 - 能源 + 科技板块

股票池:
- 石油: 601857(中国石油), 600938(中国海油)
- 电力: 600900(长江电力), 600011(华能国际)
- 半导体: 688981(中芯国际), 002371(北方华创), 603501(韦尔股份)
- AI: 002230(科大讯飞), 002415(海康威视)

用法:
    python tests/test_multi_industry.py --user 15620693228 --password 'Zrdsg0510,'
"""

import sys
import os
import pandas as pd
import numpy as np
import time
import jqdatasdk as jq

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from analysis.stock_scorer import StockScorer, score_stocks_batch, print_score_summary
from analysis.backtest_optimized import DataCache
from analysis.portfolio_backtest import PortfolioStrategy, prepare_portfolio_data

# 目标股票池
TARGET_STOCKS = {
    '601857': '中国石油',
    '600938': '中国海油',
    '600900': '长江电力',
    '600011': '华能国际',
    '688981': '中芯国际',
    '002371': '北方华创',
    '603501': '韦尔股份',
    '002230': '科大讯飞',
    '002415': '海康威视',
}

CACHE_DIR = 'data/cache'
START_DATE = '2025-01-01'
END_DATE = '2025-12-31'


def fetch_and_cache(symbols: dict, user: str, password: str):
    """获取并缓存数据"""
    cache = DataCache(CACHE_DIR)
    
    # 登录
    try:
        jq.auth(user, password)
        print("✅ 聚宽登录成功")
    except Exception as e:
        print(f"❌ 登录失败：{e}")
        return {}
        
    data = {}
    for symbol, name in symbols.items():
        # 检查缓存
        if cache.is_cached(symbol, START_DATE, END_DATE):
            print(f"📂 {name}({symbol}): 使用缓存")
            data[symbol] = cache.load_price(symbol, START_DATE, END_DATE)
            continue
            
        # 查询
        jq_symbol = f"{symbol}.XSHG" if symbol.startswith('6') else f"{symbol}.XSHE"
        print(f"🔄 正在获取 {name}({symbol})...")
        
        try:
            df = jq.get_price(
                security=jq_symbol,
                start_date=START_DATE,
                end_date=END_DATE,
                frequency='daily',
                fields=['open', 'close', 'high', 'low', 'volume']
            )
            
            if df is not None and not df.empty:
                df.index.name = 'date'
                df.reset_index(inplace=True)
                cache.save_price(df, symbol, START_DATE, END_DATE)
                data[symbol] = df
                print(f"✅ {name}: {len(df)} 条")
            else:
                print(f"⚠️ {name}: 无数据")
                
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ {name} 获取失败：{e}")
            
    return data


def run_score_test(data: dict):
    """运行评分测试"""
    print(f"\n{'='*80}")
    print("📊 股票评分测试")
    print(f"{'='*80}")
    
    scorer = StockScorer()
    results = score_stocks_batch(scorer, data)
    print_score_summary(results)
    
    return results


def run_portfolio_test(data: dict, score_results: dict):
    """运行组合回测测试"""
    # 准备数据
    prepared_data = {}
    for s, df in data.items():
        prepared_data[s] = prepare_portfolio_data(df, symbol=s, use_real_news=False)
        
    # 1. 等权组合
    print(f"\n{'='*80}")
    print("📈 等权组合回测")
    print(f"{'='*80}")
    
    equal_weights = {s: 1.0/len(prepared_data) for s in prepared_data}
    equal_strategy = PortfolioStrategy(
        symbols=list(prepared_data.keys()),
        weights=equal_weights,
        initial_capital=1_000_000,
        buy_threshold=0.25,
        take_profit_pct=0.20,
        stop_loss_pct=-0.05,
        max_hold_days=20,
    )
    equal_results = equal_strategy.run(prepared_data)
    equal_strategy.print_results(equal_results)
    
    # 2. 评分加权组合
    print(f"\n{'='*80}")
    print("📈 评分加权组合回测")
    print(f"{'='*80}")
    
    total_score = sum(score_results[s]['scores']['sentiment_suitability'] for s in prepared_data)
    score_weights = {s: score_results[s]['scores']['sentiment_suitability'] / total_score for s in prepared_data}
    score_strategy = PortfolioStrategy(
        symbols=list(prepared_data.keys()),
        weights=score_weights,
        initial_capital=1_000_000,
        buy_threshold=0.25,
        take_profit_pct=0.20,
        stop_loss_pct=-0.05,
        max_hold_days=20,
    )
    score_results_bt = score_strategy.run(prepared_data)
    score_strategy.print_results(score_results_bt)
    
    # 对比
    print(f"\n{'='*80}")
    print("📊 方案对比")
    print(f"{'='*80}")
    
    eq_ret = f"{equal_results['total_return']:+.2f}%"
    sc_ret = f"{score_results_bt['total_return']:+.2f}%"
    eq_dd = f"{equal_results['max_drawdown']:.2f}%"
    sc_dd = f"{score_results_bt['max_drawdown']:.2f}%"
    eq_sharpe = f"{equal_results['sharpe_ratio']:.2f}"
    sc_sharpe = f"{score_results_bt['sharpe_ratio']:.2f}"
    
    print(f"{'指标':<10} | {'等权':<10} | {'评分加权':<10}")
    print("-" * 40)
    print(f"{'累计收益':<10} | {eq_ret:<10} | {sc_ret:<10}")
    print(f"{'最大回撤':<10} | {eq_dd:<10} | {sc_dd:<10}")
    print(f"{'夏普比率':<10} | {eq_sharpe:<10} | {sc_sharpe:<10}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', required=True, help='聚宽账号')
    parser.add_argument('--password', required=True, help='聚宽密码')
    args = parser.parse_args()
    
    # 1. 获取数据
    print(f"\n{'='*80}")
    print("Phase 4.3: 多行业评分验证")
    print(f"目标股票：{len(TARGET_STOCKS)} 只 (能源 + 科技)")
    print(f"{'='*80}\n")
    
    data = fetch_and_cache(TARGET_STOCKS, args.user, args.password)
    
    if not data:
        print("❌ 没有获取到任何数据")
        return
        
    # 2. 评分测试
    score_results = run_score_test(data)
    
    # 3. 组合回测
    run_portfolio_test(data, score_results)


if __name__ == "__main__":
    main()
