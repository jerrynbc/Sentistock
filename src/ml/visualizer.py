"""
预测结果可视化模块

绘制：
- 预测 vs 实际价格对比图
- 准确率趋势图
- 特征重要性图
- 混淆矩阵热力图
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.gridspec import GridSpec
from sklearn.metrics import confusion_matrix
import os

# 配置中文字体
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


class PredictionVisualizer:
    """预测结果可视化器"""
    
    def __init__(self, save_dir: str = 'output/charts'):
        """
        初始化可视化器
        
        Args:
            save_dir: 图表保存目录
        """
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
    
    def plot_price_prediction(self, df: pd.DataFrame, predictions: np.ndarray,
                             symbol: str = "", save: bool = True):
        """
        绘制价格预测对比图
        
        Args:
            df: 包含收盘价和预测值的 DataFrame
            predictions: 预测值数组
            symbol: 股票代码
            save: 是否保存
        """
        fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
        
        # 上图：价格对比
        ax1 = axes[0]
        ax1.plot(df.index, df['close'], 'b-', label='Actual Close', linewidth=1.5, alpha=0.7)
        
        if 'predicted_close' in df.columns:
            ax1.plot(df.index, df['predicted_close'], 'r--', label='Predicted Close', 
                    linewidth=1.5, alpha=0.7)
        
        ax1.set_ylabel('Price', fontsize=12)
        ax1.set_title(f'{symbol} - Price Prediction vs Actual', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # 下图：预测误差
        ax2 = axes[1]
        if 'predicted_close' in df.columns:
            errors = df['close'] - df['predicted_close']
            colors = ['red' if e > 0 else 'green' for e in errors]
            ax2.bar(df.index, errors, color=colors, alpha=0.6)
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        ax2.set_ylabel('Error', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            path = os.path.join(self.save_dir, f"{symbol}_price_prediction.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            print(f"图表已保存：{path}")
        
        plt.close()
    
    def plot_direction_prediction(self, df: pd.DataFrame, predictions: np.ndarray,
                                 symbol: str = "", save: bool = True):
        """
        绘制涨跌预测准确率图
        
        Args:
            df: 包含实际标签的 DataFrame
            predictions: 预测标签
            symbol: 股票代码
            save: 是否保存
        """
        if 'label_class' not in df.columns:
            return
        
        # 计算滚动准确率
        window = 20
        correct = (df['label_class'].values == predictions)
        rolling_acc = pd.Series(correct).rolling(window=window).mean() * 100
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2, 1]})
        
        # 上图：准确率趋势
        ax1 = axes[0]
        ax1.plot(df.index[window-1:], rolling_acc.dropna().values, 'b-', linewidth=2)
        ax1.axhline(y=50, color='red', linestyle='--', alpha=0.5, label='Random (50%)')
        ax1.set_ylabel('Accuracy (%)', fontsize=12)
        ax1.set_title(f'{symbol} - Rolling Prediction Accuracy ({window}-day window)', 
                     fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 100)
        
        # 下图：实际 vs 预测
        ax2 = axes[1]
        ax2.scatter(df.index, df['label_class'], alpha=0.3, label='Actual', color='blue')
        ax2.scatter(df.index, predictions, alpha=0.3, label='Predicted', color='red', marker='x')
        ax2.set_ylabel('Direction (1=Up, 0=Down)', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.legend()
        ax2.set_yticks([0, 1])
        ax2.set_yticklabels(['Down', 'Up'])
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            path = os.path.join(self.save_dir, f"{symbol}_direction_prediction.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            print(f"图表已保存：{path}")
        
        plt.close()
    
    def plot_feature_importance(self, feature_names: list, importance: np.ndarray,
                               top_n: int = 15, symbol: str = "", save: bool = True):
        """
        绘制特征重要性图
        
        Args:
            feature_names: 特征名列表
            importance: 重要性数组
            top_n: 显示前 N 个
            symbol: 股票代码
            save: 是否保存
        """
        # 按重要性排序
        sorted_idx = np.argsort(importance)[-top_n:]
        
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.barh(range(len(sorted_idx)), importance[sorted_idx], color='steelblue', alpha=0.7)
        ax.set_yticks(range(len(sorted_idx)))
        ax.set_yticklabels([feature_names[i] for i in sorted_idx], fontsize=10)
        ax.set_xlabel('Feature Importance', fontsize=12)
        ax.set_title(f'{symbol} - Top {top_n} Feature Importance', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        
        if save:
            path = os.path.join(self.save_dir, f"{symbol}_feature_importance.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            print(f"图表已保存：{path}")
        
        plt.close()
    
    def plot_confusion_matrix(self, y_true, y_pred, symbol: str = "", save: bool = True):
        """
        绘制混淆矩阵
        
        Args:
            y_true: 真实标签
            y_pred: 预测标签
            symbol: 股票代码
            save: 是否保存
        """
        cm = confusion_matrix(y_true, y_pred)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
        ax.figure.colorbar(im, ax=ax)
        
        ax.set(xticks=[0, 1], yticks=[0, 1],
               xticklabels=['Predicted Down', 'Predicted Up'],
               yticklabels=['Actual Down', 'Actual Up'],
               ylabel='True Label',
               xlabel='Predicted Label',
               title=f'{symbol} - Confusion Matrix')
        
        # 添加数值标注
        thresh = cm.max() / 2.
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f'{cm[i, j]}',
                       ha="center", va="center",
                       color="white" if cm[i, j] > thresh else "black",
                       fontsize=14)
        
        plt.tight_layout()
        
        if save:
            path = os.path.join(self.save_dir, f"{symbol}_confusion_matrix.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            print(f"图表已保存：{path}")
        
        plt.close()
    
    def plot_all(self, df, predictions, feature_names, importance, symbol=""):
        """绘制所有预测相关图表"""
        print(f"\n{'='*60}")
        print("正在生成预测结果图表...")
        print(f"{'='*60}")
        
        self.plot_price_prediction(df, predictions, symbol)
        self.plot_direction_prediction(df, predictions, symbol)
        self.plot_feature_importance(feature_names, importance, symbol=symbol)
        self.plot_confusion_matrix(df['label_class'].values, predictions, symbol)
        
        print("所有图表生成完成！")
