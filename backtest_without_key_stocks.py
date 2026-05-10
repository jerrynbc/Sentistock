#!/usr/bin/env python3
"""
移除关键贡献股票后的策略验证
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core import get_engine

def main():
    engine = get_engine()
    
    # 获取所有缓存股票并排除关键贡献者
    cache_dir = "data/cache"
    all_symbols = []
    for filename in os.listdir(cache_dir):
        if filename.endswith("_price.csv"):
            symbol = filename.split("_")[0]
            all_symbols.append(symbol)
    
    # 排除高贡献股票
    excluded = ['002212', '002371']
    symbols = [s for s in all_symbols if s not in excluded]
    
    print(f"回测 {len(symbols)} 只股票 (已排除 {', '.join(excluded)}): {', '.join(symbols)}")
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
    print("📊 移除关键股票后的汇总报告")
    print("="*80)
    
    if not results:
        print("无有效回测结果")
        return
    
    profitable = 0
    total_return = 0
    max_drawdowns = []
    returns_list = []
    
    for symbol, result in results.items():
        ret = result.get('total_return', 0)
        dd = result.get('max_drawdown', 0)
        returns_list.append(ret)
        total_return += ret
        max_drawdowns.append(dd)
        if ret > 0:
            profitable += 1
    
    avg_return = total_return / len(results)
    avg_dd = sum(max_drawdowns) / len(max_drawdowns) if max_drawdowns else 0
    win_rate = profitable / len(results) * 100
    
    print(f"回测股票数: {len(results)}")
    print(f"盈利股票数: {profitable} ({win_rate:.1f}%)")
    print(f"平均累计收益: {avg_return:.2%}")
    print(f"平均最大回撤: {avg_dd:.2%}")
    
    # 检查是否所有股票都盈利
    if all(r > 0 for r in returns_list):
        print("\n🎉 所有股票均实现正收益！")
    else:
        print(f"\n⚠️  仍有 {len(results)-profitable} 只股票亏损")
        print("亏损股票详情:")
        for symbol, result in results.items():
            ret = result.get('total_return', 0)
            if ret <= 0:
                print(f"  {symbol}: {ret:.2%}")

if __name__ == "__main__":
    main()