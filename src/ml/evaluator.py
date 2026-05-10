"""
模型评估模块

提供全面的模型评估工具：
- 混淆矩阵
- 学习曲线
- 预测误差分析
- 时间序列交叉验证
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from sklearn.metrics import (
    confusion_matrix, classification_report, 
    mean_absolute_error, mean_squared_error, r2_score
)
from sklearn.model_selection import TimeSeriesSplit
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


class ModelEvaluator:
    """模型评估器"""
    
    def __init__(self):
        self.results = {}
    
    def evaluate_classification(self, y_true, y_pred, y_proba=None) -> Dict:
        """
        分类模型评估
        
        Args:
            y_true: 真实标签
            y_pred: 预测标签
            y_proba: 预测概率（可选）
            
        Returns:
            评估结果字典
        """
        results = {}
        
        # 基础指标
        results['accuracy'] = accuracy_score(y_true, y_pred)
        results['precision'] = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        results['recall'] = recall_score(y_true, y_pred, average='weighted', zero_division=0)
        results['f1'] = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        
        # 混淆矩阵
        cm = confusion_matrix(y_true, y_pred)
        results['confusion_matrix'] = cm
        
        # 分类报告
        results['classification_report'] = classification_report(y_true, y_pred, zero_division=0)
        
        # 涨跌分别的准确率
        tn, fp, fn, tp = cm.ravel()
        results['up_accuracy'] = tp / (tp + fn) if (tp + fn) > 0 else 0
        results['down_accuracy'] = tn / (tn + fp) if (tn + fp) > 0 else 0
        
        return results
    
    def evaluate_regression(self, y_true, y_pred) -> Dict:
        """
        回归模型评估
        
        Args:
            y_true: 真实值
            y_pred: 预测值
            
        Returns:
            评估结果字典
        """
        results = {}
        
        results['mae'] = mean_absolute_error(y_true, y_pred)
        results['mse'] = mean_squared_error(y_true, y_pred)
        results['rmse'] = np.sqrt(results['mse'])
        results['r2'] = r2_score(y_true, y_pred)
        results['mape'] = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-8))) * 100
        
        return results
    
    def time_series_cv(self, model, X, y, n_splits=5, task_type='classification') -> Dict:
        """
        时间序列交叉验证
        
        Args:
            model: 训练好的模型
            X: 特征
            y: 标签
            n_splits: 折数
            task_type: 任务类型
            
        Returns:
            CV 结果
        """
        tscv = TimeSeriesSplit(n_splits=n_splits)
        scores = []
        
        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            if task_type == 'classification':
                score = accuracy_score(y_test, y_pred)
            else:
                score = r2_score(y_test, y_pred)
            
            scores.append(score)
        
        return {
            'scores': scores,
            'mean': np.mean(scores),
            'std': np.std(scores),
            'min': np.min(scores),
            'max': np.max(scores)
        }
    
    def print_classification_report(self, y_true, y_pred):
        """打印分类报告"""
        print("\n" + "="*60)
        print("分类评估报告")
        print("="*60)
        print(classification_report(y_true, y_pred, zero_division=0))
        
        cm = confusion_matrix(y_true, y_pred)
        print(f"混淆矩阵:")
        print(f"  预测涨  预测跌")
        print(f"实际涨  {cm[1][1]:5d}  {cm[1][0]:5d}")
        print(f"实际跌  {cm[0][1]:5d}  {cm[0][0]:5d}")
