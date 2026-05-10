#!/usr/bin/env python3
"""
使用AKShare获取真实历史数据并筛选高价值股票
"""

import os
import sys
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    print("❌ 未安装 akshare，正在安装...")
    os.system(f"{sys.executable} -m pip install akshare --break-system-packages")
    import akshare as ak
    AKSHARE_AVAILABLE = True

from analysis.stock_scorer import StockScorer

def fetch_real_data(symbol: str, start_date: str = "20230101", end_date: str = "20241231") -> pd.DataFrame:
    """使用AKShare获取A股真实历史数据"""
    try:
        # AKShare股票代码格式：sh/sz + 6位数字
        if symbol.startswith(('00', '30')):
            code = f"sz{symbol}"
        else:
            code = f"sh{symbol}"
            
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        
        if df.empty:
            return pd.DataFrame()
            
        # 标准化列名
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open', 
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'money'
        })
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        return df[['open', 'close', 'high', 'low', 'volume', 'money']]
        
    except Exception as e:
        print(f"⚠️  获取 {symbol} 数据失败: {e}")
        return pd.DataFrame()

def main():
    # 获取所有缓存股票代码
    cache_dir = "data/cache"
    symbols = []
    for filename in os.listdir(cache_dir):
        if filename.endswith("_price.csv"):
            symbol = filename.split("_")[0]
            symbols.append(symbol)
    
    print(f"🔍 使用AKShare获取 {len(symbols)} 只股票的真实历史数据 (2023-2024)...")
    
    # 获取真实数据并评分
    scorer = StockScorer()
    stock_scores = {}
    
    for symbol in symbols:
        print(f"  获取 {symbol}...")
        df = fetch_real_data(symbol, "20230101", "20241231")
        if not df.empty:
            score_info = scorer.calculate_score(df)
            stock_scores[symbol] = {
                'score': score_info['total'],
                'details': score_info,
                'data': df
            }
            print(f"    评分: {score_info['total']:.2f}")
        else:
            print(f"    ❌ 无数据")
    
    # 筛选高价值股票 (评分 > 70)
    high_value_stocks = {s: info for s, info in stock_scores.items() if info['score'] > 70}
    low_value_stocks = {s: info for s, info in stock_scores.items() if info['score'] <= 70}
    
    print(f"\n📊 股票价值筛选结果:")
    print(f"  高价值股票 (>70分): {len(high_value_stocks)} 只")
    print(f"  低价值股票 (≤70分): {len(low_value_stocks)} 只")
    
    if high_value_stocks:
        print("\n📈 高价值股票详情:")
        for symbol, info in sorted(high_value_stocks.items(), key=lambda x: x[1]['score'], reverse=True):
            print(f"  {symbol}: {info['score']:.2f}分 "
                  f"(波动:{info['details']['volatility']:.1f}, "
                  f"趋势:{info['details']['trend_strength']:.1f})")
    
    # 保存高价值股票数据到缓存目录（覆盖原有未来数据）
    cache_new_dir = "data/cache_real"
    os.makedirs(cache_new_dir, exist_ok=True)
    
    for symbol, info in high_value_stocks.items():
        filepath = os.path.join(cache_new_dir, f"{symbol}_2023-01-01_2024-12-31_price.csv")
        info['data'].to_csv(filepath)
        print(f"  ✅ 保存 {symbol} 真实数据到 {filepath}")
    
    print(f"\n💾 真实历史数据已保存到: {cache_new_dir}/")
    print(f"   后续回测请使用这些真实数据文件")

if __name__ == "__main__":
    main()