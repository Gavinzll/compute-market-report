#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取模力方舟算力市场 API，生成 data/gitee_ai_{DATE}.json。
API: https://ai.gitee.com/api/base/market/products?page=N
hour_price 为多卡整机小时价，单卡时价 = hour_price ÷ gpu_num（2026-09-28 口径）。
取可租(idle>0)机器最低值，仅保留关注的国产卡型号。
"""
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))
DATE = datetime.now(TZ).date().isoformat()

TARGETS = {
    "昇腾 910B": ["910B"],
    "天数智芯 智铠100": ["智铠100"],
    "燧原 S60": ["燧原 S60", "S60"],
    "摩尔线程 MTT S4000": ["S4000"],
    "摩尔线程 MTT S5000": ["S5000"],
    "壁仞 天垓150": ["天垓150"],
    "壁仞 壁砺106M": ["壁砺106M", "106M"],
    "海光 BW1000": ["BW1000"],
    "壁仞 天垓100": ["天垓100"],
}

def fetch(url, timeout=30, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CMIS-Daily/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"[gitee] attempt {attempt+1} failed: {url} -> {e}", file=sys.stderr)
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None

def main():
    products = []
    for page in range(1, 15):
        data = fetch(f"https://ai.gitee.com/api/base/market/products?page={page}")
        if not data:
            break
        items = data.get("items") or []
        if not items:
            break
        products.extend(items)
        if len(items) < 10:
            break
    print(f"[gitee] fetched {len(products)} products")
    if not products:
        sys.exit(1)

    best = {}   # target -> (single_card_price, note)
    details = []
    for p in products:
        name = str(p.get("gpu_model") or p.get("name") or "")
        try:
            gpu_num = int(p.get("gpu_num") or 0)
            hour_price = float(p.get("hour_price") or 0)
            idle = int(p.get("gpu_idle") if p.get("gpu_idle") is not None else p.get("idle") or 0)
        except Exception:
            continue
        if not name or gpu_num <= 0 or hour_price <= 0 or idle <= 0:
            continue
        single = round(hour_price / gpu_num, 6)
        for target, keys in TARGETS.items():
            if any(k in name for k in keys):
                note = f"{name} {gpu_num}卡整机{hour_price}元/时 idle={idle}"
                details.append(note)
                if target not in best or single < best[target][0]:
                    best[target] = (single, note)

    out = {
        "scraped_at": DATE,
        "source_url": "https://ai.gitee.com/compute",
        "note": f"scraped via /api/base/market/products ({len(products)} items, paginated). hour_price 为多卡整机小时价，单卡时价 = hour_price ÷ gpu_num，取可租(idle>0)机器最低值。"
                + "；".join(f"{t}: {v[0]}元/卡/时 <- {v[1]}" for t, v in best.items()),
        "prices": {t: {"hourly_cny": v[0], "source": "模力方舟"} for t, v in best.items()},
    }
    path = ROOT / "data" / f"gitee_ai_{DATE}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[gitee] targets matched: {len(best)}")
    for t, v in best.items():
        print(f"  {t}: {v[0]} 元/卡/时  <- {v[1]}")
    print(f"[gitee] written {path}")

if __name__ == "__main__":
    main()
