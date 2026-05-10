"""
分析模块通用工具

集中管理数据准备、指标计算等逻辑，避免重复代码。
"""

import pandas as pd
from .indicators import calculate_all_indicators
from news.backtest_integration import generate_sentiment_series


def prepare_data(
    price_df: pd.DataFrame, 
    symbol: str = None, 
    use_real_news: bool = False
) -> pd.DataFrame:
    """
    统一的数据准备流程
    
    1. 统一列名
    2. 计算技术指标
    3. 生成情感分数 (真实新闻 or 技术指标模拟)
    """
    df = price_df.copy()
    
    # 1. 统一列名
    column_map = {
        'open': '开盘', 'close': '收盘', 'high': '最高', 'low': '最低',
        'volume': '成交量', 'date': '日期'
    }
    df.rename(columns=column_map, inplace=True)
    df['日期'] = pd.to_datetime(df['日期'])
    
    # 2. 技术指标
    df = calculate_all_indicators(df)
    
    # 3. 情感分数
    if use_real_news and symbol:
        trade_dates = [str(d)[:10] for d in df['日期'].tolist()]
        news_series = generate_sentiment_series(trade_dates, symbol, fallback_method='ffill')
        df['sentiment_score'] = news_series.values
    else:
        # 默认：技术指标模拟 (对齐舆情含义：低分 = 恐慌/超卖，高分 = 贪婪/超买)
        # RSI 越低 (超卖) -> 分数越低
        rsi_score = df['RSI'] / 100
        
        # MACD Hist 越小 (空头) -> 分数越低
        macd_hist = df['MACD_hist']
        # 归一化到 0-1 (最小值对应 0，最大值对应 1)
        macd_min = macd_hist.min()
        macd_max = macd_hist.max()
        macd_score = (macd_hist - macd_min) / (macd_max - macd_min + 1e-8)
        
        # BB 位置：越接近下轨 (超卖) -> 分数越低
        bb_pos = (df['收盘'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'] + 1e-8)
        # Clip to 0-1 just in case
        bb_pos = bb_pos.clip(0, 1)
        
        df['sentiment_score'] = 0.4 * rsi_score + 0.3 * macd_score + 0.3 * bb_pos
        df['sentiment_score'] = df['sentiment_score'].clip(0.05, 0.95)
        
    return df
