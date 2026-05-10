#!/usr/bin/env python3
"""
生成展示网页数据

运行此脚本会生成一个包含最新数据的 HTML 文件
"""

import sys
import json
from datetime import datetime
sys.path.insert(0, '/workspace/stock-analyzer')

from src.data.collector import get_stock_history, get_stock_info
from src.analysis.indicators import calculate_all_indicators


def generate_analysis_data(symbol: str = "000001"):
    """获取股票分析数据并保存为 JSON"""
    
    print(f"正在获取股票 {symbol} 的数据...")
    
    df = get_stock_history(symbol)
    if df.empty:
        print("获取数据失败")
        return None
    
    df = calculate_all_indicators(df)
    info = get_stock_info(symbol)
    
    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else latest
    
    data = {
        "symbol": symbol,
        "name": info.get('股票简称', symbol),
        "industry": info.get('行业', ''),
        "pe": round(float(info.get('市盈率 (PE)', 0)), 2),
        "pb": round(float(info.get('市净率 (PB)', 0)), 2),
        "market_cap": info.get('市值', ''),
        "eps": round(float(info.get('每股收益', 0)), 2),
        
        "price": {
            "latest": round(float(latest['收盘']), 2),
            "change": round(float(latest['收盘']) - float(previous['收盘']), 2),
            "change_percent": round((float(latest['收盘']) - float(previous['收盘'])) / float(previous['收盘']) * 100, 2)
        },
        
        "indicators": {
            "macd": {
                "dif": round(float(latest['DIF']), 4),
                "dea": round(float(latest['DEA']), 4),
                "histogram": round(float(latest['MACD_hist']), 4),
                "status": "bullish" if float(latest['DIF']) > float(latest['DEA']) else "bearish"
            },
            "rsi": {
                "value": round(float(latest['RSI']), 2),
                "status": "overbought" if float(latest['RSI']) > 70 else ("oversold" if float(latest['RSI']) < 30 else "normal")
            },
            "bollinger": {
                "upper": round(float(latest['BB_upper']), 2),
                "middle": round(float(latest['BB_middle']), 2),
                "lower": round(float(latest['BB_lower']), 2),
                "position": "above_upper" if float(latest['收盘']) > float(latest['BB_upper']) else (
                    "below_lower" if float(latest['收盘']) < float(latest['BB_lower']) else "within"
                )
            },
            "ma": {
                "ma5": round(float(latest['MA5']), 2),
                "ma10": round(float(latest['MA10']), 2),
                "ma20": round(float(latest['MA20']), 2)
            }
        },
        
        "signals": [],
        "recent_data": []
    }
    
    signals = df[df['signal'] != 0].tail(5)
    for idx, row in signals.iterrows():
        data["signals"].append({
            "date": str(row['日期'])[:10],
            "type": "buy" if row['signal'] == 1 else "sell",
            "reason": row['signal_type'],
            "price": round(float(row['收盘']), 2)
        })
    
    for idx in range(-1, -6, -1):
        if len(df) >= -idx:
            row = df.iloc[idx]
            data["recent_data"].append({
                "date": str(row['日期'])[:10],
                "open": round(float(row['开盘']), 2),
                "high": round(float(row['最高']), 2),
                "low": round(float(row['最低']), 2),
                "close": round(float(row['收盘']), 2),
                "volume": int(row['成交量'])
            })
    
    with open('data/data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到 data.json")
    print(f"最新价格：{data['price']['latest']}")
    print(f"MACD: {data['indicators']['macd']['status']}")
    print(f"RSI: {data['indicators']['rsi']['status']}")
    
    return data


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "000001"
    generate_analysis_data(symbol)
