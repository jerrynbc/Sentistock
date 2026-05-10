"""
技术指标计算模块

实现常用技术指标的计算：MACD, RSI, 布林带等
"""

import pandas as pd
import numpy as np


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """
    计算 MACD 指标 (Moving Average Convergence Divergence)
    
    MACD 由三部分组成：
    - DIF (快线): 快 EMA - 慢 EMA
    - DEA (慢线): DIF 的 M 日 EMA
    - MACD 柱：(DIF - DEA) * 2
    
    Args:
        df: 包含'收盘'列的 DataFrame
        fast: 快线周期，默认 12
        slow: 慢线周期，默认 26
        signal: 信号线周期，默认 9
    
    Returns:
        添加了 MACD 相关列的 DataFrame
    
    使用指南:
        - 金叉：DIF 从下向上穿越 DEA (买入信号)
        - 死叉：DIF 从上向下穿越 DEA (卖出信号)
        - 零轴上方：多头市场
        - 零轴下方：空头市场
    """
    df = df.copy()
    
    close = df['收盘']
    
    exp1 = close.ewm(span=fast, adjust=False).mean()
    exp2 = close.ewm(span=slow, adjust=False).mean()
    
    df['DIF'] = exp1 - exp2
    df['DEA'] = df['DIF'].ewm(span=signal, adjust=False).mean()
    df['MACD_hist'] = (df['DIF'] - df['DEA']) * 2
    
    return df


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    计算 RSI 指标 (Relative Strength Index)
    
    RSI 是相对强弱指标，范围 0-100
    
    Args:
        df: 包含'收盘'列的 DataFrame
        period: RSI 周期，默认 14
    
    Returns:
        添加了 RSI 列的 DataFrame
    
    使用指南:
        - RSI > 70: 超买区 (可能回调，卖出信号)
        - RSI < 30: 超卖区 (可能反弹，买入信号)
        - RSI 50: 强弱分界线
    """
    df = df.copy()
    
    delta = df['收盘'].diff()
    
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    """
    计算布林带 (Bollinger Bands)
    
    布林带由三条线组成：
    - 上轨：中轨 + K * 标准差
    - 中轨：N 日均线
    - 下轨：中轨 - K * 标准差
    
    Args:
        df: 包含'收盘'列的 DataFrame
        period: 周期，默认 20
        std_dev: 标准差倍数，默认 2
    
    Returns:
        添加了布林带三列的 DataFrame
    
    使用指南:
        - 触及上轨：可能回调 (卖出信号)
        - 触及下轨：可能反弹 (买入信号)
        - 布林带收窄：即将变盘
        - 布林带张开：趋势延续
    """
    df = df.copy()
    
    df['BB_middle'] = df['收盘'].rolling(window=period).mean()
    
    rolling_std = df['收盘'].rolling(window=period).std()
    df['BB_upper'] = df['BB_middle'] + (std_dev * rolling_std)
    df['BB_lower'] = df['BB_middle'] - (std_dev * rolling_std)
    
    df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']
    
    return df


def calculate_ma(df: pd.DataFrame, periods: list = None) -> pd.DataFrame:
    """
    计算移动平均线 (Moving Average)
    
    Args:
        df: 包含'收盘'列的 DataFrame
        periods: 周期列表，默认 [5, 10, 20, 60]
    
    Returns:
        添加了各周期均线列的 DataFrame
    """
    if periods is None:
        periods = [5, 10, 20, 60]
    
    df = df.copy()
    
    for period in periods:
        df[f'MA{period}'] = df['收盘'].rolling(window=period).mean()
    
    return df


def calculate_volume_ma(df: pd.DataFrame, periods: list = None) -> pd.DataFrame:
    """
    计算成交量均线
    
    Args:
        df: 包含'成交量'列的 DataFrame
        periods: 周期列表，默认 [5, 10]
    
    Returns:
        添加了成交量均线列的 DataFrame
    """
    if periods is None:
        periods = [5, 10]
    
    df = df.copy()
    
    for period in periods:
        df[f'VMA{period}'] = df['成交量'].rolling(window=period).mean()
    
    return df


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    基于技术指标生成买卖信号
    
    Args:
        df: 包含 MACD, RSI, 布林带等指标的 DataFrame
    
    Returns:
        添加了信号列的 DataFrame
    """
    df = df.copy()
    
    df['signal'] = 0
    
    macd_buy = (df['DIF'] > df['DEA']) & (df['DIF'].shift(1) <= df['DEA'].shift(1))
    macd_sell = (df['DIF'] < df['DEA']) & (df['DIF'].shift(1) >= df['DEA'].shift(1))
    
    rsi_buy = df['RSI'] < 30
    rsi_sell = df['RSI'] > 70
    
    bb_buy = df['收盘'] < df['BB_lower']
    bb_sell = df['收盘'] > df['BB_upper']
    
    df.loc[macd_buy, 'signal'] = 1
    df.loc[macd_sell, 'signal'] = -1
    df.loc[rsi_buy, 'signal'] = 1
    df.loc[rsi_sell, 'signal'] = -1
    df.loc[bb_buy, 'signal'] = 1
    df.loc[bb_sell, 'signal'] = -1
    
    df['signal_type'] = ''
    df.loc[macd_buy, 'signal_type'] = 'MACD 金叉'
    df.loc[macd_sell, 'signal_type'] = 'MACD 死叉'
    df.loc[rsi_buy, 'signal_type'] = 'RSI 超卖'
    df.loc[rsi_sell, 'signal_type'] = 'RSI 超买'
    df.loc[bb_buy, 'signal_type'] = '布林带下轨'
    df.loc[bb_sell, 'signal_type'] = '布林带上轨'
    
    return df


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    一次性计算所有技术指标
    
    Args:
        df: 包含 OHLC 数据的 DataFrame
    
    Returns:
        添加了所有技术指标的 DataFrame
    """
    df = calculate_ma(df, [5, 10, 20])
    df = calculate_volume_ma(df, [5, 10])
    df = calculate_macd(df)
    df = calculate_rsi(df)
    df = calculate_bollinger_bands(df)
    df = generate_signals(df)
    
    return df


if __name__ == "__main__":
    from src.data.collector import get_stock_history
    
    print("测试技术指标计算...")
    
    df = get_stock_history("000001")
    
    if not df.empty:
        df = calculate_all_indicators(df)
        
        print("\n计算完成！数据列:")
        print(df.columns.tolist())
        
        print("\n最近 5 天的指标数据:")
        print(df[['日期', '收盘', 'DIF', 'DEA', 'RSI', 'BB_upper', 'BB_lower', 'signal', 'signal_type']].tail())
