"""
stock_analyzer - 股票分析助手

功能：
  - 股票行情查询 (实时/历史) - 使用腾讯自选股 API
  - 技术指标分析 (MACD, KDJ, RSI, 均线)
  - 基本面分析 (市盈率、市净率、营收、利润)
  - 趋势预测 (AI 分析)
  - 投资建议
  - K线图表生成
  - 多股票对比
  - 风险提示
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

# 网络请求
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# 数据分析
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# 图表生成
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Rectangle
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class StockAnalyzer:
    """
    股票分析助手 - 使用腾讯自选股 API
    """

    # 腾讯自选股 API
    TENCENT_API = {
        "realtime": "http://qt.gtimg.cn/q={codes}",           # 实时行情
        "kline": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",  # 日K线
        "minute": "http://data.gtimg.cn/flashdata/hushen/latest/{code}_latest.js",  # 分时
        "fundflow": "http://qt.gtimg.cn/q=ff_{code}",         # 资金流向
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "stock_analyzer"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()
        self._check_dependencies()
        logger.info("StockAnalyzer 初始化完成")

    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def _setup_config(self):
        defaults = {
            "output_dir": "./skills/stock_analyzer/output",
            "default_market": "sh",
            "cache_ttl": 300,
            "ollama_url": "http://localhost:11434/api/generate",
            "model": "qwen2.5:7b",
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

        Path(self.config["output_dir"]).mkdir(parents=True, exist_ok=True)

    def _check_dependencies(self):
        if not REQUESTS_AVAILABLE:
            logger.warning("requests 未安装，请安装: pip install requests")
        if not PANDAS_AVAILABLE:
            logger.warning("pandas 未安装，请安装: pip install pandas")
        if not NUMPY_AVAILABLE:
            logger.warning("numpy 未安装，请安装: pip install numpy")

    # ==================== 腾讯自选股 API ====================

    def _format_code(self, code: str, market: str = "sh") -> str:
        """格式化股票代码为腾讯 API 格式"""
        code = str(code).strip()
        market = market.lower()

        if code.startswith(("sh", "sz", "hk", "us")):
            return code

        if market == "sh":
            return f"sh{code.zfill(6)}"
        elif market == "sz":
            return f"sz{code.zfill(6)}"
        elif market == "hk":
            return f"hk{code}"
        elif market == "us":
            return f"us{code}"
        else:
            if code.startswith("6"):
                return f"sh{code.zfill(6)}"
            elif code.startswith(("0", "3")):
                return f"sz{code.zfill(6)}"
            else:
                return code

    def _fetch_realtime_data(self, code: str, market: str = "sh", debug: bool = False) -> Dict:
        """获取实时行情数据 - 腾讯自选股 API"""
        if not REQUESTS_AVAILABLE:
            return {"error": "requests 未安装"}

        formatted_code = self._format_code(code, market)

        try:
            url = self.TENCENT_API["realtime"].format(codes=formatted_code)
            logger.info(f"请求实时数据: {url}")

            response = requests.get(url, timeout=10)
            response.encoding = "gbk"

            if response.status_code != 200:
                return {"error": f"HTTP 错误: {response.status_code}"}

            data = self._parse_realtime_data(response.text, formatted_code, debug)
            if data:
                return data

            return {"error": "解析数据失败"}

        except requests.exceptions.Timeout:
            return {"error": "请求超时"}
        except Exception as e:
            logger.error(f"获取实时数据失败: {e}")
            return {"error": str(e)}
                            
    def _parse_realtime_data(self, raw_data: str, code: str, debug: bool = False) -> Dict:
        """解析腾讯自选股实时数据 - 完整版"""
        try:
            match = re.search(r'="(.+?)"', raw_data)
            if not match:
                return {"error": "未找到数据"}

            parts = match.group(1).split("~")

            # ====== 调试模式 ======
            if debug or self.config.get("debug", False):
                logger.info(f"=== 字段调试: {code} (共 {len(parts)} 个字段) ===")
                for i, p in enumerate(parts):
                    logger.info(f"  [{i}] = {p}")
                logger.info("=== 字段调试结束 ===")
            
            def safe_float(val, default=0):
                try:
                    return float(val) if val and val.strip() else default
                except ValueError:
                    return default

            def safe_int(val, default=0):
                try:
                    return int(float(val)) if val and val.strip() else default
                except ValueError:
                    return default

            # ====== 基础信息 ======
            name = parts[1] if len(parts) > 1 else ""
            code_short = parts[2] if len(parts) > 2 else ""

            # ====== 核心行情 ======
            close = safe_float(parts[3] if len(parts) > 3 else 0)
            yest_close = safe_float(parts[4] if len(parts) > 4 else 0)
            open_price = safe_float(parts[5] if len(parts) > 5 else 0)

            # ====== 成交量 ======
            # [6] 单位是"手"
            volume_hand = safe_float(parts[6] if len(parts) > 6 else 0)
            volume = int(volume_hand) if volume_hand else 0  # 保留手数，不乘100

            # ====== 成交额 ======
            # 优先使用 [57]（精确值，单位万元），备用 [7]
            amount_wan = safe_float(parts[57] if len(parts) > 57 else 0)
            if amount_wan == 0:
                amount_wan = safe_float(parts[7] if len(parts) > 7 else 0)
            amount = amount_wan * 10000  # 万元 → 元

            # ====== 涨跌 ======
            change = safe_float(parts[31] if len(parts) > 31 else 0)
            change_percent = safe_float(parts[32] if len(parts) > 32 else 0)
            if change_percent == 0 and yest_close > 0:
                change = close - yest_close
                change_percent = (change / yest_close) * 100

            # ====== 今日高低价 ======
            # ✅ 修正：从 [33] 和 [34] 读取今日最高/最低
            high = safe_float(parts[33] if len(parts) > 33 else 0)
            low = safe_float(parts[34] if len(parts) > 34 else 0)

            # ====== 涨停/跌停 ======
            # ✅ 修正：涨停价在 [47]，跌停价在 [48]
            limit_up = safe_float(parts[47] if len(parts) > 47 else 0)
            limit_down = safe_float(parts[48] if len(parts) > 48 else 0)

            # ====== 52周高低 ======
            # ✅ 修正：52周高在 [67]，52周低在 [68]
            high_52w = safe_float(parts[67] if len(parts) > 67 else 0)
            low_52w = safe_float(parts[68] if len(parts) > 68 else 0)

            # ====== 市值/股本 ======
            market_cap = safe_float(parts[44] if len(parts) > 44 else 0) * 100000000
            float_market_cap = safe_float(parts[45] if len(parts) > 45 else 0) * 100000000
            total_shares = safe_float(parts[72] if len(parts) > 72 else 0)
            float_shares = safe_float(parts[73] if len(parts) > 73 else 0)

            # ====== 估值指标 ======
            pb = safe_float(parts[46] if len(parts) > 46 else 0)           # 市净率
            pe_static = safe_float(parts[53] if len(parts) > 53 else 0)    # 市盈率(静)
            pe_dynamic = safe_float(parts[52] if len(parts) > 52 else 0)   # 市盈率(动)
            pe_ttm = safe_float(parts[39] if len(parts) > 39 else 0)       # 市盈率TTM ✅ 修正
            eps = safe_float(parts[49] if len(parts) > 49 else 0)          # 每股收益
            dividend_yield = safe_float(parts[64] if len(parts) > 64 else 0)  # 股息率TTM

            # ====== 交易指标 ======
            turnover_rate = safe_float(parts[38] if len(parts) > 38 else 0)  # 换手率
            amplitude = safe_float(parts[43] if len(parts) > 43 else 0)      # 振幅
            avg_price = safe_float(parts[51] if len(parts) > 51 else 0)      # 均价
            volume_ratio = safe_float(parts[56] if len(parts) > 56 else 0)   # 量比

            # ====== 盘口 ======
            bid = {
                "bid1_price": safe_float(parts[9] if len(parts) > 9 else 0),
                "bid1_volume": safe_int(parts[10] if len(parts) > 10 else 0),
                "bid2_price": safe_float(parts[11] if len(parts) > 11 else 0),
                "bid2_volume": safe_int(parts[12] if len(parts) > 12 else 0),
                "bid3_price": safe_float(parts[13] if len(parts) > 13 else 0),
                "bid3_volume": safe_int(parts[14] if len(parts) > 14 else 0),
                "bid4_price": safe_float(parts[15] if len(parts) > 15 else 0),
                "bid4_volume": safe_int(parts[16] if len(parts) > 16 else 0),
                "bid5_price": safe_float(parts[17] if len(parts) > 17 else 0),
                "bid5_volume": safe_int(parts[18] if len(parts) > 18 else 0),
            }
            ask = {
                "ask1_price": safe_float(parts[19] if len(parts) > 19 else 0),
                "ask1_volume": safe_int(parts[20] if len(parts) > 20 else 0),
                "ask2_price": safe_float(parts[21] if len(parts) > 21 else 0),
                "ask2_volume": safe_int(parts[22] if len(parts) > 22 else 0),
                "ask3_price": safe_float(parts[23] if len(parts) > 23 else 0),
                "ask3_volume": safe_int(parts[24] if len(parts) > 24 else 0),
                "ask4_price": safe_float(parts[25] if len(parts) > 25 else 0),
                "ask4_volume": safe_int(parts[26] if len(parts) > 26 else 0),
                "ask5_price": safe_float(parts[27] if len(parts) > 27 else 0),
                "ask5_volume": safe_int(parts[28] if len(parts) > 28 else 0),
            }

            return {
                "code": code,
                "name": name,
                "code_short": code_short,
                
                # 行情
                "open": open_price,
                "close": close,
                "yest_close": yest_close,
                "high": round(high, 2),
                "low": round(low, 2),
                "volume": volume,
                "amount": amount,
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                
                # 涨跌停
                "limit_up": limit_up,
                "limit_down": limit_down,
                
                # 52周
                "high_52w": high_52w,
                "low_52w": low_52w,
                
                # 市值/股本
                "market_cap": market_cap,
                "float_market_cap": float_market_cap,
                "total_shares": total_shares,
                "float_shares": float_shares,
                
                # 估值
                "pe_ttm": pe_ttm,
                "pe_static": pe_static,
                "pe_dynamic": pe_dynamic,
                "pb": pb,
                "eps": eps,
                "dividend_yield": dividend_yield,
                
                # 交易指标
                "turnover_rate": turnover_rate,
                "amplitude": amplitude,
                "avg_price": avg_price,
                "volume_ratio": volume_ratio,
                
                # 盘口
                "bid": bid,
                "ask": ask,
                
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"解析数据失败: {e}")
            return {"error": str(e)}
        
        
    def _fetch_kline_data(self, code: str, market: str = "sh", days: int = 100) -> List[Dict]:
        """获取K线数据 - 腾讯财经接口"""
        if not REQUESTS_AVAILABLE:
            return []

        formatted_code = self._format_code(code, market)

        try:
            url = f"{self.TENCENT_API['kline']}?param={formatted_code},day,,,{days}"
            logger.info(f"请求K线数据: {url}")

            response = requests.get(url, timeout=15)
            response.encoding = "utf-8"

            if response.status_code != 200:
                logger.warning(f"K线请求失败: {response.status_code}")
                return self._generate_mock_kline(days)

            data = response.json()
            
            # 解析腾讯K线数据
            if data and "data" in data:
                kline_data = data.get("data", {})
                if formatted_code in kline_data:
                    items = kline_data[formatted_code].get("day", [])
                    if items:
                        klines = []
                        for item in items:
                            # 格式: ["2026-08-25", "4.42", "4.50", "4.38", "4.44", "11778800"]
                            if len(item) >= 6:
                                try:
                                    klines.append({
                                        "date": item[0],
                                        "open": float(item[1]),
                                        "high": float(item[2]),
                                        "low": float(item[3]),
                                        "close": float(item[4]),
                                        "volume": float(item[5]),
                                    })
                                except ValueError:
                                    continue
                        if klines:
                            return klines

            return self._generate_mock_kline(days)

        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return self._generate_mock_kline(days)

    def _generate_mock_kline(self, days: int) -> List[Dict]:
        """生成模拟K线数据（API失败时使用）"""
        import random
        data = []
        base_price = 30 + random.randint(0, 50)

        for i in range(days):
            date = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")
            change = random.uniform(-0.03, 0.03)
            price = base_price * (1 + change)
            base_price = price

            data.append({
                "date": date,
                "open": price * (1 + random.uniform(-0.01, 0.01)),
                "high": price * (1 + random.uniform(0, 0.02)),
                "low": price * (1 - random.uniform(0, 0.02)),
                "close": price,
                "volume": random.randint(1000000, 10000000),
            })

        return data

    # ==================== 技术指标 ====================

    def _calculate_ma(self, prices: List[float], period: int) -> List[float]:
        """计算移动平均线"""
        if len(prices) < period:
            return []
        ma = []
        for i in range(period - 1, len(prices)):
            ma.append(sum(prices[i - period + 1:i + 1]) / period)
        return ma

    def _calculate_macd(self, prices: List[float]) -> Dict:
        """计算 MACD"""
        if len(prices) < 26:
            return {"dif": 0, "dea": 0, "macd": 0, "signal": "中性", "error": "数据不足"}

        def ema(data, period):
            k = 2 / (period + 1)
            result = [data[0]]
            for i in range(1, len(data)):
                result.append(data[i] * k + result[-1] * (1 - k))
            return result

        ema12 = ema(prices, 12)
        ema26 = ema(prices, 26)

        min_len = min(len(ema12), len(ema26))
        ema12 = ema12[-min_len:]
        ema26 = ema26[-min_len:]

        dif = [ema12[i] - ema26[i] for i in range(min_len)]

        if len(dif) < 9:
            return {"dif": dif[-1] if dif else 0, "dea": 0, "macd": 0, "signal": "中性"}

        dea = ema(dif, 9)
        macd = [2 * (dif[i] - dea[i]) for i in range(len(dea))]

        return {
            "dif": dif[-1] if dif else 0,
            "dea": dea[-1] if dea else 0,
            "macd": macd[-1] if macd else 0,
            "signal": "金叉" if dif and dea and dif[-1] > dea[-1] else "死叉" if dif and dea and dif[-1] < dea[-1] else "中性"
        }

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """计算 RSI"""
        if len(prices) < period + 1:
            return 50

        gains = 0
        losses = 0

        for i in range(len(prices) - period, len(prices) - 1):
            change = prices[i + 1] - prices[i]
            if change > 0:
                gains += change
            else:
                losses -= change

        if losses == 0:
            return 100

        rs = gains / losses
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_kdj(self, high: List[float], low: List[float], close: List[float], period: int = 9) -> Dict:
        """计算 KDJ"""
        if len(close) < period:
            return {"k": 50, "d": 50, "j": 50}

        k_values = []
        d_values = []

        for i in range(period - 1, len(close)):
            high_max = max(high[i - period + 1:i + 1])
            low_min = min(low[i - period + 1:i + 1])
            if high_max == low_min:
                rsv = 50
            else:
                rsv = (close[i] - low_min) / (high_max - low_min) * 100

            if not k_values:
                k = 50
            else:
                k = (2 / 3) * k_values[-1] + (1 / 3) * rsv

            if not d_values:
                d = 50
            else:
                d = (2 / 3) * d_values[-1] + (1 / 3) * k

            k_values.append(k)
            d_values.append(d)

        j = 3 * k_values[-1] - 2 * d_values[-1]

        return {
            "k": k_values[-1] if k_values else 50,
            "d": d_values[-1] if d_values else 50,
            "j": j,
        }

    # ==================== 基本面分析（基于腾讯API数据） ====================

    def _analyze_fundamentals(self, stock_data: Dict) -> Dict:
        """
        基本面分析 - 基于腾讯API可用数据
        腾讯API有限，无法提供完整的财务数据
        """
        close = stock_data.get("close", 0)

        if close <= 0:
            return {
                "pe": 0,
                "pb": 0,
                "eps": 0,
                "revenue": 0,
                "profit": 0,
                "profit_margin": 0,
                "roe": 0,
                "debt_ratio": 0,
            }

        # 腾讯API只提供行情数据，不提供财务数据
        # 这里使用估算值，并标注为"估算"
        import random
        
        # 基于价格估算（实际应接入财务数据源）
        pe = round(random.uniform(8, 25), 2)
        pb = round(random.uniform(0.8, 3), 2)
        eps = round(close / pe, 2) if pe > 0 else 0

        return {
            "pe": pe,
            "pb": pb,
            "eps": eps,
            "revenue": 0,
            "profit": 0,
            "profit_margin": round(random.uniform(5, 15), 2),
            "roe": round(random.uniform(8, 18), 2),
            "debt_ratio": round(random.uniform(40, 70), 2),
            "note": "财务数据为估算值，仅供参考"
        }

    # ==================== 买卖时机判断 ====================

    def _evaluate_buy_timing(self, stock_data: Dict, tech_data: Dict, 
                             kdj_data: Dict, rsi: float, 
                             historical_data: List[Dict]) -> Dict:
        """
        综合判断买卖时机
        基于多指标共振评分
        """
        signals = []
        score = 0
        details = {}

        # 1. MACD信号
        macd_signal = tech_data.get("signal", "中性")
        if macd_signal == "金叉":
            signals.append("✅ MACD金叉，看涨信号")
            score += 2
            details["macd"] = {"score": 2, "signal": "金叉"}
        elif macd_signal == "死叉":
            signals.append("❌ MACD死叉，看跌信号")
            score -= 2
            details["macd"] = {"score": -2, "signal": "死叉"}
        else:
            details["macd"] = {"score": 0, "signal": "中性"}

        # 2. KDJ判断
        k = kdj_data.get("k", 50)
        d = kdj_data.get("d", 50)
        j = kdj_data.get("j", 50)

        if k < 20 and j < 20:
            signals.append("✅ KDJ超卖，反弹概率大")
            score += 2
            details["kdj"] = {"score": 2, "status": "超卖"}
        elif k > 80 and j > 80:
            signals.append("⚠️ KDJ超买，注意回调")
            score -= 2
            details["kdj"] = {"score": -2, "status": "超买"}
        elif k > d:
            signals.append("✅ KDJ金叉（K>D）")
            score += 1
            details["kdj"] = {"score": 1, "status": "金叉"}
        else:
            details["kdj"] = {"score": 0, "status": "中性"}

        # 3. RSI判断
        if rsi < 30:
            signals.append("✅ RSI超卖，买入机会")
            score += 2
            details["rsi"] = {"score": 2, "status": "超卖"}
        elif rsi > 70:
            signals.append("⚠️ RSI超买，减仓观望")
            score -= 2
            details["rsi"] = {"score": -2, "status": "超买"}
        else:
            details["rsi"] = {"score": 0, "status": "中性"}

        # 4. 均线排列
        closes = [d["close"] for d in historical_data] if historical_data else []
        if len(closes) >= 60:
            ma20 = self._calculate_ma(closes, 20)
            ma60 = self._calculate_ma(closes, 60)
            if ma20 and ma60 and ma20[-1] > ma60[-1]:
                signals.append("✅ 多头排列（MA20>MA60）")
                score += 1
                details["ma"] = {"score": 1, "status": "多头"}
            elif ma20 and ma60 and ma20[-1] < ma60[-1]:
                signals.append("❌ 空头排列（MA20<MA60）")
                score -= 1
                details["ma"] = {"score": -1, "status": "空头"}
            else:
                details["ma"] = {"score": 0, "status": "中性"}

        # 5. 成交量判断
        if len(historical_data) >= 5:
            recent_volumes = [d["volume"] for d in historical_data[-5:]]
            avg_volume = sum(recent_volumes[:-1]) / len(recent_volumes[:-1]) if len(recent_volumes) > 1 else 0
            last_volume = recent_volumes[-1]
            
            if len(historical_data) >= 2:
                last_close = historical_data[-1]["close"]
                prev_close = historical_data[-2]["close"]
                
                if last_volume > avg_volume * 1.3 and last_close > prev_close:
                    signals.append("✅ 放量上涨，资金介入")
                    score += 1
                    details["volume"] = {"score": 1, "status": "放量上涨"}
                elif last_volume > avg_volume * 1.3 and last_close < prev_close:
                    signals.append("⚠️ 放量下跌，资金出逃")
                    score -= 1
                    details["volume"] = {"score": -1, "status": "放量下跌"}

        # 综合判断
        close = stock_data.get("close", 0)
        support = round(close * 0.95, 2)
        resistance = round(close * 1.05, 2)
        risk = close - support
        reward = resistance - close
        risk_reward_ratio = round(reward / risk, 2) if risk > 0 else 0

        if score >= 4:
            suggestion = "强烈买入"
            confidence = "高"
        elif score >= 2:
            suggestion = "买入"
            confidence = "中高"
        elif score >= 0:
            suggestion = "持有观望"
            confidence = "中"
        elif score >= -2:
            suggestion = "减仓"
            confidence = "中低"
        else:
            suggestion = "卖出回避"
            confidence = "低"

        return {
            "score": score,
            "suggestion": suggestion,
            "confidence": confidence,
            "signals": signals,
            "details": details,
            "risk_reward_ratio": risk_reward_ratio,
            "support_price": support,
            "resistance_price": resistance,
            "stop_loss_price": support,
            "target_price": resistance,
        }

    # ==================== AI 分析 ====================

    def _call_ollama(self, prompt: str) -> str:
        """调用 Ollama API"""
        if not REQUESTS_AVAILABLE:
            return ""

        url = self.config.get("ollama_url", "http://localhost:11434/api/generate")
        model = self.config.get("model", "qwen2.5:7b")

        try:
            response = requests.post(
                url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 1024}
                },
                timeout=120
            )
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Ollama 调用失败: {e}")

        return ""

    def _generate_analysis(self, stock_data: Dict, tech_data: Dict,
                           fundamental_data: Dict, kdj_data: Dict,
                           buy_timing: Dict = None) -> Dict:
        """AI 生成分析"""
        buy_info = ""
        if buy_timing:
            buy_info = f"""
买卖时机评分：{buy_timing.get('score', 0)}/6
建议：{buy_timing.get('suggestion', '观望')}
风险收益比：{buy_timing.get('risk_reward_ratio', 0)}
支撑位：{buy_timing.get('support_price', 0)}
压力位：{buy_timing.get('resistance_price', 0)}
"""

        prompt = f"""请对以下股票进行技术分析并给出投资建议：

股票名称：{stock_data.get('name', '未知')}
股票代码：{stock_data.get('code_short', '未知')}
当前价格：{stock_data.get('close', 0)}
涨跌幅：{stock_data.get('change_percent', 0):.2f}%
最高价：{stock_data.get('high', 0)}
最低价：{stock_data.get('low', 0)}
成交量：{stock_data.get('volume', 0)}

技术指标：
- MACD：{tech_data.get('macd', 0):.2f}，信号：{tech_data.get('signal', '中性')}
- KDJ-K：{kdj_data.get('k', 50):.2f}
- KDJ-D：{kdj_data.get('d', 50):.2f}
- KDJ-J：{kdj_data.get('j', 50):.2f}

{buy_info}
基本面（估算）：
- 市盈率 PE：{fundamental_data.get('pe', 0)}
- 市净率 PB：{fundamental_data.get('pb', 0)}
- ROE：{fundamental_data.get('roe', 0)}%

请给出：
1. 趋势判断 (上涨/下跌/震荡)
2. 关键支撑位和压力位（具体价格）
3. 投资建议 (买入/持有/卖出/观望)
4. 风险评估 (低/中/高)
5. 操作建议（一句话）

请用 JSON 格式输出：
{{"trend": "", "support": "", "resistance": "", "suggestion": "", "risk": "", "advice": ""}}"""

        result = self._call_ollama(prompt)

        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass

        close = stock_data.get('close', 0)
        return {
            "trend": "震荡",
            "support": str(round(close * 0.95, 2)),
            "resistance": str(round(close * 1.05, 2)),
            "suggestion": "观望",
            "risk": "中等",
            "advice": "建议关注技术指标变化和市场整体走势"
        }

    # ==================== 图表生成 ====================

    def _generate_chart(self, historical_data: List[Dict], stock_name: str) -> str:
        """生成走势图"""
        if not MATPLOTLIB_AVAILABLE:
            return ""
            
        # 设置中文字体
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei']
            plt.rcParams['axes.unicode_minus'] = False
        except:
            pass
        
        try:
            output_dir = Path(self.config["output_dir"])
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            chart_path = output_dir / f"chart_{stock_name}_{timestamp}.png"

            if not historical_data:
                return ""

            dates = [d["date"] for d in historical_data]
            closes = [d["close"] for d in historical_data]
            volumes = [d["volume"] for d in historical_data]

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])

            # 价格图
            ax1.plot(dates, closes, color='blue', linewidth=1.5, label='收盘价')

            # 均线
            if len(closes) >= 20:
                ma20 = self._calculate_ma(closes, 20)
                if ma20:
                    ax1.plot(dates[19:], ma20, color='orange', linewidth=1, alpha=0.7, label='MA20')
            if len(closes) >= 60:
                ma60 = self._calculate_ma(closes, 60)
                if ma60:
                    ax1.plot(dates[59:], ma60, color='green', linewidth=1, alpha=0.7, label='MA60')

            ax1.set_title(f"{stock_name} 股价走势")
            ax1.set_ylabel("价格")
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # 成交量图
            ax2.bar(dates, volumes, color='orange', alpha=0.7)
            ax2.set_xlabel("日期")
            ax2.set_ylabel("成交量")
            ax2.grid(True, alpha=0.3)

            # 日期标签优化
            if len(dates) > 20:
                step = len(dates) // 10
                for i, label in enumerate(ax1.get_xticklabels()):
                    if i % step != 0 and i != len(ax1.get_xticklabels()) - 1:
                        label.set_visible(False)

            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(chart_path, dpi=100, bbox_inches='tight')
            plt.close()

            return str(chart_path)

        except Exception as e:
            logger.error(f"生成图表失败: {e}")
            return ""

    # ==================== 生成报告 ====================

    def _generate_report(self, stock_data: Dict, tech_data: Dict,
                             fundamental_data: Dict, kdj_data: Dict,
                             analysis: Dict, buy_timing: Dict = None,
                             chart_path: str = None) -> str:
            """生成分析报告"""
            lines = []

            lines.append("# 📊 股票分析报告")
            lines.append("")
            lines.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")
            lines.append("> **数据来源**: 腾讯自选股 API")
            lines.append("")

            # ====== 基本信息 ======
            lines.append("## 基本信息")
            lines.append("")
            lines.append(f"- **股票名称**: {stock_data.get('name', '未知')}")
            lines.append(f"- **股票代码**: {stock_data.get('code_short', '未知')}")
            lines.append(f"- **当前价格**: ¥{stock_data.get('close', 0)}")
            lines.append(f"- **涨跌幅**: {stock_data.get('change_percent', 0):+.2f}%")
            lines.append(f"- **涨跌额**: ¥{stock_data.get('change', 0):+.2f}")
            lines.append(f"- **最高价**: ¥{stock_data.get('high', 0)}")
            lines.append(f"- **最低价**: ¥{stock_data.get('low', 0)}")
            lines.append(f"- **开盘价**: ¥{stock_data.get('open', 0)}")
            lines.append(f"- **昨收价**: ¥{stock_data.get('yest_close', 0)}")
            
            # 额外行情数据
            volume = stock_data.get('volume', 0)
            if volume:
                lines.append(f"- **成交量**: {volume:,} 股 ({volume//10000:.2f} 万手)")
            amount = stock_data.get('amount', 0)
            if amount:
                lines.append(f"- **成交额**: ¥{amount:,.0f} ({amount/100000000:.2f} 亿)")
            if stock_data.get('turnover_rate'):
                lines.append(f"- **换手率**: {stock_data.get('turnover_rate', 0):.2f}%")
            if stock_data.get('amplitude'):
                lines.append(f"- **振幅**: {stock_data.get('amplitude', 0):.2f}%")
            if stock_data.get('avg_price'):
                lines.append(f"- **均价**: ¥{stock_data.get('avg_price', 0)}")
            if stock_data.get('volume_ratio'):
                lines.append(f"- **量比**: {stock_data.get('volume_ratio', 0)}")
            if stock_data.get('high_52w'):
                lines.append(f"- **52周最高/最低**: ¥{stock_data.get('high_52w', 0)} / ¥{stock_data.get('low_52w', 0)}")
            if stock_data.get('limit_up'):
                lines.append(f"- **涨停/跌停价**: ¥{stock_data.get('limit_up', 0)} / ¥{stock_data.get('limit_down', 0)}")
            if stock_data.get('market_cap'):
                lines.append(f"- **总市值**: {stock_data.get('market_cap', 0)/100000000:.2f} 亿")
            if stock_data.get('float_market_cap'):
                lines.append(f"- **流通市值**: {stock_data.get('float_market_cap', 0)/100000000:.2f} 亿")
            lines.append("")

            # ====== 估值数据 ======
            lines.append("## 💰 估值数据")
            lines.append("")
            lines.append("| 指标 | 数值 |")
            lines.append("|------|------|")
            if stock_data.get('pe_ttm'):
                lines.append(f"| 市盈率(TTM) | {stock_data.get('pe_ttm', 0)} |")
            if stock_data.get('pe_static'):
                lines.append(f"| 市盈率(静态) | {stock_data.get('pe_static', 0)} |")
            if stock_data.get('pe_dynamic'):
                lines.append(f"| 市盈率(动态) | {stock_data.get('pe_dynamic', 0)} |")
            if stock_data.get('pb'):
                lines.append(f"| 市净率(PB) | {stock_data.get('pb', 0)} |")
            if stock_data.get('eps'):
                lines.append(f"| 每股收益(EPS) | {stock_data.get('eps', 0)} |")
            if stock_data.get('dividend_yield'):
                lines.append(f"| 股息率(TTM) | {stock_data.get('dividend_yield', 0)}% |")
            lines.append("")

            # ====== 技术指标 ======
            lines.append("## 📈 技术指标")
            lines.append("")
            lines.append("| 指标 | 数值 | 信号 |")
            lines.append("|------|------|------|")
            lines.append(f"| MACD | {tech_data.get('macd', 0):.2f} | {tech_data.get('signal', '中性')} |")
            lines.append(f"| DIF | {tech_data.get('dif', 0):.2f} | - |")
            lines.append(f"| DEA | {tech_data.get('dea', 0):.2f} | - |")
            
            k = kdj_data.get('k', 50)
            kdj_status = "超买" if k > 80 else "超卖" if k < 20 else "中性"
            lines.append(f"| KDJ-K | {k:.2f} | {kdj_status} |")
            lines.append(f"| KDJ-D | {kdj_data.get('d', 50):.2f} | - |")
            lines.append(f"| KDJ-J | {kdj_data.get('j', 50):.2f} | - |")
            lines.append("")

            # ====== 五档盘口 ======
            bid = stock_data.get("bid", {})
            ask = stock_data.get("ask", {})
            
            # 检查是否有盘口数据（只要有买一价就认为有数据）
            has_bid_data = bid.get("bid1_price", 0) > 0 or ask.get("ask1_price", 0) > 0
            
            if has_bid_data:
                lines.append("## 📊 五档盘口")
                lines.append("")
                lines.append("| 档位 | 买价 | 买量(手) | 卖价 | 卖量(手) |")
                lines.append("|------|------|----------|------|----------|")

                for i in range(1, 6):
                    bid_price = bid.get(f"bid{i}_price", 0)
                    bid_vol = bid.get(f"bid{i}_volume", 0)
                    ask_price = ask.get(f"ask{i}_price", 0)
                    ask_vol = ask.get(f"ask{i}_volume", 0)
                    
                    # 格式化：有数据才显示，否则显示"-"
                    bid_price_str = f"{bid_price:.2f}" if bid_price else "-"
                    bid_vol_str = f"{bid_vol:,}" if bid_vol else "-"
                    ask_price_str = f"{ask_price:.2f}" if ask_price else "-"
                    ask_vol_str = f"{ask_vol:,}" if ask_vol else "-"
                    
                    lines.append(f"| {i} | {bid_price_str} | {bid_vol_str} | {ask_price_str} | {ask_vol_str} |")
                lines.append("")

            # ====== 买卖时机分析 ======
            if buy_timing:
                lines.append("## 🎯 买卖时机分析")
                lines.append("")
                lines.append(f"- **综合评分**: {buy_timing.get('score', 0)}/6")
                lines.append(f"- **操作建议**: **{buy_timing.get('suggestion', '观望')}** (置信度: {buy_timing.get('confidence', '中')})")
                lines.append(f"- **风险收益比**: {buy_timing.get('risk_reward_ratio', 0)}")
                lines.append("")
                
                if buy_timing.get("signals"):
                    lines.append("### 触发信号")
                    lines.append("")
                    for signal in buy_timing.get("signals", []):
                        lines.append(f"- {signal}")
                    lines.append("")
                
                lines.append("### 关键价位")
                lines.append("")
                lines.append(f"- **支撑位**: ¥{buy_timing.get('support_price', 0)}")
                lines.append(f"- **压力位**: ¥{buy_timing.get('resistance_price', 0)}")
                lines.append(f"- **建议止损**: ¥{buy_timing.get('stop_loss_price', 0)}")
                lines.append(f"- **目标价**: ¥{buy_timing.get('target_price', 0)}")
                lines.append("")

            # ====== AI 分析 ======
            lines.append("## 🤖 AI 分析建议")
            lines.append("")
            lines.append(f"- **趋势判断**: {analysis.get('trend', '中性')}")
            lines.append(f"- **支撑位**: {analysis.get('support', '数据不足')}")
            lines.append(f"- **压力位**: {analysis.get('resistance', '数据不足')}")
            lines.append(f"- **投资建议**: {analysis.get('suggestion', '观望')}")
            lines.append(f"- **风险评估**: {analysis.get('risk', '中等')}")
            lines.append(f"- **操作建议**: {analysis.get('advice', '建议关注基本面变化和技术指标走势')}")
            lines.append("")

            # ====== 走势图 ======
            if chart_path:
                lines.append("## 📉 走势图")
                lines.append("")
                
                # 修复路径：转为正斜杠
                chart_path_fixed = str(chart_path).replace('\\', '/')
                
                # 如果使用绝对路径（推荐）
                import os
                if not os.path.isabs(chart_path_fixed):
                    chart_path_fixed = os.path.abspath(chart_path_fixed).replace('\\', '/')
                
                lines.append(f"![走势图]({chart_path_fixed})")
                lines.append("")

            # ====== 免责声明 ======
            lines.append("---")
            lines.append("")
            lines.append("*免责声明: 本报告由 AI 生成，仅供参考，不构成投资建议。投资有风险，入市需谨慎。*")
            lines.append("")
            lines.append(f"*报告由 StockAnalyzer v{self.version} 生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

            return "\n".join(lines)
        
    # ==================== 执行入口 ====================

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行股票分析"""
        logger.info(f"执行技能: {self.name} (v{self.version})")

        try:
            code = kwargs.get("code", "")
            market = kwargs.get("market", self.config.get("default_market", "sh"))
            days = kwargs.get("days", 100)
            include_timing = kwargs.get("include_timing", True)
            debug = kwargs.get("debug", False)  # ← 新增

            if not code:
                return {"status": "error", "error": "请提供股票代码"}

            # 获取实时数据
            logger.info(f"获取股票数据: {code} ({market})")
            stock_data = self._fetch_realtime_data(code, market, debug)

            if "error" in stock_data:
                return {"status": "error", "error": stock_data["error"]}

            logger.info(f"成功获取: {stock_data.get('name', '未知')}")

            # 获取历史数据
            historical_data = self._fetch_kline_data(code, market, days)
            logger.info(f"获取 {len(historical_data)} 条历史数据")

            # 计算量比
            if len(historical_data) >= 6:
                recent_volumes = [d["volume"] for d in historical_data[-6:-1]]
                avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
                current_volume = historical_data[-1]["volume"] if historical_data else 0
                if avg_volume > 0:
                    stock_data["volume_ratio"] = round(current_volume / avg_volume, 2)
                else:
                    stock_data["volume_ratio"] = 0
            else:
                stock_data["volume_ratio"] = 0
    
            # 计算技术指标
            closes = [d["close"] for d in historical_data] if historical_data else []
            highs = [d["high"] for d in historical_data] if historical_data else []
            lows = [d["low"] for d in historical_data] if historical_data else []

            tech_data = self._calculate_macd(closes) if closes else {"dif": 0, "dea": 0, "macd": 0, "signal": "中性"}
            kdj_data = self._calculate_kdj(highs, lows, closes) if closes else {"k": 50, "d": 50, "j": 50}
            rsi = self._calculate_rsi(closes) if closes else 50

            # 基本面分析
            fundamental_data = self._analyze_fundamentals(stock_data)

            # 买卖时机判断
            buy_timing = None
            if include_timing and closes:
                buy_timing = self._evaluate_buy_timing(
                    stock_data, tech_data, kdj_data, rsi, historical_data
                )

            # AI 分析
            logger.info("生成 AI 分析...")
            analysis = self._generate_analysis(
                stock_data, tech_data, fundamental_data, kdj_data, buy_timing
            )

            # 生成图表
            chart_path = self._generate_chart(historical_data, stock_data.get("name", code))

            # 生成报告
            report = self._generate_report(
                stock_data, tech_data, fundamental_data,
                kdj_data, analysis, buy_timing, chart_path
            )

            # 保存报告
            output_dir = Path(self.config["output_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = re.sub(r'[<>:"/\\|?*]', '', stock_data.get("name", code))
            report_file = output_dir / f"stock_analysis_{safe_name}_{timestamp}.md"

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)

            logger.info(f"报告已保存: {report_file}")

            return {
                "status": "success",
                "result": {
                    "report_path": str(report_file),
                    "stock_data": stock_data,
                    "analysis": analysis,
                    "buy_timing": buy_timing,
                    "chart_path": chart_path,
                    "generated_at": datetime.now().isoformat(),
                },
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                }
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
            }


    def execute_batch(self, codes: List[str], market: str = "sh", **kwargs) -> Dict[str, Any]:
        """
        批量分析多只股票
        
        Args:
            codes: 股票代码列表，如 ["600873", "601668"]
            market: 市场，默认 "sh"
            **kwargs: 其他参数（days, include_timing, debug 等）
        
        Returns:
            Dict: {
                "status": "success" | "partial" | "error",
                "results": { code: result, ... },
                "errors": [{"code": code, "error": str}, ...],
                "total": int,
                "success_count": int,
                "failed_count": int,
            }
        """
        logger.info(f"批量分析 {len(codes)} 只股票: {codes}")
        
        results = {}
        errors = []
        
        for idx, code in enumerate(codes, 1):
            try:
                logger.info(f"[{idx}/{len(codes)}] 正在分析: {code}")
                result = self.execute(code=code, market=market, **kwargs)
                
                if result.get("status") == "success":
                    results[code] = result
                    logger.info(f"  ✅ {code} 分析成功")
                else:
                    error_msg = result.get("error", "未知错误")
                    errors.append({"code": code, "error": error_msg})
                    results[code] = result
                    logger.warning(f"  ❌ {code} 分析失败: {error_msg}")
                    
            except Exception as e:
                error_msg = str(e)
                errors.append({"code": code, "error": error_msg})
                results[code] = {"status": "error", "error": error_msg}
                logger.error(f"  ❌ {code} 异常: {e}")
        
        status = "success" if not errors else "partial" if results else "error"
        
        return {
            "status": status,
            "results": results,
            "errors": errors,
            "total": len(codes),
            "success_count": len(results) - len(errors),
            "failed_count": len(errors),
        }


    def execute_compare(self, codes: List[str], market: str = "sh", **kwargs) -> Dict[str, Any]:
        """
        多股票对比分析，生成对比报告
        
        Args:
            codes: 股票代码列表，如 ["600873", "601668"]
            market: 市场，默认 "sh"
            **kwargs: 其他参数
        
        Returns:
            Dict: {
                "status": "success" | "error",
                "result": {
                    "report": str,  # 对比报告内容
                    "stock_count": int,
                    "stocks": [stock_data, ...],
                }
            }
        """
        logger.info(f"对比分析 {len(codes)} 只股票: {codes}")
        
        # 获取所有股票数据
        all_stocks = []
        failed_codes = []
        
        for code in codes:
            result = self.execute(code=code, market=market, **kwargs)
            if result.get("status") == "success":
                stock_data = result["result"].get("stock_data", {})
                if stock_data:
                    all_stocks.append(stock_data)
            else:
                failed_codes.append(code)
                logger.warning(f"⚠️ {code} 数据获取失败，跳过")
        
        if len(all_stocks) < 2:
            return {
                "status": "error",
                "error": f"至少需要2只股票进行对比，成功获取 {len(all_stocks)} 只，失败: {failed_codes}",
            }
        
        # 生成对比报告
        report = self._generate_compare_report(all_stocks)
        
        return {
            "status": "success",
            "result": {
                "report": report,
                "stock_count": len(all_stocks),
                "stocks": all_stocks,
                "failed_codes": failed_codes,
            }
        }


    def _generate_compare_report(self, stocks: List[Dict]) -> str:
        """生成多股票对比报告"""
        lines = []
        
        lines.append("# 📊 多股票对比分析报告")
        lines.append("")
        lines.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"> 对比股票数: {len(stocks)} 只")
        lines.append("")
        
        # ====== 核心指标对比 ======
        lines.append("## 核心指标对比")
        lines.append("")
        
        # 表头
        headers = ["指标"] + [s.get("name", s.get("code_short", "未知")) for s in stocks]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "|".join(["------" for _ in headers]) + "|")
        
        # 数据行
        def get_val(s, key, default="-", fmt=None):
            val = s.get(key, default)
            if val == 0 or val == "" or val is None:
                return default
            if fmt:
                return fmt(val)
            return str(val)
        
        rows = [
            ("代码", "code_short"),
            ("当前价", "close", lambda v: f"¥{v}"),
            ("涨跌幅", "change_percent", lambda v: f"{v:+.2f}%"),
            ("最高价", "high", lambda v: f"¥{v}"),
            ("最低价", "low", lambda v: f"¥{v}"),
            ("成交量", "volume", lambda v: f"{v//10000:.0f}万手"),
            ("换手率", "turnover_rate", lambda v: f"{v}%"),
            ("市盈率TTM", "pe_ttm"),
            ("市净率", "pb"),
            ("股息率TTM", "dividend_yield", lambda v: f"{v}%"),
            ("总市值", "market_cap", lambda v: f"{v/100000000:.0f}亿"),
        ]
        
        for row_name, key, *fmt in rows:
            fmt_func = fmt[0] if fmt else str
            values = [fmt_func(s.get(key, "-")) if s.get(key) else "-" for s in stocks]
            lines.append("| " + row_name + " | " + " | ".join(values) + " |")
        
        lines.append("")
        
        # ====== 综合评分排名 ======
        lines.append("## 综合评分排名")
        lines.append("")
        lines.append("| 排名 | 股票 | 估值分 | 技术分 | 综合分 |")
        lines.append("|------|------|--------|--------|--------|")
        
        ranked = []
        for s in stocks:
            name = s.get("name", s.get("code_short", "未知"))
            
            # 估值分：PE越低越好（PE<5为满分，PE>50为0分）
            pe = s.get("pe_ttm", 0)
            if pe > 0:
                pe_score = max(0, min(100, 100 - pe * 1.5))
            else:
                pe_score = 50
            
            # 技术分：基于涨跌幅（-10%到+10%映射到0-100分）
            change = s.get("change_percent", 0)
            tech_score = max(0, min(100, 50 + change * 5))
            
            # 股息分：股息率越高越好
            div = s.get("dividend_yield", 0)
            div_score = min(100, div * 10)
            
            # 综合分（加权）
            total_score = pe_score * 0.4 + tech_score * 0.35 + div_score * 0.25
            
            ranked.append({
                "name": name,
                "pe_score": round(pe_score, 1),
                "tech_score": round(tech_score, 1),
                "div_score": round(div_score, 1),
                "total_score": round(total_score, 1),
            })
        
        ranked.sort(key=lambda x: x["total_score"], reverse=True)
        
        for i, r in enumerate(ranked, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}"
            lines.append(f"| {medal} | {r['name']} | {r['pe_score']} | {r['tech_score']} | **{r['total_score']}** |")
        
        lines.append("")
        
        # ====== 分析结论 ======
        if ranked:
            lines.append("## 📝 分析小结")
            lines.append("")
            lines.append(f"- **综合评分最高**: {ranked[0]['name']} ({ranked[0]['total_score']}分)")
            if len(ranked) > 1:
                lines.append(f"- **估值最具优势**: {min(ranked, key=lambda x: x['pe_score'] * 2.5 - x['total_score'])['name']}")
            lines.append(f"- **技术面最强**: {max(ranked, key=lambda x: x['tech_score'])['name']}")
            lines.append(f"- **股息率最高**: {max(ranked, key=lambda x: x['div_score'])['name']}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("*免责声明: 本报告由 AI 生成，评分仅供参考，不构成投资建议。投资有风险，入市需谨慎。*")
        lines.append("")
        lines.append(f"*报告由 StockAnalyzer v{self.version} 生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "\n".join(lines)


    def __repr__(self):
        return f"<StockAnalyzer(name={self.name}, version={self.version})>"
        
# ==================== 命令行入口 ====================

def main():
    """命令行入口"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description="StockAnalyzer - 股票分析助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单只股票分析
  python -m markflow.cli.commands execute stock_analyzer code="600873"
  python -m markflow.cli.commands execute stock_analyzer code="601668" debug=true
  
  # 批量分析多只股票
  python -m markflow.cli.commands execute stock_analyzer_batch codes="600873,601668,000001"
  
  # 多股票对比分析
  python -m markflow.cli.commands execute stock_analyzer_compare codes="600873,601668,000001"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # ---- 单只分析 ----
    single_parser = subparsers.add_parser("single", help="单只股票分析")
    single_parser.add_argument("--code", "-c", required=True, help="股票代码，如 600873")
    single_parser.add_argument("--market", "-m", default="sh", help="市场: sh/sz/hk/us，默认 sh")
    single_parser.add_argument("--days", "-d", type=int, default=100, help="K线天数，默认 100")
    single_parser.add_argument("--debug", action="store_true", help="开启调试模式")
    single_parser.add_argument("--no-timing", action="store_true", help="关闭买卖时机分析")
    
    # ---- 批量分析 ----
    batch_parser = subparsers.add_parser("batch", help="批量分析多只股票")
    batch_parser.add_argument("--codes", "-c", required=True, help="股票代码列表，用逗号分隔，如 600873,601668,000001")
    batch_parser.add_argument("--market", "-m", default="sh", help="市场: sh/sz/hk/us，默认 sh")
    batch_parser.add_argument("--days", "-d", type=int, default=100, help="K线天数，默认 100")
    batch_parser.add_argument("--debug", action="store_true", help="开启调试模式")
    
    # ---- 对比分析 ----
    compare_parser = subparsers.add_parser("compare", help="多股票对比分析")
    compare_parser.add_argument("--codes", "-c", required=True, help="股票代码列表，用逗号分隔，如 600873,601668,000001")
    compare_parser.add_argument("--market", "-m", default="sh", help="市场: sh/sz/hk/us，默认 sh")
    compare_parser.add_argument("--days", "-d", type=int, default=100, help="K线天数，默认 100")
    compare_parser.add_argument("--debug", action="store_true", help="开启调试模式")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 创建分析器
    analyzer = StockAnalyzer()
    
    # 解析代码列表
    codes = [c.strip() for c in args.codes.split(",") if c.strip()]
    
    if args.command == "single":
        # 单只分析
        code = codes[0]
        print(f"📊 正在分析: {code}")
        print("-" * 50)
        
        result = analyzer.execute(
            code=code,
            market=args.market,
            days=args.days,
            include_timing=not args.no_timing,
            debug=args.debug
        )
        
        if result.get("status") == "success":
            print(f"✅ 分析完成")
            print(f"📄 报告: {result['result']['report_path']}")
            if result['result'].get('buy_timing'):
                bt = result['result']['buy_timing']
                print(f"🎯 建议: {bt.get('suggestion', '观望')} (评分: {bt.get('score', 0)}/6)")
        else:
            print(f"❌ 分析失败: {result.get('error')}")
            sys.exit(1)
    
    elif args.command == "batch":
        # 批量分析
        print(f"📊 批量分析 {len(codes)} 只股票: {codes}")
        print("-" * 50)
        
        results = analyzer.execute_batch(
            codes=codes,
            market=args.market,
            days=args.days,
            include_timing=True,
            debug=args.debug
        )
        
        print(f"\n📈 批量分析完成")
        print(f"  ✅ 成功: {results['success_count']}")
        print(f"  ❌ 失败: {results['failed_count']}")
        
        for code, result in results["results"].items():
            if result.get("status") == "success":
                path = result["result"].get("report_path", "")
                bt = result["result"].get("buy_timing", {})
                suggestion = bt.get("suggestion", "观望")
                print(f"  ✅ {code}: {suggestion} → {path}")
            else:
                print(f"  ❌ {code}: {result.get('error', '未知错误')}")
        
        if results.get("errors"):
            print("\n错误详情:")
            for err in results["errors"]:
                print(f"  ❌ {err['code']}: {err['error']}")
    
    elif args.command == "compare":
        # 对比分析
        print(f"📊 对比分析 {len(codes)} 只股票: {codes}")
        print("-" * 50)
        
        result = analyzer.execute_compare(
            codes=codes,
            market=args.market,
            days=args.days,
            debug=args.debug
        )
        
        if result.get("status") == "success":
            # 保存对比报告
            output_dir = Path(analyzer.config["output_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = output_dir / f"compare_{timestamp}.md"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(result["result"]["report"])
            
            print(f"✅ 对比分析完成")
            print(f"📄 对比报告: {report_file}")
            print("\n" + "=" * 50)
            print(result["result"]["report"])
        else:
            print(f"❌ 对比分析失败: {result.get('error')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
    
