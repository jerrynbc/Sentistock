"""
情绪指标量化回测模块

回测情绪指标的历史表现，验证有效性
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.collector import get_stock_history
from analysis.time_weighted_sentiment import TimeWeightedSentiment


class SentimentBacktester:
    """情绪指标回测器"""
    
    def __init__(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        benchmark_symbol: str = "000300",
        half_life_days: float = 7.0,
        buy_threshold: float = 0.3,
        sell_threshold: float = 0.7,
        initial_capital: float = 100000
    ):
        """
        初始化回测器
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期 '2025-11-01'
            end_date: 结束日期 '2026-05-10'
            benchmark_symbol: 基准指数 (默认沪深 300)
            half_life_days: 半衰期 (天)
            buy_threshold: 买入阈值 (情绪 < 该值)
            sell_threshold: 卖出阈值 (情绪 > 该值)
            initial_capital: 初始资金
        """
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.benchmark_symbol = benchmark_symbol
        self.half_life_days = half_life_days
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.initial_capital = initial_capital
        
        self.data = {}
        self.results = {}
        self.trades = {}
    
    def load_data(self):
        """加载股票数据"""
        print("="*80)
        print("加载回测数据")
        print("="*80)
        
        for symbol in self.symbols:
            print(f"\n正在加载 {symbol}...")
            df = get_stock_history(
                symbol,
                start_date=(datetime.strptime(self.start_date, '%Y-%m-%d') - timedelta(days=60)).strftime('%Y-%m-%d'),
                end_date=self.end_date,
                use_yfinance=True
            )
            
            if not df.empty:
                # 转换时间格式
                df['日期'] = pd.to_datetime(df['日期'])
                df.set_index('日期', inplace=True)
                # 计算涨跌幅
                df['涨跌幅'] = df['收盘'].pct_change() * 100
                self.data[symbol] = df
                print(f"✓ {symbol}: {len(df)} 条数据")
            else:
                print(f"✗ {symbol}: 数据获取失败")
        
        # 加载基准指数
        print(f"\n正在加载基准指数 {self.benchmark_symbol}...")
        benchmark_df = get_stock_history(
            self.benchmark_symbol,
            start_date=(datetime.strptime(self.start_date, '%Y-%m-%d') - timedelta(days=60)).strftime('%Y-%m-%d'),
            end_date=self.end_date,
            use_yfinance=True
        )
        
        if not benchmark_df.empty:
            benchmark_df['日期'] = pd.to_datetime(benchmark_df['日期'])
            benchmark_df.set_index('日期', inplace=True)
            benchmark_df['涨跌幅'] = benchmark_df['收盘'].pct_change() * 100
            self.data[self.benchmark_symbol] = benchmark_df
            print(f"✓ {self.benchmark_symbol}: {len(benchmark_df)} 条数据")
        
        print(f"\n共加载 {len(self.data)-1} 只股票 + 1 个基准指数")
        return len(self.data) > 1
    
    def _date_to_str(self, date: datetime) -> str:
        """日期对象转字符串"""
        return date.strftime('%Y%m%d')
    
    def generate_historical_sentiment(
        self,
        symbol: str,
        date: datetime
    ) -> float:
        """
        生成历史情绪得分 (模拟)
        
        在真实环境中，这里应该是历史新闻的情绪分析
        现在用模拟数据 + 价格波动来生成"历史情绪"
        
        Args:
            symbol: 股票代码
            date: 日期
        
        Returns:
            情绪得分 (0-1)
        """
        df = self.data[symbol]
        
        # 获取过去 7 天的数据
        past_7days = df.loc[:date.strftime('%Y-%m-%d')].head(7)
        
        if len(past_7days) < 3:
            return 0.5  # 数据不足
        
        # 基于价格波动"模拟"情绪
        # 上涨 = 情绪好，下跌 = 情绪差
        avg_return = past_7days['涨跌幅'].mean()
        
        # 将收益率映射到情绪得分 (0-1)
        # 假设：涨 5% 以上情绪极好 (0.8+)，跌 5% 以上情绪极差 (0.2-)
        sentiment_score = 0.5 + avg_return / 10
        
        # 限制在 0-1 范围
        sentiment_score = max(0, min(1, sentiment_score))
        
        # 添加一些随机波动 (模拟新闻的影响)
        np.random.seed(hash(str(date)) % 2**32)
        noise = np.random.normal(0, 0.05)
        sentiment_score += noise
        sentiment_score = max(0, min(1, sentiment_score))
        
        return round(sentiment_score, 3)
    
    def backtest_sentiment_strategy(self, symbol: str) -> Dict:
        """
        回测情绪策略
        
        Args:
            symbol: 股票代码
        
        Returns:
            回测结果字典
        """
        print(f"\n{'='*80}")
        print(f"回测 {symbol} - 情绪策略")
        print(f"{'='*80}")
        
        df = self.data[symbol].copy()
        df = df.sort_index()
        
        # 生成历史情绪得分
        print("正在生成历史情绪数据...")
        sentiment_scores = []
        for date in df.index:
            score = self.generate_historical_sentiment(symbol, date)
            sentiment_scores.append(score)
        
        df['情绪得分'] = sentiment_scores
        
        # 应用时间加权
        analyzer = TimeWeightedSentiment(half_life_days=self.half_life_days)
        df['加权情绪'] = df['情绪得分'].rolling(window=7).apply(
            lambda x: analyzer.calculate_weighted_sentiment([
                {'sentiment': {'score': s}, 'created_at': str(idx)}
                for idx, s in zip(x.index, x)
            ])['weighted_score'],
            raw=False
        )
        
        # 填充 NaN
        df['加权情绪'].fillna(df['情绪得分'], inplace=True)
        
        # 交易信号
        df['信号'] = 0
        df.loc[df['加权情绪'] < self.buy_threshold, '信号'] = 1   # 买入
        df.loc[df['加权情绪'] > self.sell_threshold, '信号'] = -1  # 卖出
        
        # 回测
        print("执行回测...")
        position = 0  # 持仓数量
        cash = self.initial_capital
        trades = []
        portfolio_values = []
        
        for i, (date, row) in enumerate(df.iterrows()):
            if i < 7:  # 前 7 天数据不足
                portfolio_values.append(cash)
                continue
            
            # 买入信号
            if row['信号'] == 1 and position == 0:
                # 全仓买入
                shares = int(cash * 0.95 / row['收盘'])  # 留 5% 现金
                if shares > 0:
                    cost = shares * row['收盘']
                    cash -= cost
                    position = shares
                    trades.append({
                        'date': date,
                        'type': 'buy',
                        'price': row['收盘'],
                        'shares': shares,
                        'emotion': row['加权情绪']
                    })
            
            # 卖出信号
            elif row['信号'] == -1 and position > 0:
                # 全部卖出
                revenue = position * row['收盘']
                cash += revenue
                profit = revenue - (self.initial_capital - cash)
                trades.append({
                    'date': date,
                    'type': 'sell',
                    'price': row['收盘'],
                    'shares': position,
                        'emotion': row['加权情绪'],
                    'profit': profit
                })
                position = 0
            
            # 计算组合价值
            portfolio_value = cash + (position * row['收盘'])
            portfolio_values.append(portfolio_value)
        
        # 清仓
        if position > 0:
            final_value = cash + position * df.iloc[-1]['收盘']
        else:
            final_value = cash
        
        # 计算指标
        portfolio_values = pd.Series(portfolio_values, index=df.index[:len(portfolio_values)])
        
        returns = portfolio_values.pct_change().dropna()
        
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        annual_return = (1 + total_return/100) ** (365/len(df)) - 1
        annual_return *= 100
        
        # 基准收益
        benchmark_df = self.data[self.benchmark_symbol]
        benchmark_df = benchmark_df[benchmark_df.index.isin(df.index)]
        benchmark_return = (
            (benchmark_df['收盘'].iloc[-1] - benchmark_df['收盘'].iloc[0]) / 
            benchmark_df['收盘'].iloc[0] * 100
        )
        
        # 最大回撤
        rolling_max = portfolio_values.expanding().max()
        drawdowns = (portfolio_values - rolling_max) / rolling_max * 100
        max_drawdown = drawdowns.min()
        
        # 夏普比率 (假设无风险利率 3%)
        if len(returns) > 0 and returns.std() != 0:
            sharpe = (returns.mean() - 0.03/252) / returns.std() * np.sqrt(252)
        else:
            sharpe = 0
        
        # 交易统计
        buy_trades = [t for t in trades if t['type'] == 'buy']
        sell_trades = [t for t in trades if t['type'] == 'sell']
        
        profitable_trades = len([t for t in sell_trades if t['profit'] > 0])
        total_closed_trades = len(sell_trades)
        win_rate = profitable_trades / total_closed_trades * 100 if total_closed_trades > 0 else 0
        
        return {
            'symbol': symbol,
            'total_return': round(total_return, 2),
            'annual_return': round(annual_return, 2),
            'benchmark_return': round(benchmark_return, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe, 2),
            'total_trades': len(trades),
            'buy_signals': len(buy_trades),
            'sell_signals': len(sell_trades),
            'win_rate': round(win_rate, 2),
            'final_value': round(final_value, 2),
            'trades': trades,
            'portfolio_values': portfolio_values,
            'df': df
        }
    
    def run_backtest(self) -> Dict:
        """
        运行完整回测
        
        Returns:
            综合回测结果
        """
        if not self.data:
            self.load_data()
        
        all_results = {}
        
        for symbol in self.symbols:
            result = self.backtest_sentiment_strategy(symbol)
            all_results[symbol] = result
        
        self.results = all_results
        
        # 打印汇总
        self.print_summary()
        
        return all_results
    
    def print_summary(self):
        """打印回测汇总"""
        print("\n" + "="*80)
        print("回测结果汇总")
        print("="*80)
        print(f"回测周期：{self.start_date} 至 {self.end_date}")
        print(f"半衰期：{self.half_life_days} 天")
        print(f"买入阈值：< {self.buy_threshold}")
        print(f"卖出阈值：> {self.sell_threshold}")
        print("="*80)
        
        print(f"\n{'股票':<10} {'总收益':>10} {'年化':>10} {'基准':>10} {'回撤':>10} {'夏普':>8} {'胜率':>8} {'交易':>6}")
        print("-"*80)
        
        for symbol, result in self.results.items():
            print(
                f"{symbol:<10} "
                f"{result['total_return']:>9.2f}% "
                f"{result['annual_return']:>9.2f}% "
                f"{result['benchmark_return']:>9.2f}% "
                f"{result['max_drawdown']:>9.2f}% "
                f"{result['sharpe_ratio']:>8.2f} "
                f"{result['win_rate']:>7.1f}% "
                f"{result['total_trades']:>6}次"
            )
        
        # 计算平均表现
        avg_return = np.mean([r['total_return'] for r in self.results.values()])
        avg_win_rate = np.mean([r['win_rate'] for r in self.results.values()])
        avg_sharpe = np.mean([r['sharpe_ratio'] for r in self.results.values()])
        
        print("-"*80)
        print(f"{'平均':<10} {avg_return:>9.2f}% {'':>9} {'':>10} {'':>10} {avg_sharpe:>8.2f} {avg_win_rate:>7.1f}%")
        
        print("\n" + "="*80)
        print("【回测结论】")
        if avg_win_rate > 55:
            print("✓ 情绪指标有效！胜率超过随机水平")
        else:
            print("⚠ 情绪指标胜率一般，需要优化参数或结合其他指标")
        
        if avg_sharpe > 1:
            print("✓ 风险调整后收益良好 (夏普 > 1)")
        
        print(f"✓ 平均年化收益：{avg_return:.1f}%")
        print(f"✓ 平均胜率：{avg_win_rate:.1f}%")
        print("="*80)
    
    def plot_results(self, symbol: str = None):
        """
        绘制回测结果
        
        Args:
            symbol: 股票代码，None 则绘制所有
        """
        if symbol:
            symbols_to_plot = [symbol]
        else:
            symbols_to_plot = list(self.results.keys())
        
        for symbol in symbols_to_plot:
            if symbol not in self.results:
                continue
            
            result = self.results[symbol]
            df = result['df']
            
            fig, axes = plt.subplots(3, 1, figsize=(14, 10))
            
            # 图 1: 价格和情绪
            ax1 = axes[0]
            ax1.plot(df.index, df['收盘'], label='Price', linewidth=2)
            ax1.set_ylabel('Price', fontsize=12)
            ax1.set_title(f'{symbol} - 回测结果', fontsize=14, fontweight='bold')
            
            # 标记买卖点
            buy_trades = [t for t in result['trades'] if t['type'] == 'buy']
            sell_trades = [t for t in result['trades'] if t['type'] == 'sell']
            
            if buy_trades:
                buy_dates = [t['date'] for t in buy_trades]
                buy_prices = [t['price'] for t in buy_trades]
                ax1.scatter(buy_dates, buy_prices, color='green', marker='^', 
                          s=100, label='Buy', zorder=5)
            
            if sell_trades:
                sell_dates = [t['date'] for t in sell_trades]
                sell_prices = [t['price'] for t in sell_trades]
                ax1.scatter(sell_dates, sell_prices, color='red', marker='v', 
                          s=100, label='Sell', zorder=5)
            
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 图 2: 情绪得分
            ax2 = axes[1]
            ax2.plot(df.index, df['加权情绪'], label='Weighted Sentiment', 
                    color='purple', linewidth=2)
            ax2.axhline(y=self.buy_threshold, color='green', linestyle='--', 
                       label='Buy Threshold', alpha=0.5)
            ax2.axhline(y=self.sell_threshold, color='red', linestyle='--', 
                       label='Sell Threshold', alpha=0.5)
            ax2.fill_between(df.index, self.buy_threshold, self.sell_threshold, 
                           alpha=0.2, color='gray', label='Neutral Zone')
            ax2.set_ylabel('Sentiment Score', fontsize=12)
            ax2.legend(loc='upper left', fontsize=9)
            ax2.grid(True, alpha=0.3)
            
            # 图 3: 组合价值 vs 基准
            ax3 = axes[2]
            ax3.plot(result['portfolio_values'].index, 
                    result['portfolio_values'] / self.initial_capital,
                    label='Portfolio', linewidth=2, color='blue')
            
            # 基准
            benchmark_df = self.data[self.benchmark_symbol]
            benchmark_normalized = (
                benchmark_df['收盘'] / benchmark_df['收盘'].iloc[0]
            )
            ax3.plot(benchmark_normalized.index, benchmark_normalized, 
                    label='Benchmark', linewidth=2, color='gray', linestyle='--')
            
            ax3.set_ylabel('Normalized Value', fontsize=12)
            ax3.set_xlabel('Date', fontsize=12)
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            os.makedirs('output/charts', exist_ok=True)
            save_path = os.path.join('output', 'charts', f"{symbol}_backtest_result.png")
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存：{save_path}")
            plt.show()


def demo_backtest():
    """演示回测"""
    print("="*80)
    print("情绪指标量化回测 - 演示")
    print("="*80)
    
    backtester = SentimentBacktester(
        symbols=['300454', '000001'],
        start_date='2025-11-01',
        end_date='2026-05-10',
        benchmark_symbol='000300',
        half_life_days=7,
        buy_threshold=0.3,
        sell_threshold=0.7,
        initial_capital=100000
    )
    
    if not backtester.load_data():
        print("数据加载失败")
        return
    
    results = backtester.run_backtest()
    
    # 绘制结果
    for symbol in backtester.symbols:
        backtester.plot_results(symbol)
    
    # 保存报告
    backtester.save_report()


if __name__ == "__main__":
    demo_backtest()
