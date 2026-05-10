"""
股票数据可视化模块

提供 K 线图、均线图等绘制功能
"""

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np

# 设置中文字体 (解决中文显示问题)
# 尝试多种中文字体
import platform
system = platform.system()

if system == 'Windows':
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
elif system == 'Darwin':  # macOS
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Heiti TC', 'STHeiti']
else:  # Linux
    # 尝试使用系统可能有的中文字体
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'SimHei', 'DejaVu Sans']

plt.rcParams['axes.unicode_minus'] = False


def plot_candlestick(
    df: pd.DataFrame,
    title: str = "Stock Candlestick Chart",
    show_ma: bool = True,
    ma_days: list = None,
    figsize: tuple = (14, 8),
    save_path: str = None
):
    """
    绘制 K 线图 (蜡烛图)
    
    Args:
        df: OHLC 数据 DataFrame
        title: 图表标题
        show_ma: 是否显示均线
        ma_days: 均线周期列表
        figsize: 图片大小
        save_path: 保存路径
    """
    if ma_days is None:
        ma_days = [5, 10, 20]
    
    fig, ax = plt.subplots(figsize=figsize)
    
    dates = pd.to_datetime(df['日期'])
    opens = df['开盘'].values
    closes = df['收盘'].values
    highs = df['最高'].values
    lows = df['最低'].values
    
    up_color = 'red'
    down_color = 'green'
    
    for i in range(len(df)):
        if closes[i] >= opens[i]:
            color = up_color
            ax.plot([dates[i], dates[i]], [lows[i], highs[i]], color=color, linewidth=1)
            rect = Rectangle(
                (dates[i] - 0.3, opens[i]),
                0.6,
                closes[i] - opens[i],
                facecolor=color,
                edgecolor=color,
                linewidth=0
            )
        else:
            color = down_color
            ax.plot([dates[i], dates[i]], [lows[i], highs[i]], color=color, linewidth=1)
            rect = Rectangle(
                (dates[i] - 0.3, opens[i]),
                0.6,
                closes[i] - opens[i],
                facecolor=color,
                edgecolor=color,
                linewidth=0
            )
        ax.add_patch(rect)
    
    if show_ma:
        for day in ma_days:
            ma = df['收盘'].rolling(window=day).mean()
            ax.plot(dates, ma, label=f'MA{day}', linewidth=1.5, alpha=0.8)
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Price', fontsize=12)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Chart saved to: {save_path}")
    
    plt.show()
    
    return fig, ax


def plot_price_with_volume(
    df: pd.DataFrame,
    title: str = "Stock Price and Volume",
    ma_days: list = None,
    figsize: tuple = (14, 10),
    save_path: str = None
):
    """
    绘制价格和成交量组合图
    
    Args:
        df: 股票数据 DataFrame
        title: 图表标题
        ma_days: 均线周期
        figsize: 图片大小
        save_path: 保存路径
    """
    if ma_days is None:
        ma_days = [5, 10, 20]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[3, 1])
    
    dates = pd.to_datetime(df['日期'])
    
    ax1.plot(dates, df['收盘'], label='Close Price', linewidth=2, color='blue')
    
    for day in ma_days:
        ma = df['收盘'].rolling(window=day).mean()
        ax1.plot(dates, ma, label=f'MA{day}', linewidth=1.5, alpha=0.7)
    
    ax1.set_title(title, fontsize=16, fontweight='bold')
    ax1.set_ylabel('Price', fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    colors = ['red' if df['收盘'].iloc[i] >= df['开盘'].iloc[i] else 'green' 
              for i in range(len(df))]
    ax2.bar(dates, df['成交量'], color=colors, alpha=0.7, width=0.8)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Volume', fontsize=12)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Chart saved to: {save_path}")
    
    plt.show()
    
    return fig, ax1, ax2
