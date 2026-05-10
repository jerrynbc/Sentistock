"""
技术指标可视化模块

绘制 MACD, RSI, 布林带等技术指标图表
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np


def plot_macd(df: pd.DataFrame, title: str = "MACD 指标", figsize: tuple = (14, 6), save_path: str = None):
    """
    绘制 MACD 指标图
    
    Args:
        df: 包含 DIF, DEA, MACD_hist 列的 DataFrame
        title: 图表标题
        figsize: 图片大小
        save_path: 保存路径
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    dates = pd.to_datetime(df['日期'])
    
    colors = ['red' if df['MACD_hist'].iloc[i] >= 0 else 'green' for i in range(len(df))]
    ax.bar(dates, df['MACD_hist'], color=colors, alpha=0.6, width=0.8, label='MACD Histogram')
    
    ax.plot(dates, df['DIF'], label='DIF (快线)', linewidth=2, color='blue')
    ax.plot(dates, df['DEA'], label='DEA (慢线)', linewidth=2, color='orange')
    
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=1)
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('MACD', fontsize=12)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    plt.show()
    
    return fig, ax


def plot_rsi(df: pd.DataFrame, title: str = "RSI 指标", figsize: tuple = (14, 4), save_path: str = None):
    """
    绘制 RSI 指标图
    
    Args:
        df: 包含 RSI 列的 DataFrame
        title: 图表标题
        figsize: 图片大小
        save_path: 保存路径
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    dates = pd.to_datetime(df['日期'])
    
    ax.plot(dates, df['RSI'], label='RSI', linewidth=2, color='purple')
    
    ax.axhline(y=70, color='red', linestyle='--', linewidth=1, label='Overbought (70)')
    ax.axhline(y=30, color='green', linestyle='--', linewidth=1, label='Oversold (30)')
    ax.axhline(y=50, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    
    ax.fill_between(dates, 70, 100, alpha=0.2, color='red')
    ax.fill_between(dates, 0, 30, alpha=0.2, color='green')
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('RSI', fontsize=12)
    ax.set_ylim(0, 100)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    plt.show()
    
    return fig, ax


def plot_bollinger_bands(df: pd.DataFrame, title: str = "Bollinger Bands", figsize: tuple = (14, 8), save_path: str = None):
    """
    绘制布林带图
    
    Args:
        df: 包含收盘、BB_upper、BB_middle、BB_lower 列的 DataFrame
        title: 图表标题
        figsize: 图片大小
        save_path: 保存路径
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[3, 1])
    
    dates = pd.to_datetime(df['日期'])
    
    ax1.plot(dates, df['收盘'], label='Close Price', linewidth=2, color='blue')
    ax1.plot(dates, df['BB_middle'], label='Middle (MA20)', linewidth=1.5, color='gray')
    ax1.plot(dates, df['BB_upper'], label='Upper Band', linewidth=1.5, color='red', linestyle='--')
    ax1.plot(dates, df['BB_lower'], label='Lower Band', linewidth=1.5, color='green', linestyle='--')
    
    ax1.fill_between(dates, df['BB_upper'], df['BB_lower'], alpha=0.2)
    
    ax1.set_title(title, fontsize=16, fontweight='bold')
    ax1.set_ylabel('Price', fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    ax1.plot(dates[df['signal'] == 1], df['收盘'][df['signal'] == 1], '^', 
             color='green', markersize=10, label='Buy Signal', alpha=0.7)
    ax1.plot(dates[df['signal'] == -1], df['收盘'][df['signal'] == -1], 'v', 
             color='red', markersize=10, label='Sell Signal', alpha=0.7)
    
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
    
    plt.show()
    
    return fig, ax1, ax2


def plot_all_indicators(df: pd.DataFrame, title: str = "技术指标全景图", save_path: str = None):
    """
    绘制完整的技术指标面板 (价格 + MACD + RSI)
    
    Args:
        df: 包含所有技术指标的 DataFrame
        title: 图表标题
        save_path: 保存路径
    """
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), height_ratios=[3, 1, 1])
    
    dates = pd.to_datetime(df['日期'])
    
    ax1.plot(dates, df['收盘'], label='Close Price', linewidth=2, color='blue')
    ax1.plot(dates, df['MA5'], label='MA5', linewidth=1.5, alpha=0.7)
    ax1.plot(dates, df['MA10'], label='MA10', linewidth=1.5, alpha=0.7)
    ax1.plot(dates, df['MA20'], label='MA20', linewidth=1.5, alpha=0.7)
    
    ax1.set_title(title, fontsize=16, fontweight='bold')
    ax1.set_ylabel('Price', fontsize=12)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    ax1.plot(dates[df['signal'] == 1], df['收盘'][df['signal'] == 1], '^', 
             color='green', markersize=8, label='Buy Signal', alpha=0.7)
    ax1.plot(dates[df['signal'] == -1], df['收盘'][df['signal'] == -1], 'v', 
             color='red', markersize=8, label='Sell Signal', alpha=0.7)
    
    colors = ['red' if df['收盘'].iloc[i] >= df['开盘'].iloc[i] else 'green' for i in range(len(df))]
    ax2.bar(dates, df['MACD_hist'], color=colors, alpha=0.6, width=0.8)
    ax2.plot(dates, df['DIF'], label='DIF', linewidth=2, color='blue')
    ax2.plot(dates, df['DEA'], label='DEA', linewidth=2, color='orange')
    ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1)
    ax2.set_ylabel('MACD', fontsize=12)
    ax2.legend(loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    ax3.plot(dates, df['RSI'], label='RSI', linewidth=2, color='purple')
    ax3.axhline(y=70, color='red', linestyle='--', linewidth=1, label='Overbought')
    ax3.axhline(y=30, color='green', linestyle='--', linewidth=1, label='Oversold')
    ax3.axhline(y=50, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    ax3.fill_between(dates, 70, 100, alpha=0.2, color='red')
    ax3.fill_between(dates, 0, 30, alpha=0.2, color='green')
    ax3.set_ylabel('RSI', fontsize=12)
    ax3.set_ylim(0, 100)
    ax3.legend(loc='upper left', fontsize=9)
    ax3.grid(True, alpha=0.3)
    
    plt.xlabel('Date', fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Chart saved to: {save_path}")
    
    plt.show()
    
    return fig, ax1, ax2, ax3
