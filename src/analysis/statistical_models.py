#!/usr/bin/env python3
"""
多模型集成 - 统计模型实现
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA
import warnings
warnings.filterwarnings('ignore')


class StatisticalModels:
    """统计模型集成"""
    
    def __init__(self):
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'linear_regression': LinearRegression(),
            'arima': None  # ARIMA需要单独处理
        }
        self.scaler = StandardScaler()
        self.is_fitted = False
        
    def _prepare_features(self, df: pd.DataFrame, lookback: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """准备特征和目标变量"""
        # 特征工程
        features = []
        targets = []
        
        for i in range(lookback, len(df)):
            # 基础价格特征
            close_prices = df['close'].iloc[i-lookback:i].values
            high_prices = df['high'].iloc[i-lookback:i].values  
            low_prices = df['low'].iloc[i-lookback:i].values
            volumes = df['volume'].iloc[i-lookback:i].values
            
            # 技术指标特征
            returns = np.diff(close_prices) / close_prices[:-1]
            volatility = np.std(returns)
            avg_volume = np.mean(volumes)
            
            # 趋势特征
            price_change = (close_prices[-1] - close_prices[0]) / close_prices[0]
            ma_5 = np.mean(close_prices[-5:]) if len(close_prices) >= 5 else close_prices[-1]
            ma_10 = np.mean(close_prices[-10:]) if len(close_prices) >= 10 else close_prices[-1]
            ma_ratio = ma_5 / ma_10 if ma_10 != 0 else 1.0
            
            feature_vector = [
                close_prices[-1],      # 最新收盘价
                volatility,           # 波动率
                avg_volume,          # 平均成交量
                price_change,        # 价格变化
                ma_ratio,            # 移动平均比率
                high_prices[-1] - low_prices[-1],  # 当日振幅
                returns[-1] if len(returns) > 0 else 0  # 最新收益率
            ]
            
            features.append(feature_vector)
            # 目标：下一周期的收益率
            next_return = (df['close'].iloc[i] - close_prices[-1]) / close_prices[-1]
            targets.append(next_return)
            
        return np.array(features), np.array(targets)
    
    def _fit_arima(self, df: pd.DataFrame) -> float:
        """拟合ARIMA模型并预测"""
        try:
            # 使用收盘价序列
            prices = df['close'].values
            
            if len(prices) < 10:
                return 0.0
                
            # 简单ARIMA(1,1,1)模型
            model = ARIMA(prices, order=(1, 1, 1))
            fitted_model = model.fit()
            
            # 预测下一个值
            forecast = fitted_model.forecast(steps=1)
            current_price = prices[-1]
            predicted_return = (forecast[0] - current_price) / current_price
            
            return float(predicted_return)
            
        except Exception as e:
            # ARIMA失败时返回0
            return 0.0
    
    def fit(self, df: pd.DataFrame):
        """训练统计模型"""
        if len(df) < 20:
            self.is_fitted = False
            return
            
        # 准备训练数据
        X, y = self._prepare_features(df)
        
        if len(X) == 0:
            self.is_fitted = False
            return
            
        # 标准化特征
        X_scaled = self.scaler.fit_transform(X)
        
        # 训练模型
        for name, model in self.models.items():
            if name != 'arima':
                try:
                    model.fit(X_scaled, y)
                except Exception as e:
                    print(f"⚠️ {name}模型训练失败: {e}")
        
        self.is_fitted = True
    
    def predict(self, df: pd.DataFrame) -> Dict[str, float]:
        """预测各模型的收益率"""
        if not self.is_fitted or len(df) < 10:
            # 如果未训练或数据不足，使用ARIMA直接预测
            arima_pred = self._fit_arima(df)
            return {
                'random_forest': 0.0,
                'linear_regression': 0.0, 
                'arima': arima_pred
            }
        
        # 准备最新特征
        lookback = min(10, len(df))
        close_prices = df['close'].iloc[-lookback:].values
        high_prices = df['high'].iloc[-lookback:].values
        low_prices = df['low'].iloc[-lookback:].values
        volumes = df['volume'].iloc[-lookback:].values
        
        returns = np.diff(close_prices) / close_prices[:-1] if len(close_prices) > 1 else np.array([0])
        volatility = np.std(returns) if len(returns) > 0 else 0
        avg_volume = np.mean(volumes)
        price_change = (close_prices[-1] - close_prices[0]) / close_prices[0] if len(close_prices) > 1 else 0
        ma_5 = np.mean(close_prices[-5:]) if len(close_prices) >= 5 else close_prices[-1]
        ma_10 = np.mean(close_prices[-10:]) if len(close_prices) >= 10 else close_prices[-1]
        ma_ratio = ma_5 / ma_10 if ma_10 != 0 else 1.0
        
        latest_features = np.array([[
            close_prices[-1],
            volatility,
            avg_volume, 
            price_change,
            ma_ratio,
            high_prices[-1] - low_prices[-1],
            returns[-1] if len(returns) > 0 else 0
        ]])
        
        # 标准化
        latest_features_scaled = self.scaler.transform(latest_features)
        
        predictions = {}
        for name, model in self.models.items():
            if name != 'arima':
                try:
                    pred = model.predict(latest_features_scaled)[0]
                    predictions[name] = float(pred)
                except Exception as e:
                    predictions[name] = 0.0
            else:
                predictions[name] = self._fit_arima(df)
        
        return predictions
    
    def get_ensemble_prediction(self, df: pd.DataFrame, weights: Dict[str, float] = None) -> float:
        """获取加权集成预测"""
        if weights is None:
            weights = {
                'random_forest': 0.4,
                'linear_regression': 0.3,
                'arima': 0.3
            }
        
        predictions = self.predict(df)
        ensemble_pred = sum(predictions[name] * weights.get(name, 0) for name in predictions.keys())
        
        return ensemble_pred


# 全局实例
statistical_models = StatisticalModels()