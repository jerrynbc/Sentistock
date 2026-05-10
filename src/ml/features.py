"""
特征工程模块

将技术指标、情绪指数、量价数据转换为机器学习模型可用的特征
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.indicators import calculate_all_indicators


class FeatureEngineer:
    """特征工程器 - 将原始数据转换为 ML 特征"""
    
    def __init__(self, df: pd.DataFrame, symbol: str = ""):
        """
        初始化特征工程器
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
            symbol: 股票代码
        """
        self.df = df.copy()
        self.symbol = symbol
        self.feature_names = []
    
    def create_all_features(self) -> pd.DataFrame:
        """
        创建所有特征
        
        Returns:
            包含所有特征的 DataFrame
        """
        # 1. 基础技术指标
        self.df = self._add_technical_indicators()
        
        # 2. 价格形态特征
        self.df = self._add_price_patterns()
        
        # 3. 成交量特征
        self.df = self._add_volume_features()
        
        # 4. 时间特征
        self.df = self._add_time_features()
        
        # 5. 动量特征
        self.df = self._add_momentum_features()
        
        # 6. 波动率特征
        self.df = self._add_volatility_features()
        
        # 7. 创建标签（未来涨跌）
        self.df = self._create_labels()
        
        # 记录特征名
        self.feature_names = [col for col in self.df.columns 
                             if col not in ['date', 'open', 'high', 'low', 'close', 'volume',
                                           'label_class', 'label_return', 'label_pct']]
        
        return self.df
    
    def _add_technical_indicators(self) -> pd.DataFrame:
        """添加技术指标特征"""
        df = self.df.copy()
        
        # 移动平均线
        for period in [5, 10, 20, 60]:
            df[f'ma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'close_ma_{period}_ratio'] = df['close'] / df[f'ma_{period}'] - 1
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # 布林带
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        return df
    
    def _add_price_patterns(self) -> pd.DataFrame:
        """添加价格形态特征"""
        df = self.df.copy()
        
        # 日内振幅
        df['intraday_range'] = (df['high'] - df['low']) / df['open']
        
        # 实体大小
        df['body_size'] = abs(df['close'] - df['open']) / df['open']
        
        # 上下影线
        df['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['open']
        df['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['open']
        
        # 涨跌标识
        df['is_up'] = (df['close'] > df['open']).astype(int)
        
        # 连续涨跌天数
        df['up_streak'] = 0
        df['down_streak'] = 0
        for i in range(1, len(df)):
            if df.iloc[i]['close'] > df.iloc[i]['open']:
                df.iloc[i, df.columns.get_loc('up_streak')] = df.iloc[i-1]['up_streak'] + 1
            else:
                df.iloc[i, df.columns.get_loc('down_streak')] = df.iloc[i-1]['down_streak'] + 1
        
        return df
    
    def _add_volume_features(self) -> pd.DataFrame:
        """添加成交量特征"""
        df = self.df.copy()
        
        # 成交量均线
        for period in [5, 10, 20]:
            df[f'vol_ma_{period}'] = df['volume'].rolling(window=period).mean()
            df[f'vol_ratio_{period}'] = df['volume'] / df[f'vol_ma_{period}']
        
        # 量价关系
        df['price_vol_corr'] = df['close'].pct_change().rolling(window=20).corr(df['volume'].pct_change())
        
        # 成交额（近似）
        if 'amount' not in df.columns:
            df['amount'] = df['close'] * df['volume']
        
        return df
    
    def _add_time_features(self) -> pd.DataFrame:
        """添加时间特征"""
        df = self.df.copy()
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['day_of_week'] = df['date'].dt.dayofweek
            df['month'] = df['date'].dt.month
            df['quarter'] = df['date'].dt.quarter
            df['is_month_start'] = df['date'].dt.is_month_start.astype(int)
            df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
        
        return df
    
    def _add_momentum_features(self) -> pd.DataFrame:
        """添加动量特征"""
        df = self.df.copy()
        
        # 不同周期的收益率
        for period in [1, 3, 5, 10, 20]:
            df[f'return_{period}d'] = df['close'].pct_change(period)
        
        # 价格位置（相对于 N 日高低点）
        for period in [20, 60]:
            high_n = df['high'].rolling(window=period).max()
            low_n = df['low'].rolling(window=period).min()
            df[f'price_position_{period}d'] = (df['close'] - low_n) / (high_n - low_n)
        
        return df
    
    def _add_volatility_features(self) -> pd.DataFrame:
        """添加波动率特征"""
        df = self.df.copy()
        
        # 历史波动率
        for period in [5, 10, 20]:
            df[f'volatility_{period}d'] = df['close'].pct_change().rolling(window=period).std() * np.sqrt(252)
        
        # 真实波动范围 (ATR)
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['close'].shift())
        df['tr3'] = abs(df['low'] - df['close'].shift())
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        df['atr_14'] = df['tr'].rolling(window=14).mean()
        df['atr_ratio'] = df['atr_14'] / df['close']
        
        return df
    
    def _create_labels(self) -> pd.DataFrame:
        """
        创建预测标签
        
        - label_class: 分类标签 (1=涨, 0=跌)
        - label_return: 回归标签 (未来收益率)
        - label_pct: 未来涨跌幅百分比
        """
        df = self.df.copy()
        
        # 未来 1 天收盘价
        df['close_next'] = df['close'].shift(-1)
        
        # 未来收益率
        df['label_return'] = (df['close_next'] - df['close']) / df['close']
        df['label_pct'] = df['label_return'] * 100
        
        # 分类标签：涨=1, 跌=0
        df['label_class'] = (df['label_return'] > 0).astype(int)
        
        return df
    
    def get_features_and_labels(self, drop_na: bool = True) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """
        获取特征和标签
        
        Args:
            drop_na: 是否删除包含 NaN 的行
            
        Returns:
            X: 特征 DataFrame
            y_class: 分类标签
            y_return: 回归标签
        """
        feature_cols = self.feature_names
        label_cols = ['label_class', 'label_return']
        
        df = self.df[feature_cols + label_cols].copy()
        
        if drop_na:
            df = df.dropna()
        
        X = df[feature_cols]
        y_class = df['label_class']
        y_return = df['label_return']
        
        return X, y_class, y_return
    
    def get_feature_importance_preview(self) -> List[str]:
        """获取特征名列表"""
        return self.feature_names
