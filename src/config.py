"""
全局配置

集中管理费率、阈值、路径、默认参数等。
"""

import os

# ================= 路径配置 =================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
CACHE_DIR = os.path.join(DATA_DIR, 'cache')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
DAILY_REPORT_DIR = os.path.join(OUTPUT_DIR, 'daily_reports')

# 确保目录存在
for d in [DATA_DIR, CACHE_DIR, OUTPUT_DIR, DAILY_REPORT_DIR]:
    os.makedirs(d, exist_ok=True)

# ================= 交易成本 =================
# A 股实际费率
COMMISSION_RATE = 0.00025   # 佣金 0.025% (双向)
STAMP_TAX_RATE = 0.0005     # 印花税 0.05% (卖出)
TRANSFER_RATE = 0.00001     # 过户费 0.001% (双向)
SLIPPAGE_RATE = 0.001       # 滑点 0.1%

# ================= 策略默认参数 =================
DEFAULT_BUY_THRESHOLD = 0.25
DEFAULT_SELL_THRESHOLD = 0.65
DEFAULT_STOP_LOSS = -0.05
DEFAULT_TAKE_PROFIT = 0.20
DEFAULT_MAX_HOLD_DAYS = 20
DEFAULT_TREND_FILTER = True
DEFAULT_SIGNAL_CONFIRM = 1

# 优化参数 (针对能源/科技板块)
OPTIMIZED_PARAMS = {
    'buy_threshold': 0.25,
    'take_profit_pct': 0.30,  # 30% 止盈
    'stop_loss_pct': -0.05,
    'max_hold_days': 15,      # 15 天持仓
}

# ================= 默认股票池 =================
DEFAULT_STOCKS = {
    '300454': '深信服',
    '600519': '贵州茅台',
    '000001': '平安银行',
    '601318': '中国平安',
    '002594': '比亚迪',
    # 能源
    '601857': '中国石油',
    '600938': '中国海油',
    '600900': '长江电力',
    '600011': '华能国际',
    # 科技/半导体
    '688981': '中芯国际',
    '002371': '北方华创',
    '603501': '韦尔股份',
    '002230': '科大讯飞',
    '002415': '海康威视',
    # 字节/智谱概念
    '688111': '金山办公',
    '300058': '蓝色光标',
    '300624': '万兴科技',
    '300229': '拓尔思',
}

# ================= 舆情配置 =================
SENTIMENT_BUY_THRESHOLD = 0.60
SENTIMENT_SELL_THRESHOLD = 0.40
ALERT_NEGATIVE_COUNT = 3  # 连续负面新闻阈值
