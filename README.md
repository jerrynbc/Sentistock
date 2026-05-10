# 📊 Sentistock - AI 股票情绪分析系统

<div align="center">

**基于 NLP 和时间加权模型的股票投资决策辅助系统**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Phase](https://img.shields.io/badge/Phase-3%20Complete-green.svg)]()

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [使用文档](#-使用文档) • [项目结构](#-项目结构) • [开发计划](#-开发计划)

</div>

---

##  项目简介

**Sentistock** 是一个专业的股票情绪分析系统，通过 NLP 技术分析新闻情感，结合时间加权模型和技术指标，为投资决策提供数据支持。

### 核心理念

> **不是所有消息都同样重要，不是所有消息都一样持久。**

传统的舆情分析平等对待所有新闻，但 Sentistock 考虑了：
- ⏰ **时间衰减** - 新消息权重更高
- 📢 **事件影响力** - 重大事件影响更深远
-  **多维度整合** - 技术面 + 情绪面综合判断

---

## ✨ 功能特性

### ✅ 已完成 (Phase 3)

| 功能 | 说明 | 状态 |
|------||------|
| **新闻情绪分析** | SnowNLP 情感打分，详细解释 | ✅ |
| **时间加权模型** | 半衰期 + 影响力 + 新鲜度 | ✅ |
| **个人记忆库** | 记录小道消息和个人观察 | ✅ |
| **完整证据链** | 每条判断都有据可查 | ✅ |
| **情绪可视化** | 5 种专业图表 | ✅ |
| **详细文档** | 5 份使用指南 | ✅ |
| **回测框架** | 聚宽数据回测 | ✅ |

### 🚧 开发中

| 功能 | 说明 | 进度 |
|------|------|------|
| 真实数据回测 | 聚宽/财联社数据 | 🟡 50% |
| 多维度整合 | 技术 + 情绪综合评分 | ⏳ 待开发 |
| AI 预测模型 | 机器学习预测 | ⏳ Phase 4 |

---

## 🔧 技术栈

- **语言**: Python 3.11+
- **NLP**: SnowNLP, jieba
- **数据分析**: pandas, numpy
- **可视化**: matplotlib
- **数据源**: 聚宽 (JoinQuant), yfinance
- **回测**: 自定义回测框架

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 基础使用 - 分析单只股票

```bash
python3 src/main.py 300454
```

**输出包括:**
- 📊 技术指标分析
- 📰 新闻情绪分析
- 💬 个人观察记录
- ⏰ 时间加权分析
- 📁 完整分析报告

### 3. 聚宽回测 (需要免费账号)

```bash
# 1. 注册聚宽账号 (https://www.joinquant.com/)
# 2. 设置环境变量
export JQ_USER=你的手机号
export JQ_PASSWORD=你的密码

# 3. 运行回测
python3 src/analysis/joinquant_backtest.py
```

### 4. 个人记忆库

```bash
python3 src/analysis/memory_bank.py 300454

# 交互式命令:
> rumor 听说公司要裁员了 员工 high
> obs 产品大卖 [产品]
> trend
> report
```

---

## 📚 使用文档

| 文档 | 说明 |
|------|------|
| [情绪分析详解](docs/情绪分析详解.md) | 情感分析原理和过程 |
| [证据链指南](docs/情绪分析证据链指南.md) | 完整证据链输出 |
| [记忆库使用指南](docs/记忆库使用指南.md) | 个人观察系统 |
| [时间加权指南](docs/时间加权情绪分析指南.md) | 时间衰减模型 |
| [聚宽回测指南](docs/聚宽回测使用指南.md) | 回测框架使用 |

---

## 📊 项目结构

```
sentistock/
├── src/
│   ├── data/                # 数据采集
│   │   └── collector.py     # 股票数据获取
│   ├── analysis/            # 分析模块
│   │   ├── indicators.py    # 技术指标
│   │   ├── sentiment.py     # 情感分析
│   │   ├── memory_bank.py   # 个人记忆库
│   │   ├── time_weighted_sentiment.py  # 时间加权
│   │   └── news_crawler.py  # 新闻爬虫
│   ├── visual/              # 可视化
│   │   ├── charts.py        # K 线图
│   │   ├── indicator_charts.py # 指标图
│   │   └── sentiment_charts.py # 情绪图
│   └── main.py              # 主程序
├── docs/                    # 文档
├── plan/                    # 开发计划
├── requirements.txt         # 依赖
└── README.md               # 本文件
```

---

## 🎯 开发计划

| Phase | 主题 | 状态 | 完成度 |
|-------|------|------|--------|
| **Phase 1** | 数据查看器 | ✅ 完成 | 100% |
| **Phase 2** | 技术指标分析 | ✅ 完成 | 100% |
| **Phase 3** | 情绪分析 | ✅ 完成 | 100% |
| Phase 4 | AI 预测模型 | ⏳ 待开发 | 0% |
| Phase 5 | Web 界面 | ⏳ 待开发 | 0% |

---

## 📈 使用案例

### 案例 1: 深信服 (300454) 综合分析

```bash
$ python3 src/main.py 300454
```

**分析结果:**
```
技术指标：🟢 多头趋势
公开新闻：⚪ 中性偏多
小道消息：🔴 负面担忧
时间加权：🔴 负面权重高

综合信号：-1 (偏向谨慎)
投资建议：考虑减仓，规避风险
```

### 案例 2: 情绪回测验证

```bash
$ python3 src/analysis/joinquant_backtest.py
```

**回测结果 (模拟数据):**
```
买入信号：16 次
买入后平均收益：+1.31%
买入胜率：68.8% ✓

卖出信号：14 次
卖出后平均收益：+1.50%
卖出胜率：14.3% (需优化)
```

---

## 🔒 安全提醒

### ⚠️ 不要上传的文件

以下文件包含敏感信息，已添加到 `.gitignore`:

```bash
# 个人数据
memory_*.json       # 个人观察记录
*_分析报告_*.txt    # 投资分析报告

# 测试文件 (可能包含密码)
test_jq.py          # 聚宽测试 (含密码)
.env                # 环境变量 (含密码)

# 生成的图表
*.png
```

### ✅ 使用环境变量

不要在代码中硬编码密码：

```bash
# 推荐方式
export JQ_USER=你的手机号
export JQ_PASSWORD=你的密码
```

```python
# 错误方式 ❌
password = '你的真实密码'

# 正确方式 ✅
password = os.getenv('JQ_PASSWORD')
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

- 本项目仅供**学习和研究**使用
- 所有分析结果**不构成投资建议**
- 股市有风险，投资需谨慎
- 使用本项目做出的任何投资决策，风险自负

---

## 📞 联系方式

- 问题反馈：[GitHub Issues](https://github.com/你的用户名/sentistock/issues)
- 项目讨论：[GitHub Discussions](https://github.com/你的用户名/sentistock/discussions)

---

<div align="center">

**如果觉得项目有用，请给个 ⭐ Star 支持一下！**

Made with ❤️ by Sentistock Team

</div>
