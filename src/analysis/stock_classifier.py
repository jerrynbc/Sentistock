"""
股票分类模块

根据波动率和趋势特征将股票分类：
- 高波动趋势股：适用情绪模块
- 窄幅震荡股：需要其他分析方案
- 低波动趋势股：适用技术指标
- 高波动震荡股：高风险，谨慎操作

分类标准：
- 波动率：年化波动率（20日滚动标准差年化）
- 趋势强度：ADX 指标 + MA 排列
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


class StockClassifier:
    """股票分类器"""
    
    def __init__(
        self,
        high_vol_threshold: float = 0.35,
        low_vol_threshold: float = 0.20,
        adx_trend_threshold: float = 20,
    ):
        self.high_vol_threshold = high_vol_threshold
        self.low_vol_threshold = low_vol_threshold
        self.adx_trend_threshold = adx_trend_threshold
    
    def classify(self, df: pd.DataFrame) -> Dict:
        """分类股票"""
        df = df.copy()
        
        if 'close' not in df.columns:
            col_map = {'收盘': 'close', '日期': 'date', '开盘': 'open', '最高': 'high', '最低': 'low'}
            df.rename(columns=col_map, inplace=True)
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        
        # 1. 年化波动率
        df['daily_return'] = df['close'].pct_change()
        df['volatility'] = df['daily_return'].rolling(20).std() * np.sqrt(252)
        annual_vol = df['volatility'].mean()
        
        # 2. ADX 趋势强度
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(abs(df['high'] - df['close'].shift()), abs(df['low'] - df['close'].shift()))
        )
        df['atr'] = df['tr'].rolling(14).mean()
        
        df['up_move'] = df['high'] - df['high'].shift()
        df['down_move'] = df['low'].shift() - df['low']
        
        df['plus_dm'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0)
        df['minus_dm'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0)
        
        df['plus_di'] = 100 * df['plus_dm'].rolling(14).mean() / (df['atr'] + 1e-8)
        df['minus_di'] = 100 * df['minus_dm'].rolling(14).mean() / (df['atr'] + 1e-8)
        df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'] + 1e-8)
        adx = df['dx'].rolling(14).mean().mean()
        
        # 3. MA 趋势
        df['MA20'] = df['close'].rolling(20).mean()
        df['MA60'] = df['close'].rolling(60).mean()
        df_valid = df.dropna()
        
        if len(df_valid) > 0:
            ma20_above_ma60 = (df_valid['MA20'] > df_valid['MA60']).mean()
            trend_pct = ma20_above_ma60
        else:
            trend_pct = 0
        
        # 4. 年度收益率
        year_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
        
        # 5. 分类
        is_high_vol = annual_vol > self.high_vol_threshold
        is_low_vol = annual_vol < self.low_vol_threshold
        is_trending = adx > self.adx_trend_threshold and trend_pct > 0.4
        
        if is_high_vol and is_trending:
            category = '高波动趋势股'
            strategy = '情绪模块'
            confidence = '高'
            description = '适合情绪模块：波动大 + 趋势明确'
        elif is_low_vol and not is_trending:
            category = '窄幅震荡股'
            strategy = '待定'
            confidence = '低'
            description = '情绪模块无效：波动小 + 无趋势'
        elif is_low_vol and is_trending:
            category = '低波动趋势股'
            strategy = '技术指标'
            confidence = '中'
            description = '适合技术指标：趋势明确但波动小'
        elif is_high_vol and not is_trending:
            category = '高波动震荡股'
            strategy = '谨慎'
            confidence = '低'
            description = '高风险：波动大但无趋势'
        else:
            category = '中等波动'
            strategy = '混合'
            confidence = '中'
            description = '可尝试情绪模块 + 技术指标'
        
        return {
            'category': category,
            'strategy': strategy,
            'confidence': confidence,
            'description': description,
            'metrics': {
                'annual_volatility': annual_vol,
                'adx': adx,
                'trend_pct': trend_pct,
                'year_return': year_return,
            }
        }
    
    def print_classification(self, result: Dict, name: str = ''):
        """打印分类结果"""
        m = result['metrics']
        print(f"\n{'='*60}")
        print(f"股票分类：{name}")
        print(f"{'='*60}")
        print(f"分类：{result['category']}")
        print(f"推荐策略：{result['strategy']}")
        print(f"置信度：{result['confidence']}")
        print()
        print(f"指标：")
        print(f"  年化波动率：{m['annual_volatility']*100:.1f}%")
        print(f"  ADX：{m['adx']:.1f}")
        print(f"  MA20>MA60 占比：{m['trend_pct']*100:.1f}%")
        print(f"  全年收益：{m['year_return']:+.1f}%")
        print()
        print(f"说明：{result['description']}")
        print(f"{'='*60}")


def classify_stocks_batch(classifier: StockClassifier, stocks_data: Dict[str, pd.DataFrame]) -> Dict:
    """批量分类股票"""
    return {name: classifier.classify(df) for name, df in stocks_data.items()}


def print_classification_summary(results: Dict):
    """打印分类汇总"""
    print(f"\n{'='*100}")
    print("股票分类汇总")
    print(f"{'='*100}")
    
    fmt = '{:<10} {:<12} {:<10} {:<6} {:>8} {:>6} {:>8} {:>8}'
    print(fmt.format('股票', '分类', '策略', '置信度', '波动率', 'ADX', '趋势占比', '全年收益'))
    print('-'*100)
    
    for name, result in results.items():
        m = result['metrics']
        print(fmt.format(
            name,
            result['category'],
            result['strategy'],
            result['confidence'],
            f"{m['annual_volatility']*100:.1f}%",
            f"{m['adx']:.1f}",
            f"{m['trend_pct']*100:.1f}%",
            f"{m['year_return']:+.1f}%",
        ))
    
    print(f"{'='*100}")
    
    # 统计
    categories = {}
    for r in results.values():
        cat = r['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\n分类统计：")
    for cat, count in categories.items():
        print(f"  {cat}：{count} 只")
