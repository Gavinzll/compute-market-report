#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CMIS Daily 价格变动追踪模块。

借鉴 tokencanopy/price (LLM Price Index) 的做法：
- Append-only change log：只在价格实际变动时才写入一行
- 价格历史不可回补，只有持续记录才存在
- 通过对比前一天的快照自动检测变动

数据文件：
- data/price_changes.csv  — append-only 变动日志
- data/raw/               — 原始 API 响应缓存（借鉴 LLM Price Index raw/ 目录）

用法：
    from change_log import record_price_changes, get_recent_changes
    record_price_changes(today_snapshot)  # 在日报生成后调用
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))
NOW = datetime.now(TZ)
DATE = NOW.date().isoformat()

CHANGE_LOG_PATH = ROOT / "data" / "price_changes.csv"
RAW_DIR = ROOT / "data" / "raw"

# CSV 表头
CSV_HEADERS = [
    "observed_at",       # 检测到变动的时间
    "category",          # token / gpu_domestic / gpu_overseas / fx_rate
    "model",             # 模型名或 GPU 型号
    "vendor",            # 厂商（token 专用）
    "metric",            # input / output / rental_price / purchase_price / usd_cny
    "platform",          # official / overseas_3rd / domestic_3rd / provider_name
    "old_value",         # 旧值
    "new_value",         # 新值
    "change_pct",        # 变化百分比
    "source_url",        # 数据来源 URL
]


def _ensure_csv_header():
    """确保 CSV 文件存在且有表头。"""
    if not CHANGE_LOG_PATH.exists():
        CHANGE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CHANGE_LOG_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()


def _load_previous_snapshot() -> dict[str, Any] | None:
    """加载前一天的快照数据，用于对比价格变动。"""
    # 尝试找最近 7 天内的快照
    for days_back in range(1, 8):
        d = (NOW - timedelta(days=days_back)).date().isoformat()
        path = ROOT / "data" / f"cmis_snapshot_{d}.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
    return None


def _extract_prices_from_snapshot(snap: dict) -> list[dict[str, Any]]:
    """从快照中提取所有价格点，标准化为统一的比较格式。

    返回 list of {category, model, vendor, metric, platform, value, source_url}
    """
    prices: list[dict[str, Any]] = []

    # Token 价格
    for r in snap.get("token_prices", []):
        model = r.get("模型", "")
        vendor = r.get("厂商", "")
        # 官方价
        for metric, field in [("input", "官方输入价"), ("output", "官方输出价")]:
            v = r.get(field)
            if v is not None:
                prices.append({
                    "category": "token",
                    "model": model, "vendor": vendor,
                    "metric": metric, "platform": "official",
                    "value": str(v), "source_url": "",
                })
        # 海外三方
        for metric, field in [("input", "海外三方输入价"), ("output", "海外三方输出价")]:
            v = r.get(field)
            if v is not None:
                prices.append({
                    "category": "token", "model": model, "vendor": vendor,
                    "metric": metric, "platform": "overseas_3rd",
                    "value": str(v), "source_url": r.get("海外三方来源", ""),
                })
        # 境内三方
        for metric, field in [("input", "境内三方输入价"), ("output", "境内三方输出价")]:
            v = r.get(field)
            if v is not None:
                prices.append({
                    "category": "token", "model": model, "vendor": vendor,
                    "metric": metric, "platform": "domestic_3rd",
                    "value": str(v), "source_url": r.get("境内三方来源", ""),
                })

    # GPU 国内租赁
    for r in snap.get("domestic_rental", []):
        gpu = r.get("GPU 型号", "")
        v = r.get("标准化价格")
        if v is not None:
            prices.append({
                "category": "gpu_domestic", "model": gpu, "vendor": "",
                "metric": "rental_price", "platform": r.get("来源", ""),
                "value": str(v), "source_url": r.get("来源链接", ""),
            })

    # GPU 采购
    for r in snap.get("gpu_procurement", []):
        gpu = r.get("GPU 型号", "")
        v = r.get("采购价中位数（万元）")
        if v is not None:
            prices.append({
                "category": "gpu_purchase", "model": gpu, "vendor": "",
                "metric": "purchase_price", "platform": "market",
                "value": str(v), "source_url": "",
            })

    # GPU 海外租赁
    for r in snap.get("overseas_rental", []):
        gpu = r.get("GPU 型号", "")
        v = r.get("标准化价格")
        if v is not None:
            prices.append({
                "category": "gpu_overseas", "model": gpu, "vendor": "",
                "metric": "rental_price", "platform": r.get("来源", ""),
                "value": str(v), "source_url": r.get("来源链接", ""),
            })

    # 汇率
    fx = snap.get("fx_rate")
    if fx is not None:
        prices.append({
            "category": "fx_rate", "model": "USD/CNY", "vendor": "",
            "metric": "usd_cny", "platform": snap.get("fx_rate_source", ""),
            "value": str(fx), "source_url": "",
        })

    return prices


def _price_key(p: dict) -> str:
    """生成价格点的唯一键。"""
    return f"{p['category']}|{p['model']}|{p['metric']}|{p['platform']}"


def _safe_pct(old: str, new: str) -> str:
    """计算变化百分比，处理非数值情况。"""
    try:
        old_f = float(old)
        new_f = float(new)
        if old_f == 0:
            return "N/A" if new_f == 0 else "+∞"
        pct = (new_f - old_f) / old_f * 100
        if abs(pct) < 0.01:
            return "0%"
        return f"{pct:+.1f}%"
    except (ValueError, TypeError):
        return "N/A"


def record_price_changes(current_snap: dict) -> int:
    """对比前一天快照，记录价格变动到 CSV。

    只在价格实际变化时才写入一行（append-only）。
    返回记录的变动数量。
    """
    prev_snap = _load_previous_snapshot()
    if not prev_snap:
        return 0

    prev_prices = {_price_key(p): p for p in _extract_prices_from_snapshot(prev_snap)}
    curr_prices = {_price_key(p): p for p in _extract_prices_from_snapshot(current_snap)}

    changes: list[dict[str, Any]] = []
    observed_at = NOW.isoformat()

    # 检测变化和新增
    for key, curr in curr_prices.items():
        prev = prev_prices.get(key)
        if not prev:
            # 新增价格点
            changes.append({
                "observed_at": observed_at,
                "category": curr["category"],
                "model": curr["model"],
                "vendor": curr["vendor"],
                "metric": curr["metric"],
                "platform": curr["platform"],
                "old_value": "",
                "new_value": curr["value"],
                "change_pct": "NEW",
                "source_url": curr.get("source_url", ""),
            })
        elif prev["value"] != curr["value"]:
            # 价格变动
            changes.append({
                "observed_at": observed_at,
                "category": curr["category"],
                "model": curr["model"],
                "vendor": curr["vendor"],
                "metric": curr["metric"],
                "platform": curr["platform"],
                "old_value": prev["value"],
                "new_value": curr["value"],
                "change_pct": _safe_pct(prev["value"], curr["value"]),
                "source_url": curr.get("source_url", ""),
            })

    # 检测消失的价格点（不再出现在当日快照中）
    for key, prev in prev_prices.items():
        if key not in curr_prices:
            changes.append({
                "observed_at": observed_at,
                "category": prev["category"],
                "model": prev["model"],
                "vendor": prev["vendor"],
                "metric": prev["metric"],
                "platform": prev["platform"],
                "old_value": prev["value"],
                "new_value": "",
                "change_pct": "REMOVED",
                "source_url": prev.get("source_url", ""),
            })

    if changes:
        _ensure_csv_header()
        with open(CHANGE_LOG_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            for c in changes:
                writer.writerow(c)

    return len(changes)


def get_recent_changes(days: int = 7) -> list[dict[str, Any]]:
    """读取最近 N 天的价格变动记录。"""
    if not CHANGE_LOG_PATH.exists():
        return []

    cutoff = (NOW - timedelta(days=days)).isoformat()
    results: list[dict[str, Any]] = []

    with open(CHANGE_LOG_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("observed_at", "") >= cutoff:
                results.append(row)

    return results


def cache_raw_response(source: str, data: Any) -> None:
    """缓存原始 API 响应，便于后续重新解析。

    借鉴 LLM Price Index 的 data/raw/ 目录做法：
    存储 verbatim provider payloads，任何解析错误都可以用原始数据重新处理。
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{source}_{DATE}.json"
    path = RAW_DIR / filename
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_raw_response(source: str, target_date: str | None = None) -> Any:
    """读取缓存的原始 API 响应。"""
    d = target_date or DATE
    path = RAW_DIR / f"{source}_{d}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def get_change_summary() -> dict[str, Any]:
    """生成价格变动摘要，用于报告展示。"""
    changes = get_recent_changes(1)  # 当天变动

    # 按类别分组
    by_category: dict[str, int] = {}
    notable: list[dict] = []  # 显著变动（>5%）

    for c in changes:
        cat = c.get("category", "unknown")
        by_category[cat] = by_category.get(cat, 0) + 1

        pct_str = c.get("change_pct", "")
        if pct_str not in ("NEW", "REMOVED", "N/A", "0%"):
            try:
                pct = float(pct_str.replace("+", "").replace("%", ""))
                if abs(pct) >= 5:
                    notable.append({
                        "model": c.get("model", ""),
                        "metric": c.get("metric", ""),
                        "platform": c.get("platform", ""),
                        "change_pct": pct_str,
                        "old": c.get("old_value", ""),
                        "new": c.get("new_value", ""),
                    })
            except ValueError:
                pass

    return {
        "total_changes": len(changes),
        "by_category": by_category,
        "notable_changes": notable[:10],  # 最多展示 10 个
        "log_file": str(CHANGE_LOG_PATH.name),
    }
