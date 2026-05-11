#!/usr/bin/env python3
"""
多模型集成 - 技术指标模型扩展
"""

import talib
import pandas as pd
import numpy as np
from typing import Dict, List


class ADXModel:
    """ADX趋势强度模型"""
    
    def __init__(self, period: int = 14):
        self.period = period
        
    def score(self, df: pd.DataFrame) -> float:
        """计算ADX趋势强度得分 (0-100)"""
        if len(df) < self.period + 1:
            return 50.0
            
        adx = talib.ADX(
            df['high'], df['low'], df['close'], 
            timeperiod=self.period
        )
        
        # ADX > 25 表示强趋势，得分高
        latest_adx = adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 0
        score = min(100, latest_adx * 4)  # ADX 25 = 100分
        
        return max(0, score)


class RSImodel:
    """RSI动量模型"""
    
    def __init__(self, period: int = 14):
        self.period = period
        
    def score(self, df: pd.DataFrame) -> float:
        """计算RSI动量得分 (-100到100)"""
        if len(df) < self.period + 1:
            return 0.0
            
        rsi = talib.RSI(df['close'], timeperiod=self.period)
        latest_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        
        # RSI 70以上超买，30以下超卖
        if latest_rsi > 70:
            return -((latest_rsi - 70) / 30) * 100  # 超买，负分
        elif latest_rsi < 30:
            return ((30 - latest_rsi) / 30) * 100   # 超卖，正分
        else:
            # 中性区域，根据趋势方向给分
            return ((50 - latest_rsi) / 20) * 50     # 50为中心


class ATRModel:
    """ATR波动率模型"""
    
    def __init__(self, period: int = 14):
        self.period = period
        
    def score(self, df: pd.DataFrame) -> float:
        """计算ATR波动率得分 (0-100)"""
        if len(df) < self.period + 1:
            return 50.0
            
        atr = talib.ATR(df['high'], df['low'], df['close'], timeperiod=self.period)
        atr_ratio = atr.iloc[-1] / df['close'].iloc[-1]
        
        # 最佳波动率区间 2%-8%
        if 0.02 <= atr_ratio <= 0.08:
            return 100.0
        elif atr_ratio < 0.02:
            return max(0, 100 - (0.02 - atr_ratio) * 5000)
        else:
            return max(0, 100 - (atr_ratio - 0.08) * 2500)


class SARModel:
    """SAR支撑阻力模型"""
    
    def __init__(self, acceleration: float = 0.02, maximum: float = 0.2):
        self.acceleration = acceleration
        self.maximum = maximum
        
    def score(self, df: pd.DataFrame) -> float:
        """计算SAR支撑阻力得分 (-100到100)"""
        if len(df) < 10:
            return 0.0
            
        sar = talib.SAR(
            df['high'], df['low'], 
            acceleration=self.acceleration, 
            maximum=self.maximum
        )
        
        # SAR在价格下方表示上升趋势（买入信号）
        # SAR在价格上方表示下降趋势（卖出信号）
        latest_sar = sar.iloc[-1]
        latest_close = df['close'].iloc[-1]
        
        if pd.isna(latest_sar):
            return 0.0
            
        if latest_close > latest_sar:
            # 上升趋势
            trend_strength = (latest_close - latest_sar) / latest_sar
            return min(100, trend_strength * 1000)
        else:
            # 下降趋势
            trend_strength = (latest_sar - latest_close) / latest_sar
            return -min(100, trend_strength * 1000)


class TechnicalEnsemble:
    """技术指标集成模型"""
    
    def __init__(self):
        self.models = {
            'adx': ADXModel(),
            'rsi': RSImodel(), 
            'atr': ATRModel(),
            'sar': SARModel()
        }
        
        # 权重配置
        self.weights = {
            'adx': 0.3,    # 趋势强度最重要
            'rsi': 0.25,   # 动量指标
            'atr': 0.25,   # 波动率筛选
            'sar': 0.2     # 趋势方向确认
        }
    
    def predict(self, df: pd.DataFrame) -> float:
        """预测综合技术面得分 (-100到100)"""
        scores = {}
        for name, model in self.models.items():
            try:
                scores[name] = model.score(df)
            except Exception as e:
                print(f"⚠️ {name}模型计算失败: {e}")
                scores[name] = 0.0
        
        # 加权平均
        weighted_score = sum(
            scores[name] * self.weights[name] 
            for name in self.models.keys()
        )
        
        return weighted_score
    
    def get_detailed_scores(self, df: pd.DataFrame) -> Dict[str, float]:
        """获取详细各模型得分"""
        scores = {}
        for name, model in self.models.items():
            try:
                scores[name] = model.score(df)
            except Exception as e:
                scores[name] = 0.0
        return scores