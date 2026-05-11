# 📊 Sentistock - AI 股票情绪分析系统

<div align="center">

**基于多模型集成的智能股票筛选与交易策略系统**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Phase](https://img.shields.io/badge/Phase-6%20Complete-green.svg)]()

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [CLI 使用指南](#-cli-使用指南) • [Web 端启动](#-web-端启动) • [项目结构](#-项目结构)

</div>

---

## 🎯 项目简介

**Sentistock** 是一个专业的 AI 股票分析系统，通过多模型集成（技术指标 + 统计模型 + 情绪分析）为投资决策提供数据支持。

### 核心理念

> **不是所有股票都值得投资，不是所有信号都同样可靠。**

Sentistock 通过三重验证确保交易信号质量：
- 📈 **技术面**: ADX/RSI/ATR/SAR 四重指标验证
- 📊 **统计面**: Random Forest/ARIMA/Linear Regression 集成预测
- 💭 **情绪面**: 金融词典情感分析 + 时间加权模型

---

## ✨ 功能特性

### ✅ 已完成

| 功能 | 说明 | 状态 |
|------|------|------|
| **多模型集成** | 技术指标 + 统计模型 + 情绪分析 | ✅ |
| **价值筛选机制** | 70分门槛过滤低质量股票 | ✅ |
| **高级交易策略** | 分批止盈 + 追踪止损 + 舆情熔断 | ✅ |
| **CLI 命令行工具** | scan/backtest/portfolio/monitor 命令 | ✅ |
| **Web 界面** | React + Tailwind CSS 现代化前端 | ✅ |
| **舆情记忆库** | SQLite 持久化存储历史情感数据 | ✅ |
| **多数据源支持** | 聚宽SDK / Yahoo Finance / RSSHub | ✅ |

### 🚧 开发中

| 功能 | 说明 | 进度 |
|------|------|------|
| A股专用功能 | 涨停板/北向资金/ST股特殊处理 | 🟡 30% |
| 移动端优化 | 响应式设计完善 | ⏳ 待开发 |
| 数据源扩展 | Alpha Vantage 免费API集成 | ⏳ 待开发 |

---

## 🔧 技术栈

- **语言**: Python 3.11+
- **数据分析**: pandas, numpy, scikit-learn, statsmodels
- **技术指标**: TA-Lib (ADX/RSI/MACD/BBANDS)
- **可视化**: matplotlib, plotly, recharts (React)
- **Web 框架**: React 18 + TypeScript + Vite + Tailwind CSS
- **数据源**: 聚宽 (JoinQuant), yfinance, RSSHub
- **回测**: 自定义多模型回测框架

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 TA-Lib (技术指标库)
pip install TA-Lib

# 安装统计模型库
pip install scikit-learn statsmodels
```

### 2. 基础使用

```bash
# 分析单只股票
python3 src/cli.py scan 300454

# 运行回测
python3 src/cli.py backtest 300454

# 高级策略回测
python3 src/cli.py backtest 300454 --advanced
```

---

## 💻 CLI 使用指南

Sentistock 提供完整的命令行工具，支持多种分析模式：

### 命令总览

| 命令 | 说明 | 示例 |
|------|------|------|
| `scan` | 扫描股票舆情和基本面 | `python3 src/cli.py scan 300454` |
| `backtest` | 运行单股回测 | `python3 src/cli.py backtest 300454` |
| `portfolio` | 运行组合回测 | `python3 src/cli.py portfolio --symbols 300454,688561` |
| `monitor` | 启动实时监控 | `python3 src/cli.py monitor --symbols 300454 --interval 5` |

### 详细用法

#### 1. 股票扫描 (scan)

扫描单只或多只股票的基本面和舆情数据：

```bash
# 扫描单只股票
python3 src/cli.py scan 300454

# 扫描多只股票
python3 src/cli.py scan --symbols 300454,688561,002371

# 启用真实新闻源
python3 src/cli.py scan 300454 --real-news
```

**输出示例:**
```
📊 深信服 (300454) 分析报告
━━━━━━━━━━━━━━━━━━━━━━━━
技术指标：🟢 多头趋势
公开新闻：⚪ 中性偏多
综合评分：82.2/100
投资建议：高价值股票
```

#### 2. 回测分析 (backtest)

运行单股历史回测，验证策略有效性：

```bash
# 基础策略回测
python3 src/cli.py backtest 300454

# 高级策略回测 (分批止盈 + 追踪止损)
python3 src/cli.py backtest 300454 --advanced

# 自定义参数回测
python3 src/cli.py backtest 300454 --advanced \
  --buy-threshold 0.35 \
  --stop-loss -0.10 \
  --take-profit 0.20
```

**输出示例:**
```
================================================================================
高级策略回测结果 (分批止盈 + 舆情联动)
================================================================================
  交易次数：8 (笔)
  胜率：62.5% (5胜 3负)
  平均收益：+4.47%
  累计收益：+37.34%
  最大回撤：-7.80%
  夏普比率：4.68

【卖出原因分布】
  trailing_stop: 4 次
  stop_loss: 2 次
  take_profit_1: 2 次
```

#### 3. 组合回测 (portfolio)

运行多股票组合回测，验证策略在不同股票上的表现：

```bash
# 等权重组合回测
python3 src/cli.py portfolio --symbols 300454,688561,002371

# 评分加权组合回测
python3 src/cli.py portfolio --symbols 300454,688561,002371 --weight-type score

# 高级策略组合回测
python3 src/cli.py portfolio --symbols 300454,688561 --advanced
```

#### 4. 实时监控 (monitor)

启动实时监控守护进程，跟踪关注股票的舆情变化：

```bash
# 监控单只股票 (每5分钟扫描一次)
python3 src/cli.py monitor --symbols 300454

# 监控多只股票 (每1分钟扫描一次)
python3 src/cli.py monitor --symbols 300454,688561,002371 --interval 1

# 启用真实新闻源监控
python3 src/cli.py monitor --symbols 300454 --real-news
```

**输出示例:**
```
🤖 启动舆情监控守护进程...
监控列表：300454
扫描间隔：5 分钟
------------------------------------------------------------

============================================================
📡 扫描开始：2026-05-10 10:30:00
============================================================
📊 300454 (深信服):
   得分：0.78 | 信号：观望
   负面词：无
   📈 趋势：上升 (加速度: +0.05)
💤 等待下次扫描...
```

### 高级参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--buy-threshold` | 买入阈值 (sentiment_score < 阈值时买入) | 0.35 |
| `--sell-threshold` | 卖出阈值 | 0.65 |
| `--stop-loss` | 止损百分比 | -0.05 |
| `--take-profit` | 止盈百分比 | 0.20 |
| `--max-hold-days` | 最大持仓天数 | 20 |
| `--position-pct` | 仓位百分比 (0.0-1.0) | 1.0 |
| `--real-news` | 启用真实新闻源 | False |
| `--interval` | 监控扫描间隔 (分钟) | 5 |

---

## 🌐 Web 端启动

Sentistock 提供两种 Web 界面选择：

### 方案一：React + Tailwind CSS (推荐)

现代化前端界面，支持响应式设计和丰富的数据可视化：

#### 1. 安装前端依赖

```bash
cd frontend/react-ui
npm install
```

#### 2. 启动开发服务器

```bash
cd frontend/react-ui
npm run dev
```

#### 3. 访问界面

打开浏览器访问：`http://localhost:3000`

**功能特性:**
- 📊 股票价值评分展示
- 📈 多模型回测结果可视化
- 🔍 实时舆情监控面板
- 📋 多股票对比表格
- 📱 响应式设计 (支持移动端)

#### 4. 构建生产版本

```bash
cd frontend/react-ui
npm run build
```

### 方案二：Streamlit (轻量级)

基于 Python 的轻量级 Web 界面，快速部署：

#### 1. 安装 Streamlit

```bash
pip install streamlit
```

#### 2. 启动应用

```bash
cd frontend
streamlit run app.py --server.port=8501
```

#### 3. 访问界面

打开浏览器访问：`http://localhost:8501`

**功能特性:**
- 📊 股票评分卡片
- 📈 回测结果展示
- 🔍 实时监控状态
- ⚡ 快速部署 (无需 npm)

---

## 📊 项目结构

```
sentistock/
├── src/                     # 源代码
│   ├── analysis/            # 分析模块
│   │   ├── advanced_strategy.py    # 高级交易策略 (分批止盈 + 追踪止损)
│   │   ├── backtest_optimized.py   # 优化回测框架
│   │   ├── technical_models.py     # 技术指标模型 (ADX/RSI/ATR/SAR)
│   │   ├── statistical_models.py   # 统计模型 (RF/ARIMA/LR)
│   │   ├── stock_scorer.py         # 股票评分系统
│   │   └── utils.py                # 数据处理工具
│   ├── core/                # 核心模块
│   │   ├── __init__.py             # 引擎入口
│   │   └── monitor.py              # 实时监控守护进程
│   ├── db/                  # 数据库模块
│   │   └── memory.py               # SQLite 舆情记忆库
│   ├── news/                # 新闻模块
│   │   ├── scanner.py              # 舆情扫描器
│   │   ├── sources.py              # 多数据源适配器
│   │   └── rsshub_fetcher.py       # RSSHub 新闻获取器
│   ├── sentiment/           # 情感分析模块
│   │   ├── lexicon_analyzer.py     # 金融词典情感分析
│   │   └── finance_lexicon.py      # 金融专业词典
│   └── cli.py               # 命令行工具入口
├── frontend/                # Web 前端
│   ├── react-ui/            # React + Tailwind CSS 前端
│   │   ├── src/             # React 源代码
│   │   ├── package.json     # npm 依赖
│   │   └── vite.config.ts   # Vite 配置
│   └── app.py               # Streamlit 前端
├── data/                    # 数据文件
│   ├── cache/               # 股票数据缓存
│   └── sentistock.db        # SQLite 数据库
├── tests/                   # 测试文件
│   ├── test_multi_period.py        # 多周期回测测试
│   └── test_multi_industry.py      # 多行业回测测试
├── requirements.txt         # Python 依赖
└── README.md               # 本文件
```

---

## 📈 使用案例

### 案例 1: 单股综合分析

```bash
$ python3 src/cli.py scan 300454
```

**分析结果:**
```
技术指标：🟢 多头趋势
公开新闻：⚪ 中性偏多
综合评分：82.2/100
投资建议：高价值股票
```

### 案例 2: 高级策略回测

```bash
$ python3 src/cli.py backtest 300454 --advanced
```

**回测结果:**
```
交易次数：8 笔
胜率：62.5%
累计收益：+37.34%
最大回撤：-7.80%
```

### 案例 3: 批量回测验证

```bash
$ python3 value_filtered_backtest.py
```

**批量结果 (13只高价值股票):**
```
平均收益: +2158.60%
胜率: 92.3% (12/13 盈利)
```

### 案例 4: 实时监控

```bash
$ python3 src/cli.py monitor --symbols 300454 --interval 5
```

**监控输出:**
```
📊 300454 (深信服):
   得分：0.78 | 信号：观望
   2小时加速度：+0.05 📈
   持仓状态：持有 ✅
```

---

## 🎯 开发计划

| Phase | 主题 | 状态 | 完成度 |
|-------|------|------|--------|
| **Phase 1** | 数据查看器 | ✅ 完成 | 100% |
| **Phase 2** | 技术指标分析 | ✅ 完成 | 100% |
| **Phase 3** | 情绪分析 | ✅ 完成 | 100% |
| **Phase 4** | AI 预测模型 | ✅ 完成 | 100% |
| **Phase 5** | Web 界面 | ✅ 完成 | 100% |
| **Phase 6** | 多模型集成 | ✅ 完成 | 100% |
| Phase 7 | A股专用功能 | 🟡 开发中 | 30% |

---

## 🔒 安全提醒

### ⚠️ 不提交到 Git 的文件

以下文件已添加到 `.gitignore`，不会提交到远程仓库：

```bash
data/cache/               # 股票数据缓存
data/sentistock.db        # SQLite 数据库
output/                   # 生成结果 (图表、报告)
.env                      # 环境变量 (含密码)
```

### ✅ 使用环境变量

不要在代码中硬编码密码：

```bash
# 推荐方式
export JQ_USER=你的手机号
export JQ_PASSWORD=你的密码
```

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## ⚠️ 免责声明

**重要提示:**

- 本项目仅供**学习和研究** 使用
- 所有分析结果**不构成投资建议**
- 股市有风险，投资需谨慎
- 使用本项目做出的任何投资决策，风险自负

---

## 📞 联系方式

- 问题反馈：[GitHub Issues](https://github.com/jerrynbc/Sentistock/issues)
- 项目讨论：[GitHub Discussions](https://github.com/jerrynbc/Sentistock/discussions)

---

<div align="center">

**如果觉得项目有用，请给个 ⭐ Star 支持一下！**

Made with ❤️ by Sentistock Team

</div>
