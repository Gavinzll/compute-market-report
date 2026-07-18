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


def _fmt_price(v):
    """格式化价格数值，None 返回空串。"""
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def _gpu_rental_line(domestic_index):
    """从快照 domestic_rental 中提取关键 GPU 价格，生成 GPU 租赁摘要。

    只使用「是否进入主指数 == 是」且「校验状态 == PASS」且「标准化价格」为数值的样本，
    避免引用 REVIEW / Rejected / 价格待补 的样本。
    优先展示 H100 80G、A100 80G、RTX 5090、昇腾 910C、昇腾 910B；若都不存在则回退到前 3 个 PASS 样本。
    """
    key_order = ["H100 80G", "A100 80G", "RTX 5090", "昇腾 910C", "昇腾 910B"]
    pass_rows = {
        r.get("GPU 型号"): r for r in domestic_index
        if r.get("校验状态") == "PASS"
        and isinstance(r.get("标准化价格"), (int, float))
    }
    parts = []
    for gpu in key_order:
        row = pass_rows.get(gpu)
        if not row:
            continue
        price = row["标准化价格"]
        unit = row.get("标准化单位", "万元/8卡整机/月")
        parts.append(f"{gpu} {_fmt_price(price)}万/月")
    if not parts:
        # 回退：取前 3 个 PASS 样本
        for row in list(pass_rows.values())[:3]:
            gpu = row.get("GPU 型号", "")
            price = row.get("标准化价格")
            if gpu and isinstance(price, (int, float)):
                parts.append(f"{gpu} {_fmt_price(price)}万/月")
    if not parts:
        return "国内主指数暂无 PASS 样本，数据存在分歧，等待进一步确认"
    return "国内 " + "，".join(parts) + "（8卡整机/月）"


def _gpu_purchase_line(procurement):
    """从 gpu_procurement 中提取有采购价中位数的样本，生成 GPU 采购摘要。"""
    valid = [
        r for r in procurement
        if isinstance(r.get("采购价中位数（万元）"), (int, float))
    ]
    if not valid:
        return "主流卡采购价多为待补或估算口径，暂无新增公开成交价"
    parts = []
    for r in valid[:4]:
        gpu = r.get("GPU 型号", "")
        med = r.get("采购价中位数（万元）")
        band = r.get("采购价区间（万元/8卡整机）", "")
        if gpu and isinstance(med, (int, float)):
            parts.append(f"{gpu} 中位{_fmt_price(med)}万")
    if not parts:
        return "主流卡采购价多为待补或估算口径，暂无新增公开成交价"
    return "；".join(parts) + "（8卡整机采购）"


def _token_line(token_rows):
    """从 token_prices 中提取代表性模型官方价，生成 Token 价格摘要。

    优先展示 GPT-5.5、DeepSeek-V4-Pro、Qwen3.7-Max；若不存在则回退到前 3 个 PASS 样本。
    价格一律取自「输入官方价（人民币/百万Token）」「输出官方价（人民币/百万Token）」。
    """
    key_models = ["GPT-5.5", "DeepSeek-V4-Pro", "Qwen3.7-Max"]
    pass_rows = {
        r.get("模型"): r for r in token_rows
        if r.get("校验状态") == "PASS"
        and isinstance(r.get("输入官方价（人民币/百万Token）"), (int, float))
    }
    parts = []
    for model in key_models:
        row = pass_rows.get(model)
        if not row:
            continue
        inp = row["输入官方价（人民币/百万Token）"]
        outp = row["输出官方价（人民币/百万Token）"]
        parts.append(f"{model} ¥{_fmt_price(inp)}/¥{_fmt_price(outp)}")
    if not parts:
        for row in list(pass_rows.values())[:3]:
            model = row.get("模型", "")
            inp = row.get("输入官方价（人民币/百万Token）")
            outp = row.get("输出官方价（人民币/百万Token）")
            if model and isinstance(inp, (int, float)) and isinstance(outp, (int, float)):
                parts.append(f"{model} ¥{_fmt_price(inp)}/¥{_fmt_price(outp)}")
    if not parts:
        return "Token 官方价暂无 PASS 样本"
    return "；".join(parts) + "（输入/输出，元/百万Token）"


def _key_change_line(data):
    """生成关键异动摘要：覆盖范围 + REVIEW 样本数 + 新增来源。"""
    sources = data.get("sources", [])
    audit = data.get("audit", [])
    rejected = data.get("rejected", [])
    review_total = len([r for r in audit if r.get("validate_status") in {"REVIEW", "REJECT"}]) or len(rejected)
    src_count = len(sources)
    return f"当日采集 {src_count} 个数据源，{review_total} 条样本进入 REVIEW/REJECT（详见审计文件）"


def _ai_one_liner(data):
    """基于 PASS 且 Consensus 非 Low 的数据生成一句话总结。

    只统计 domestic_rental 中「校验状态 == PASS」且「Source Consensus != Low」的样本，
    不做方向性价格判断（涨/跌），只描述覆盖与共识状态。
    """
    domestic = data.get("domestic_rental", [])
    overseas = data.get("overseas_rental", [])
    token = data.get("token_prices", [])
    dom_pass = [r for r in domestic if r.get("校验状态") == "PASS" and r.get("Source Consensus") != "Low"]
    os_pass = [r for r in overseas if r.get("校验状态") == "PASS"]
    tok_pass = [r for r in token if r.get("校验状态") == "PASS"]
    low_consensus = [r for r in domestic if r.get("Source Consensus") == "Low"]
    if low_consensus:
        return "部分型号数据存在分歧，等待进一步确认；仅展示高置信样本进入主指数"
    return f"国内 {len(dom_pass)} 款、海外 {len(os_pass)} 款 GPU PASS；Token {len(tok_pass)} 个模型 PASS，价格共识整体稳定"


def build_summary(data):
    domestic = data.get("domestic_rental", [])
    overseas = data.get("overseas_rental", [])
    token = data.get("token_prices", [])
    audit = data.get("audit", [])
    rejected = data.get("rejected", [])
    procurement = data.get("gpu_procurement", [])

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

    # 从快照中自动提取关键价格，避免执行端引用过期硬编码值
    gpu_rental_text = _gpu_rental_line(domestic_index)
    gpu_purchase_text = _gpu_purchase_line(procurement)
    token_text = _token_line(token)
    key_change_text = _key_change_line(data)
    ai_liner = _ai_one_liner(data)

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
        # 新增：按 report_config.md 模板自动生成的摘要文字
        "gpu_rental_text": gpu_rental_text,
        "gpu_purchase_text": gpu_purchase_text,
        "token_text": token_text,
        "key_change_text": key_change_text,
        "ai_liner": ai_liner,
    }


def build_card_success(s):
    """构建成功通知的 Interactive Card JSON 2.0

    按 report_config.md 第 9 节飞书通知固定模板渲染：
    日期 / GPU 租赁 / GPU 采购 / Token 价格 / 关键异动 / AI 一句话 / 完整报告链接。
    所有价格摘要均由 build_summary 从 cmis_snapshot_<date>.json 自动提取，
    禁止执行端自行编写含具体数字的摘要，避免引用过期硬编码值。
    """
    return {
        "schema": "2.0",
        "config": {
            "wide_screen_mode": True,
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": "📌 全球算力市场情报日报",
            },
            "template": "blue",
        },
        "body": {
            "direction": "vertical",
            "elements": [
                # 日期 + 版本 + Freeze
                {
                    "tag": "markdown",
                    "content": f"📅 **日期：** {date}    **版本：** {s['report_version']}    **Freeze：** {s['freeze_time']}",
                },
                {"tag": "hr"},
                # GPU 租赁（从快照 domestic_rental PASS 样本提取）
                {
                    "tag": "markdown",
                    "content": f"📈 **GPU 租赁：**\n{s['gpu_rental_text']}",
                },
                {"tag": "hr"},
                # GPU 采购（从快照 gpu_procurement 提取）
                {
                    "tag": "markdown",
                    "content": f"💰 **GPU 采购：**\n{s['gpu_purchase_text']}",
                },
                {"tag": "hr"},
                # Token 价格（从快照 token_prices PASS 样本提取）
                {
                    "tag": "markdown",
                    "content": f"🪙 **Token 价格：**\n{s['token_text']}",
                },
                {"tag": "hr"},
                # 关键异动
                {
                    "tag": "markdown",
                    "content": f"⚡ **关键异动：**\n{s['key_change_text']}",
                },
                {"tag": "hr"},
                # AI 一句话（基于 PASS 且 Consensus 非 Low 的数据）
                {
                    "tag": "markdown",
                    "content": f"🧠 **AI 一句话：**\n{s['ai_liner']}",
                },
                {"tag": "hr"},
                # 覆盖率统计（补充信息）
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
                                    "content": f"**Token 价格**\n{s['token_vendors']} 厂商 / {s['token_models']} 模型\nPASS {s['token_pass']} 个",
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
                {"tag": "hr"},
                # 国产战略关注
                {
                    "tag": "markdown",
                    "content": f"**国产战略关注观察：** {s['strategic_watch']}",
                },
                {"tag": "hr"},
                # 按钮行
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "📊 查看完整报告（桌面版）"},
                            "type": "primary",
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
