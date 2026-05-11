#!/usr/bin/env python3
"""
测试免费数据源可用性
"""

import yfinance as yf
import pandas as pd
import os
from datetime import datetime

def test_yahoo_finance():
    """测试Yahoo Finance A股数据获取"""
    print("🔍 测试 Yahoo Finance A股数据...")
    
    # A股代码格式测试
    test_symbols = ['300454.SZ', '600000.SS', '000001.SZ']
    
    for symbol in test_symbols:
        try:
            print(f"  获取 {symbol} 数据...")
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1mo")
            
            if not hist.empty:
                print(f"    ✅ 成功获取 {len(hist)} 天数据")
                print(f"    最新价格: {hist['Close'].iloc[-1]:.2f}")
                print(f"    数据范围: {hist.index.min().date()} 到 {hist.index.max().date()}")
            else:
                print(f"    ❌ 数据为空")
                
        except Exception as e:
            print(f"    ❌ 获取失败: {e}")

def test_alpha_vantage():
    """测试Alpha Vantage (需要API key)"""
    print("\n🔍 测试 Alpha Vantage...")
    
    api_key = os.getenv('ALPHA_VANTAGE_KEY')
    if not api_key:
        print("  ⚠️  ALPHA_VANTAGE_KEY 未设置，跳过测试")
        return
        
    try:
        from alpha_vantage.timeseries import TimeSeries
        ts = TimeSeries(key=api_key, output_format='pandas')
        
        # A股代码格式: SSE:600000, SZSE:300454
        symbols = ['SSE:600000', 'SZSE:300454']
        
        for symbol in symbols:
            print(f"  获取 {symbol} 数据...")
            data, meta_data = ts.get_daily(symbol=symbol, outputsize='compact')
            
            if not data.empty:
                print(f"    ✅ 成功获取 {len(data)} 天数据")
                print(f"    最新价格: {data['4. close'].iloc[0]:.2f}")
            else:
                print(f"    ❌ 数据为空")
                
    except ImportError:
        print("  ⚠️  alpha_vantage 库未安装")
    except Exception as e:
        print(f"  ❌ API调用失败: {e}")

def test_rsshub_news():
    """测试RSSHub新闻获取"""
    print("\n🔍 测试 RSSHub 新闻...")
    
    try:
        import requests
        import feedparser
        
        url = "https://rsshub.app/10jqka/realtimenews/A股"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            if feed.entries:
                print(f"  ✅ 成功获取 {len(feed.entries)} 条新闻")
                print(f"  最新新闻: {feed.entries[0].title}")
            else:
                print("  ❌ RSS解析成功但无新闻条目")
        else:
            print(f"  ❌ HTTP状态码: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ RSSHub测试失败: {e}")

def main():
    print("📊 免费数据源可用性测试")
    print("=" * 50)
    
    # 安装依赖
    print("📦 安装必要依赖...")
    os.system(f"{__import__('sys').executable} -m pip install yfinance feedparser requests --break-system-packages")
    
    # 测试各数据源
    test_yahoo_finance()
    test_alpha_vantage()
    test_rsshub_news()
    
    print("\n" + "=" * 50)
    print("✅ 测试完成！")

if __name__ == "__main__":
    main()