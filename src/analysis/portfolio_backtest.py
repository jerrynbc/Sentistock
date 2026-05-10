"""
多股组合回测器

功能:
1. 支持等权 (Equal Weight) 和 评分加权 (Score Weight)
2. 资金独立子账户模型 (每个股票分配固定比例资金，独立交易)
3. 组合收益曲线、组合夏普、组合最大回撤
4. 个股贡献度分析
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from analysis.indicators import calculate_all_indicators
from analysis.stock_scorer import StockScorer, score_stocks_batch
from analysis.backtest_optimized import TradingStrategy
from analysis.utils import prepare_data as prepare_portfolio_data


class PortfolioStrategy:
    """多股组合策略"""
    
    def __init__(
        self,
        symbols: List[str],
        weights: Dict[str, float],
        initial_capital: float = 1_000_000,
        **kwargs
    ):
        self.symbols = symbols
        self.weights = weights
        self.initial_capital = initial_capital
        self.strategy_params = kwargs
        
    def run(self, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """
        执行组合回测
        
        Args:
            data_dict: {symbol: prepared_df}
            
        Returns:
            组合结果字典
        """
        all_dates = set()
        for df in data_dict.values():
            all_dates.update(df['日期'].tolist())
        all_dates = sorted(list(all_dates))
        
        sub_capital = {s: self.initial_capital * self.weights[s] for s in self.symbols}
        positions = {s: None for s in self.symbols}
        
        portfolio_equity = [self.initial_capital]
        trades_log = []
        
        strategies = {s: TradingStrategy(**self.strategy_params) for s in self.symbols}
        
        signals = {}
        for s, df in data_dict.items():
            df = df.copy()
            df.set_index('日期', inplace=True)
            df.sort_index(inplace=True)
            
            df['trend'] = 0
            df.loc[df['收盘'] > df['MA20'], 'trend'] = 1
            df.loc[df['收盘'] < df['MA20'], 'trend'] = -1
            
            df['signal_raw'] = 0
            df.loc[df['sentiment_score'] < strategies[s].buy_threshold, 'signal_raw'] = 1
            
            if strategies[s].signal_confirm > 1:
                df['signal'] = df['signal_raw'].rolling(window=strategies[s].signal_confirm).apply(
                    lambda x: 1 if (x == 1).all() else 0
                )
            else:
                df['signal'] = df['signal_raw']
                
            if strategies[s].trend_filter:
                df.loc[(df['signal'] == 1) & (df['trend'] != 1), 'signal'] = 0
                
            signals[s] = df
            signals[s].reset_index(inplace=True)
            signals[s].set_index('日期', inplace=True)
            
        for date in all_dates:
            date_val = pd.Timestamp(date)
            
            for s in self.symbols:
                if s not in signals or date_val not in signals[s].index:
                    continue
                    
                row = signals[s].loc[date_val]
                current_price = row['收盘']
                
                if positions[s] is None:
                    if row['signal'] == 1:
                        buy_price = current_price * (1 + strategies[s].slippage_rate)
                        invest_amount = sub_capital[s] * strategies[s].position_pct
                        
                        shares = int(invest_amount / buy_price // 100) * 100
                        if shares > 0:
                            cost = shares * buy_price * (strategies[s].commission_rate + strategies[s].transfer_rate)
                            deduction = shares * buy_price + cost
                            
                            if deduction <= sub_capital[s]:
                                sub_capital[s] -= deduction
                                positions[s] = {
                                    'buy_date': date,
                                    'buy_price': buy_price,
                                    'shares': shares,
                                    'high_price': current_price,
                                    'days_held': 0,
                                }
                else:
                    pos = positions[s]
                    pos['days_held'] += 1
                    pos['high_price'] = max(pos['high_price'], current_price)
                    
                    current_return = (current_price - pos['buy_price']) / pos['buy_price']
                    max_return = (pos['high_price'] - pos['buy_price']) / pos['buy_price']
                    
                    sell_reason = None
                    
                    if strategies[s].trend_filter and current_price < row['MA20']:
                        sell_reason = 'stop_loss_trend'
                    elif current_return <= strategies[s].stop_loss_pct:
                        sell_reason = 'stop_loss'
                    elif max_return > 0.10 and current_return < max_return - 0.10:
                        sell_reason = 'trailing_stop'
                    elif current_return >= strategies[s].take_profit_pct:
                        sell_reason = 'take_profit'
                    elif pos['days_held'] >= strategies[s].max_hold_days:
                        sell_reason = 'timeout'
                        
                    if sell_reason:
                        sell_price = current_price * (1 - strategies[s].slippage_rate)
                        shares = pos['shares']
                        
                        gross_revenue = shares * sell_price
                        cost = gross_revenue * (strategies[s].stamp_tax_rate + strategies[s].commission_rate + strategies[s].transfer_rate)
                        net_revenue = gross_revenue - cost
                        
                        sub_capital[s] += net_revenue
                        
                        buy_cost_total = pos['shares'] * pos['buy_price'] * (1 + strategies[s].commission_rate + strategies[s].transfer_rate)
                        net_pnl = net_revenue - buy_cost_total
                        return_pct = net_pnl / buy_cost_total * 100
                        
                        trades_log.append({
                            'symbol': s,
                            'buy_date': pos['buy_date'],
                            'sell_date': date,
                            'return_pct': return_pct,
                            'sell_reason': sell_reason,
                        })
                        
                        positions[s] = None
            
            total_equity = sum(sub_capital.values())
            for s in self.symbols:
                if positions[s]:
                    if date_val in signals[s].index:
                        p = signals[s].loc[date_val]['收盘']
                    else:
                        p = positions[s]['buy_price']
                    total_equity += positions[s]['shares'] * p
                    
            portfolio_equity.append(total_equity)
            
        equity_series = pd.Series(portfolio_equity)
        total_return = (equity_series.iloc[-1] / equity_series.iloc[0] - 1) * 100
        
        running_max = equity_series.cummax()
        drawdown = (equity_series - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        daily_returns = equity_series.pct_change().dropna()
        if daily_returns.std() > 0:
            sharpe = (daily_returns.mean() * 252 - 0.03) / (daily_returns.std() * np.sqrt(252))
        else:
            sharpe = 0
            
        trades_df = pd.DataFrame(trades_log)
        symbol_stats = {}
        if not trades_df.empty:
            for s in self.symbols:
                s_trades = trades_df[trades_df['symbol'] == s]
                if not s_trades.empty:
                    win_rate = (s_trades['return_pct'] > 0).mean() * 100
                    avg_ret = s_trades['return_pct'].mean()
                    symbol_stats[s] = {
                        'trades': len(s_trades),
                        'win_rate': win_rate,
                        'avg_return': avg_ret,
                    }
                    
        return {
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'equity_curve': equity_series,
            'symbol_stats': symbol_stats,
            'trades': trades_log,
        }

    def print_results(self, results: Dict):
        print(f"\n{'='*80}")
        print(f"📊 多股组合回测结果")
        print(f"{'='*80}")
        print(f"\n【组合表现】")
        print(f"  累计收益：{results['total_return']:+.2f}%")
        print(f"  最大回撤：{results['max_drawdown']:.2f}%")
        print(f"  夏普比率：{results['sharpe_ratio']:.2f}")
        
        print(f"\n【个股贡献】")
        for s, stats in results['symbol_stats'].items():
            print(f"  {s}: {stats['trades']} 笔 | 胜率 {stats['win_rate']:.1f}% | 均收益 {stats['avg_return']:+.2f}%")
