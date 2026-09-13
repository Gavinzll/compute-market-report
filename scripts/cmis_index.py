#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CMIS 价格指数模块。

借鉴 Silicon Data 的指数化思路：
- 每个 GPU 型号有一个标准化指数值（CMIS Index）
- 指数基于多源数据聚合，而非单一报价
- 提供 7 日 / 30 日趋势指标
- Token 价格也有综合指数

数据来源：
- 从历史快照（data/cmis_snapshot_*.json）计算趋势
- 当日指数值来自标准化后的多源聚合

指数代码（Ticker）命名规则：
- CMIS-{GPU_MODEL}-CN  ：国内租赁指数（万元/8卡整机/月）
- CMIS-{GPU_MODEL}-US  ：海外租赁指数（美元/卡/小时）
- CMIS-TOKEN-INDEX     ：Token 综合价格指数（美元/百万输入 token，加权平均）
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))
NOW = datetime.now(TZ)
DATE = NOW.date().isoformat()

# 指数代码映射（GPU 型号 -> ticker 后缀）
GPU_TICKER_MAP = {
    "H100 80G": "H100",
    "H200 141GB": "H200",
    "B200": "B200",
    "B300": "B300",
    "GB200": "GB200",
    "GB300": "GB300",
    "A100 80G": "A100",
    "A10": "A10",
    "L40S": "L40S",
    "L4": "L4",
    "H20": "H20",
    "RTX 5090": "RTX5090",
    "RTX 4090": "RTX4090",
    "昇腾 910C": "ASC910C",
    "昇腾 910B": "ASC910B",
    "寒武纪 MLU370-X8": "MLU370",
    "海光 DCU K100": "K100",
    "壁仞 BR100": "BR100",
    "摩尔线程 MTT S4000": "MTTS4000",
    "MI300X": "MI300X",
    "MI300A": "MI300A",
}


def gpu_ticker(gpu_model: str, region: str = "CN") -> str:
    """生成 GPU 指数代码。"""
    suffix = GPU_TICKER_MAP.get(gpu_model, gpu_model.replace(" ", "").upper())
    return f"CMIS-{suffix}-{region.upper()}"


def _load_snapshot(date_str: str) -> dict | None:
    """加载指定日期的快照。"""
    path = ROOT / "data" / f"cmis_snapshot_{date_str}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _find_available_snapshots(days_back: int = 60) -> list[str]:
    """查找最近 N 天内可用的快照日期列表（倒序，最新在前）。"""
    dates = []
    for d in range(days_back + 1):
        day = (NOW - timedelta(days=d)).date().isoformat()
        path = ROOT / "data" / f"cmis_snapshot_{day}.json"
        if path.exists():
            dates.append(day)
    return dates


def _get_price_from_snapshot(snap: dict, gpu_model: str, region: str) -> float | None:
    """从快照中提取指定 GPU 型号的价格。

    region: "CN" -> 国内标准化价格（万元/8卡整机/月）
            "US" -> 海外单卡小时价（美元）
    """
    if region == "CN":
        rows = snap.get("domestic_rental", [])
        for r in rows:
            if r.get("GPU 型号") == gpu_model and r.get("校验状态") == "PASS":
                price = r.get("标准化价格")
                if price is not None and isinstance(price, (int, float)) and price > 0:
                    return float(price)
    else:  # US
        rows = snap.get("overseas_rental", [])
        for r in rows:
            if r.get("GPU 型号") == gpu_model and r.get("校验状态") == "PASS":
                # 海外快照里存的是人民币单卡小时价，需要转美元
                cny = r.get("单卡小时价（人民币）")
                fx = snap.get("fx", {}).get("rate")
                if cny is not None and fx and isinstance(cny, (int, float)) and cny > 0 and fx > 0:
                    return round(float(cny) / float(fx), 4)
    return None


def calc_gpu_index(gpu_model: str, region: str = "CN",
                   current_price: float | None = None) -> dict[str, Any]:
    """计算单个 GPU 型号的指数及趋势。

    返回：
    {
        "ticker": "CMIS-H100-CN",
        "current": 7.6,           # 当前指数值
        "unit": "万元/8卡整机/月",  # 单位
        "change_7d": 0.023,       # 7 日变化率（小数，如 0.023 = +2.3%）
        "change_30d": -0.051,     # 30 日变化率
        "change_7d_pct": "+2.3%", # 格式化字符串
        "change_30d_pct": "-5.1%",
        "direction": "up",        # up / down / flat
        "history_7d": [...],      # 最近 7 个有效数据点
        "history_30d": [...],     # 最近 30 个有效数据点
        "data_points_7d": 5,      # 实际可用的数据点数
        "data_points_30d": 20,
        "source_count": 3,        # 数据源数量（当日）
    }
    """
    ticker = gpu_ticker(gpu_model, region)
    unit = "万元/8卡整机/月" if region == "CN" else "美元/卡/小时"
    
    # 收集历史数据
    available_dates = _find_available_snapshots(60)
    
    history: list[tuple[str, float]] = []  # [(date, price), ...]
    
    # 如果传入了当前价格，优先使用
    if current_price is not None:
        history.append((DATE, current_price))
    
    # 从历史快照补充
    seen_dates = {d for d, _ in history}
    for d in available_dates:
        if d in seen_dates:
            continue
        snap = _load_snapshot(d)
        if not snap:
            continue
        price = _get_price_from_snapshot(snap, gpu_model, region)
        if price is not None:
            history.append((d, price))
            seen_dates.add(d)
    
    # 按日期排序（旧 -> 新）
    history.sort(key=lambda x: x[0])
    
    if not history:
        return {
            "ticker": ticker,
            "current": None,
            "unit": unit,
            "change_7d": None,
            "change_30d": None,
            "change_7d_pct": "N/A",
            "change_30d_pct": "N/A",
            "direction": "unknown",
            "history_7d": [],
            "history_30d": [],
            "data_points_7d": 0,
            "data_points_30d": 0,
            "source_count": 0,
        }
    
    current_val = history[-1][1]
    
    # 找 7 天前（前后 2 天容错）的价格
    def find_price_n_days_ago(n: int) -> tuple[str, float] | None:
        target_date = (NOW - timedelta(days=n)).date().isoformat()
        # 精确匹配优先
        for d, p in history:
            if d == target_date:
                return (d, p)
        # 否则找最接近的（前后 2 天内）
        best = None
        best_diff = 999
        target_dt = datetime.fromisoformat(target_date).date()
        for d, p in history:
            dt = datetime.fromisoformat(d).date()
            diff = abs((dt - target_dt).days)
            if diff <= 3 and diff < best_diff:
                best_diff = diff
                best = (d, p)
        return best
    
    price_7d_ago = find_price_n_days_ago(7)
    price_30d_ago = find_price_n_days_ago(30)
    
    def calc_change(old: float | None) -> tuple[float | None, str, str]:
        if old is None or old == 0 or current_val is None:
            return (None, "N/A", "unknown")
        change = (current_val - old) / old
        pct_str = f"{'+' if change >= 0 else ''}{change * 100:.1f}%"
        direction = "up" if change > 0.005 else ("down" if change < -0.005 else "flat")
        return (change, pct_str, direction)
    
    change_7d, change_7d_pct, dir_7d = calc_change(price_7d_ago[1] if price_7d_ago else None)
    change_30d, change_30d_pct, dir_30d = calc_change(price_30d_ago[1] if price_30d_ago else None)
    
    # 历史序列（最多 30 个点）
    history_30d = history[-30:] if len(history) >= 7 else history
    history_7d = history[-7:] if len(history) >= 3 else history
    
    return {
        "ticker": ticker,
        "current": current_val,
        "unit": unit,
        "change_7d": change_7d,
        "change_30d": change_30d,
        "change_7d_pct": change_7d_pct,
        "change_30d_pct": change_30d_pct,
        "direction": dir_7d if change_7d is not None else "unknown",
        "history_7d": history_7d,
        "history_30d": history_30d,
        "data_points_7d": len(history_7d),
        "data_points_30d": len(history_30d),
        "source_count": 0,  # 调用方填充
    }


def _parse_token_price(price_str: str | float | int | None) -> float | None:
    """从 Token 价格字符串中解析出美元/百万 token 的数值。
    
    支持格式：
    - "USD 5.0/百万Token（约 ¥33.54；精确同名）" -> 5.0
    - "CNY 0.8/百万Token（同系列参考，海外三方折算）" -> 需配合汇率转 USD
    - 直接数值 -> 直接返回
    """
    if price_str is None:
        return None
    if isinstance(price_str, (int, float)):
        return float(price_str) if price_str > 0 else None
    
    s = str(price_str).strip()
    # USD 格式
    if s.upper().startswith("USD"):
        import re
        m = re.search(r'USD\s*([\d.]+)', s, re.IGNORECASE)
        if m:
            try:
                val = float(m.group(1))
                return val if val > 0 else None
            except ValueError:
                pass
    # CNY 格式（暂时跳过，需汇率转换，此处不处理）
    if s.upper().startswith("CNY"):
        return None  # CNY 价格暂不纳入海外指数计算
    return None


def calc_token_index(token_data: list[dict]) -> dict[str, Any]:
    """计算 Token 综合价格指数。

    借鉴 Silicon Data 的 Token Market Pulse：
    - 以主流模型为样本，计算加权平均输入价格
    - 权重按模型市场热度/重要性分配
    - 单位：美元 / 百万输入 token

    返回：
    {
        "ticker": "CMIS-TOKEN-INDEX",
        "current": 2.35,            # 当前指数值（美元/百万输入 token）
        "unit": "USD/1M input tokens",
        "change_7d": ...,
        "change_30d": ...,
        "sample_size": 53,
        "history_7d": [...],
    }
    """
    # 主流模型权重（按市场重要性分配，基于实际模型名）
    # 权重总和约为 10
    WEIGHTS = {
        "GPT-5.5": 1.5,
        "GPT-5.4": 1.2,
        "Claude Opus 4.8": 1.0,
        "Claude Sonnet 4.6": 1.5,
        "Claude Haiku 4.5": 0.5,
        "Gemini 3.1 Pro": 1.0,
        "Grok 4.3": 0.6,
        "Llama 4 Maverick": 0.8,
        "DeepSeek-V4-Pro": 0.8,
        "Qwen3.7-Max": 0.6,
        "GLM-5.2": 0.5,
    }
    
    # 从 token_data 中收集海外三方输入价
    model_prices: dict[str, float] = {}
    for row in token_data:
        model = row.get("模型", "")
        status = row.get("校验状态", "")
        if status != "PASS":
            continue
        price_raw = row.get("海外三方输入价")
        price = _parse_token_price(price_raw)
        if price is not None and price > 0:
            model_prices[model] = price
    
    # 计算加权平均
    total_weight = 0.0
    weighted_sum = 0.0
    used_models = []
    for model, weight in WEIGHTS.items():
        if model in model_prices:
            weighted_sum += model_prices[model] * weight
            total_weight += weight
            used_models.append(model)
    
    current = round(weighted_sum / total_weight, 4) if total_weight > 0 else None
    
    # 计算历史趋势（从快照中提取）
    available_dates = _find_available_snapshots(60)
    history: list[tuple[str, float]] = []
    
    if current is not None:
        history.append((DATE, current))
    
    seen = {DATE}
    for d in available_dates:
        if d in seen:
            continue
        snap = _load_snapshot(d)
        if not snap:
            continue
        tokens = snap.get("token_prices", [])
        if not tokens:
            continue
        snap_prices = {}
        for row in tokens:
            model = row.get("模型", "")
            status = row.get("校验状态", "")
            if status != "PASS":
                continue
            price_raw = row.get("海外三方输入价")
            price = _parse_token_price(price_raw)
            if price is not None and price > 0:
                snap_prices[model] = price
        
        wsum = 0.0
        tw = 0.0
        for model, weight in WEIGHTS.items():
            if model in snap_prices:
                wsum += snap_prices[model] * weight
                tw += weight
        if tw > 0:
            history.append((d, round(wsum / tw, 4)))
            seen.add(d)
    
    history.sort(key=lambda x: x[0])
    
    def calc_change(n_days: int) -> tuple[float | None, str]:
        if not history or current is None:
            return (None, "N/A")
        target = (NOW - timedelta(days=n_days)).date().isoformat()
        # 找最接近的点
        best = None
        best_diff = 999
        target_dt = datetime.fromisoformat(target).date()
        for d, p in history:
            dt = datetime.fromisoformat(d).date()
            diff = abs((dt - target_dt).days)
            if diff <= 3 and diff < best_diff:
                best_diff = diff
                best = p
        if best is None or best == 0:
            return (None, "N/A")
        change = (current - best) / best
        pct_str = f"{'+' if change >= 0 else ''}{change * 100:.1f}%"
        return (change, pct_str)
    
    change_7d, change_7d_pct = calc_change(7)
    change_30d, change_30d_pct = calc_change(30)
    
    direction = "unknown"
    if change_7d is not None:
        direction = "up" if change_7d > 0.005 else ("down" if change_7d < -0.005 else "flat")
    
    return {
        "ticker": "CMIS-TOKEN-INDEX",
        "current": current,
        "unit": "USD/1M input tokens",
        "change_7d": change_7d,
        "change_30d": change_30d,
        "change_7d_pct": change_7d_pct,
        "change_30d_pct": change_30d_pct,
        "direction": direction,
        "sample_size": len(model_prices),
        "weighted_models": used_models,
        "history_7d": history[-7:] if len(history) >= 3 else history,
        "history_30d": history[-30:] if len(history) >= 7 else history,
    }


def build_all_indices(domestic_rental: list[dict],
                      overseas_rental: list[dict],
                      token_data: list[dict]) -> dict[str, Any]:
    """构建所有指数数据。"""
    gpu_cn_indices: list[dict] = []
    gpu_us_indices: list[dict] = []
    
    # 国内 GPU 指数
    for row in domestic_rental:
        gpu = row["GPU 型号"]
        price = row.get("标准化价格")
        if row.get("校验状态") == "PASS" and price is not None:
            idx = calc_gpu_index(gpu, "CN", current_price=float(price))
            # 估算数据源数量（从 source 字段中统计）
            source = row.get("主数据源", "")
            source_count = source.count("+") + 1 if "+" in source else 1
            idx["source_count"] = source_count
            gpu_cn_indices.append(idx)
    
    # 海外 GPU 指数
    for row in overseas_rental:
        gpu = row["GPU 型号"]
        cny_price = row.get("单卡小时价（人民币）")
        fx_rate = row.get("_fx_rate", 7.2)
        if row.get("校验状态") == "PASS" and cny_price is not None and fx_rate > 0:
            usd_price = round(float(cny_price) / float(fx_rate), 4)
            idx = calc_gpu_index(gpu, "US", current_price=usd_price)
            source = row.get("主数据源", "")
            source_count = source.count("+") + 1 if "+" in source else 1
            idx["source_count"] = source_count
            gpu_us_indices.append(idx)
    
    # Token 指数
    token_idx = calc_token_index(token_data)
    
    # 按当前价格排序（从高到低）
    gpu_cn_indices.sort(key=lambda x: x["current"] or 0, reverse=True)
    gpu_us_indices.sort(key=lambda x: x["current"] or 0, reverse=True)
    
    return {
        "gpu_cn": gpu_cn_indices,
        "gpu_us": gpu_us_indices,
        "token": token_idx,
        "as_of": DATE,
    }
