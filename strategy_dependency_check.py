#!/usr/bin/env python3
"""
验证策略收益是否依赖单只股票异常表现
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core import get_engine

def main():
    engine = get_engine()
    
    # 获取所有缓存股票
    cache_dir = "data/cache"
    symbols = []
    for filename in os.listdir(cache_dir):
        if filename.endswith("_price.csv"):
            symbol = filename.split("_")[0]
            symbols.append(symbol)
    
    print(f"分析 {len(symbols)} 只股票的策略贡献度...")
    
    # 1. 计算完整组合收益
    all_results = {}
    for symbol in symbols:
        result = engine.run_backtest(symbol, use_advanced=True)
        if result:
            all_results[symbol] = result
    
    total_return_all = sum(r.get('total_return', 0) for r in all_results.values())
    print(f"\n📊 完整组合累计收益: {total_return_all:.2%}")
    
    # 2. 逐一剔除每只股票计算收益
    print("\n🔍 单只股票剔除测试:")
    contributions = {}
    
    for symbol in symbols:
        if symbol not in all_results:
            continue
            
        return_without_symbol = total_return_all - all_results[symbol].get('total_return', 0)
        contribution_pct = (all_results[symbol].get('total_return', 0) / total_return_all * 100) if total_return_all != 0 else 0
        contributions[symbol] = contribution_pct
        
        print(f"  剔除 {symbol}: 组合收益 {return_without_symbol:.2%} (该股贡献 {contribution_pct:.1f}%)")
    
    # 3. 识别关键贡献者
    print("\n📈 关键贡献股票 (贡献度 > 20%):")
    key_contributors = {s: c for s, c in contributions.items() if abs(c) > 20}
    
    if key_contributors:
        for symbol, contrib in sorted(key_contributors.items(), key=lambda x: abs(x[1]), reverse=True):
            print(f"  {symbol}: {contrib:.1f}%")
        print(f"\n⚠️  策略收益高度依赖 {len(key_contributors)} 只股票")
    else:
        print("  无显著单一贡献者，收益分布均衡")
    
    # 4. 风险分析
    extreme_returns = [s for s, r in all_results.items() if abs(r.get('total_return', 0)) > 2.0]  # 超过200%
    if extreme_returns:
        print(f"\n❗ 存在极端收益股票: {', '.join(extreme_returns)}")
        print("   建议检查这些股票的回测逻辑是否合理")

if __name__ == "__main__":
    main()