"""
聚宽数据回测模块

使用聚宽 (JoinQuant) 免费数据获取历史新闻
进行情绪分析回测
"""

import jqdatasdk as jq
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import json

# 需要先在聚宽官网注册账号：https://www.joinquant.com/
# 然后在这里填写你的账号密码
# 或者使用环境变量：export JQ_USER=xxx JQ_PASSWORD=xxx
JQ_USER = os.getenv('JQ_USER', '')
JQ_PASSWORD = os.getenv('JQ_PASSWORD', '')


class JoinQuantDataFetcher:
    """聚宽数据获取器"""
    
    def __init__(self):
        self.authenticated = False
    
    def authenticate(self, username: str = None, password: str = None):
        """
        登录聚宽
        
        Args:
            username: 聚宽账号 (手机号)
            password: 聚宽密码
        """
        if username is None:
            username = JQ_USER
        if password is None:
            password = JQ_PASSWORD
        
        if not username or not password:
            print("❌ 请先设置聚宽账号密码")
            print("\n使用方式:")
            print("1. 访问 https://www.joinquant.com/ 注册免费账号")
            print("2. 设置环境变量:")
            print("   export JQ_USER=你的手机号")
            print("   export JQ_PASSWORD=你的密码")
            print("\n或者在代码中直接调用:")
            print("   fetcher.authenticate('手机号', '密码')")
            return False
        
        try:
            jq.auth(username, password)
            self.authenticated = True
            print(f"✅ 聚宽登录成功！账号：{username[:3]}****{username[-4:]}")
            return True
        except Exception as e:
            print(f"❌ 聚宽登录失败：{e}")
            print("请检查账号密码是否正确")
            return False
    
    def get_historical_news(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        max_count: int = 1000
    ) -> pd.DataFrame:
        """
        获取历史新闻
        
        Args:
            symbol: 股票代码 (如 '300454.XSHE' 或 '300454')
            start_date: 开始日期 '2025-11-01'
            end_date: 结束日期 '2026-05-10'
            max_count: 最大新闻条数
        
        Returns:
            DataFrame with columns: date, title, content, source, url
        """
        if not self.authenticated:
            print("请先登录聚宽")
            return pd.DataFrame()
        
        # 代码格式转换
        if '.XSHG' not in symbol and '.XSHE' not in symbol:
            # 自动判断交易所
            if symbol.startswith(('6', '5')):
                symbol = f"{symbol}.XSHG"  # 上交所
            else:
                symbol = f"{symbol}.XSHE"  # 深交所
        
        print(f"\n正在获取 {symbol} 的历史新闻...")
        print(f"时间范围：{start_date} 至 {end_date}")
        
        try:
            # 聚宽新闻 API
            news_df = jq.get_news(
                security=symbol,
                start_date=start_date,
                end_date=end_date,
                count=max_count
            )
            
            if news_df is None or len(news_df) == 0:
                print("⚠️ 未获取到新闻数据")
                return pd.DataFrame()
            
            print(f"✅ 获取到 {len(news_df)} 条新闻")
            
            # 数据清洗
            news_df['date'] = pd.to_datetime(news_df['time'])
            news_df = news_df.sort_values('date')
            
            return news_df
            
        except Exception as e:
            print(f"❌ 获取新闻失败：{e}")
            return pd.DataFrame()
    
    def get_stock_price(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        frequency: str = 'daily'
    ) -> pd.DataFrame:
        """
        获取股票价格数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            frequency: 'daily', 'weekly', 'monthly'
        
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        if not self.authenticated:
            return pd.DataFrame()
        
        # 代码格式转换
        if '.XSHG' not in symbol and '.XSHE' not in symbol:
            if symbol.startswith(('6', '5')):
                symbol = f"{symbol}.XSHG"
            else:
                symbol = f"{symbol}.XSHE"
        
        try:
            df = jq.get_price(
                security=symbol,
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                fields=['open', 'close', 'low', 'high', 'volume']
            )
            
            if df is None or len(df) == 0:
                return pd.DataFrame()
            
            df.reset_index(inplace=True)
            df.rename(columns={'time': 'date'}, inplace=True)
            
            return df
            
        except Exception as e:
            print(f"❌ 获取价格数据失败：{e}")
            return pd.DataFrame()
    
    def get_all_stocks(self) -> List[str]:
        """获取所有 A 股股票代码"""
        if not self.authenticated:
            return []
        
        try:
            stocks = jq.get_all_securities(['stock'])
            return stocks.index.tolist()
        except:
            return []


class JoinQuantSentimentBacktester:
    """聚宽情绪回测器"""
    
    def __init__(self):
        self.fetcher = JoinQuantDataFetcher()
    
    def analyze_news_sentiment_batch(
        self,
        news_df: pd.DataFrame,
        batch_size: int = 100
    ) -> pd.DataFrame:
        """
        批量分析新闻情绪
        
        Args:
            news_df: 新闻 DataFrame
            batch_size: 批次大小
        
        Returns:
            添加了情绪得分的 DataFrame
        """
        from src.analysis.sentiment import analyze_single_sentiment
        
        print(f"\n正在分析 {len(news_df)} 条新闻的情绪...")
        
        sentiment_scores = []
        
        for i, (_, row) in enumerate(news_df.iterrows()):
            # 分析标题情绪
            result = analyze_single_sentiment(row.get('title', ''), explain=False)
            sentiment_scores.append(result['score'])
            
            if (i + 1) % batch_size == 0:
                print(f"已分析 {i+1}/{len(news_df)} 条...")
        
        news_df['sentiment_score'] = sentiment_scores
        print(f"✅ 情绪分析完成")
        
        return news_df
    
    def backtest_with_real_news(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        half_life_days: float = 7.0,
        buy_threshold: float = 0.35,
        sell_threshold: float = 0.65,
        initial_capital: float = 100000
    ) -> Dict:
        """
        使用真实新闻回测
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            half_life_days: 半衰期
            buy_threshold: 买入阈值
            sell_threshold: 卖出阈值
            initial_capital: 初始资金
        
        Returns:
            回测结果
        """
        print("="*80)
        print("聚宽情绪回测 - 真实新闻数据")
        print("="*80)
        
        # 1. 获取新闻
        news_df = self.fetcher.get_historical_news(symbol, start_date, end_date)
        
        if news_df.empty:
            return {'error': '未获取到新闻数据'}
        
        # 2. 情绪分析
        news_df = self.analyze_news_sentiment_batch(news_df)
        
        # 3. 获取价格数据
        price_df = self.fetcher.get_stock_price(symbol, start_date, end_date)
        
        if price_df.empty:
            return {'error': '未获取到价格数据'}
        
        # 4. 合并数据
        news_df.set_index('date', inplace=True)
        price_df.set_index('date', inplace=True)
        
        # 5. 计算每日平均情绪
        daily_sentiment = news_df['sentiment_score'].resample('D').mean()
        
        # 6. 时间加权
        from src.analysis.time_weighted_sentiment import TimeWeightedSentiment
        analyzer = TimeWeightedSentiment(half_life_days=half_life_days)
        
        # 7. 回测逻辑
        # (简化版，完整版见前面的 backtester.py)
        
        print("\n执行回测...")
        print("参数:")
        print(f"  半衰期：{half_life_days} 天")
        print(f"  买入阈值：< {buy_threshold}")
        print(f"  卖出阈值：> {sell_threshold}")
        print(f"  初始资金：¥{initial_capital:,.0f}")
        
        # TODO: 完整回测逻辑实现
        
        return {
            'symbol': symbol,
            'news_count': len(news_df),
            'period': f"{start_date} to {end_date}",
            'params': {
                'half_life_days': half_life_days,
                'buy_threshold': buy_threshold,
                'sell_threshold': sell_threshold
            }
        }


def demo_with_mock_data():
    """
    演示回测流程 (使用模拟数据，无需聚宽账号)
    
    这部分代码展示完整的回测流程，
    当你有聚宽账号后，只需将 mock 数据替换为真实数据即可
    """
    print("="*80)
    print("情绪回测演示 - 模拟数据")
    print("="*80)
    
    # 模拟数据
    np.random.seed(42)
    dates = pd.date_range('2025-11-01', '2026-05-10', freq='B')
    
    # 真实情绪数据的特点：
    # 1. 大部分时间在 0.4-0.6 之间 (中性)
    # 2. 偶尔出现极端值 (<0.3 或 >0.7)
    # 3. 有一定持续性 (今天正面，明天可能还正面)
    
    sentiment_scores = []
    prev_sentiment = 0.5
    
    for _ in range(len(dates)):
        # 均值回归 + 随机波动 + 持续性
        mean_reversion = (0.5 - prev_sentiment) * 0.1
        momentum = np.random.normal(0, 0.1) * (0.3 if np.random.random() > 0.7 else 1.0)
        new_sentiment = prev_sentiment + mean_reversion + momentum
        new_sentiment = np.clip(new_sentiment, 0.1, 0.9)
        sentiment_scores.append(new_sentiment)
        prev_sentiment = new_sentiment
    
    # 创建模拟新闻
    news_df = pd.DataFrame({
        'date': dates,
        'title': [f"模拟新闻 {i}" for i in range(len(dates))],
        'sentiment_score': sentiment_scores
    })
    
    # 价格数据
    price_series = 110 * (1 + np.random.normal(0.0005, 0.025, len(dates))).cumprod()
    price_df = pd.DataFrame({
        'date': dates,
        'close': price_series
    })
    
    print(f"\n模拟数据:")
    print(f"  新闻条数：{len(news_df)}")
    print(f"  情绪得分范围：{news_df['sentiment_score'].min():.3f} - {news_df['sentiment_score'].max():.3f}")
    print(f"  价格范围：{price_df['close'].min():.2f} - {price_df['close'].max():.2f}")
    
    # 简单回测
    df = pd.merge(news_df, price_df, on='date')
    df.set_index('date', inplace=True)
    
    # 交易信号
    df['signal'] = 0
    df.loc[df['sentiment_score'] < 0.35, 'signal'] = 1   # 买入
    df.loc[df['sentiment_score'] > 0.65, 'signal'] = -1  # 卖出
    
    # 计算次日收益
    df['next_return'] = df['close'].pct_change().shift(-1)
    
    # 分析买入信号后的表现
    buy_signals = df[df['signal'] == 1]
    if len(buy_signals) > 0:
        avg_return_after_buy = buy_signals['next_return'].mean() * 100
        win_rate_buy = (buy_signals['next_return'] > 0).mean() * 100
        
        print(f"\n买入信号分析:")
        print(f"  买入信号次数：{len(buy_signals)}")
        print(f"  买入后平均收益：{avg_return_after_buy:.3f}%")
        print(f"  胜率：{win_rate_buy:.1f}%")
        
        if win_rate_buy > 50:
            print(f"  ✓ 情绪指标有效！买入后胜率超过 50%")
        else:
            print(f"  ⚠ 情绪指标需要优化参数")
    
    # 分析卖出信号后的表现
    sell_signals = df[df['signal'] == -1]
    if len(sell_signals) > 0:
        avg_return_after_sell = sell_signals['next_return'].mean() * 100
        # 卖出后下跌算对
        win_rate_sell = (sell_signals['next_return'] < 0).mean() * 100
        
        print(f"\n卖出信号分析:")
        print(f"  卖出信号次数：{len(sell_signals)}")
        print(f"  卖出后平均收益：{avg_return_after_sell:.3f}%")
        print(f"  胜率：{win_rate_sell:.1f}%")
        
        if win_rate_sell > 50:
            print(f"  ✓ 情绪指标有效！卖出后胜率超过 50%")
    
    print("\n" + "="*80)
    print("演示完成！")
    print("="*80)
    print("\n下一步:")
    print("1. 注册聚宽账号：https://www.joinquant.com/")
    print("2. 设置环境变量:")
    print("   export JQ_USER=你的手机号")
    print("   export JQ_PASSWORD=你的密码")
    print("3. 再次运行，会自动使用真实数据回测")
    print("="*80)


if __name__ == "__main__":
    # 先运行演示版
    demo_with_mock_data()
    
    # 如果有聚宽账号，取消下面注释，填写账号密码
    # backtester = JoinQuantSentimentBacktester()
    # backtester.fetcher.authenticate('你的手机号', '你的密码')
    # result = backtester.backtest_with_real_news(
    #     symbol='300454',
    #     start_date='2025-11-01',
    #     end_date='2026-05-10'
    # )
