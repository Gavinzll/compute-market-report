#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飞书机器人富文本卡片消息推送（Interactive Card JSON 2.0）"""
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
REPORT_URL = f"https://gavinzll.github.io/compute-market-report/latest.html?v={stamp}"
REPORT_MOBILE_URL = f"https://gavinzll.github.io/compute-market-report/latest-mobile.html?v={stamp}"


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
        "domestic_total": len(domestic_index),
        "domestic_pass": len(domestic_pass),
        "overseas_pass": len(overseas_pass),
        "token_vendors": len(token_vendors),
        "token_models": len(token),
        "token_pass": len(token_pass),
        "review_total": review_total,
        "strategic_watch": strategic_text,
    }


def build_card_success(s):
    """构建成功通知的 Interactive Card JSON 2.0"""
    return {
        "schema": "2.0",
        "config": {
            "wide_screen_mode": True,
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": "全球算力市场情报日报",
            },
            "template": "blue",
        },
        "body": {
            "direction": "vertical",
            "elements": [
                # 日期 + 版本行
                {
                    "tag": "markdown",
                    "content": f"**日期：** {date}    **版本：** {s['report_version']}    **Freeze：** {s['freeze_time']}",
                },
                # 分割线
                {"tag": "hr"},
                # GPU / 算力
                {
                    "tag": "column_set",
                    "flex_mode": "none",
                    "background_style": "default",
                    "columns": [
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "vertical_align": "center",
                            "elements": [
                                {
                                    "tag": "markdown",
                                    "content": f"**国内指数**\n{s['domestic_pass']} / {s['domestic_total']} 型号 PASS",
                                },
                            ],
                        },
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "vertical_align": "center",
                            "elements": [
                                {
                                    "tag": "markdown",
                                    "content": f"**海外 GPU Cloud**\n{s['overseas_pass']} 个型号 PASS",
                                },
                            ],
                        },
                    ],
                },
                # Token 价格
                {
                    "tag": "column_set",
                    "flex_mode": "none",
                    "background_style": "default",
                    "columns": [
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "vertical_align": "center",
                            "elements": [
                                {
                                    "tag": "markdown",
                                    "content": f"**Token 价格**\n{s['token_vendors']} 家厂商 / {s['token_models']} 个模型\nPASS {s['token_pass']} 个",
                                },
                            ],
                        },
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "vertical_align": "center",
                            "elements": [
                                {
                                    "tag": "markdown",
                                    "content": f"**待复核样本**\n{s['review_total']} 条",
                                },
                            ],
                        },
                    ],
                },
                # 分割线
                {"tag": "hr"},
                # 国产战略关注
                {
                    "tag": "markdown",
                    "content": f"**国产战略关注观察：** {s['strategic_watch']}",
                },
                # 分割线
                {"tag": "hr"},
                # 按钮行
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "查看完整报告（桌面版）"},
                            "type": "default",
                            "url": REPORT_URL,
                        },
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "手机版"},
                            "type": "default",
                            "url": REPORT_MOBILE_URL,
                        },
                    ],
                },
            ],
        },
    }


def build_card_failure():
    """构建失败通知的 Interactive Card JSON 2.0"""
    return {
        "schema": "2.0",
        "config": {
            "wide_screen_mode": True,
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": "全球算力市场情报日报 - 生成异常",
            },
            "template": "red",
        },
        "body": {
            "direction": "vertical",
            "elements": [
                {
                    "tag": "markdown",
                    "content": f"**日期：** {date}",
                },
                {"tag": "hr"},
                {
                    "tag": "markdown",
                    "content": (
                        "未找到当天结构化快照 `cmis_snapshot_<date>.json`，"
                        "本次飞书通知无法生成动态市场摘要。\n\n"
                        "请检查日报生成脚本是否已成功运行，"
                        "并确认 `data`、`latest.html`、`latest-mobile.html` 和 `reports` 目录已更新。"
                    ),
                },
                {"tag": "hr"},
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "前往报告入口"},
                            "type": "default",
                            "url": REPORT_URL,
                        },
                    ],
                },
            ],
        },
    }


# 构建卡片
data = load_snapshot()
if data:
    summary = build_summary(data)
    card = build_card_success(summary)
else:
    card = build_card_failure()

payload = json.dumps({"msg_type": "interactive", "card": card}, ensure_ascii=False).encode("utf-8")

if os.environ.get("FEISHU_DRY_RUN") == "1":
    print(json.dumps(card, ensure_ascii=False, indent=2))
    raise SystemExit(0)

req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=20) as resp:
    print(resp.read().decode("utf-8", errors="ignore"))
