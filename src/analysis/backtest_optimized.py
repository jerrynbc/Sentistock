"""
真实数据回测优化版 - 完整交易策略 + 参数优化 + 数据缓存

优化点:
1. 数据缓存 - 避免重复查询聚宽 SDK
2. 完整交易策略 - 买入后按止损/止盈卖出
3. 参数优化 - 网格搜索最优参数
4. 多股票测试 - 验证策略普适性

用法:
    # 首次运行（获取数据 + 回测 + 参数优化）
    python src/analysis/backtest_optimized.py 300454 --user 15620693228 --password 'Zrdsg0510,'
    
    # 使用缓存数据（不查询聚宽）
    python src/analysis/backtest_optimized.py 300454 --use-cache --optimize
    
    # 多股票测试
    python src/analysis/backtest_optimized.py --multi-test --use-cache
    
    # 批量查询多只股票（会消耗 SDK 次数）
    python src/analysis/backtest_optimized.py --multi-test --user ... --password ...
"""

import jqdatasdk as jq
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from itertools import product
import argparse
import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.sentiment import analyze_single_sentiment
from analysis.time_weighted_sentiment import TimeWeightedSentiment
from analysis.indicators import calculate_all_indicators
from analysis.stock_scorer import StockScorer, score_stocks_batch, print_score_summary

# 聚宽账号配置
JQ_USER = os.getenv('JQ_USER', '')
JQ_PASSWORD = os.getenv('JQ_PASSWORD', '')

# 缓存目录
CACHE_DIR = 'data/cache'
RESULTS_FILE = 'data/backtest_results.json'


class DataCache:
    """数据缓存 - 避免重复查询聚宽 SDK"""
    
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _price_path(self, symbol: str, start: str, end: str) -> str:
        return os.path.join(self.cache_dir, f"{symbol}_{start}_{end}_price.csv")
    
    def save_price(self, df: pd.DataFrame, symbol: str, start: str, end: str):
        path = self._price_path(symbol, start, end)
        df.to_csv(path, index=False)
        print(f"💾 价格数据已缓存：{path}")
    
    def load_price(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        path = self._price_path(symbol, start, end)
        if os.path.exists(path):
            df = pd.read_csv(path)
            print(f"📂 从缓存加载：{symbol}")
            return df
        return pd.DataFrame()
    
    def is_cached(self, symbol: str, start: str, end: str) -> bool:
        return os.path.exists(self._price_path(symbol, start, end))


class TradingStrategy:
    """
    完整交易策略回测
    
    策略逻辑:
    1. 情绪 < buy_threshold + 价格 > MA20 → 买入
    2. 持仓期间:
       - 跌破 MA20 → 止损卖出
       - 收益 > take_profit → 止盈卖出
       - 持有 > max_hold_days → 强制卖出
    """
    
    def __init__(
        self,
        buy_threshold: float = 0.25,
        sell_threshold: float = 0.65,
        stop_loss_pct: float = -0.05,
        take_profit_pct: float = 0.20,
        max_hold_days: int = 20,
        trend_filter: bool = True,
        signal_confirm: int = 1,
    ):
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_hold_days = max_hold_days
        self.trend_filter = trend_filter
        self.signal_confirm = signal_confirm
    
    def run(self, df: pd.DataFrame) -> Dict:
        """
        执行策略回测
        
        Returns:
            策略结果字典
        """
        df = df.copy()
        
        # 统一列名
        column_map = {
            '日期': 'date', '收盘': 'close', '开盘': 'open',
            '最高': 'high', '最低': 'low', '成交量': 'volume'
        }
        df.rename(columns=column_map, inplace=True)
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        
        # 趋势判断
        df['trend'] = 0
        df.loc[df['close'] > df['MA20'], 'trend'] = 1
        df.loc[df['close'] < df['MA20'], 'trend'] = -1
        
        # 信号确认
        df['signal_raw'] = 0
        df.loc[df['sentiment_score'] < self.buy_threshold, 'signal_raw'] = 1
        
        if self.signal_confirm > 1:
            df['signal'] = df['signal_raw'].rolling(window=self.signal_confirm).apply(
                lambda x: 1 if (x == 1).all() else 0
            )
        else:
            df['signal'] = df['signal_raw']
        
        # 趋势过滤
        if self.trend_filter:
            df.loc[(df['signal'] == 1) & (df['trend'] != 1), 'signal'] = 0
        
        # 交易模拟
        trades = []
        position = None  # None = 空仓, dict = 持仓
        
        for i, (date, row) in enumerate(df.iterrows()):
            if position is None:
                # 空仓，检查买入信号
                if row['signal'] == 1:
                    position = {
                        'buy_date': date,
                        'buy_price': row['close'],
                        'buy_sentiment': row['sentiment_score'],
                        'high_price': row['close'],
                        'days_held': 0,
                    }
            else:
                # 持仓中
                position['days_held'] += 1
                position['high_price'] = max(position['high_price'], row['close'])
                
                current_return = (row['close'] - position['buy_price']) / position['buy_price']
                max_return = (position['high_price'] - position['buy_price']) / position['buy_price']
                
                # 卖出条件检查
                sell_reason = None
                
                # 1. 止损：跌破 MA20
                if self.trend_filter and row['close'] < row['MA20']:
                    sell_reason = 'stop_loss_trend'
                
                # 2. 止损：亏损超过阈值
                elif current_return <= self.stop_loss_pct:
                    sell_reason = 'stop_loss'
                
                # 3. 止盈：从最高点回撤超过 10%
                elif max_return > 0.10 and current_return < max_return - 0.10:
                    sell_reason = 'trailing_stop'
                
                # 4. 止盈：收益达到目标
                elif current_return >= self.take_profit_pct:
                    sell_reason = 'take_profit'
                
                # 5. 超时：持仓天数超过上限
                elif position['days_held'] >= self.max_hold_days:
                    sell_reason = 'timeout'
                
                if sell_reason:
                    trade = {
                        'buy_date': position['buy_date'],
                        'sell_date': date,
                        'buy_price': position['buy_price'],
                        'sell_price': row['close'],
                        'buy_sentiment': position['buy_sentiment'],
                        'return_pct': current_return * 100,
                        'max_return_pct': max_return * 100,
                        'days_held': position['days_held'],
                        'sell_reason': sell_reason,
                    }
                    trades.append(trade)
                    position = None
        
        # 计算结果
        if not trades:
            return {
                'trade_count': 0,
                'avg_return': 0,
                'win_rate': 0,
                'avg_hold_days': 0,
                'total_return': 0,
                'max_return': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
            }
        
        trades_df = pd.DataFrame(trades)
        
        # 基础指标
        win_trades = trades_df[trades_df['return_pct'] > 0] if len(trades) > 0 else pd.DataFrame()
        total_return = (trades_df['return_pct'] / 100 + 1).prod() - 1 if len(trades) > 0 else 0
        
        # 最大回撤
        if len(trades) > 0:
            cumulative = (trades_df['return_pct'] / 100 + 1).cumprod()
            running_max = cumulative.cummax()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()
        else:
            max_drawdown = 0
        
        # 夏普比率 (假设无风险利率 3%)
        if len(trades) > 0 and trades_df['days_held'].std() > 0:
            daily_returns = trades_df['return_pct'] / trades_df['days_held']
            sharpe = (daily_returns.mean() * 252 - 3) / (daily_returns.std() * np.sqrt(252))
        else:
            sharpe = 0
        
        # 按卖出原因统计
        sell_reason_count = {}
        sell_reason_return = {}
        sell_reason_days = {}
        for t in trades:
            reason = t['sell_reason']
            sell_reason_count[reason] = sell_reason_count.get(reason, 0) + 1
            sell_reason_return[reason] = sell_reason_return.get(reason, 0) + t['return_pct']
            sell_reason_days[reason] = sell_reason_days.get(reason, 0) + t['days_held']
        
        sell_reason_stats = {}
        for reason in sell_reason_count:
            count = sell_reason_count[reason]
            sell_reason_stats[reason] = {
                'count': count,
                'avg_return': sell_reason_return[reason] / count,
                'avg_days': sell_reason_days[reason] / count,
            }
        
        results = {
            'trade_count': len(trades),
            'win_count': len(win_trades),
            'lose_count': len(trades) - len(win_trades),
            'win_rate': len(win_trades) / len(trades) * 100 if len(trades) > 0 else 0,
            'avg_return': trades_df['return_pct'].mean() if len(trades) > 0 else 0,
            'avg_win': win_trades['return_pct'].mean() if len(win_trades) > 0 else 0,
            'avg_loss': trades_df[trades_df['return_pct'] < 0]['return_pct'].mean() if len(trades) - len(win_trades) > 0 else 0,
            'avg_hold_days': trades_df['days_held'].mean() if len(trades) > 0 else 0,
            'total_return': total_return * 100,
            'max_return': trades_df['return_pct'].max() if len(trades) > 0 else 0,
            'min_return': trades_df['return_pct'].min() if len(trades) > 0 else 0,
            'max_drawdown': max_drawdown * 100,
            'sharpe_ratio': sharpe,
            'sell_reasons': sell_reason_stats,
        }
        
        return results
    
    def print_results(self, results: Dict):
        """打印策略结果"""
        print(f"\n{'='*80}")
        print("交易策略回测结果")
        print(f"{'='*80}")
        
        if results['trade_count'] == 0:
            print("\n⚠️ 没有交易信号")
            return
        
        print(f"\n【总体表现】")
        print(f"  交易次数：{results['trade_count']}")
        print(f"  胜率：{results['win_rate']:.1f}% ({results['win_count']}胜 {results['lose_count']}负)")
        print(f"  平均收益：{results['avg_return']:+.2f}%")
        print(f"  最大单笔盈利：{results['max_return']:+.2f}%")
        print(f"  最大单笔亏损：{results['min_return']:+.2f}%")
        print(f"  平均持仓：{results['avg_hold_days']:.1f} 天")
        print(f"  累计收益：{results['total_return']:+.2f}%")
        print(f"  最大回撤：{results['max_drawdown']:.2f}%")
        print(f"  夏普比率：{results['sharpe_ratio']:.2f}")
        
        print(f"\n【卖出原因统计】")
        if 'sell_reasons' in results and results['sell_reasons']:
            reason_map = {
                'stop_loss_trend': '跌破 MA20',
                'stop_loss': '止损',
                'trailing_stop': '回撤止盈',
                'take_profit': '目标止盈',
                'timeout': '超时',
            }
            for reason, stats in results['sell_reasons'].items():
                label = reason_map.get(reason, reason)
                print(f"  {label}: {stats['count']} 次 | 平均收益 {stats['avg_return']:+.2f}% | 平均持仓 {stats['avg_days']:.0f} 天")
    
    def score(self, results: Dict) -> float:
        """
        策略评分
        
        评分公式:
        胜率 * 0.3 + 累计收益 * 0.3 + 夏普比率 * 20 * 0.2 - 最大回撤 * 0.2
        """
        win_score = min(results['win_rate'], 80) / 80 * 100  # 最高 80% = 满分
        return_score = min(results['total_return'], 100)  # 最高 100% = 满分
        sharpe_score = min(max(results['sharpe_ratio'] * 20 + 50, 0), 100)  # 夏普 0-2.5 = 50-100
        drawdown_score = max(100 + results['max_drawdown'], 0)  # 回撤 0% = 满分
        
        return win_score * 0.3 + return_score * 0.3 + sharpe_score * 0.2 + drawdown_score * 0.2


class OptimizedBacktester:
    """优化版回测器"""
    
    def __init__(self):
        self.authenticated = False
        self.cache = DataCache()
    
    def login(self, user: str = None, password: str = None) -> bool:
        if user is None:
            user = JQ_USER
        if password is None:
            password = JQ_PASSWORD
        
        if not user or not password:
            print("❌ 请提供聚宽账号密码")
            return False
        
        try:
            jq.auth(user, password)
            self.authenticated = True
            print(f"✅ 聚宽登录成功：{user[:3]}****{user[-4:]}")
            return True
        except Exception as e:
            print(f"❌ 登录失败：{e}")
            return False
    
    def fetch_price_data(self, symbol: str, start_date: str, end_date: str,
                        use_cache: bool = True) -> pd.DataFrame:
        if use_cache:
            df = self.cache.load_price(symbol, start_date, end_date)
            if not df.empty:
                return df
        
        if not self.authenticated:
            print("❌ 未登录聚宽，无法获取数据")
            return pd.DataFrame()
        
        jq_symbol = self._to_jq_symbol(symbol)
        print(f"🔄 查询聚宽：{jq_symbol}")
        
        df = jq.get_price(
            security=jq_symbol,
            start_date=start_date,
            end_date=end_date,
            frequency='daily',
            fields=['open', 'close', 'high', 'low', 'volume']
        )
        
        if df is None or df.empty:
            print(f"❌ {symbol} 无数据")
            return pd.DataFrame()
        
        df.index.name = 'date'
        df.reset_index(inplace=True)
        print(f"✅ {symbol}: {len(df)} 条")
        
        self.cache.save_price(df, symbol, start_date, end_date)
        
        # 休眠避免限流
        time.sleep(0.5)
        
        return df
    
    def prepare_data(self, price_df: pd.DataFrame) -> pd.DataFrame:
        print("📊 计算指标和情绪分数...")
        
        df = price_df.copy()
        column_map = {
            'open': '开盘', 'close': '收盘', 'high': '最高', 'low': '最低',
            'volume': '成交量', 'date': '日期'
        }
        df.rename(columns=column_map, inplace=True)
        df['日期'] = pd.to_datetime(df['日期'])
        
        df = calculate_all_indicators(df)
        
        # 情绪分数
        rsi_norm = 1 - (df['RSI'] / 100)
        macd_hist = df['MACD_hist']
        macd_norm = (macd_hist - macd_hist.min()) / (macd_hist.max() - macd_hist.min() + 1e-8)
        bb_pos = (df['收盘'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'] + 1e-8)
        bb_norm = 1 - bb_pos
        
        df['sentiment_score'] = 0.4 * rsi_norm + 0.3 * macd_norm + 0.3 * bb_norm
        df['sentiment_score'] = df['sentiment_score'].clip(0.1, 0.9)
        
        return df
    
    def optimize_parameters(self, df: pd.DataFrame) -> Dict:
        print(f"\n{'='*80}")
        print("参数优化 - 网格搜索")
        print(f"{'='*80}")
        
        buy_thresholds = [0.15, 0.20, 0.25, 0.30, 0.35]
        sell_thresholds = [0.60, 0.65, 0.70, 0.75]
        stop_losses = [-0.03, -0.05, -0.08, -0.10]
        take_profits = [0.15, 0.20, 0.25, 0.30]
        max_holds = [10, 15, 20, 30]
        
        best_score = -999
        best_params = {}
        best_results = {}
        
        total = len(buy_thresholds) * len(sell_thresholds) * len(stop_losses) * len(take_profits) * len(max_holds)
        count = 0
        
        print(f"共 {total} 组参数...\n")
        
        for buy_th, sell_th, sl, tp, mh in product(
            buy_thresholds, sell_thresholds, stop_losses, take_profits, max_holds
        ):
            count += 1
            if count % 100 == 0:
                print(f"  已测试 {count}/{total}...")
            
            strategy = TradingStrategy(
                buy_threshold=buy_th,
                sell_threshold=sell_th,
                stop_loss_pct=sl,
                take_profit_pct=tp,
                max_hold_days=mh,
            )
            
            results = strategy.run(df)
            
            if results['trade_count'] >= 5:
                score = strategy.score(results)
                if score > best_score:
                    best_score = score
                    best_params = {
                        'buy_threshold': buy_th,
                        'sell_threshold': sell_th,
                        'stop_loss_pct': sl,
                        'take_profit_pct': tp,
                        'max_hold_days': mh,
                    }
                    best_results = results
        
        print(f"\n{'='*80}")
        print("最优参数")
        print(f"{'='*80}")
        print(f"买入阈值：{best_params['buy_threshold']}")
        print(f"卖出阈值：{best_params['sell_threshold']}")
        print(f"止损：{best_params['stop_loss_pct']*100:.0f}%")
        print(f"止盈：{best_params['take_profit_pct']*100:.0f}%")
        print(f"最大持仓：{best_params['max_hold_days']} 天")
        print(f"综合得分：{best_score:.2f}")
        
        return {
            'params': best_params,
            'results': best_results,
            'score': best_score,
        }
    
    def test_multi_stocks(self, symbols: List[str], start_date: str, end_date: str,
                         use_cache: bool = True) -> Dict:
        """多股票测试"""
        print(f"\n{'='*80}")
        print(f"多股票测试")
        print(f"{'='*80}")
        print(f"股票列表：{', '.join(symbols)}")
        print(f"时间范围：{start_date} 至 {end_date}")
        print(f"{'='*80}")
        
        # 先获取所有数据
        all_data = {}
        for symbol in symbols:
            if use_cache and self.cache.is_cached(symbol, start_date, end_date):
                price_df = self.cache.load_price(symbol, start_date, end_date)
            else:
                if not self.authenticated:
                    print(f"⚠️ 未登录，跳过 {symbol}")
                    continue
                price_df = self.fetch_price_data(symbol, start_date, end_date, use_cache=True)
            
            if not price_df.empty:
                all_data[symbol] = price_df
        
        if not all_data:
            print("❌ 没有可用数据")
            return {}
        
        # 股票评分
        print(f"\n{'='*80}")
        print("股票评分")
        print(f"{'='*80}")
        
        scorer = StockScorer()
        score_results = score_stocks_batch(scorer, all_data)
        print_score_summary(score_results)
        
        # 过滤：只对情绪适用度 >= 阈值的股票回测
        min_score = 50  # 默认阈值
        suitable_stocks = {
            name: df for name, df in all_data.items()
            if score_results.get(name, {}).get('scores', {}).get('sentiment_suitability', 0) >= min_score
        }
        
        skipped = {
            name: score_results[name]['scores']['sentiment_suitability']
            for name in set(all_data.keys()) - set(suitable_stocks.keys())
        }
        if skipped:
            print(f"\n⚠️ 以下股票情绪适用度 < {min_score}，跳过回测：")
            for name, score in skipped.items():
                print(f"   {name}: {score:.0f} 分")
        
        if not suitable_stocks:
            print("❌ 没有适合情绪模块的股票")
            return {}
        
        # 用最优参数测试
        print(f"\n{'='*80}")
        print(f"情绪模块回测（适用度 >= {min_score} 的标的）")
        print(f"{'='*80}")
        
        # 先用第一只股票做参数优化
        first_symbol = list(suitable_stocks.keys())[0]
        print(f"\n📈 用 {first_symbol} 做参数优化...")
        first_df = self.prepare_data(suitable_stocks[first_symbol])
        opt = self.optimize_parameters(first_df)
        params = opt['params']
        
        strategy = TradingStrategy(**params)
        
        # 测试所有适合的股票
        results_all = {}
        for symbol, price_df in suitable_stocks.items():
            print(f"\n📊 测试 {symbol}...")
            df = self.prepare_data(price_df)
            results = strategy.run(df)
            results_all[symbol] = results
            
            print(f"  交易次数：{results['trade_count']}")
            print(f"  胜率：{results['win_rate']:.1f}%")
            print(f"  平均收益：{results['avg_return']:+.2f}%")
            print(f"  累计收益：{results['total_return']:+.2f}%")
            print(f"  夏普比率：{results['sharpe_ratio']:.2f}")
        
        # 汇总
        print(f"\n{'='*80}")
        print("汇总统计（仅情绪模块适用标的）")
        print(f"{'='*80}")
        
        total_trades = sum(r['trade_count'] for r in results_all.values())
        avg_win_rate = np.mean([r['win_rate'] for r in results_all.values() if r['trade_count'] > 0])
        avg_return = np.mean([r['avg_return'] for r in results_all.values() if r['trade_count'] > 0])
        total_return = np.mean([r['total_return'] for r in results_all.values() if r['trade_count'] > 0])
        avg_sharpe = np.mean([r['sharpe_ratio'] for r in results_all.values() if r['trade_count'] > 0])
        
        print(f"测试股票数：{len(results_all)}")
        print(f"总交易次数：{total_trades}")
        print(f"平均胜率：{avg_win_rate:.1f}%")
        print(f"平均收益：{avg_return:+.2f}%")
        print(f"平均累计收益：{total_return:+.2f}%")
        print(f"平均夏普比率：{avg_sharpe:.2f}")
        
        return {
            'scores': score_results,
            'params': params,
            'results': results_all,
            'summary': {
                'stock_count': len(results_all),
                'skipped_count': len(skipped),
                'total_trades': total_trades,
                'avg_win_rate': avg_win_rate,
                'avg_return': avg_return,
                'total_return': total_return,
                'avg_sharpe': avg_sharpe,
            }
        }
    
    def _to_jq_symbol(self, symbol: str) -> str:
        if '.XSHG' in symbol or '.XSHE' in symbol:
            return symbol
        if symbol.startswith(('6', '5')):
            return f"{symbol}.XSHG"
        return f"{symbol}.XSHE"


def main():
    parser = argparse.ArgumentParser(description='优化版回测')
    parser.add_argument('symbol', nargs='?', default=None, help='股票代码')
    parser.add_argument('--start', default=None, help='开始日期')
    parser.add_argument('--end', default=None, help='结束日期')
    parser.add_argument('--user', default=None, help='聚宽账号')
    parser.add_argument('--password', default=None, help='聚宽密码')
    parser.add_argument('--use-cache', action='store_true', help='使用缓存')
    parser.add_argument('--optimize', action='store_true', help='参数优化')
    parser.add_argument('--multi-test', action='store_true', help='多股票测试')
    
    args = parser.parse_args()
    
    if args.end is None:
        args.end = '2025-12-31'
    if args.start is None:
        args.start = '2025-01-01'
    
    backtester = OptimizedBacktester()
    
    # 多股票测试
    if args.multi_test:
        symbols = [
            '300454',  # 深信服
            '000001',  # 平安银行
            '600519',  # 贵州茅台
            '000858',  # 五粮液
            '601318',  # 中国平安
            '002594',  # 比亚迪
            '600036',  # 招商银行
            '000333',  # 美的集团
        ]
        
        if args.use_cache:
            print("📂 缓存模式，不查询聚宽")
        else:
            if not backtester.login(args.user, args.password):
                return
        
        results = backtester.test_multi_stocks(symbols, args.start, args.end, args.use_cache)
        return
    
    # 单股票测试
    symbol = args.symbol
    if not symbol:
        print("❌ 请指定股票代码")
        return
    
    print(f"\n{'='*80}")
    print(f"Sentistock 优化版回测")
    print(f"股票：{symbol}")
    print(f"时间：{args.start} 至 {args.end}")
    print(f"{'='*80}")
    
    if args.use_cache:
        print("📂 缓存模式")
        price_df = backtester.cache.load_price(symbol, args.start, args.end)
        if price_df.empty:
            print("❌ 缓存中无数据，请先运行不带 --use-cache 的命令")
            return
    else:
        if not backtester.login(args.user, args.password):
            return
        price_df = backtester.fetch_price_data(symbol, args.start, args.end, use_cache=True)
    
    if price_df.empty:
        return
    
    df = backtester.prepare_data(price_df)
    
    if args.optimize:
        opt = backtester.optimize_parameters(df)
        print(f"\n最优参数回测结果:")
        strategy = TradingStrategy(**opt['params'])
        results = strategy.run(df)
        strategy.print_results(results)
    else:
        strategy = TradingStrategy()
        results = strategy.run(df)
        strategy.print_results(results)
    
    print(f"\n{'='*80}")
    print("回测完成")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
