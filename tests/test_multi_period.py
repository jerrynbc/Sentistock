"""
Phase 4.3: 多周期验证 + 新股票池 (AI/字节/智谱)

股票池 (13 只):
- 能源: 601857(中石油), 600938(中海油), 600900(长电), 600011(华能)
- 半导体/AI: 688981(中芯), 002371(北创), 603501(韦尔), 002230(讯飞), 002415(海康)
- 字节/智谱概念: 
    - 688111(金山办公): 智谱战略合作
    - 300058(蓝色光标): 字节跳动核心代理
    - 300624(万兴科技): AI 应用/字节合作
    - 300229(拓尔思): AI 大模型

周期:
- 2023 (熊市): 验证防御性
- 2024 (震荡): 验证适应性
- 2025 (牛市/当前): 验证进攻性

用法:
    python tests/test_multi_period.py --user 15620693228 --password 'Zrdsg0510,'
"""

import sys
import os
import pandas as pd
import numpy as np
import time
import jqdatasdk as jq

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from analysis.portfolio_backtest import PortfolioStrategy, prepare_portfolio_data, DataCache
from analysis.stock_scorer import StockScorer, score_stocks_batch

# 股票池
STOCKS = {
    # 能源
    '601857': '中国石油', '600938': '中国海油', '600900': '长江电力', '600011': '华能国际',
    # 半导体/AI
    '688981': '中芯国际', '002371': '北方华创', '603501': '韦尔股份', '002230': '科大讯飞', '002415': '海康威视',
    # 字节/智谱概念
    '688111': '金山办公', '300058': '蓝色光标', '300624': '万兴科技', '300229': '拓尔思'
}

# 时间段定义
PERIODS = {
    '2023 (熊)': ('2023-01-01', '2023-12-31'),
    '2024 (震荡)': ('2024-01-01', '2024-12-31'),
    '2025 (牛)': ('2025-01-01', '2025-12-31'),
    '全周期': ('2023-01-01', '2025-12-31'),
}

CACHE_DIR = 'data/cache_multi'

def fetch_data(user: str, password: str):
    """全量拉取数据"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache = DataCache(CACHE_DIR)
    
    try:
        jq.auth(user, password)
        print("✅ 聚宽登录成功")
    except Exception as e:
        print(f"❌ 登录失败：{e}")
        return {}
        
    all_data = {}
    
    # 拉取全周期 (2023-2025)
    start, end = '2023-01-01', '2025-12-31'
    
    for symbol, name in STOCKS.items():
        if cache.is_cached(symbol, start, end):
            print(f"📂 {name}: 缓存命中")
            all_data[symbol] = cache.load_price(symbol, start, end)
            continue
            
        jq_symbol = f"{symbol}.XSHG" if symbol.startswith('6') else f"{symbol}.XSHE"
        print(f"🔄 获取 {name} ({symbol})...")
        
        try:
            df = jq.get_price(
                security=jq_symbol,
                start_date=start,
                end_date=end,
                frequency='daily',
                fields=['open', 'close', 'high', 'low', 'volume']
            )
            if df is not None and not df.empty:
                df.index.name = 'date'
                df.reset_index(inplace=True)
                cache.save_price(df, symbol, start, end)
                all_data[symbol] = df
                print(f"✅ {name}: {len(df)} 条")
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ {name} 失败: {e}")
            
    return all_data

def run_period(name, start, end, all_data):
    """运行单周期回测"""
    # 切片数据
    period_data = {}
    for s, df in all_data.items():
        df['date'] = pd.to_datetime(df['date'])
        mask = (df['date'] >= pd.to_datetime(start)) & (df['date'] <= pd.to_datetime(end))
        sub_df = df[mask]
        if len(sub_df) > 20: # 至少有 20 天数据
            period_data[s] = sub_df
            
    if not period_data:
        return None
        
    # 准备
    prepared = {s: prepare_portfolio_data(df, symbol=s) for s, df in period_data.items()}
    
    # 评分权重
    scorer = StockScorer()
    scores = score_stocks_batch(scorer, period_data)
    total = sum(scores[s]['scores']['sentiment_suitability'] for s in prepared)
    weights = {s: scores[s]['scores']['sentiment_suitability'] / total for s in prepared}
    
    # 策略：使用优化参数 (止盈 30%, 持仓 15 天)
    strategy = PortfolioStrategy(
        symbols=list(prepared.keys()),
        weights=weights,
        initial_capital=1_000_000,
        buy_threshold=0.25,
        take_profit_pct=0.30,  # 优化后参数
        stop_loss_pct=-0.05,
        max_hold_days=15,      # 优化后参数
        trend_filter=True,
    )
    
    res = strategy.run(prepared)
    return res

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', required=True)
    parser.add_argument('--password', required=True)
    args = parser.parse_args()
    
    print(f"\n{'='*80}")
    print("Phase 4.3: 多周期验证 (AI/字节/智谱)")
    print(f"{'='*80}")
    
    # 1. 获取数据
    all_data = fetch_data(args.user, args.password)
    if not all_data:
        print("❌ 数据获取失败")
        return

    # 2. 遍历周期
    results = {}
    for name, (s, e) in PERIODS.items():
        print(f"\n{'='*80}")
        print(f"📅 正在回测：{name}")
        print(f"{'='*80}")
        res = run_period(name, s, e, all_data)
        if res:
            results[name] = res
            print(f"  累计收益：{res['total_return']:+.2f}%")
            print(f"  最大回撤：{res['max_drawdown']:.2f}%")
            print(f"  夏普比率：{res['sharpe_ratio']:.2f}")
            
    # 3. 总结
    print(f"\n{'='*80}")
    print("📊 多周期验证总结")
    print(f"{'='*80}")
    print(f"{'周期':<12} | {'累计收益':<10} | {'最大回撤':<10} | {'夏普':<10} | {'交易笔数':<10}")
    print("-" * 60)
    for name, res in results.items():
        trades = len(res['trades'])
        print(f"{name:<12} | {res['total_return']:>+9.2f}% | {res['max_drawdown']:>8.2f}% | {res['sharpe_ratio']:>8.2f} | {trades:>8}")

if __name__ == "__main__":
    main()
