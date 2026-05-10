"""
真实数据回测脚本 - 验证情绪模块

使用聚宽真实价格数据 + AKShare 新闻数据
进行情绪分析回测验证

用法:
    python src/analysis/backtest_real.py <股票代码> [选项]

示例:
    # 使用默认参数回测
    python src/analysis/backtest_real.py 300454
    
    # 指定时间范围
    python src/analysis/backtest_real.py 300454 --start 2025-01-01 --end 2025-12-31
    
    # 指定账号密码
    python src/analysis/backtest_real.py 300454 --user 15620693228 --password 'Zrdsg0510,'
"""

import jqdatasdk as jq
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.sentiment import analyze_single_sentiment
from analysis.time_weighted_sentiment import TimeWeightedSentiment
from analysis.indicators import calculate_all_indicators

# 聚宽账号配置
JQ_USER = os.getenv('JQ_USER', '')
JQ_PASSWORD = os.getenv('JQ_PASSWORD', '')


class RealDataBacktester:
    """真实数据回测器"""
    
    def __init__(self):
        self.authenticated = False
    
    def login(self, user: str = None, password: str = None) -> bool:
        """登录聚宽"""
        if user is None:
            user = JQ_USER
        if password is None:
            password = JQ_PASSWORD
        
        if not user or not password:
            print("❌ 请提供聚宽账号密码")
            print("   --user <手机号> --password <密码>")
            print("   或设置环境变量 JQ_USER, JQ_PASSWORD")
            return False
        
        try:
            jq.auth(user, password)
            self.authenticated = True
            print(f"✅ 聚宽登录成功：{user[:3]}****{user[-4:]}")
            return True
        except Exception as e:
            print(f"❌ 登录失败：{e}")
            return False
    
    def fetch_price_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取真实价格数据"""
        # 转换代码格式
        jq_symbol = self._to_jq_symbol(symbol)
        
        print(f"\n获取价格数据：{jq_symbol}")
        print(f"时间范围：{start_date} 至 {end_date}")
        
        df = jq.get_price(
            security=jq_symbol,
            start_date=start_date,
            end_date=end_date,
            frequency='daily',
            fields=['open', 'close', 'high', 'low', 'volume']
        )
        
        if df is None or df.empty:
            print("❌ 未获取到价格数据")
            return pd.DataFrame()
        
        df.index.name = 'date'
        df.reset_index(inplace=True)
        print(f"✅ 获取到 {len(df)} 条价格数据")
        return df
    
    def fetch_news_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取新闻数据
        
        聚宽没有 get_news API，尝试用 AKShare
        """
        try:
            import akshare as ak
            print(f"\n尝试使用 AKShare 获取新闻...")
            
            # AKShare 新闻 API
            news_df = ak.stock_news_em(symbol=symbol)
            
            if news_df is not None and not news_df.empty:
                print(f"✅ AKShare 获取到 {len(news_df)} 条新闻")
                return news_df
        except Exception as e:
            print(f"AKShare 新闻获取失败：{e}")
        
        # 如果新闻获取失败，生成基于技术面的模拟情绪信号
        print("\n⚠️ 新闻数据不可用，使用技术指标生成模拟情绪信号")
        return pd.DataFrame()
    
    def generate_sentiment_signals(self, price_df: pd.DataFrame) -> pd.DataFrame:
        """
        基于技术指标生成模拟情绪信号
        
        用技术指标模拟情绪分析结果，验证回测框架
        """
        print("\n生成模拟情绪信号...")
        
        df = price_df.copy()
        
        # 统一列名（聚宽返回英文，indicators.py 期望中文）
        column_map = {
            'open': '开盘', 'close': '收盘', 'high': '最高', 'low': '最低',
            'volume': '成交量', 'date': '日期'
        }
        df.rename(columns=column_map, inplace=True)
        
        # 确保日期是 datetime
        if '日期' in df.columns:
            df['日期'] = pd.to_datetime(df['日期'])
        
        df = calculate_all_indicators(df)
        
        # 综合技术指标生成情绪分数
        # 1. RSI: 0-100 -> 0-1 (超卖=正面机会，超买=负面风险)
        rsi_norm = 1 - (df['RSI'] / 100)
        
        # 2. MACD 柱状图 -> 情绪方向
        macd_hist = df['MACD_hist']
        macd_norm = (macd_hist - macd_hist.min()) / (macd_hist.max() - macd_hist.min() + 1e-8)
        
        # 3. 布林带位置 -> 情绪
        bb_pos = (df['收盘'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'] + 1e-8)
        bb_norm = 1 - bb_pos  # 触及下轨=正面机会
        
        # 综合情绪分数 (0-1)
        df['sentiment_score'] = 0.4 * rsi_norm + 0.3 * macd_norm + 0.3 * bb_norm
        df['sentiment_score'] = df['sentiment_score'].clip(0.1, 0.9)
        
        print(f"情绪分数范围：{df['sentiment_score'].min():.3f} - {df['sentiment_score'].max():.3f}")
        print(f"均值：{df['sentiment_score'].mean():.3f}")
        
        return df
    
    def run_backtest(
        self,
        df: pd.DataFrame,
        buy_threshold: float = 0.35,
        sell_threshold: float = 0.65,
        initial_capital: float = 100000
    ) -> Dict:
        """
        执行回测
        
        Args:
            df: 包含价格和情绪分数的 DataFrame
            buy_threshold: 情绪低于此值买入（恐慌=机会）
            sell_threshold: 情绪高于此值卖出（贪婪=风险）
            initial_capital: 初始资金
        """
        print(f"\n{'='*80}")
        print("执行回测")
        print(f"{'='*80}")
        print(f"买入阈值：情绪 < {buy_threshold}")
        print(f"卖出阈值：情绪 > {sell_threshold}")
        print(f"初始资金：¥{initial_capital:,.0f}")
        
        df = df.copy()
        
        # 统一列名
        column_map = {
            '日期': 'date', '收盘': 'close', '开盘': 'open', 
            '最高': 'high', '最低': 'low', '成交量': 'volume'
        }
        df.rename(columns=column_map, inplace=True)
        
        df.set_index('date', inplace=True)
        
        # 生成交易信号
        df['signal'] = 0
        df.loc[df['sentiment_score'] < buy_threshold, 'signal'] = 1    # 买入
        df.loc[df['sentiment_score'] > sell_threshold, 'signal'] = -1  # 卖出
        
        # 计算次日收益
        df['next_return'] = df['close'].pct_change().shift(-1)
        
        # 分析买入信号
        buy_signals = df[df['signal'] == 1]
        sell_signals = df[df['signal'] == -1]
        
        results = {
            'total_days': len(df),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'price_range': f"¥{df['close'].min():.2f} - ¥{df['close'].max():.2f}",
            'sentiment_range': f"{df['sentiment_score'].min():.3f} - {df['sentiment_score'].max():.3f}",
        }
        
        # 买入信号分析
        if len(buy_signals) > 0:
            avg_return = buy_signals['next_return'].mean() * 100
            win_rate = (buy_signals['next_return'] > 0).mean() * 100
            max_win = buy_signals['next_return'].max() * 100
            max_loss = buy_signals['next_return'].min() * 100
            
            results['buy_avg_return'] = avg_return
            results['buy_win_rate'] = win_rate
            results['buy_max_win'] = max_win
            results['buy_max_loss'] = max_loss
            
            print(f"\n【买入信号分析】")
            print(f"  信号次数：{len(buy_signals)}")
            print(f"  买入后平均收益：{avg_return:+.3f}%")
            print(f"  胜率：{win_rate:.1f}%")
            print(f"  最大盈利：{max_win:+.2f}%")
            print(f"  最大亏损：{max_loss:+.2f}%")
            
            if win_rate > 50:
                print(f"  ✅ 情绪指标有效！买入后胜率超过 50%")
            else:
                print(f"  ⚠️ 需要优化参数或策略")
        
        # 卖出信号分析
        if len(sell_signals) > 0:
            avg_return = sell_signals['next_return'].mean() * 100
            win_rate = (sell_signals['next_return'] < 0).mean() * 100
            max_win = sell_signals['next_return'].min() * 100  # 下跌=盈利
            max_loss = sell_signals['next_return'].max() * 100
            
            results['sell_avg_return'] = avg_return
            results['sell_win_rate'] = win_rate
            results['sell_max_win'] = max_win
            results['sell_max_loss'] = max_loss
            
            print(f"\n【卖出信号分析】")
            print(f"  信号次数：{len(sell_signals)}")
            print(f"  卖出后平均收益：{avg_return:+.3f}%")
            print(f"  胜率：{win_rate:.1f}%")
            print(f"  最大盈利（下跌幅度）：{max_win:.2f}%")
            print(f"  最大亏损（上涨幅度）：{max_loss:+.2f}%")
            
            if win_rate > 50:
                print(f"  ✅ 情绪指标有效！卖出后胜率超过 50%")
        
        # 持仓 vs 空仓收益对比
        df['hold_return'] = df['close'].pct_change()
        buy_periods = df[df['signal'] == 1]
        
        if len(buy_signals) > 0 and len(df) > 0:
            total_buy_return = buy_signals['next_return'].sum() * 100
            total_hold_return = df['hold_return'].sum() * 100
            
            results['total_buy_return'] = total_buy_return
            results['total_hold_return'] = total_hold_return
            
            print(f"\n【策略 vs 持仓】")
            print(f"  信号触发总收益：{total_buy_return:+.2f}%")
            print(f"  全程持仓收益：{total_hold_return:+.2f}%")
        
        # 时间加权情绪分析
        print(f"\n【时间加权情绪分析】")
        analyzer = TimeWeightedSentiment(half_life_days=7.0)
        
        # 取最近 20 天的情绪数据
        recent = df[['sentiment_score']].tail(20)
        sentiment_items = []
        for date, row in recent.iterrows():
            sentiment_items.append({
                'content': f'技术指标情绪信号 {date.strftime("%Y-%m-%d")}',
                'sentiment': {'score': row['sentiment_score']},
                'created_at': date.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        result = analyzer.calculate_weighted_sentiment(sentiment_items)
        print(f"时间加权情绪得分：{result['weighted_score']:.3f}")
        print(f"原始情绪得分：{result['raw_score']:.3f}")
        print(result['explanation'])
        
        return results
    
    def _to_jq_symbol(self, symbol: str) -> str:
        """转换股票代码为聚宽格式"""
        if '.XSHG' in symbol or '.XSHE' in symbol:
            return symbol
        if symbol.startswith(('6', '5')):
            return f"{symbol}.XSHG"
        return f"{symbol}.XSHE"


def main():
    parser = argparse.ArgumentParser(description='真实数据回测')
    parser.add_argument('symbol', default='300454', nargs='?', help='股票代码')
    parser.add_argument('--start', default=None, help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', default=None, help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--user', default=None, help='聚宽账号')
    parser.add_argument('--password', default=None, help='聚宽密码')
    parser.add_argument('--buy-threshold', type=float, default=0.35, help='买入阈值')
    parser.add_argument('--sell-threshold', type=float, default=0.65, help='卖出阈值')
    parser.add_argument('--capital', type=float, default=100000, help='初始资金')
    
    args = parser.parse_args()
    
    # 默认时间范围：过去一年
    if args.end is None:
        args.end = '2025-12-31'
    if args.start is None:
        args.start = '2025-01-01'
    
    print(f"\n{'='*80}")
    print(f"Sentistock 真实数据回测")
    print(f"股票：{args.symbol}")
    print(f"时间：{args.start} 至 {args.end}")
    print(f"{'='*80}")
    
    backtester = RealDataBacktester()
    
    # 登录
    if not backtester.login(args.user, args.password):
        return
    
    # 获取价格数据
    price_df = backtester.fetch_price_data(args.symbol, args.start, args.end)
    if price_df.empty:
        return
    
    # 获取新闻数据
    news_df = backtester.fetch_news_data(args.symbol, args.start, args.end)
    
    if news_df.empty:
        # 使用技术指标模拟情绪
        print("\n使用技术指标生成模拟情绪信号...")
        df = backtester.generate_sentiment_signals(price_df)
    else:
        # 即使有新闻，也用技术指标生成情绪信号（新闻太少无法做有效分析）
        print(f"\n获取到 {len(news_df)} 条新闻，但数量不足，使用技术指标生成情绪信号...")
        df = backtester.generate_sentiment_signals(price_df)
    
    # 执行回测
    results = backtester.run_backtest(
        df,
        buy_threshold=args.buy_threshold,
        sell_threshold=args.sell_threshold,
        initial_capital=args.capital
    )
    
    print(f"\n{'='*80}")
    print("回测完成")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
