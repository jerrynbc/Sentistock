"""
情绪分析可视化模块

绘制情绪趋势图、词云等
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime


def plot_sentiment_timeline(
    timeline: pd.DataFrame,
    title: str = "情绪趋势图",
    figsize: tuple = (14, 6),
    save_path: str = None
):
    """
    绘制情绪时间线
    
    Args:
        timeline: 情绪时间线 DataFrame
        title: 图表标题
        figsize: 图片大小
        save_path: 保存路径
    """
    if timeline.empty:
        print("时间线数据为空")
        return
    
    fig, ax = plt.subplots(figsize=figsize)
    
    dates = pd.to_datetime(timeline['date'])
    
    # 绘制情绪得分
    ax.plot(dates, timeline['avg_score'], linewidth=2, color='purple', marker='o', label='情绪得分')
    
    # 绘制参考线
    ax.axhline(y=0.6, color='green', linestyle='--', linewidth=1, label='正面 (>0.6)', alpha=0.5)
    ax.axhline(y=0.4, color='red', linestyle='--', linewidth=1, label='负面 (<0.4)', alpha=0.5)
    ax.axhline(y=0.5, color='gray', linestyle='-', linewidth=0.5, alpha=0.3)
    
    # 填充区域
    ax.fill_between(dates, timeline['avg_score'], 0.6, 
                    where=(timeline['avg_score'] > 0.6), 
                    alpha=0.3, color='green', label='乐观区')
    ax.fill_between(dates, timeline['avg_score'], 0.4, 
                    where=(timeline['avg_score'] < 0.4), 
                    alpha=0.3, color='red', label='悲观区')
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Sentiment Score', fontsize=12)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    plt.show()
    
    return fig, ax


def plot_sentiment_distribution(
    analyzed_news: list,
    title: str = "情绪分布",
    figsize: tuple = (8, 6),
    save_path: str = None
):
    """
    绘制情绪分布饼图
    
    Args:
        analyzed_news: 已分析的新闻列表
        title: 图表标题
        figsize: 图片大小
        save_path: 保存路径
    """
    if not analyzed_news:
        print("新闻数据为空")
        return
    
    # 统计各类情感数量
    positive = sum(1 for n in analyzed_news if n['sentiment'] == 'positive')
    negative = sum(1 for n in analyzed_news if n['sentiment'] == 'negative')
    neutral = sum(1 for n in analyzed_news if n['sentiment'] == 'neutral')
    
    fig, ax = plt.subplots(figsize=figsize)
    
    labels = ['正面', '中性', '负面']
    sizes = [positive, neutral, negative]
    colors = ['#2ecc71', '#95a5a6', '#e74c3c']
    
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
           startangle=90, explode=(0.05, 0, 0.05))
    
    ax.set_title(title, fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    plt.show()
    
    return fig, ax


def plot_keyword_cloud(
    keywords: list,
    title: str = "关键词云",
    figsize: tuple = (10, 8),
    save_path: str = None
):
    """
    绘制关键词条形图 (简化版词云)
    
    Args:
        keywords: 关键词频率列表 [(keyword, count), ...]
        title: 图表标题
        figsize: 图片大小
        save_path: 保存路径
    """
    if not keywords:
        print("关键词数据为空")
        return
    
    # 取前 15 个关键词
    top_keywords = keywords[:15]
    
    fig, ax = plt.subplots(figsize=figsize)
    
    words = [kw[0] for kw in top_keywords]
    counts = [kw[1] for kw in top_keywords]
    
    # 创建颜色渐变
    colors = plt.cm.Blues(range(256, 256 - len(words) * 15, -15))
    
    y_pos = range(len(words))
    
    bars = ax.barh(y_pos, counts, color=colors)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(words, fontsize=12)
    ax.invert_yaxis()
    ax.set_xlabel('Frequency', fontsize=12)
    ax.set_title(title, fontsize=16, fontweight='bold')
    
    # 在条子上显示数值
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                str(count), va='center', fontsize=10)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    plt.show()
    
    return fig, ax


def plot_sentiment_vs_price(
    timeline: pd.DataFrame,
    price_data: pd.DataFrame,
    title: str = "情绪 vs 价格",
    figsize: tuple = (14, 8),
    save_path: str = None
):
    """
    绘制情绪与价格对比图
    
    Args:
        timeline: 情绪时间线
        price_data: 价格数据
        title: 图表标题
        figsize: 图片大小
        save_path: 保存路径
    """
    if timeline.empty or price_data.empty:
        print("数据不足")
        return
    
    # 合并数据
    merged = pd.merge(
        timeline,
        price_data[['日期', '收盘']],
        left_on='date',
        right_on='日期',
        how='inner'
    )
    
    if len(merged) < 3:
        print("匹配数据不足")
        return
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[1, 2])
    
    dates = pd.to_datetime(merged['date'])
    
    # 上图：情绪得分
    ax1.plot(dates, merged['avg_score'], linewidth=2, color='purple', 
             marker='o', label='情绪得分')
    ax1.axhline(y=0.5, color='gray', linestyle='--', linewidth=0.5, alpha=0.3)
    ax1.set_ylabel('Sentiment', fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 1)
    
    # 下图：价格走势
    ax2.plot(dates, merged['收盘'], linewidth=2, color='blue', 
             marker='.', label='收盘价')
    ax2.set_ylabel('Price', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)
    
    # 计算相关性
    correlation = merged['avg_score'].corr(merged['收盘'])
    fig.suptitle(f"{title} (相关系数：{correlation:.3f})", fontsize=16, fontweight='bold')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    plt.show()
    
    return fig, ax1, ax2


def plot_all_sentiment_charts(
    timeline: pd.DataFrame,
    analyzed_news: list,
    keywords: list,
    price_data: pd.DataFrame = None,
    title: str = "情绪分析全景图",
    save_path: str = None
):
    """
    绘制情绪分析完整面板
    
    Args:
        timeline: 情绪时间线
        analyzed_news: 已分析的新闻列表
        keywords: 关键词列表
        price_data: 价格数据 (可选)
        title: 图表标题
        save_path: 保存路径
    """
    if price_data is not None and not timeline.empty:
        # 有价格数据时显示 4 个子图
        fig = plt.figure(figsize=(16, 12))
        
        # 子图 1: 情绪趋势
        ax1 = fig.add_subplot(2, 2, 1)
        dates = pd.to_datetime(timeline['date'])
        ax1.plot(dates, timeline['avg_score'], linewidth=2, color='purple', marker='o')
        ax1.axhline(y=0.6, color='green', linestyle='--', alpha=0.5)
        ax1.axhline(y=0.4, color='red', linestyle='--', alpha=0.5)
        ax1.set_title('Sentiment Trend', fontsize=14)
        ax1.set_ylim(0, 1)
        ax1.grid(True, alpha=0.3)
        
        # 子图 2: 情绪分布
        ax2 = fig.add_subplot(2, 2, 2)
        positive = sum(1 for n in analyzed_news if n['sentiment'] == 'positive')
        negative = sum(1 for n in analyzed_news if n['sentiment'] == 'negative')
        neutral = sum(1 for n in analyzed_news if n['sentiment'] == 'neutral')
        ax2.pie([positive, neutral, negative], labels=['Positive', 'Neutral', 'Negative'],
                colors=['#2ecc71', '#95a5a6', '#e74c3c'], autopct='%1.1f%%')
        ax2.set_title('Sentiment Distribution', fontsize=14)
        
        # 子图 3: 关键词
        ax3 = fig.add_subplot(2, 2, 3)
        if keywords:
            top_keywords = keywords[:10]
            words = [kw[0] for kw in top_keywords]
            counts = [kw[1] for kw in top_keywords]
            ax3.barh(range(len(words)), counts, color=plt.cm.Blues(range(200, 255, 5)))
            ax3.set_yticks(range(len(words)))
            ax3.set_yticklabels(words)
            ax3.invert_yaxis()
            ax3.set_title('Top Keywords', fontsize=14)
        
        # 子图 4: 情绪 vs 价格
        ax4 = fig.add_subplot(2, 2, 4)
        if price_data is not None:
            merged = pd.merge(timeline, price_data[['日期', '收盘']],
                            left_on='date', right_on='日期', how='inner')
            if len(merged) >= 3:
                merge_dates = pd.to_datetime(merged['date'])
                ax4.plot(merge_dates, merged['收盘'], 'b-', linewidth=2, label='Price')
                ax4_sec = ax4.twinx()
                ax4_sec.plot(merge_dates, merged['avg_score'], 'r--', linewidth=2, label='Sentiment')
                ax4_sec.set_ylim(0, 1)
                ax4.set_ylabel('Price', fontsize=12)
                ax4_sec.set_ylabel('Sentiment', fontsize=12)
                ax4.set_title('Price vs Sentiment', fontsize=14)
        
        plt.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        plt.show()
        
        return fig
    else:
        # 无价格数据时显示 3 个子图
        fig = plt.figure(figsize=(14, 10))
        
        # 子图 1: 情绪趋势
        ax1 = fig.add_subplot(2, 2, 1)
        if not timeline.empty:
            dates = pd.to_datetime(timeline['date'])
            ax1.plot(dates, timeline['avg_score'], linewidth=2, color='purple', marker='o')
        ax1.set_title('Sentiment Trend', fontsize=14)
        ax1.grid(True, alpha=0.3)
        
        # 子图 2: 情绪分布
        ax2 = fig.add_subplot(2, 2, 2)
        if analyzed_news:
            positive = sum(1 for n in analyzed_news if n['sentiment'] == 'positive')
            negative = sum(1 for n in analyzed_news if n['sentiment'] == 'negative')
            neutral = sum(1 for n in analyzed_news if n['sentiment'] == 'neutral')
            ax2.pie([positive, neutral, negative], labels=['Positive', 'Neutral', 'Negative'],
                    colors=['#2ecc71', '#95a5a6', '#e74c3c'], autopct='%1.1f%%')
        ax2.set_title('Sentiment Distribution', fontsize=14)
        
        # 子图 3: 关键词
        ax3 = fig.add_subplot(2, 1, 2)
        if keywords:
            top_keywords = keywords[:10]
            words = [kw[0] for kw in top_keywords]
            counts = [kw[1] for kw in top_keywords]
            ax3.barh(range(len(words)), counts, color=plt.cm.Greens(range(200, 255, 5)))
            ax3.set_yticks(range(len(words)))
            ax3.set_yticklabels(words)
            ax3.invert_yaxis()
            ax3.set_title('Top Keywords', fontsize=14)
        
        plt.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        plt.show()
        
        return fig
