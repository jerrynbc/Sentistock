#!/usr/bin/env python3
"""
基于价值筛选的回测验证（使用现有缓存数据）
"""

import os
import sys
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core import get_engine
from analysis.stock_scorer import StockScorer

def is_high_value_stock(symbol: str, df: pd.DataFrame) -> bool:
    """判断股票是否值得交易"""
    # 1. 评分门槛
    scorer = StockScorer()
    score_info = scorer.score(df)
    sentiment_suitability = score_info['scores']['sentiment_suitability']
    if sentiment_suitability <= 70:
        return False, f"评分过低 ({sentiment_suitability:.1f})"
    
    # 2. 行业过滤（排除银行/公用事业代码前缀）
    bank_codes = ['000001', '600000', '601166', '601398']  # 示例银行股
    utility_codes = ['600900', '600027', '600863']  # 示例公用事业
    if symbol in bank_codes + utility_codes:
        return False, "属于低波动板块"
    
    # 3. 流动性检查 (使用volume替代money)
    avg_volume = df['volume'].mean()
    if avg_volume < 1e6:  # 100万股
        return False, f"流动性不足 (日均{avg_volume/1e6:.2f}百万股)"
    
    return True, f"高价值股票 (评分{sentiment_suitability:.1f})"

def main():
    engine = get_engine()
    
    # 获取所有缓存股票
    cache_dir = "data/cache"
    symbols = []
    for filename in os.listdir(cache_dir):
        if filename.endswith("_price.csv"):
            symbol = filename.split("_")[0]
            symbols.append(symbol)
    
    print(f"📊 对 {len(symbols)} 只股票进行价值筛选...")
    
    high_value_symbols = []
    results = {}
    
    for symbol in symbols:
        # 获取数据
        data = engine.get_stock_data([symbol])
        if not data or symbol not in data:
            continue
            
        df = data[symbol]
        is_valuable, reason = is_high_value_stock(symbol, df)
        
        print(f"  {symbol}: {reason}")
        
        if is_valuable:
            high_value_symbols.append(symbol)
            # 执行回测
            result = engine.run_backtest(symbol, use_advanced=True, data={symbol: df})
            if result:
                results[symbol] = result
    
    print(f"\n✅ 筛选出 {len(high_value_symbols)} 只高价值股票: {high_value_symbols}")
    
    if results:
        # 汇总高价值股票表现
        total_return = sum(r.get('total_return', 0) for r in results.values())
        profitable = sum(1 for r in results.values() if r.get('total_return', 0) > 0)
        win_rate = profitable / len(results) * 100
        
        print(f"\n📈 高价值股票回测结果:")
        print(f"  平均收益: {total_return/len(results):.2%}")
        print(f"  胜率: {win_rate:.1f}%")
        
        # 检查是否全部盈利
        if all(r.get('total_return', 0) > 0 for r in results.values()):
            print("  🎉 所有高价值股票均实现正收益！")
        else:
            print("  ⚠️  部分高价值股票仍亏损，需优化策略")
    else:
        print("\n❌ 无符合价值标准的股票")

if __name__ == "__main__":
    import pandas as pd
    main()