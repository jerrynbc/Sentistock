# AI 股票分析项目开发计划

> 项目定位：面向初学者的 A 股分析工具，边学边做，渐进式开发  
> 创建时间：2026-05-10  
> 当前状态：Phase 1 待开始

---

## Phase 1: 数据查看器

**时间**：1-2 天  
**目标**：获取 A 股历史数据并可视化显示

### 功能清单

- [ ] 使用 AKShare 获取 A 股历史行情数据
- [ ] 绘制 K 线图（蜡烛图）
- [ ] 绘制均线（MA5、MA10、MA20）
- [ ] 显示股票基本信息（名称、行业、市盈率等）
- [ ] 支持输入股票代码查询

### 技术栈

| 模块 | 技术选型 | 说明 |
|------|---------|------|
| 数据源 | AKShare | A 股数据，免费开源 |
| 数据处理 | pandas | 数据清洗和计算 |
| 可视化 | matplotlib / pyecharts | K 线图和指标图 |

### 学习要点

1. AKShare API 使用方法
2. K 线图的含义（开盘价、收盘价、最高价、最低价）
3. 均线的含义和计算方法
4. pandas 基础操作

### 交付成果

- 命令行脚本：输入股票代码，显示 K 线图
- 数据模块：可复用的数据采集函数

### 关键代码示例

```python
import akshare as ak
import pandas as pd

# 获取 A 股历史数据
def get_stock_history(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取 A 股历史行情数据
    
    Args:
        symbol: 股票代码，如 "000001"
        start_date: 开始日期，如 "20230101"
        end_date: 结束日期，如 "20231231"
    
    Returns:
        DataFrame containing 日期、开盘、最高、最低、收盘、成交量等
    """
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date
    )
    return df
```

---

## Phase 2: 技术指标分析

**时间**：2-3 天  
**目标**：计算常用技术指标并生成买卖信号

### 功能清单

- [ ] 计算 MACD 指标（异同移动平均线）
- [ ] 计算 RSI 指标（相对强弱指标）
- [ ] 计算布林带（Bollinger Bands）
- [ ] 计算成交量均线
- [ ] 可视化所有指标
- [ ] 简单的买入/卖出信号提示

### 技术栈

| 模块 | 技术选型 | 说明 |
|------|---------|------|
| 指标计算 | ta-lib 或 talipp | 技术指标库 |
| 可视化 | pyecharts | 交互式图表 |

### 学习要点

1. MACD 的原理和信号解读
2. RSI 的超买超卖判断
3. 布林带的支撑压力含义
4. 技术指标的局限性

### 交付成果

- 指标计算模块：可复用的指标计算函数
- 指标可视化：多图表联动展示
- 信号提示：基于指标的简单策略

### 关键代码示例

```python
# MACD 计算示例
def calculate_macd(df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame:
    """计算 MACD 指标"""
    exp1 = df['close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['close'].ewm(span=slow, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
    df['histogram'] = df['macd'] - df['signal']
    return df
```

---

## Phase 3: 情绪分析

**时间**：2-3 天  
**目标**：分析股票相关新闻和舆情

### 功能清单

- [ ] 爬取股票相关新闻（东方财富、新浪财经等）
- [ ] 爬取股吧/雪球评论数据
- [ ] NLP 情感分析（正面/负面）
- [ ] 情绪指数计算
- [ ] 情绪趋势图
- [ ] 情绪与价格相关性分析

### 技术栈

| 模块 | 技术选型 | 说明 |
|------|---------|------|
| 网页爬虫 | requests + BeautifulSoup | 新闻和评论抓取 |
| NLP | jieba + SnowNLP | 中文分词和情感分析 |
| 可视化 | matplotlib | 情绪趋势图 |

### 学习要点

1. 网页爬虫基础
2. 中文文本分词
3. 情感分析原理
4. 舆情对股价的影响

### 交付成果

- 新闻爬虫模块
- 情感分析模块
- 情绪指数可视化

### 关键代码示例

```python
from snownlp import SnowNLP

# 情感分析示例
def analyze_sentiment(text: str) -> float:
    """
    分析文本情感
    Returns:
        0-1 之间的分数，越接近 1 表示越正面
    """
    s = SnowNLP(text)
    return s.sentiments
```

---

## Phase 4: AI 预测模型

**时间**：3-5 天  
**目标**：用机器学习模型预测短期走势

### 功能清单

- [ ] 特征工程（技术指标、情绪指数等作为特征）
- [ ] 训练分类模型（预测涨/跌）
- [ ] 训练回归模型（预测涨跌幅）
- [ ] 模型评估（准确率、召回率等）
- [ ] 回测框架（历史数据验证策略）
- [ ] 预测结果可视化

### 技术栈

| 模块 | 技术选型 | 说明 |
|------|---------|------|
| 机器学习 | scikit-learn | 分类/回归模型 |
| 深度学习 | pytorch (可选) | LSTM 等时序模型 |
| 回测 | backtrader (可选) | 策略回测 |

### 学习要点

1. 特征工程方法
2. 时间序列预测特点
3. 过拟合与欠拟合
4. 模型评估指标
5. 回测的陷阱和注意事项

### 交付成果

- 特征工程模块
- 模型训练和预测模块
- 简单的回测报告

### 关键代码示例

```python
from sklearn.ensemble import RandomForestClassifier

# 简单预测模型
def train_model(X_train, y_train):
    """训练预测模型"""
    model = RandomForestClassifier(n_estimators=100)
    model.fit(X_train, y_train)
    return model

def predict(model, X_test):
    """预测涨跌"""
    return model.predict(X_test)
```

---

## Phase 5: 整合 Web 界面

**时间**：2-3 天  
**目标**：构建可视化 Web 面板

### 功能清单

- [ ] 设计 Web 界面原型
- [ ] 后端 API（FastAPI）
- [ ] 前端界面（Vue / React / Streamlit）
- [ ] 股票搜索功能
- [ ] 数据展示面板（K 线、指标、情绪、预测）
- [ ] 部署上线（可选）

### 技术栈

| 模块 | 技术选型 | 说明 |
|------|---------|------|
| 后端 | FastAPI | 快速构建 API |
| 前端 | Streamlit (推荐) 或 Vue | 数据可视化 Web 应用 |
| 部署 | Vercel / Railway | 免费部署 |

### 学习要点

1. Web API 设计
2. 前后端交互
3. Web 应用部署

### 交付成果

- 完整的 Web 应用
- 可访问的在线预览

---

## 调整记录

| 日期 | 调整内容 | 原因 |
|------|----------|------|
| 2026-05-10 | 创建初始计划 | 项目启动 |

---

## 附录：股票分析知识速查

### K 线图基础

- **阳线**（通常红色）：收盘价 > 开盘价，表示上涨
- **阴线**（通常绿色）：收盘价 < 开盘价，表示下跌
- **上影线**：最高价与实体之间的线
- **下影线**：最低价与实体之间的线

### 常用指标解释

| 指标 | 含义 | 使用方法 |
|------|------|----------|
| MA | 移动平均线 | 价格在均线上方为强势 |
| MACD | 异同移动平均线 | 金叉买入，死叉卖出 |
| RSI | 相对强弱指标 | >70 超买，<30 超卖 |
| 布林带 | 价格波动区间 | 触及上轨可能回调，触及下轨可能反弹 |

### 风险提示

⚠️ 技术指标和历史分析不能保证未来收益，所有模型仅供参考，不构成投资建议。
