#!/usr/bin/env python3
"""
批量回测所有缓存股票的高级策略
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core import get_engine

def main():
    engine = get_engine()
    
    # 从缓存目录提取股票代码
    cache_dir = "data/cache"
    symbols = []
    for filename in os.listdir(cache_dir):
        if filename.endswith("_price.csv"):
            symbol = filename.split("_")[0]
            symbols.append(symbol)
    
    print(f"发现 {len(symbols)} 只已缓存股票: {', '.join(symbols)}")
    print("="*80)
    
    results = {}
    for symbol in symbols:
        print(f"\n📈 回测 {symbol}...")
        try:
            result = engine.run_backtest(symbol, use_advanced=True)
            if result:
                results[symbol] = result
                print(f"✅ 完成: 累计收益 {result.get('total_return', 0):.2%}")
            else:
                print(f"❌ 跳过: 无有效数据")
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    # 汇总报告
    print("\n" + "="*80)
    print("📊 批量回测汇总报告")
    print("="*80)
    
    profitable = 0
    total_return = 0
    max_drawdowns = []
    
    for symbol, result in results.items():
        ret = result.get('total_return', 0)
        dd = result.get('max_drawdown', 0)
        total_return += ret
        max_drawdowns.append(dd)
        if ret > 0:
            profitable += 1
    
    if results:
        avg_return = total_return / len(results)
        avg_dd = sum(max_drawdowns) / len(max_drawdowns) if max_drawdowns else 0
        win_rate = profitable / len(results) * 100
        
        print(f"回测股票数: {len(results)}")
        print(f"盈利股票数: {profitable} ({win_rate:.1f}%)")
        print(f"平均累计收益: {avg_return:.2%}")
        print(f"平均最大回撤: {avg_dd:.2%}")
    else:
        print("无有效回测结果")

if __name__ == "__main__":
    main()