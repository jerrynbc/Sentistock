"""
高级交易策略

特性:
1. 分批止盈 (Split Take Profit)
2. 追踪止损 (Trailing Stop)
3. 舆情联动卖出 (Sentiment-Driven Exit)
4. 保本机制 (Break-Even Protection)
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from analysis.backtest_optimized import TradingStrategy


class AdvancedTradingStrategy(TradingStrategy):
    """
    增强版交易策略
    
    新增逻辑:
    - Phase 1: 利润达 15% -> 卖出 50%，止损上移至保本
    - Phase 2: 利润达 30% 或 回撤超 8% -> 清仓
    - 舆情熔断: 情绪分 < 0.35 -> 立即清仓
    """
    
    def __init__(
        self,
        buy_threshold: float = 0.50, # 放宽至 0.5 (中性偏空即可)
        sell_threshold: float = 0.65,
        stop_loss_pct: float = -0.05,
        take_profit_pct: float = 0.20,
        max_hold_days: int = 20,
        trend_filter: bool = True,
        signal_confirm: int = 1,
        transaction_costs: bool = True,
        initial_capital: float = 1_000_000,
        position_strategy: str = 'fixed',
        position_pct: float = 1.0,
        # 高级参数
        sentiment_kill_switch: float = 0.15, # 舆情极度恶化阈值 (Goodness < 0.15)
        target_1_pct: float = 0.15,
        target_2_pct: float = 0.30,
        trail_stop_pct: float = 0.08,
    ):
        super().__init__(
            buy_threshold=buy_threshold,
            sell_threshold=sell_threshold,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            max_hold_days=max_hold_days,
            trend_filter=trend_filter,
            signal_confirm=signal_confirm,
            transaction_costs=transaction_costs,
            initial_capital=initial_capital,
            position_strategy=position_strategy,
            position_pct=position_pct
        )
        self.sentiment_kill_switch = sentiment_kill_switch
        self.target_1_pct = target_1_pct
        self.target_2_pct = target_2_pct
        self.trail_stop_pct = trail_stop_pct
    
    def run(self, df: pd.DataFrame) -> Dict:
        """执行增强版回测"""
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
            
        if self.trend_filter:
            df.loc[(df['signal'] == 1) & (df['trend'] != 1), 'signal'] = 0
            
        # 交易模拟
        trades = []
        position = None
        current_capital = self.initial_capital
        
        for i, (date, row) in enumerate(df.iterrows()):
            # 舆情熔断检查 (最高优先级)
            kill_signal = self.sentiment_kill_switch is not None and row['sentiment_score'] < self.sentiment_kill_switch
            
            if position is None:
                # 空仓
                if row['signal'] == 1:
                    buy_price = row['close'] * (1 + self.slippage_rate)
                    shares = int((current_capital * self.position_pct) / buy_price // 100) * 100
                    
                    if shares > 0:
                        cost = shares * buy_price * (self.commission_rate + self.transfer_rate)
                        actual_cost = shares * buy_price + cost
                        
                        if actual_cost <= current_capital:
                            current_capital -= actual_cost
                            position = {
                                'buy_date': date,
                                'buy_price': buy_price,
                                'shares': shares,
                                'remaining_shares': shares,
                                'max_price': row['close'],
                                'break_even_price': buy_price,
                                'phase': 1,
                                'buy_sentiment': row['sentiment_score'],
                                'days_held': 0, # 初始化
                            }
            else:
                # 持仓中
                pos = position
                pos['max_price'] = max(pos['max_price'], row['close'])
                
                # 计算收益率 (相对于买入价)
                current_return = (row['close'] - pos['buy_price']) / pos['buy_price']
                
                sell_reason = None
                sell_ratio = 1.0 # 默认全部卖出
                
                # 1. 舆情熔断
                if kill_signal:
                    sell_reason = 'sentiment_kill'
                    
                # 2. 追踪止损 (Phase 1 & 2)
                elif row['close'] < pos['max_price'] * (1 - self.trail_stop_pct):
                    sell_reason = 'trailing_stop'
                    
                # 3. 第一阶段止盈 (卖出 50%)
                elif pos['phase'] == 1 and current_return >= self.target_1_pct:
                    sell_ratio = 0.5
                    sell_reason = 'take_profit_1'
                    # 更新状态：止损上移至保本
                    pos['break_even_price'] = pos['buy_price'] * (1 + self.commission_rate * 2) # 覆盖成本
                    pos['phase'] = 2
                    
                # 4. 第二阶段清仓 (最终止盈)
                elif pos['phase'] == 2 and current_return >= self.target_2_pct:
                    sell_reason = 'take_profit_2'
                    
                # 5. 第二阶段保本止损 (Phase 2 防亏损)
                elif pos['phase'] == 2 and row['close'] <= pos['break_even_price']:
                    sell_reason = 'break_even_exit'
                    
                # 6. 原始止损 (Phase 1) - 如果没触发其他条件
                elif pos['phase'] == 1 and current_return <= self.stop_loss_pct:
                    sell_reason = 'stop_loss'
                    
                # 7. 超时
                elif pos['days_held'] >= self.max_hold_days: # 需要维护 days_held，这里简化处理
                     # 注意：position 中并没有 days_held 字段，需要在上面补上，或者用索引差
                     # 由于这里重构了 position dict，需要重新维护 days_held
                     pass

                # 注意：上面代码缺少 days_held 的维护，修正如下
                if 'days_held' in pos:
                    pos['days_held'] += 1
                else:
                    pos['days_held'] = 1
                    
                if 'days_held' in pos and pos['days_held'] >= self.max_hold_days and not sell_reason:
                    sell_reason = 'timeout'

                # 执行卖出
                if sell_reason:
                    sell_price = row['close'] * (1 - self.slippage_rate)
                    
                    # 计算卖出数量
                    shares_to_sell = int(pos['remaining_shares'] * sell_ratio // 100) * 100
                    if shares_to_sell == 0: shares_to_sell = pos['remaining_shares'] # 强制清仓零头
                    
                    # 收入
                    gross_revenue = shares_to_sell * sell_price
                    cost = gross_revenue * (self.stamp_tax_rate + self.commission_rate + self.transfer_rate)
                    net_revenue = gross_revenue - cost
                    
                    current_capital += net_revenue
                    
                    # 记录交易
                    buy_cost_base = shares_to_sell * pos['buy_price'] * (1 + self.commission_rate + self.transfer_rate)
                    pnl = net_revenue - buy_cost_base
                    ret_pct = pnl / buy_cost_base * 100
                    
                    trades.append({
                        'buy_date': pos['buy_date'],
                        'sell_date': date,
                        'buy_price': pos['buy_price'],
                        'sell_price': sell_price,
                        'shares': shares_to_sell,
                        'return_pct': ret_pct,
                        'pnl': pnl,
                        'sell_reason': sell_reason,
                        'days_held': pos['days_held'],
                        'phase': pos['phase'] if sell_ratio < 1.0 else 'final',
                    })
                    
                    pos['remaining_shares'] -= shares_to_sell
                    
                    # 如果卖完了，清空仓位
                    if pos['remaining_shares'] <= 0:
                        position = None
                    # 否则继续持有 (Phase 2)
                    
        # ... 结果统计部分复用父类或重写 ...
        return self._calculate_results(trades)

    def _calculate_results(self, trades: List[Dict]) -> Dict:
        """计算回测结果"""
        if not trades:
            return {'trade_count': 0, 'win_rate': 0, 'avg_return': 0, 'total_return': 0, 'max_drawdown': 0, 'sharpe_ratio': 0}
            
        df = pd.DataFrame(trades)
        wins = df[df['return_pct'] > 0]
        total_ret = (df['return_pct'] / 100 + 1).prod() - 1
        
        # 回撤
        cumulative = (df['return_pct'] / 100 + 1).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_dd = drawdown.min() * 100
        
        # 夏普
        sharpe = 0
        if df['days_held'].std() > 0:
            daily = df['return_pct'] / df['days_held']
            sharpe = (daily.mean() * 252 - 3) / (daily.std() * np.sqrt(252))
            
        return {
            'trade_count': len(df),
            'win_count': len(wins),
            'win_rate': len(wins) / len(df) * 100,
            'avg_return': df['return_pct'].mean(),
            'avg_win': wins['return_pct'].mean() if not wins.empty else 0,
            'avg_loss': df[df['return_pct'] < 0]['return_pct'].mean() if len(df) - len(wins) > 0 else 0,
            'total_return': total_ret * 100,
            'max_return': df['return_pct'].max(),
            'min_return': df['return_pct'].min(),
            'max_drawdown': max_dd,
            'sharpe_ratio': sharpe,
            'sell_reasons': df['sell_reason'].value_counts().to_dict()
        }
        
    def print_results(self, results: Dict):
        """打印结果"""
        print(f"\n{'='*80}")
        print("高级策略回测结果 (分批止盈 + 舆情联动)")
        print(f"{'='*80}")
        
        if results['trade_count'] == 0:
            print("无交易")
            return
            
        print(f"  交易次数：{results['trade_count']} (笔)")
        print(f"  胜率：{results['win_rate']:.1f}% ({results['win_count']}胜 {results['trade_count']-results['win_count']}负)")
        print(f"  平均收益：{results['avg_return']:+.2f}%")
        print(f"  累计收益：{results['total_return']:+.2f}%")
        print(f"  最大回撤：{results['max_drawdown']:.2f}%")
        print(f"  夏普比率：{results['sharpe_ratio']:.2f}")
        
        print(f"\n【卖出原因分布】")
        for reason, count in results['sell_reasons'].items():
            print(f"  {reason}: {count} 次")
