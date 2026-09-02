# stock_analyzer

> 股票行情查询、技术指标分析、多股票对比、AI趋势预测、投资建议


## 概览

- **版本**: 1.1.0
- **文件数**: 1
- **类数**: 1
- **方法数**: 20+
- **数据源**: 腾讯自选股 API


## 技能描述

股票分析助手，支持实时行情查询、技术指标分析 (MACD、KDJ、RSI、均线)、估值分析 (PE/PB/股息率)、五档盘口、多股票对比、AI 趋势预测、K线图生成和买卖时机判断。

### 核心功能

- 📊 **实时行情** - 获取股票实时价格、涨跌幅、成交量、成交额
- 📈 **技术指标** - MACD、KDJ、RSI、MA20/MA60
- 💰 **估值分析** - 市盈率(TTM/静态/动态)、市净率、股息率TTM
- 📋 **五档盘口** - 买卖各5档价格和数量
- 🎯 **买卖时机** - 多维度综合评分 (MACD/KDJ/RSI/均线/成交量)
- 🤖 **AI 预测** - 基于大模型的趋势分析和投资建议
- 📉 **K线图表** - 自动生成股价走势图 (含MA均线)
- 📊 **多股票对比** - 核心指标对比、综合评分排名
- 📦 **批量分析** - 一次分析多只股票
- ⚠️ **风险评估** - 综合风险评估


## 输入参数

### 单只分析

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `code` | string | 是 | - | 股票代码 (如: 600036) |
| `market` | string | 否 | sh | 市场 (sh/sz/hk/us) |
| `days` | integer | 否 | 100 | 历史数据天数 |
| `include_timing` | boolean | 否 | true | 是否开启买卖时机分析 |
| `debug` | boolean | 否 | false | 开启调试模式，打印88个字段 |
| `model` | string | 否 | qwen2.5:7b | Ollama 模型 |

### 批量分析

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `codes` | List[str] | 是 | - | 股票代码列表 |
| `market` | string | 否 | sh | 市场 |
| `days` | integer | 否 | 100 | 历史数据天数 |

### 对比分析

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `codes` | List[str] | 是 | - | 股票代码列表 (至少2只) |
| `market` | string | 否 | sh | 市场 |
| `days` | integer | 否 | 100 | 历史数据天数 |


## 输出字段

| 字段 | 说明 |
|------|------|
| `report_path` | 分析报告路径 |
| `stock_data` | 股票实时/估值/盘口数据 |
| `analysis` | AI 分析建议 |
| `buy_timing` | 买卖时机评分和建议 |
| `chart_path` | 走势图路径 |
| `generated_at` | 生成时间 |


## 使用示例

### 命令行 (单只分析)

```bash
# 基本使用
python -m markflow.cli.commands execute stock_analyzer code="600036"

# 指定市场和天数
python -m markflow.cli.commands execute stock_analyzer code="601668" market="sh" days=200

# 开启调试模式 (打印88个字段)
python -m markflow.cli.commands execute stock_analyzer code="600873" debug=true

# 关闭买卖时机分析
python -m markflow.cli.commands execute stock_analyzer code="600036" no-timing=true

# 指定AI模型
python -m markflow.cli.commands execute stock_analyzer code="600036" model="qwen2.5:3b"
```

### 命令行 (批量分析)

```bash
# 批量分析多只股票
python -m markflow.cli.commands execute stock_analyzer_batch codes="600873,601668,000001"

# 指定市场和天数
python -m markflow.cli.commands execute stock_analyzer_batch codes="600873,601668" market="sh" days=200
```

### 命令行 (多股票对比)

```bash
# 对比分析
python -m markflow.cli.commands execute stock_analyzer_compare codes="600873,601668,000001"

# 指定市场和天数
python -m markflow.cli.commands execute stock_analyzer_compare codes="600873,601668" market="sh" days=200
```

### 模块导入

```python
from skills.stock_analyzer.skill import StockAnalyzer

# 创建分析器
analyzer = StockAnalyzer()

# 单只分析
result = analyzer.execute(code="600873")
print(result["result"]["report_path"])

# 批量分析
results = analyzer.execute_batch(
    codes=["600873", "601668", "000001"],
    days=100
)
print(f"成功: {results['success_count']}, 失败: {results['failed_count']}")

# 对比分析
compare_result = analyzer.execute_compare(
    codes=["600873", "601668", "000001"]
)
print(compare_result["result"]["report"])

# 自定义配置
analyzer = StockAnalyzer(config={
    "ollama_url": "http://localhost:11434/api/generate",
    "model": "deepseek-r1:7b",
    "output_dir": "./output",
    "debug": False,
})
```

### 输出示例

单只分析报告
markdown
# 📊 股票分析报告

> 生成时间: 2026-08-25 15:07:42
> **数据来源**: 腾讯自选股 API

## 基本信息

- **股票名称**: 梅花生物
- **股票代码**: 600873
- **当前价格**: ¥7.87
- **涨跌幅**: +0.00%
- **涨跌额**: ¥+0.00
- **最高价**: ¥7.92
- **最低价**: ¥7.78
- **开盘价**: ¥7.85
- **昨收价**: ¥7.87
- **成交量**: 155,201 股 (15.00 万手)
- **成交额**: ¥121,563,876 (1.22 亿)
- **换手率**: 0.55%
- **振幅**: 1.78%
- **均价**: ¥7.83
- **量比**: 0.64
- **52周最高/最低**: ¥12.81 / ¥6.70
- **涨停/跌停价**: ¥8.66 / ¥7.08
- **总市值**: 220.69 亿
- **流通市值**: 220.69 亿

## 💰 估值数据

| 指标 | 数值 |
|------|------|
| 市盈率(TTM) | 10.15 |
| 市盈率(静态) | 6.73 |
| 市盈率(动态) | 16.67 |
| 市净率(PB) | 1.41 |
| 每股收益(EPS) | 0.71 |
| 股息率(TTM) | 5.49% |

## 📈 技术指标

| 指标 | 数值 | 信号 |
|------|------|------|
| MACD | 0.20 | 金叉 |
| DIF | -0.43 | - |
| DEA | -0.53 | - |
| KDJ-K | 48.37 | 中性 |
| KDJ-D | 51.52 | - |
| KDJ-J | 42.06 | - |

## 📊 五档盘口

| 档位 | 买价 | 买量(手) | 卖价 | 卖量(手) |
|------|------|----------|------|----------|
| 1 | 7.86 | 1,880 | 7.87 | 1,216 |
| 2 | 7.85 | 2,180 | 7.88 | 800 |
| 3 | 7.84 | 768 | 7.89 | 616 |
| 4 | 7.83 | 2,189 | 7.90 | 465 |
| 5 | 7.82 | 2,986 | 7.91 | 392 |

## 🎯 买卖时机分析

- **综合评分**: 1/6
- **操作建议**: **持有观望** (置信度: 中)
- **风险收益比**: 1.0

### 触发信号

- ✅ MACD金叉，看涨信号
- ❌ 空头排列（MA20<MA60）

### 关键价位

- **支撑位**: ¥7.48
- **压力位**: ¥8.26
- **建议止损**: ¥7.48
- **目标价**: ¥8.26

## 🤖 AI 分析建议

- **趋势判断**: 震荡
- **支撑位**: 7.48
- **压力位**: 8.26
- **投资建议**: 持有观望
- **风险评估**: 中
- **操作建议**: 保持谨慎，关注市场动态
多股票对比报告
markdown
# 📊 多股票对比分析报告

> 生成时间: 2026-08-25 15:30:00
> 对比股票数: 3 只

## 核心指标对比

| 指标 | 梅花生物 | 中国建筑 | 万科A |
|------|---------|---------|-------|
| 代码 | 600873 | 601668 | 000002 |
| 当前价 | ¥7.87 | ¥4.46 | ¥8.52 |
| 涨跌幅 | +0.00% | +0.90% | -1.20% |
| 最高价 | ¥7.92 | ¥4.50 | ¥8.65 |
| 最低价 | ¥7.78 | ¥4.40 | ¥8.40 |
| 成交量 | 15万手 | 136万手 | 89万手 |
| 换手率 | 0.55% | 0.37% | 0.42% |
| 市盈率TTM | 10.15 | 4.86 | 8.32 |
| 市净率 | 1.41 | 0.85 | 1.12 |
| 股息率TTM | 5.49% | 6.09% | 5.12% |
| 总市值 | 220亿 | 1842亿 | 1024亿 |

## 综合评分排名

| 排名 | 股票 | 估值分 | 技术分 | 综合分 |
|------|------|--------|--------|--------|
| 🥇 | 中国建筑 | 92.7 | 54.5 | **77.5** |
| 🥈 | 梅花生物 | 84.8 | 50.0 | **71.4** |
| 🥉 | 万科A | 87.5 | 44.0 | **69.5** |

## 📝 分析小结

- **综合评分最高**: 中国建筑 (77.5分)
- **估值最具优势**: 中国建筑
- **技术面最强**: 中国建筑
- **股息率最高**: 中国建筑

依赖安装

```bash
pip install requests pandas numpy matplotlib
```

Ollama (AI分析)

```bash

# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载模型
ollama pull qwen2.5:7b
# 或
ollama pull deepseek-r1:7b
```

输出位置

生成的报告和图表保存在 skills/stock_analyzer/output/ 目录下：

路径	说明
stock_analysis_{name}_{timestamp}.md	单只分析报告
chart_{name}_{timestamp}.png	走势图
compare_{timestamp}.md	多股票对比报告

数据源说明
数据源	说明
腾讯自选股	实时行情、K线数据、估值数据、盘口数据
Ollama	AI 分析 (本地大模型)

技术指标说明
指标	说明
MACD	指数平滑异同移动平均线 (12,26,9)
KDJ	随机指标 (9,3,3)
RSI	相对强弱指标 (14)
MA20	20日移动平均线
MA60	60日移动平均线

买卖时机评分维度
维度	权重	信号
MACD	+2/-2	金叉/死叉
KDJ	+2/-2	超卖/超买
RSI	+2/-2	超卖/超买
均线排列	+1/-1	多头/空头
成交量	+1/-1	放量上涨/放量下跌

注意事项
⚠️ 数据仅供参考，不构成投资建议

⚠️ 投资有风险，入市需谨慎

⚠️ AI 分析结果仅供参考，请结合自身判断

⚠️ 财务数据 (PE/ROE等) 为估算值，实际以公司财报为准

更新日志
v1.1.0 (2026-08-25)
✨ 新增多股票对比分析功能

✨ 新增批量分析功能

✨ 新增五档盘口数据解析和展示

✨ 新增买卖时机综合评分系统

✨ 新增股息率TTM、量比等估值指标

🐛 修复腾讯API字段映射错误 (最高/最低/涨跌停/52周/PE)

🐛 修复成交量和成交额单位错误

📝 优化报告结构，增加估值数据板块

🔧 新增调试模式，支持打印88个字段

v1.0.0 (2026-08-24)
🎉 初始版本

📊 实时行情查询

📈 技术指标分析 (MACD/KDJ/RSI/均线)

🤖 AI 趋势预测

📉 K线图表生成

文档版本: 1.1.0 | 生成于 2026-08-25


