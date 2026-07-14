#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

now = datetime.now(timezone(timedelta(hours=8)))
date = now.date().isoformat()
stamp = now.strftime("%Y%m%d%H%M")
url = os.environ.get("FEISHU_WEBHOOK")
if not url:
    print("FEISHU_WEBHOOK not set; skip notification.")
    raise SystemExit(0)

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / f"cmis_snapshot_{date}.json"


def fmt(value, suffix=""):
    if value is None or value == "":
        return "暂不可得"
    if isinstance(value, float):
        text = f"{value:.2f}".rstrip("0").rstrip(".")
    else:
        text = str(value)
    return f"{text}{suffix}"


def load_snapshot():
    if not SNAPSHOT.exists():
        return None
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def build_summary(data):
    domestic = data.get("domestic_rental", [])
    overseas = data.get("overseas_rental", [])
    token = data.get("token_prices", [])
    audit = data.get("audit", [])
    rejected = data.get("rejected", [])

    domestic_index = [r for r in domestic if r.get("是否进入主指数") == "是"]
    domestic_pass = [
        r for r in domestic_index
        if r.get("校验状态") == "PASS" and (r.get("Confidence Score") or 0) >= 70
    ]
    strategic_watch = [
        r for r in domestic_index
        if r.get("校验状态") != "PASS"
    ]
    overseas_pass = [r for r in overseas if r.get("校验状态") == "PASS"]
    token_vendors = sorted({r.get("厂商") for r in token if r.get("厂商")})
    token_pass = [r for r in token if r.get("校验状态") == "PASS"]

    strategic_text = "无"
    if strategic_watch:
        names = "、".join(r.get("GPU 型号", "") for r in strategic_watch[:4])
        if len(strategic_watch) > 4:
            names += f"等 {len(strategic_watch)} 个"
        strategic_text = names

    review_total = len([r for r in audit if r.get("validate_status") in {"REVIEW", "REJECT"}]) or len(rejected)

    return {
        "freeze_time": data.get("freeze_time", "未记录"),
        "report_version": data.get("report_version", "unknown"),
        "gpu_line": f"国内指数展示 {len(domestic_index)} 个型号，PASS 主口径 {len(domestic_pass)} 个；海外 GPU Cloud PASS 参考 {len(overseas_pass)} 个型号。",
        "token_line": f"Token 覆盖 {len(token_vendors)} 家厂商、{len(token)} 个模型，PASS {len(token_pass)} 个。",
        "risk_line": f"待复核/审计样本 {review_total} 条；国产战略关注观察样本：{strategic_text}。",
    }


def build_notable_links(data, max_items=5):
    sources = data.get("sources", [])
    keyword_score = {
        "主口径": 100,
        "官方": 90,
        "海外云价": 80,
        "Token": 75,
        "采购": 65,
        "聚合源": 55,
        "Marketplace": 50,
    }
    items = []
    seen = set()
    for source in sources:
        url_value = source.get("url")
        title = source.get("title")
        if not url_value or not title or url_value in seen:
            continue
        seen.add(url_value)
        tier = source.get("tier", "")
        note = source.get("note", "")
        text = f"{tier} {title} {note}"
        score = max((score for key, score in keyword_score.items() if key in text), default=10)
        items.append((score, source.get("id", 9999), tier, title, url_value))

    items.sort(key=lambda x: (-x[0], x[1]))
    selected = items[:max_items]
    if not selected:
        return "暂无可展示链接。"
    lines = []
    for _, _, tier, title, url_value in selected:
        prefix = f"{tier}｜" if tier else ""
        lines.append(f"- {prefix}{title}\n  {url_value}")
    return "\n".join(lines)


data = load_snapshot()
if data:
    summary = build_summary(data)
    notable_links = build_notable_links(data)
    text = f"""📌 全球算力市场情报日报
📅 日期：{date}
🧊 Freeze：{summary["freeze_time"]}
🏷️ 版本：{summary["report_version"]}

📈 GPU / 算力：
{summary["gpu_line"]}

🪙 Token 价格：
{summary["token_line"]}

⚡ 待复核：
{summary["risk_line"]}

📰 今日值得看：
{notable_links}

📊 完整报告：https://gavinzll.github.io/compute-market-report/latest.html?v={stamp}"""
else:
    text = f"""📌 全球算力市场情报日报
📅 日期：{date}

⚠️ 未找到当天结构化快照：data/cmis_snapshot_{date}.json

本次飞书通知无法生成动态市场摘要。请检查日报生成脚本是否已成功运行，并确认 data、latest.html、latest-mobile.html 和 reports 目录已更新。

📊 报告入口：https://gavinzll.github.io/compute-market-report/latest.html?v={stamp}"""

payload = json.dumps({"msg_type": "text", "content": {"text": text}}, ensure_ascii=False).encode("utf-8")
if os.environ.get("FEISHU_DRY_RUN") == "1":
    print(text)
    raise SystemExit(0)

req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=20) as resp:
    print(resp.read().decode("utf-8", errors="ignore"))
