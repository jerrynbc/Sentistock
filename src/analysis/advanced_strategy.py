"""
高级交易策略 - 简化版

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
import talib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from analysis.backtest_optimized import TradingStrategy
from analysis.technical_models import TechnicalEnsemble
from analysis.statistical_models import StatisticalModels


class AdvancedTradingStrategy(TradingStrategy):
    """
    增强版交易策略
    
    新增逻辑:
    - Phase 1: 利润达 15% -> 卖出 50%，止损上移至保本
    - Phase 2: 利润达 30% 或 回撤超 8% -> 清仓
    - 舆情熔断: 情绪分 < 0.15 -> 立即清仓
    """
    
    def __init__(
        self,
        buy_threshold: float = 0.35, # 调整到适合当前sentiment_score范围
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
        sentiment_kill_switch: float = 0.15,
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
        
        # 多模型集成
        self.technical_ensemble = TechnicalEnsemble()
        self.statistical_models = StatisticalModels()
    
    def run(self, df: pd.DataFrame) -> Dict:
        """执行增强版回测"""
        df = df.copy()
        
        # 检查是否需要列名转换
        if 'date' in df.columns or df.index.name == 'date':
            pass
        else:
            column_map = {
                '日期': 'date', '收盘': 'close', '开盘': 'open',
                '最高': 'high', '最低': 'low', '成交量': 'volume'
            }
            df.rename(columns=column_map, inplace=True)
            df.set_index('date', inplace=True)
        
        df.sort_index(inplace=True)
        
        # 计算技术指标
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['RSI'] = talib.RSI(df['close'], timeperiod=14)
        df['MACD'], df['MACD_signal'], df['MACD_hist'] = talib.MACD(df['close'])
        df['BB_upper'], df['BB_middle'], df['BB_lower'] = talib.BBANDS(df['close'])
        
        # 计算sentiment_score (0-1范围)
        rsi_score = df['RSI'] / 100
        macd_hist = df['MACD_hist']
        macd_min = macd_hist.min()
        macd_max = macd_hist.max()
        macd_score = (macd_hist - macd_min) / (macd_max - macd_min + 1e-8)
        bb_pos = (df['close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'] + 1e-8)
        bb_pos = bb_pos.clip(0, 1)
        
        df['sentiment_score'] = 0.4 * rsi_score + 0.3 * macd_score + 0.3 * bb_pos
        df['sentiment_score'] = df['sentiment_score'].clip(0.05, 0.95)
        
        # 趋势判断
        df['trend'] = 0
        df.loc[df['close'] > df['MA20'], 'trend'] = 1
        df.loc[df['close'] < df['MA20'], 'trend'] = -1
        
        # 训练统计模型
        train_size = int(len(df) * 0.8)
        if train_size > 20:
            train_df = df.iloc[:train_size]
            self.statistical_models.fit(train_df)
        
        # 技术面和统计模型评分
        df['technical_score'] = 0.0
        df['statistical_score'] = 0.0
        
        for i in range(len(df)):
            if i >= 20:
                technical_score = self.technical_ensemble.predict(df.iloc[:i+1])
                df.loc[df.index[i], 'technical_score'] = technical_score
                
                if self.statistical_models.is_fitted:
                    stat_pred = self.statistical_models.get_ensemble_prediction(df.iloc[:i+1])
                    statistical_score = np.clip(stat_pred * 1000, -100, 100)
                    df.loc[df.index[i], 'statistical_score'] = statistical_score
        
        # 信号确认：仅使用sentiment_score
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
            kill_signal = self.sentiment_kill_switch is not None and row['sentiment_score'] < self.sentiment_kill_switch
            
            if position is None:
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
                                'days_held': 0,
                            }
            else:
                pos = position
                pos['max_price'] = max(pos['max_price'], row['close'])
                pos['days_held'] += 1
                
                current_return = (row['close'] - pos['buy_price']) / pos['buy_price']
                
                sell_reason = None
                sell_ratio = 1.0
                
                # 卖出条件检查
                if kill_signal:
                    sell_reason = 'sentiment_kill'
                elif row['close'] < pos['max_price'] * (1 - self.trail_stop_pct):
                    sell_reason = 'trailing_stop'
                elif pos['phase'] == 1 and current_return >= self.target_1_pct:
                    sell_ratio = 0.5
                    sell_reason = 'take_profit_1'
                    pos['break_even_price'] = pos['buy_price'] * (1 + self.commission_rate * 2)
                    pos['phase'] = 2
                elif pos['phase'] == 2 and current_return >= self.target_2_pct:
                    sell_reason = 'take_profit_2'
                elif pos['phase'] == 2 and row['close'] <= pos['break_even_price']:
                    sell_reason = 'break_even_exit'
                elif pos['phase'] == 1 and current_return <= self.stop_loss_pct:
                    sell_reason = 'stop_loss'
                elif pos['days_held'] >= self.max_hold_days:
                    sell_reason = 'max_hold_days'
                
                if sell_reason:
                    shares_to_sell = int(pos['remaining_shares'] * sell_ratio)
                    if shares_to_sell > 0:
                        sell_price = row['close'] * (1 - self.slippage_rate)
                        proceeds = shares_to_sell * sell_price
                        sell_cost = proceeds * (self.commission_rate + self.stamp_tax_rate)
                        net_proceeds = proceeds - sell_cost
                        current_capital += net_proceeds
                        
                        trade_return = (sell_price - pos['buy_price']) / pos['buy_price']
                        
                        trades.append({
                            'symbol': df.attrs.get('symbol', 'UNKNOWN'),
                            'buy_date': pos['buy_date'],
                            'sell_date': date,
                            'buy_price': pos['buy_price'],
                            'sell_price': sell_price,
                            'shares': shares_to_sell,
                            'return_pct': trade_return,
                            'reason': sell_reason,
                            'phase': pos['phase']
                        })
                        
                        pos['remaining_shares'] -= shares_to_sell
                        
                        if pos['remaining_shares'] <= 0:
                            position = None
        
        # 计算结果
        total_return = (current_capital - self.initial_capital) / self.initial_capital
        win_trades = [t for t in trades if t['return_pct'] > 0]
        win_rate = len(win_trades) / len(trades) if trades else 0
        max_drawdown = self._calculate_max_drawdown(trades)
        
        return {
            'total_return': total_return,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'trade_count': len(trades),
            'trades': trades,
            'final_capital': current_capital
        }
    
    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """计算最大回撤"""
        if not trades:
            return 0.0
            
        cumulative_returns = []
        cum_return = 0
        
        for trade in trades:
            cum_return += trade['return_pct']
            cumulative_returns.append(cum_return)
        
        if not cumulative_returns:
            return 0.0
            
        peak = cumulative_returns[0]
        max_dd = 0.0
        
        for ret in cumulative_returns:
            if ret > peak:
                peak = ret
            dd = (peak - ret) / (1 + peak) if peak != -1 else 0
            max_dd = min(max_dd, -dd)
        
        return max_dd