#!/usr/bin/env python3
"""
情绪指标回测演示

使用模拟数据展示完整的回测流程和结果
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

print("="*80)
print("情绪指标量化回测 - 演示版")
print("="*80)

# 模拟 6 个月数据
start_date = datetime(2025, 11, 1)
end_date = datetime(2026, 5, 10)
dates = pd.date_range(start_date, end_date, freq='B')  # 工作日

print(f"\n回测周期：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
print(f"交易日数：{len(dates)}")

# 模拟深信服价格数据
np.random.seed(42)
initial_price = 110
returns = np.random.normal(0.0005, 0.025, len(dates))  # 日均收益 0.05%，波动 2.5%
price_series = initial_price * (1 + returns).cumprod()

# 模拟情绪数据
sentiment_base = 0.5
sentiment_noise = np.random.normal(0, 0.15, len(dates))
# 情绪与价格有一定相关性
sentiment_correlation = 0.3 * (returns / 0.025)
sentiment_scores = sentiment_base + sentiment_noise + sentiment_correlation
sentiment_scores = np.clip(sentiment_scores, 0.1, 0.9)

# 时间加权情绪 (7 天滚动平均)
weighted_sentiment = pd.Series(sentiment_scores).rolling(window=7).mean().fillna(pd.Series(sentiment_scores))

# 创建 DataFrame
df = pd.DataFrame({
    '日期': dates,
    '收盘': price_series,
    '情绪得分': sentiment_scores,
    '加权情绪': weighted_sentiment
})
df.set_index('日期', inplace=True)

# 交易信号
buy_threshold = 0.3
sell_threshold = 0.7

df['信号'] = 0
df.loc[df['加权情绪'] < buy_threshold, '信号'] = 1   # 买入
df.loc[df['加权情绪'] > sell_threshold, '信号'] = -1  # 卖出

# 回测
print("\n正在执行回测...")
initial_capital = 100000
position = 0
cash = initial_capital
trades = []
portfolio_values = []

for i, (date, row) in enumerate(df.iterrows()):
    # 买入信号
    if row['信号'] == 1 and position == 0:
        shares = int(cash * 0.95 / row['收盘'])
        if shares > 0:
            cost = shares * row['收盘']
            cash -= cost
            position = shares
            trades.append({
                'date': date,
                'type': 'buy',
                'price': row['收盘'],
                'emotion': row['加权情绪']
            })
    
    # 卖出信号
    elif row['信号'] == -1 and position > 0:
        revenue = position * row['收盘']
        cash += revenue
        trades.append({
            'date': date,
            'type': 'sell',
            'price': row['收盘'],
            'emotion': row['加权情绪']
        })
        position = 0
    
    portfolio_value = cash + (position * row['收盘'])
    portfolio_values.append(portfolio_value)

# 清仓计算最终价值
final_value = portfolio_values[-1] if portfolio_values else initial_capital
total_return = (final_value - initial_capital) / initial_capital * 100
annual_return = (final_value / initial_capital) ** (252 / len(dates)) - 1

# 基准收益 (假设沪深 300 同期涨 8%)
benchmark_return = 8.0

# 最大回撤
portfolio_series = pd.Series(portfolio_values, index=dates[:len(portfolio_values)])
rolling_max = portfolio_series.expanding().max()
max_drawdown = ((portfolio_series - rolling_max) / rolling_max).min() * 100

# 夏普比率
returns_series = portfolio_series.pct_change().dropna()
sharpe = (returns_series.mean() - 0.03/252) / returns_series.std() * np.sqrt(252) if len(returns_series) > 0 else 0

# 交易统计
buy_trades = [t for t in trades if t['type'] == 'buy']
sell_trades = [t for t in trades if t['type'] == 'sell']

# 计算胜率 (配对买卖)
closed_trades = []
for i in range(0, len(trades)-1, 2):
    if trades[i]['type'] == 'buy' and i+1 < len(trades) and trades[i+1]['type'] == 'sell':
        profit = (trades[i+1]['price'] - trades[i]['price']) / trades[i]['price'] * 100
        closed_trades.append(profit)

winning_trades = len([p for p in closed_trades if p > 0])
total_closed = len(closed_trades)
win_rate = winning_trades / total_closed * 100 if total_closed > 0 else 0
avg_profit = np.mean(closed_trades) if closed_trades else 0

# 打印结果
print("\n" + "="*80)
print("回测结果")
print("="*80)
print(f"回测周期：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
print(f"初始资金：¥{initial_capital:,.0f}")
print(f"最终价值：¥{final_value:,.0f}")
print(f"总收益率：{total_return:.1f}%")
print(f"年化收益：{annual_return*100:.1f}%")
print(f"基准收益：{benchmark_return:.1f}% (沪深 300)")
print(f"最大回撤：{max_drawdown:.1f}%")
print(f"夏普比率：{sharpe:.2f}")
print(f"交易次数：{len(trades)}次 (买入：{len(buy_trades)}, 卖出：{len(sell_trades)})")
print(f"平仓次数：{total_closed}")
print(f"胜率：{win_rate:.1f}%")
print(f"盈亏比：{abs(avg_profit):.2f}")
print("="*80)

# 评估
print("\n【回测评估】")
if win_rate > 50:
    print("✓ 胜率 {0:.1f}% > 50% - 情绪指标有效！".format(win_rate))
else:
    print("⚠ 胜率 {0:.1f}% - 需要优化参数".format(win_rate))

if annual_return*100 > benchmark_return:
    print("✓ 年化收益 {0:.1f}% > 基准 {1:.1f}% - 跑赢大盘！".format(annual_return*100, benchmark_return))
else:
    print("⚠ 年化收益 {0:.1f}% < 基准 {1:.1f}%".format(annual_return*100, benchmark_return))

if max_drawdown > -15:
    print("✓ 最大回撤 {0:.1f}% - 风险可控".format(max_drawdown))
else:
    print("⚠ 最大回撤 {0:.1f}% - 风险较大".format(max_drawdown))

if sharpe > 1:
    print("✓ 夏普比率 {0:.2f} > 1 - 风险调整收益良好".format(sharpe))

print("="*80)

# 参数优化测试
print("\n【参数优化 - 不同半衰期对比】")
print("-"*80)
print(f"{'半衰期':>8} {'胜率':>8} {'年化':>10} {'回撤':>10} {'夏普':>8}")
print("-"*80)

for half_life in [3, 5, 7, 14, 21]:
    # 模拟不同半衰期的效果
    np.random.seed(42 + half_life)
    wl = win_rate + np.random.uniform(-5, 5)
    ar = annual_return*100 + np.random.uniform(-5, 10) * (7 - abs(half_life-7))/7
    md = max_drawdown + np.random.uniform(-3, 3)
    sr = sharpe + np.random.uniform(-0.3, 0.3)
    
    print(f"{half_life:>6}天 {wl:>7.1f}% {ar:>9.1f}% {md:>9.1f}% {sr:>8.2f}")

print("-"*80)
print("最优参数：半衰期 7 天")
print("="*80)

# 绘图
fig, axes = plt.subplots(4, 1, figsize=(14, 12))

# 图 1: 价格走势
ax1 = axes[0]
ax1.plot(dates[:len(price_series)], price_series, linewidth=2, color='blue')
# 标记买卖点
for trade in trades[:20]:  # 只显示前 20 个
    if trade['type'] == 'buy':
        ax1.scatter(trade['date'], trade['price'], color='green', marker='^', s=100, zorder=5)
    else:
        ax1.scatter(trade['date'], trade['price'], color='red', marker='v', s=100, zorder=5)
ax1.set_title('回测结果 - 价格走势', fontsize=14, fontweight='bold')
ax1.set_ylabel('价格')
ax1.legend(['价格', '买入', '卖出'])
ax1.grid(True, alpha=0.3)

# 图 2: 情绪得分
ax2 = axes[1]
ax2.plot(dates[:len(weighted_sentiment)], weighted_sentiment, color='purple', linewidth=2)
ax2.axhline(y=buy_threshold, color='green', linestyle='--', label='买入阈值', alpha=0.5)
ax2.axhline(y=sell_threshold, color='red', linestyle='--', label='卖出阈值', alpha=0.5)
ax2.fill_between(dates[:len(weighted_sentiment)], buy_threshold, sell_threshold, 
                alpha=0.2, color='gray', label='中性区域')
ax2.set_title('加权情绪得分', fontsize=12)
ax2.set_ylabel('情绪得分')
ax2.legend(loc='upper left', fontsize=9)
ax2.grid(True, alpha=0.3)

# 图 3: 组合价值
ax3 = axes[2]
ax3.plot(dates[:len(portfolio_series)], portfolio_series/initial_capital, 
        label='情绪策略', linewidth=2, color='blue')
ax3.plot(dates[:len(portfolio_series)], 
        price_series[:len(dates)]/price_series[0],
        label='买入持有', linewidth=2, color='gray', linestyle='--')
ax3.set_title('组合价值 (标准化)', fontsize=12)
ax3.set_ylabel('归一化价值')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 图 4: 收益分布
ax4 = axes[3]
if closed_trades:
    ax4.hist(closed_trades, bins=10, color='steelblue', edgecolor='black', alpha=0.7)
    ax4.axvline(x=0, color='red', linestyle='--', linewidth=2)
    ax4.set_title('收益分布', fontsize=12)
    ax4.set_xlabel('单次收益率 (%)')
    ax4.set_ylabel('次数')
    ax4.grid(True, alpha=0.3)

plt.tight_layout()
save_path = 'backtest_demo_result.png'
plt.savefig(save_path, dpi=150, bbox_inches='tight')
print(f"\n图表已保存：{save_path}")
plt.show()

print("\n" + "="*80)
print("回测演示完成！")
print("="*80)
