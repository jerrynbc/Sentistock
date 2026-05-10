"""
模型训练和预测模块

支持多种机器学习模型：
- 随机森林（分类/回归）
- 梯度提升（XGBoost/LightGBM 如果安装）
- SVM
- LSTM（可选，需要 PyTorch）
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.svm import SVC, SVR
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
import joblib
import os
import sys
import warnings
warnings.filterwarnings('ignore')


class StockPredictor:
    """股票预测器 - 训练和预测模型"""
    
    def __init__(self, model_type: str = 'rf'):
        """
        初始化预测器
        
        Args:
            model_type: 模型类型 ('rf', 'gb', 'svm', 'lr', 'lstm')
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        self.model_info = {}
    
    def _create_model(self, task_type: str = 'classification'):
        """
        创建模型实例
        
        Args:
            task_type: 任务类型 ('classification' 或 'regression')
        """
        if self.model_type == 'rf':
            if task_type == 'classification':
                self.model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=5,
                    random_state=42,
                    n_jobs=-1
                )
            else:
                self.model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
        
        elif self.model_type == 'gb':
            if task_type == 'classification':
                self.model = GradientBoostingClassifier(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=5,
                    random_state=42
                )
            else:
                self.model = GradientBoostingRegressor(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=5,
                    random_state=42
                )
        
        elif self.model_type == 'svm':
            if task_type == 'classification':
                self.model = SVC(kernel='rbf', probability=True, random_state=42)
            else:
                self.model = SVR(kernel='rbf')
        
        elif self.model_type == 'lr':
            if task_type == 'classification':
                self.model = LogisticRegression(max_iter=1000, random_state=42)
            else:
                self.model = Ridge(alpha=1.0)
        
        else:
            raise ValueError(f"不支持的模型类型：{self.model_type}")
    
    def train(self, X: pd.DataFrame, y: pd.Series, task_type: str = 'classification',
              test_size: float = 0.2, cv_folds: int = 5) -> Dict:
        """
        训练模型
        
        Args:
            X: 特征数据
            y: 标签数据
            task_type: 任务类型
            test_size: 测试集比例
            cv_folds: 交叉验证折数
            
        Returns:
            训练结果字典
        """
        print(f"\n{'='*60}")
        print(f"开始训练模型：{self.model_type.upper()} ({task_type})")
        print(f"{'='*60}")
        
        # 创建模型
        self._create_model(task_type)
        self.feature_names = X.columns.tolist()
        
        # 分割数据集（时间序列需要按时间顺序分割）
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # 标准化
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 训练模型
        print(f"\n训练集大小：{len(X_train)}")
        print(f"测试集大小：{len(X_test)}")
        print(f"\n正在训练模型...")
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # 预测
        y_pred = self.model.predict(X_test_scaled)
        
        # 评估
        metrics = self._evaluate(y_test, y_pred, task_type)
        
        # 交叉验证
        print(f"\n正在进行 {cv_folds} 折交叉验证...")
        cv_scores = cross_val_score(
            self.model, 
            self.scaler.transform(X), 
            y, 
            cv=cv_folds,
            scoring='accuracy' if task_type == 'classification' else 'r2'
        )
        metrics['cv_mean'] = cv_scores.mean()
        metrics['cv_std'] = cv_scores.std()
        
        # 特征重要性（仅树模型）
        if hasattr(self.model, 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            metrics['feature_importance'] = importance_df
            
            print(f"\n前 10 个最重要特征:")
            for i, row in importance_df.head(10).iterrows():
                print(f"  {row['feature']:30s} {row['importance']:.4f}")
        
        self.model_info = metrics
        print(f"\n{'='*60}")
        print(f"训练完成！")
        print(f"{'='*60}")
        
        return metrics
    
    def _evaluate(self, y_true, y_pred, task_type: str) -> Dict:
        """评估模型性能"""
        metrics = {}
        
        if task_type == 'classification':
            metrics['accuracy'] = accuracy_score(y_true, y_pred)
            metrics['precision'] = precision_score(y_true, y_pred, average='weighted', zero_division=0)
            metrics['recall'] = recall_score(y_true, y_pred, average='weighted', zero_division=0)
            metrics['f1'] = f1_score(y_true, y_pred, average='weighted', zero_division=0)
            
            print(f"\n分类评估结果:")
            print(f"  准确率 (Accuracy):  {metrics['accuracy']:.4f}")
            print(f"  精确率 (Precision): {metrics['precision']:.4f}")
            print(f"  召回率 (Recall):    {metrics['recall']:.4f}")
            print(f"  F1 分数:            {metrics['f1']:.4f}")
        
        else:  # regression
            metrics['mse'] = mean_squared_error(y_true, y_pred)
            metrics['rmse'] = np.sqrt(metrics['mse'])
            metrics['r2'] = r2_score(y_true, y_pred)
            
            print(f"\n回归评估结果:")
            print(f"  MSE:  {metrics['mse']:.6f}")
            print(f"  RMSE: {metrics['rmse']:.6f}")
            print(f"  R²:   {metrics['r2']:.4f}")
        
        return metrics
    
    def predict(self, X: pd.DataFrame, task_type: str = 'classification') -> np.ndarray:
        """
        预测
        
        Args:
            X: 特征数据
            task_type: 任务类型
            
        Returns:
            预测结果
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练！")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        预测概率（仅分类模型）
        
        Args:
            X: 特征数据
            
        Returns:
            各类别概率
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练！")
        
        if not hasattr(self.model, 'predict_proba'):
            raise ValueError(f"{self.model_type} 不支持概率预测")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def save_model(self, path: str):
        """保存模型"""
        if not self.is_trained:
            raise ValueError("模型尚未训练！")
        
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'model_info': self.model_info
        }
        
        joblib.dump(model_data, path)
        print(f"模型已保存到：{path}")
    
    def load_model(self, path: str):
        """加载模型"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"模型文件不存在：{path}")
        
        model_data = joblib.load(path)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.model_type = model_data['model_type']
        self.feature_names = model_data['feature_names']
        self.model_info = model_data['model_info']
        self.is_trained = True
        
        print(f"模型已从 {path} 加载")
    
    def get_training_summary(self) -> str:
        """获取训练摘要"""
        if not self.is_trained:
            return "模型尚未训练"
        
        summary = []
        summary.append(f"模型类型：{self.model_type.upper()}")
        summary.append(f"特征数量：{len(self.feature_names)}")
        summary.append(f"交叉验证均值：{self.model_info.get('cv_mean', 'N/A'):.4f}")
        summary.append(f"交叉验证标准差：{self.model_info.get('cv_std', 'N/A'):.4f}")
        
        if 'accuracy' in self.model_info:
            summary.append(f"测试集准确率：{self.model_info['accuracy']:.4f}")
        if 'r2' in self.model_info:
            summary.append(f"测试集 R²：{self.model_info['r2']:.4f}")
        
        return "\n".join(summary)
