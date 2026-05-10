"""
Phase 4: AI 预测模型主程序

用法:
    python src/ml/predictor.py <股票代码> [选项]

选项:
    --model rf|gb|svm|lr    模型类型（默认 rf）
    --task class|regress     任务类型（默认 class）
    --train                  训练新模型
    --predict                预测最新走势
    --test                   运行测试示例

示例:
    # 训练模型
    python src/ml/predictor.py 300454 --train

    # 预测最新走势
    python src/ml/predictor.py 300454 --predict

    # 指定模型类型
    python src/ml/predictor.py 300454 --train --model gb
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.collector import get_stock_history, get_stock_info
from ml.features import FeatureEngineer
from ml.models import StockPredictor
from ml.visualizer import PredictionVisualizer


def train_model(symbol: str, model_type: str = 'rf', task_type: str = 'classification'):
    """
    训练预测模型
    
    Args:
        symbol: 股票代码
        model_type: 模型类型
        task_type: 任务类型
    """
    print(f"\n{'='*80}")
    print(f"Phase 4: AI 预测模型训练")
    print(f"股票：{symbol}")
    print(f"模型：{model_type.upper()}")
    print(f"任务：{task_type}")
    print(f"{'='*80}")
    
    # 1. 获取数据
    print("\n[1/5] 获取历史数据...")
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - pd.Timedelta(days=365*3)).strftime("%Y%m%d")
    df = get_stock_history(symbol, start_date=start_date, end_date=end_date)
    
    if df is None or len(df) < 200:
        print("数据不足，需要至少 200 个交易日")
        return
    
    # 统一列名
    if '日期' in df.columns:
        df = df.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close', 
                                '最高': 'high', '最低': 'low', '成交量': 'volume'})
    
    print(f"获取到 {len(df)} 条数据")
    
    # 2. 特征工程
    print("\n[2/5] 特征工程...")
    fe = FeatureEngineer(df, symbol)
    df_features = fe.create_all_features()
    X, y_class, y_return = fe.get_features_and_labels()
    
    print(f"生成 {len(fe.feature_names)} 个特征")
    print(f"特征：{fe.feature_names[:5]}...")
    
    # 3. 训练模型
    print("\n[3/5] 训练模型...")
    y = y_class if task_type == 'classification' else y_return
    predictor = StockPredictor(model_type=model_type)
    metrics = predictor.train(X, y, task_type=task_type)
    
    # 4. 保存模型
    print("\n[4/5] 保存模型...")
    os.makedirs('models', exist_ok=True)
    model_path = f"models/{symbol}_{model_type}_{task_type}.pkl"
    predictor.save_model(model_path)
    
    # 5. 可视化
    print("\n[5/5] 生成可视化...")
    visualizer = PredictionVisualizer(save_dir='output/charts')
    
    # 生成预测结果用于可视化
    predictions = predictor.predict(X)
    
    visualizer.plot_direction_prediction(df_features, predictions, symbol)
    
    if hasattr(predictor.model, 'feature_importances_'):
        importance = predictor.model.feature_importances_
        visualizer.plot_feature_importance(fe.feature_names, importance, symbol=symbol)
    
    visualizer.plot_confusion_matrix(y.values, predictions, symbol)
    
    # 打印训练摘要
    print(f"\n{'='*80}")
    print("训练完成摘要")
    print(f"{'='*80}")
    print(predictor.get_training_summary())
    print(f"\n模型已保存到：{model_path}")
    print(f"图表已保存到：output/charts/")


def predict_latest(symbol: str, model_type: str = 'rf', task_type: str = 'classification'):
    """
    预测最新走势
    
    Args:
        symbol: 股票代码
        model_type: 模型类型
        task_type: 任务类型
    """
    print(f"\n{'='*80}")
    print(f"Phase 4: 预测最新走势")
    print(f"股票：{symbol}")
    print(f"{'='*80}")
    
    # 加载模型
    model_path = f"models/{symbol}_{model_type}_{task_type}.pkl"
    if not os.path.exists(model_path):
        print(f"模型不存在：{model_path}")
        print("请先运行训练：python src/ml/predictor.py {symbol} --train")
        return
    
    predictor = StockPredictor()
    predictor.load_model(model_path)
    
    # 获取最新数据
    print("\n获取最新数据...")
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - pd.Timedelta(days=365)).strftime("%Y%m%d")
    df = get_stock_history(symbol, start_date=start_date, end_date=end_date)
    
    # 统一列名
    if '日期' in df.columns:
        df = df.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close', 
                                '最高': 'high', '最低': 'low', '成交量': 'volume'})
    
    # 特征工程
    fe = FeatureEngineer(df, symbol)
    df_features = fe.create_all_features()
    X, _, _ = fe.get_features_and_labels()
    
    # 预测
    print(f"\n正在预测...")
    if task_type == 'classification':
        predictions = predictor.predict(X, task_type='classification')
        proba = predictor.predict_proba(X)
        
        last_pred = predictions[-1]
        last_proba = proba[-1]
        
        print(f"\n{'='*60}")
        print("预测结果")
        print(f"{'='*60}")
        print(f"明日走势：{'🟢 上涨' if last_pred == 1 else '🔴 下跌'}")
        print(f"上涨概率：{last_proba[1]*100:.1f}%")
        print(f"下跌概率：{last_proba[0]*100:.1f}%")
        
        if last_proba[1] > 0.6:
            print(f"\n信号：偏向看多")
        elif last_proba[0] > 0.6:
            print(f"\n信号：偏向看空")
        else:
            print(f"\n信号：震荡，方向不明")
    
    else:
        predictions = predictor.predict(X, task_type='regression')
        last_pred = predictions[-1]
        
        print(f"\n{'='*60}")
        print("预测结果")
        print(f"{'='*60}")
        print(f"明日预期涨跌幅：{last_pred*100:+.2f}%")
        
        if last_pred > 0.01:
            print(f"\n信号：小幅看多")
        elif last_pred < -0.01:
            print(f"\n信号：小幅看空")
        else:
            print(f"\n信号：震荡")


def run_test():
    """运行测试示例"""
    print("\n" + "="*80)
    print("Phase 4: AI 预测模型 - 测试示例")
    print("="*80)
    
    # 生成模拟数据
    np.random.seed(42)
    n_days = 500
    
    dates = pd.date_range(start='2024-01-01', periods=n_days, freq='B')
    close = 100 + np.cumsum(np.random.randn(n_days) * 2)
    
    df = pd.DataFrame({
        'date': dates,
        'open': close + np.random.randn(n_days) * 0.5,
        'high': close + abs(np.random.randn(n_days)) * 1.5,
        'low': close - abs(np.random.randn(n_days)) * 1.5,
        'close': close,
        'volume': np.random.randint(1000000, 10000000, n_days)
    })
    
    print(f"\n生成 {n_days} 天模拟数据")
    print(f"价格范围：¥{df['close'].min():.2f} - ¥{df['close'].max():.2f}")
    
    # 特征工程
    print("\n[1/3] 特征工程...")
    fe = FeatureEngineer(df, "TEST")
    df_feat = fe.create_all_features()
    X, y_class, y_return = fe.get_features_and_labels()
    print(f"特征数：{len(fe.feature_names)}")
    print(f"样本数：{len(X)}")
    
    # 训练分类模型
    print("\n[2/3] 训练分类模型（预测涨跌）...")
    clf = StockPredictor(model_type='rf')
    clf_metrics = clf.train(X, y_class, task_type='classification')
    
    # 训练回归模型
    print("\n[3/3] 训练回归模型（预测涨跌幅）...")
    reg = StockPredictor(model_type='rf')
    reg_metrics = reg.train(X, y_return, task_type='regression')
    
    # 保存测试模型
    os.makedirs('models', exist_ok=True)
    clf.save_model('models/test_rf_classification.pkl')
    reg.save_model('models/test_rf_regression.pkl')
    
    print("\n" + "="*80)
    print("测试完成！")
    print("="*80)


def main():
    parser = argparse.ArgumentParser(description='Phase 4: AI 预测模型')
    parser.add_argument('symbol', nargs='?', default='300454', help='股票代码')
    parser.add_argument('--model', default='rf', choices=['rf', 'gb', 'svm', 'lr'],
                       help='模型类型')
    parser.add_argument('--task', default='class', choices=['class', 'regress'],
                       help='任务类型')
    parser.add_argument('--train', action='store_true', help='训练模型')
    parser.add_argument('--predict', action='store_true', help='预测走势')
    parser.add_argument('--test', action='store_true', help='运行测试')
    
    args = parser.parse_args()
    
    if args.test:
        run_test()
    elif args.train:
        task = 'classification' if args.task == 'class' else 'regression'
        train_model(args.symbol, args.model, task)
    elif args.predict:
        task = 'classification' if args.task == 'class' else 'regression'
        predict_latest(args.symbol, args.model, task)
    else:
        # 默认运行训练
        train_model(args.symbol, args.model, 'classification')


if __name__ == "__main__":
    main()
