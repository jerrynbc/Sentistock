"""
股票评分模块

不是把股票硬塞进某个分类，而是从多个维度打分：
- 波动率得分 (0-100)：波动越大，情绪模块信号越多
- 趋势强度得分 (0-100)：趋势越明确，假信号越少
- 情绪模块适用度 (0-100)：综合评分，决定策略推荐

输出：每只股票在各个维度上的得分 + 策略推荐概率
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class StockScorer:
    """股票评分器"""
    
    def __init__(
        self,
        vol_ideal: float = 0.50,      # 理想波动率 (50%)
        vol_max: float = 0.80,        # 最大波动率 (超过后收益递减)
        adx_ideal: float = 35,        # 理想 ADX
        adx_min: float = 15,          # 最小有效 ADX
    ):
        self.vol_ideal = vol_ideal
        self.vol_max = vol_max
        self.adx_ideal = adx_ideal
        self.adx_min = adx_min
    
    def score(self, df: pd.DataFrame) -> Dict:
        """
        对股票多维度评分
        
        Returns:
            评分结果字典
        """
        df = df.copy()
        
        # 统一列名
        if 'close' not in df.columns:
            col_map = {'收盘': 'close', '日期': 'date', '开盘': 'open', '最高': 'high', '最低': 'low', '成交量': 'volume'}
            df.rename(columns=col_map, inplace=True)
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        
        # === 1. 波动率得分 ===
        df['daily_return'] = df['close'].pct_change()
        df['volatility'] = df['daily_return'].rolling(20).std() * np.sqrt(252)
        annual_vol = df['volatility'].mean()
        
        # 波动率得分：理想值附近最高，过高或过低都扣分
        vol_score = self._gaussian_score(annual_vol, self.vol_ideal, self.vol_max * 0.5)
        
        # === 2. 趋势强度得分 (ADX) ===
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
        
        # ADX 得分：越高越好，但有上限
        adx_score = min((adx - self.adx_min) / (self.adx_ideal - self.adx_min) * 80, 100)
        adx_score = max(adx_score, 0)
        
        # === 3. 趋势方向得分 (MA 排列) ===
        df['MA20'] = df['close'].rolling(20).mean()
        df['MA60'] = df['close'].rolling(60).mean()
        df_valid = df.dropna()
        
        if len(df_valid) > 0:
            ma20_above_ma60 = (df_valid['MA20'] > df_valid['MA60']).mean()
            # 趋势方向得分：MA20>MA60 占比越高越好
            trend_dir_score = ma20_above_ma60 * 100
        else:
            ma20_above_ma60 = 0
            trend_dir_score = 0
        
        # === 4. 趋势稳定性得分 ===
        # 计算 ADX 的标准差，ADX 越稳定越好
        adx_series = df['dx'].rolling(14).mean()
        adx_stability = 1 - (adx_series.std() / (adx_series.mean() + 1e-8))
        stability_score = max(adx_stability * 100, 0)
        
        # === 5. 情绪模块适用度 (综合) ===
        # 公式：波动率得分 (40%) + ADX 得分 (30%) + 趋势方向 (20%) + 稳定性 (10%)
        sentiment_suitability = (
            vol_score * 0.40 +
            adx_score * 0.30 +
            trend_dir_score * 0.20 +
            stability_score * 0.10
        )
        
        # === 6. 年度收益率 ===
        year_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
        
        # === 7. 策略推荐 ===
        if sentiment_suitability >= 70:
            recommendation = '强烈推荐使用情绪模块'
            confidence = '高'
            action = 'sentiment'
        elif sentiment_suitability >= 50:
            recommendation = '可以尝试情绪模块，建议配合技术指标'
            confidence = '中'
            action = 'hybrid'
        elif sentiment_suitability >= 30:
            recommendation = '情绪模块效果有限，建议以技术指标为主'
            confidence = '低'
            action = 'technical'
        else:
            recommendation = '不建议使用情绪模块，需要其他分析方案'
            confidence = '极低'
            action = 'other'
        
        return {
            'scores': {
                'volatility': vol_score,
                'adx': adx_score,
                'trend_direction': trend_dir_score,
                'stability': stability_score,
                'sentiment_suitability': sentiment_suitability,
            },
            'metrics': {
                'annual_volatility': annual_vol,
                'adx': adx,
                'ma20_above_ma60_pct': ma20_above_ma60,
                'year_return': year_return,
            },
            'recommendation': recommendation,
            'confidence': confidence,
            'action': action,
        }
    
    def _gaussian_score(self, value: float, center: float, sigma: float) -> float:
        """高斯型得分函数：中心值最高，向两侧衰减"""
        return 100 * np.exp(-0.5 * ((value - center) / sigma) ** 2)
    
    def print_score(self, result: Dict, name: str = ''):
        """打印评分结果"""
        s = result['scores']
        m = result['metrics']
        
        print(f"\n{'='*60}")
        print(f"股票评分：{name}")
        print(f"{'='*60}")
        print()
        print(f"维度得分：")
        print(f"  波动率适配度：{s['volatility']:.0f}/100")
        print(f"  趋势强度 (ADX)：{s['adx']:.0f}/100")
        print(f"  趋势方向 (MA)：{s['trend_direction']:.0f}/100")
        print(f"  趋势稳定性：{s['stability']:.0f}/100")
        print()
        
        # 情绪模块适用度（突出显示）
        suit = s['sentiment_suitability']
        bar_len = int(suit / 2)
        bar = '█' * bar_len + '░' * (50 - bar_len)
        print(f"情绪模块适用度：{suit:.0f}/100")
        print(f"  [{bar}]")
        print()
        print(f"原始指标：")
        print(f"  年化波动率：{m['annual_volatility']*100:.1f}%")
        print(f"  ADX：{m['adx']:.1f}")
        print(f"  MA20>MA60：{m['ma20_above_ma60_pct']*100:.1f}%")
        print(f"  全年收益：{m['year_return']:+.1f}%")
        print()
        print(f"推荐：{result['recommendation']}")
        print(f"{'='*60}")


def score_stocks_batch(scorer: StockScorer, stocks_data: Dict[str, pd.DataFrame]) -> Dict:
    """批量评分"""
    return {name: scorer.score(df) for name, df in stocks_data.items()}


def print_score_summary(results: Dict):
    """打印评分汇总"""
    print(f"\n{'='*100}")
    print("股票评分汇总")
    print(f"{'='*100}")
    
    fmt = '{:<10} {:>8} {:>8} {:>8} {:>8} {:>12} {:<8} {:<30}'
    print(fmt.format('股票', '波动率', 'ADX', '趋势方向', '稳定性', '情绪适用度', '置信度', '推荐'))
    print('-'*100)
    
    for name, result in results.items():
        s = result['scores']
        print(fmt.format(
            name,
            f"{s['volatility']:.0f}",
            f"{s['adx']:.0f}",
            f"{s['trend_direction']:.0f}",
            f"{s['stability']:.0f}",
            f"{s['sentiment_suitability']:.0f}",
            result['confidence'],
            result['recommendation'][:28],
        ))
    
    print(f"{'='*100}")
