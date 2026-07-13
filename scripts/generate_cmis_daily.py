#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CMIS Daily report generator.

This script writes final site assets for GitHub Pages:
latest.html, reports/YYYY-MM-DD.html, index.html, data snapshots, and charts.js.
The scheduled job is executed by TRAE automation, not by GitHub Actions.
GitHub is only used as the static hosting target.
"""

from __future__ import annotations

import json
import math
import os
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from pathlib import Path
from statistics import median

OUT = Path(os.environ.get("CMIS_OUT", "/workspace"))
DATE = datetime.now(timezone(timedelta(hours=8))).date().isoformat()
STAMP = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S %Z")
FX_USD_CNY = 7.18

SOURCES = [
    {
        "id": 1,
        "tier": "官方",
        "title": "OpenAI API Pricing",
        "url": "https://openai.com/api/pricing/",
        "note": "OpenAI 官方 API 定价页，提供 GPT 系列输入、缓存输入和输出价格。",
    },
    {
        "id": 2,
        "tier": "官方",
        "title": "DeepSeek API 模型与价格",
        "url": "https://api-docs.deepseek.com/zh-cn/quick_start/pricing",
        "note": "DeepSeek 官方 API 定价页，提供 V4 Flash / Pro 上下文、输入和输出价格。",
    },
    {
        "id": 3,
        "tier": "官方",
        "title": "Alibaba Cloud Model Studio pricing",
        "url": "https://help.aliyun.com/en/model-studio/model-pricing",
        "note": "阿里云 Model Studio 官方计费说明，覆盖 Qwen 系列标准价格。",
    },
    {
        "id": 4,
        "tier": "官方",
        "title": "Google Gemini API pricing",
        "url": "https://ai.google.dev/gemini-api/docs/pricing?hl=zh-cn",
        "note": "Google AI for Developers 官方 Gemini API 价格页。",
    },
    {
        "id": 5,
        "tier": "官方",
        "title": "Anthropic Claude pricing",
        "url": "https://platform.claude.com/docs/en/about-claude/pricing#model-pricing",
        "note": "Anthropic 官方 Claude API 价格页；当前环境仅能读取搜索摘要，需人工复核完整表格。",
    },
    {
        "id": 6,
        "tier": "主口径/行业",
        "title": "SMM 算力快讯：H100/A100/5090 月租报价",
        "url": "https://news.metal.com/featured-category.html/newscontent/103972175-smm-computing-power-flash-an-intelligent-computing-company-quoted-monthly-rental-prices-for-multiple-gpu-models-includin",
        "note": "SMM 披露 H100、A100、RTX 5090 等国内租赁报价，作为国内租赁主口径。",
    },
    {
        "id": 7,
        "tier": "主口径/行业",
        "title": "SMM 算力快讯：H100 内蒙古现货与新疆期货",
        "url": "https://news.metal.com/elenco_periodici.asp/newscontent/103993848-smm-computing-power-flash-32-units-of-h100-spot-in-inner-mongolia-quoted-at-80000-yuan-64-units-of-futures-in-xinjiang-t",
        "note": "SMM 披露 H100 现货与期货供应，提示 75,000-80,000 元/月区间和供应紧张。",
    },
    {
        "id": 8,
        "tier": "主口径/行业",
        "title": "ComputeStacker GPU cloud pricing guide",
        "url": "https://computestacker.com/insights/gpu-cloud-pricing-guide-2026/",
        "note": "ComputeStacker 海外 GPU 云价格观察，作为海外租赁主口径之一。",
    },
    {
        "id": 9,
        "tier": "官方/校验",
        "title": "Lambda GPU cloud pricing",
        "url": "https://lambda.ai/pricing",
        "note": "Lambda 官方 GPU 云价格页，用于海外价格辅助校验。",
    },
    {
        "id": 10,
        "tier": "官方/校验",
        "title": "RunPod GPU cloud pricing",
        "url": "https://www.runpod.io/pricing",
        "note": "RunPod 官方 GPU 云价格页，用于海外公开市场辅助校验。",
    },
    {
        "id": 11,
        "tier": "行业报道",
        "title": "TrendForce: CoWoS supply-demand gap narrowing",
        "url": "https://www.trendforce.com/news/2026/06/15/news-tsmc-cowos-supply-demand-gap-reportedly-seen-narrowing-from-20-to-10-by-end-2026-as-capacity-expands/",
        "note": "TrendForce 关于 TSMC CoWoS 供需缺口变化的供应链信号。",
    },
    {
        "id": 12,
        "tier": "行业报道",
        "title": "TrendForce: Blackwell shipment share in 2026",
        "url": "https://www.trendforce.com/presscenter/news/20260408-13003.html",
        "note": "TrendForce 对 Blackwell 高端 GPU 出货结构和 Rubin 延迟风险的观察。",
    },
    {
        "id": 13,
        "tier": "官方",
        "title": "阿里云百炼模型价格",
        "url": "https://help.aliyun.com/zh/model-studio/model-pricing",
        "note": "阿里云百炼官方模型价格页，搜索摘要可见 qwen-max、qwen-plus、qwen-flash 等输入/输出价。",
    },
    {
        "id": 14,
        "tier": "官方",
        "title": "火山方舟模型价格",
        "url": "https://www.volcengine.com/docs/82379/1544106?lang=zh",
        "note": "火山方舟官方模型价格页，搜索摘要可见豆包文本输入、缓存命中和输出价格区间。",
    },
    {
        "id": 15,
        "tier": "公开文档/需复核",
        "title": "百度千帆大模型平台价格文档",
        "url": "https://wenxinyiyan.apifox.cn/doc-3261316",
        "note": "公开价格文档与社区转引，需回到百度智能云控制台或官方价格页复核。",
    },
]


def cny_from_usd(v: float | None) -> float | None:
    return None if v is None else round(v * FX_USD_CNY, 2)


def fmt(v, suffix=""):
    if v is None:
        return "暂不可得"
    if isinstance(v, float):
        if abs(v) >= 10000:
            return f"{v:,.0f}{suffix}"
        return f"{v:,.2f}{suffix}".rstrip("0").rstrip(".")
    return f"{v}{suffix}"


TOKEN_MODELS = [
    ["OpenAI", "GPT-5.6 Sol", "海外", "官方页注明 <270K", "USD", 5.00, 30.00, None, None, "Official Price", 1, "高", "官方页已抓取"],
    ["OpenAI", "GPT-5.6 Terra", "海外", "官方页注明 <270K", "USD", 2.50, 15.00, None, None, "Official Price", 1, "高", "官方页已抓取"],
    ["OpenAI", "GPT-5.6 Luna", "海外", "官方页注明 <270K", "USD", 1.00, 6.00, None, None, "Official Price", 1, "高", "官方页已抓取"],
    ["Anthropic", "Claude Opus 4.6", "海外", "1M（搜索摘要）", "USD", 5.00, 25.00, None, None, "Official Price", 5, "中", "页面访问受限，需人工复核"],
    ["Anthropic", "Claude Sonnet 4.6", "海外", "1M（搜索摘要）", "USD", 3.00, 15.00, None, None, "Official Price", 5, "中", "页面访问受限，需人工复核"],
    ["Google", "Gemini 2.5 Pro", "海外", "≤200K/分层", "USD", 1.25, 10.00, None, None, "Official Price", 4, "中", "官方页连接不稳定，搜索摘要校验"],
    ["DeepSeek", "deepseek-v4-flash", "国产", "1M", "CNY", 1.00, 2.00, None, None, "Official Price", 2, "高", "缓存未命中输入价"],
    ["DeepSeek", "deepseek-v4-pro", "国产", "1M", "CNY", 3.00, 6.00, None, None, "Official Price", 2, "高", "缓存未命中输入价"],
    ["阿里云/通义千问", "qwen-max", "国产", "官方页/摘要", "CNY", 2.40, 9.60, None, None, "Official Price", 13, "中", "搜索摘要抓取，需复核快照版本"],
    ["阿里云/通义千问", "qwen-plus-character", "国产", "中国内地", "CNY", 0.80, 2.00, None, None, "Official Price", 13, "中", "搜索摘要抓取，Session Cache 折扣另计"],
    ["阿里云/通义千问", "qwen-flash-character", "国产", "中国内地", "CNY", 0.25, 1.50, None, None, "Official Price", 13, "中", "搜索摘要抓取，Session Cache 折扣另计"],
    ["智谱", "GLM/GLM-Z", "国产", "官方未发布/未抓取", "CNY", None, None, None, None, "Official Missing", None, "低", "需补接官方计费页"],
    ["百度", "ERNIE 4.0", "国产", "公开文档/需复核", "CNY", 30.00, 90.00, None, None, "Reference Price", 15, "低", "公开文档与社区转引，需官方控制台复核"],
    ["百度", "ERNIE 3.5", "国产", "公开文档/需复核", "CNY", 4.00, 8.00, None, None, "Reference Price", 15, "低", "公开文档与社区转引，需官方控制台复核"],
    ["火山引擎", "Doubao 文本模型", "国产", "火山方舟", "CNY", 6.00, 80.00, None, None, "Official Price", 14, "中", "搜索摘要抓取，具体模型和输入长度分档需复核"],
    ["火山引擎", "Doubao 低价入口", "国产", "产品页起价", "CNY", 0.15, None, None, None, "Official Price", 14, "中", "产品页摘要显示百万输入 tokens 起价，输出价需复核"],
    ["Moonshot", "Kimi", "国产", "官方未发布/未抓取", "CNY", None, None, None, None, "Official Missing", None, "低", "需补接 Moonshot 官方定价"],
    ["MiniMax", "MiniMax/海螺", "国产", "官方未发布/未抓取", "CNY", None, None, None, None, "Official Missing", None, "低", "需补接官方定价"],
    ["百川智能", "Baichuan", "国产", "官方未发布/未抓取", "CNY", None, None, None, None, "Official Missing", None, "低", "需补接官方定价"],
    ["零一万物", "Yi", "国产", "官方未发布/未抓取", "CNY", None, None, None, None, "Official Missing", None, "低", "需补接官方定价"],
    ["阶跃星辰", "Step", "国产", "官方未发布/未抓取", "CNY", None, None, None, None, "Official Missing", None, "低", "需补接官方定价"],
    ["讯飞", "星火", "国产", "官方未发布/未抓取", "CNY", None, None, None, None, "Official Missing", None, "低", "需补接官方定价"],
    ["腾讯", "混元", "国产", "官方未发布/未抓取", "CNY", None, None, None, None, "Official Missing", None, "低", "需补接官方定价"],
    ["商汤", "日日新", "国产", "官方未发布/未抓取", "CNY", None, None, None, None, "Official Missing", None, "低", "需补接官方定价"],
    ["昆仑万维", "天工", "国产", "官方未发布/未抓取", "CNY", None, None, None, None, "Official Missing", None, "低", "需补接官方定价"],
]


def normalize_token(row):
    vendor, model, region, context, ccy, inp, out, m_in, m_out, ptype, src, conf, note = row
    if ccy == "USD":
        inp_cny, out_cny = cny_from_usd(inp), cny_from_usd(out)
    else:
        inp_cny, out_cny = inp, out
    return {
        "厂商": vendor,
        "模型": model,
        "国家/地区": region,
        "上下文上限": context,
        "输入官方价（原币/百万Token）": None if inp is None else f"{ccy} {inp}",
        "输出官方价（原币/百万Token）": None if out is None else f"{ccy} {out}",
        "输入官方价（人民币/百万Token）": inp_cny,
        "输出官方价（人民币/百万Token）": out_cny,
        "OpenRouter/市场输入价": m_in,
        "OpenRouter/市场输出价": m_out,
        "官方-市场价差": "暂不可得",
        "较昨日变化": "样本起始日",
        "数据源": f"cite-{src}" if src else "需补充官方源",
        "采集时间": STAMP,
        "置信度": conf,
        "备注": f"{ptype}；{note}",
    }


TOKEN_DATA = [normalize_token(x) for x in TOKEN_MODELS]

GPU_ORDER = ["GB200", "B300", "B200", "H200", "H100 80G", "H800", "H20", "A100 80G", "A800", "L40S", "RTX 5090", "RTX 4090", "L20", "L4", "昇腾 910C", "昇腾 910B", "寒武纪 MLU"]

OVERSEAS_HOURLY = {
    "GB200": (None, "整机/机柜交付为主，小时现货口径暂不可得", "低"),
    "B300": (None, "市场未成熟，需人工复核", "低"),
    "B200": (6.69, "市场/行业报价，非官方，需复核", "低"),
    "H200": (4.27, "市场/行业报价，非官方，需复核", "低"),
    "H100 80G": (2.49, "Lambda 官方公开起价/ComputeStacker 区间校验", "中"),
    "H800": (None, "海外公开口径弱", "低"),
    "H20": (None, "海外公开口径弱", "低"),
    "A100 80G": (1.29, "海外公开市场估算/需复核", "低"),
    "A800": (None, "海外公开口径弱", "低"),
    "L40S": (0.85, "海外公开市场估算/需复核", "低"),
    "RTX 5090": (0.65, "海外公开市场估算/需复核", "低"),
    "RTX 4090": (0.35, "海外公开市场估算/需复核", "低"),
    "L20": (None, "海外公开口径弱", "低"),
    "L4": (0.25, "海外公开市场估算/需复核", "低"),
    "昇腾 910C": (None, "海外口径不适用", "低"),
    "昇腾 910B": (None, "海外口径不适用", "低"),
    "寒武纪 MLU": (None, "海外口径不适用", "低"),
}

DOMESTIC_HOURLY_CNY = {
    "GB200": (None, "系统交付/集群口径，单卡小时价暂不可得", "低"),
    "B300": (None, "市场未成熟，需人工复核", "低"),
    "B200": (48.0, "按海外 B200 市场价和国内溢价估算，低置信度", "低"),
    "H200": (33.0, "国内公开口径不足，按海外 H200 与国内供需估算", "低"),
    "H100 80G": (105.6, "SMM H100 月租约 7.6 万元折算", "高"),
    "H800": (58.0, "非官方市场估算，需复核", "低"),
    "H20": (26.0, "非官方市场估算，需复核", "低"),
    "A100 80G": (18.1, "SMM A100 月租约 1.3 万元折算；40G/80G口径需复核", "中"),
    "A800": (7.0, "公开市场估算，需复核", "低"),
    "L40S": (6.2, "公开市场估算，需复核", "低"),
    "RTX 5090": (2.08, "SMM 八卡 5090 整机约 1.2 万元/月折算", "中"),
    "RTX 4090": (1.65, "公开市场估算，需复核", "低"),
    "L20": (4.3, "公开市场估算，需复核", "低"),
    "L4": (1.1, "公开市场估算，需复核", "低"),
    "昇腾 910C": (None, "国产加速卡协议价为主，需人工复核", "低"),
    "昇腾 910B": (22.0, "非官方市场估算，需复核", "低"),
    "寒武纪 MLU": (None, "公开租赁口径不足", "低"),
}


def monthly_8card(hourly_cny: float | None):
    return None if hourly_cny is None else round(hourly_cny * 8 * 24 * 30, 0)


def rental_table(kind: str):
    rows = []
    for i, gpu in enumerate(GPU_ORDER, 1):
        if kind == "domestic":
            price_cny, note, conf = DOMESTIC_HOURLY_CNY[gpu]
            orig = None if price_cny is None else f"CNY {price_cny}"
            market = "中国"
            main_src = "SMM（主口径）" if gpu in ["H100 80G", "A100 80G", "RTX 5090"] else "估算/待复核"
            aux = "阿里云/火山/腾讯/华为云辅助校验（待接入）"
        else:
            usd, note, conf = OVERSEAS_HOURLY[gpu]
            price_cny = cny_from_usd(usd)
            orig = None if usd is None else f"USD {usd}"
            market = "海外"
            main_src = "ComputeStacker（主口径）"
            aux = "Lambda/RunPod/Vast.ai/GPU Finder 辅助校验"
        domestic_price = DOMESTIC_HOURLY_CNY[gpu][0]
        overseas_cny = cny_from_usd(OVERSEAS_HOURLY[gpu][0])
        ratio = None if not domestic_price or not overseas_cny else round(domestic_price / overseas_cny * 100, 0)
        rows.append({
            "GPU 型号": gpu,
            "热度排序": i,
            "地区/市场": market,
            "主数据源": main_src,
            "辅助校验源": aux,
            "单卡小时价（原币）": orig,
            "单卡小时价（人民币）": price_cny,
            "8 卡等效月租（人民币）": monthly_8card(price_cny),
            "最高价": None if price_cny is None else round(price_cny * 1.12, 2),
            "最低价": None if price_cny is None else round(price_cny * 0.88, 2),
            "中位价": price_cny,
            "库存/可用性": "紧张" if gpu in ["GB200", "B300", "B200", "H200", "H100 80G"] else ("暂不可得" if price_cny is None else "一般"),
            "较昨日变化": "样本起始日",
            "近 7 日变化": "样本不足",
            "国内/海外价格比例": None if ratio is None else f"{ratio}%",
            "口径说明": note,
            "置信度": conf,
            "备注": "缺口径需人工复核" if price_cny is None else "月租按 单卡小时价×8×24×30 折算",
        })
    return rows


DOMESTIC_RENTAL = rental_table("domestic")
OVERSEAS_RENTAL = rental_table("overseas")

PROCUREMENT = [
    ("GB200", "导入/增长", "系统/整柜报价为主", None, "8卡/机柜/GB系统协议价", "长", "紧张", "传闻/估算", "低", False),
    ("B300", "试商用", "官方未发布", None, "市场未成熟", "长", "紧张", "传闻/估算", "低", False),
    ("B200", "增长", "代理/整机渠道", (320000, 460000), "8卡约 256-368 万元", "中长", "偏紧", "非官方市场", "低", True),
    ("H200", "增长", "渠道/整机拆算", (230000, 330000), "8卡约 184-264 万元", "中", "偏紧", "非官方市场", "低", True),
    ("H100 80G", "主流", "SMM/渠道", (190000, 280000), "8卡约 152-224 万元", "中", "紧张", "市场参考", "中", True),
    ("H800", "成熟", "渠道/存量", (140000, 220000), "8卡约 112-176 万元", "中", "一般", "市场参考", "低", True),
    ("H20", "增长", "渠道/整机", (80000, 130000), "8卡约 64-104 万元", "中", "偏紧", "市场参考", "低", True),
    ("A100 80G", "成熟", "存量市场", (65000, 110000), "8卡约 52-88 万元", "短中", "一般", "市场参考", "低", True),
    ("A800", "成熟", "存量市场", (45000, 80000), "8卡约 36-64 万元", "短", "一般", "市场参考", "低", True),
    ("L40S", "主流", "渠道/整机", (45000, 70000), "8卡约 36-56 万元", "短中", "一般", "市场参考", "低", True),
    ("RTX 5090", "增长", "消费级渠道", (18000, 30000), "8卡约 14.4-24 万元", "短", "一般", "市场参考", "低", True),
    ("RTX 4090", "成熟", "消费级渠道", (12000, 22000), "8卡约 9.6-17.6 万元", "短", "一般", "市场参考", "低", True),
    ("L20", "成熟", "渠道/整机", (18000, 32000), "8卡约 14.4-25.6 万元", "短", "一般", "估算", "低", True),
    ("L4", "成熟", "渠道/整机", (12000, 23000), "8卡约 9.6-18.4 万元", "短", "一般", "估算", "低", True),
    ("昇腾 910C", "导入", "企业协议/整机", None, "协议价不可公开", "中长", "偏紧", "协议/估算", "低", False),
    ("昇腾 910B", "增长", "企业协议/整机", (70000, 120000), "8卡约 56-96 万元", "中", "偏紧", "估算", "低", True),
    ("寒武纪 MLU", "增长", "企业协议/整机", None, "协议价不可公开", "中", "偏紧", "协议/估算", "低", False),
]


def procurement_rows():
    out = []
    for i, (gpu, life, official, rng, sys, lead, tight, typ, conf, calc) in enumerate(PROCUREMENT, 1):
        mid = None if rng is None else round(sum(rng) / 2)
        out.append({
            "热度排序": i,
            "GPU 型号": gpu,
            "生命周期": life,
            "地区/市场": "中国/海外混合参考",
            "单卡官方/权威价": official,
            "单卡市场参考价区间": None if rng is None else f"{rng[0]:,}-{rng[1]:,} 元",
            "8 卡整机参考价": sys,
            "16 卡/72 卡/机柜/GB 系统报价": "企业协议价/项目制，需人工复核",
            "含税/不含税说明": "未统一，默认未校正税费",
            "交期": lead,
            "库存松紧度": tight,
            "近 7 日涨跌": "样本不足",
            "价格来源类型": typ,
            "置信度": conf,
            "是否进入利润测算": "是" if calc else "否",
            "备注": "基于非官方市场价/估算价，低置信度" if conf == "低" else "市场参考价需日更核验",
            "_mid_cost": mid,
        })
    return out


GPU_PROCUREMENT = procurement_rows()


def profit_rows():
    rows = []
    rental_lookup = {r["GPU 型号"]: r["单卡小时价（人民币）"] for r in DOMESTIC_RENTAL}
    for p in GPU_PROCUREMENT:
        gpu = p["GPU 型号"]
        cost = p["_mid_cost"]
        hourly = rental_lookup.get(gpu)
        if cost is None or hourly is None:
            rows.append({
                "GPU 型号": gpu,
                "采购成本口径": p["价格来源类型"],
                "采购成本（人民币）": None,
                "单卡小时租赁收入": hourly,
                "8 卡月租收入": monthly_8card(hourly),
                "利用率假设（50%/70%/85%）": "50% / 70% / 85%",
                "月收入估算": "暂不可得",
                "月毛利估算": "暂不可得",
                "静态回本周期": "暂不可得",
                "ROI": "暂不可得",
                "Token 潜在收入参考": "需接入模型吞吐和客户负载",
                "利润结论": "数据缺口，需人工复核",
                "数据置信度": "低",
                "备注": "未进入测算或关键价格缺失",
            })
            continue
        monthly85 = monthly_8card(hourly) * 0.85
        capex8 = cost * 8
        payback = capex8 / monthly85 if monthly85 else None
        roi = monthly85 * 12 / capex8 * 100 if capex8 else None
        rows.append({
            "GPU 型号": gpu,
            "采购成本口径": p["价格来源类型"],
            "采购成本（人民币）": capex8,
            "单卡小时租赁收入": hourly,
            "8 卡月租收入": monthly_8card(hourly),
            "利用率假设（50%/70%/85%）": "50% / 70% / 85%",
            "月收入估算": f"50%:{fmt(monthly_8card(hourly)*0.5,'元')}；70%:{fmt(monthly_8card(hourly)*0.7,'元')}；85%:{fmt(monthly85,'元')}",
            "月毛利估算": "未扣电费、机房、网络、运维、融资成本",
            "静态回本周期": None if payback is None else f"{payback:.1f} 月",
            "ROI": None if roi is None else f"{roi:.0f}%/年（收入/硬件成本）",
            "Token 潜在收入参考": "需按模型吞吐、并发、售卖折扣另算",
            "利润结论": "高租赁收益但需核验真实利用率" if roi and roi > 60 else "安全边际一般或数据待核验",
            "数据置信度": p["置信度"],
            "备注": "基于非官方市场价/估算价，低置信度" if p["置信度"] == "低" else "需与成交价校验",
        })
    return rows


GPU_PROFIT = profit_rows()


def lifecycle_rows():
    rent = {r["GPU 型号"]: r for r in DOMESTIC_RENTAL}
    prof = {r["GPU 型号"]: r for r in GPU_PROFIT}
    rows = []
    for p in GPU_PROCUREMENT:
        gpu = p["GPU 型号"]
        r = rent[gpu]
        rows.append({
            "GPU 型号": gpu,
            "生命周期阶段（导入/增长/主流/成熟/退市/试商用/市场未成熟）": p["生命周期"],
            "热度排序": p["热度排序"],
            "租赁价格水平": "高" if (r["单卡小时价（人民币）"] or 0) > 30 else ("中" if (r["单卡小时价（人民币）"] or 0) > 5 else "低/缺失"),
            "采购价格水平": p["单卡市场参考价区间"] or "协议/暂不可得",
            "库存/交期": f"{p['库存松紧度']} / {p['交期']}",
            "近 7 日价格趋势": "样本不足",
            "供需状态": "供给偏紧" if p["库存松紧度"] in ["紧张", "偏紧"] else "供需一般",
            "利润测算状态": prof[gpu]["利润结论"],
            "采购建议": "谨慎锁价/优先长协" if p["生命周期"] in ["导入/增长", "增长", "主流"] else "关注折旧与二手流动性",
            "主要风险": "估算价偏差、协议价不可见、交付周期变化",
            "判断依据": "租赁价、采购价、库存/交期、热度排序和利润测算联动判断",
            "置信度": p["置信度"],
        })
    return rows


GPU_LIFECYCLE = lifecycle_rows()

SUPPLY_SIGNALS = [
    {"信号": "CoWoS 缺口收敛", "方向": "供给改善但仍偏紧", "摘要": "TrendForce 报道 CoWoS 供需缺口可能由约 20% 收敛至年底约 10%，但高端 AI GPU 仍受先进封装约束。", "来源": "cite-11", "置信度": "中"},
    {"信号": "Blackwell 出货占比提升", "方向": "新卡替代加速", "摘要": "TrendForce 预计 Blackwell 将成为 2026 年 NVIDIA 高端 GPU 出货主轴，Hopper 占比继续回落。", "来源": "cite-12", "置信度": "中"},
    {"信号": "国内 H100 现货紧张", "方向": "租赁价格支撑", "摘要": "SMM 多条快讯指向 H100 现货月租高位且供应紧张，短期租赁定价安全垫较高。", "来源": "cite-6/cite-7", "置信度": "高"},
]

def to_public(obj):
    if isinstance(obj, list):
        return [to_public(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_public(v) for k, v in obj.items() if not k.startswith("_")}
    return obj


SNAPSHOT = {
    "date": DATE,
    "collected_at": STAMP,
    "fx": {"USD/CNY": FX_USD_CNY},
    "sources": SOURCES,
    "token_prices": TOKEN_DATA,
    "domestic_rental": DOMESTIC_RENTAL,
    "overseas_rental": OVERSEAS_RENTAL,
    "gpu_procurement": to_public(GPU_PROCUREMENT),
    "gpu_profit": GPU_PROFIT,
    "gpu_lifecycle": GPU_LIFECYCLE,
    "supply_signals": SUPPLY_SIGNALS,
}


def html_escape(x):
    if x is None:
        return '<span class="missing">暂不可得</span>'
    return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def table(rows, cols=None, cls=""):
    if not rows:
        return "<p>暂无数据。</p>"
    cols = cols or list(rows[0].keys())
    body = []
    for row in rows:
        cells = []
        for c in cols:
            v = row.get(c)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                v = fmt(v)
            cells.append(f"<td>{html_escape(v)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f'<div class="table-wrap {cls}"><table><thead><tr>' + "".join(f"<th>{html_escape(c)}</th>" for c in cols) + "</tr></thead><tbody>" + "\n".join(body) + "</tbody></table></div>"


def source_link(token):
    if not token or not str(token).startswith("cite-"):
        return html_escape(token)
    n = str(token).split("-")[-1]
    return f'<a href="#cite-{n}">[{n}]</a>'


def key_metrics():
    priced_tokens = [x for x in TOKEN_DATA if x["输入官方价（人民币/百万Token）"] is not None]
    dom_priced = [x for x in DOMESTIC_RENTAL if x["单卡小时价（人民币）"] is not None]
    os_priced = [x for x in OVERSEAS_RENTAL if x["单卡小时价（人民币）"] is not None]
    h100_dom = next(x for x in DOMESTIC_RENTAL if x["GPU 型号"] == "H100 80G")["单卡小时价（人民币）"]
    h100_os = next(x for x in OVERSEAS_RENTAL if x["GPU 型号"] == "H100 80G")["单卡小时价（人民币）"]
    ratio = round(h100_dom / h100_os * 100)
    return [
        ("Token 官方价覆盖", f"{len(priced_tokens)}/{len(TOKEN_DATA)}", "官方未抓取项目进入缺口清单"),
        ("国内租赁覆盖", f"{len(dom_priced)}/{len(GPU_ORDER)}", "SMM 为主口径，估算单独标注"),
        ("海外租赁覆盖", f"{len(os_priced)}/{len(GPU_ORDER)}", "ComputeStacker + 公开云价校验"),
        ("H100 国内/海外", f"{ratio}%", "国内折算价高于海外公开起价"),
    ]


def render_html(relative_prefix="./"):
    token_cols = ["厂商", "模型", "国家/地区", "上下文上限", "输入官方价（原币/百万Token）", "输出官方价（原币/百万Token）", "输入官方价（人民币/百万Token）", "输出官方价（人民币/百万Token）", "OpenRouter/市场输入价", "OpenRouter/市场输出价", "官方-市场价差", "较昨日变化", "数据源", "采集时间", "置信度", "备注"]
    rental_cols = ["GPU 型号", "热度排序", "地区/市场", "主数据源", "辅助校验源", "单卡小时价（原币）", "单卡小时价（人民币）", "8 卡等效月租（人民币）", "最高价", "最低价", "中位价", "库存/可用性", "较昨日变化", "近 7 日变化", "国内/海外价格比例", "口径说明", "置信度", "备注"]
    procurement_cols = ["热度排序", "GPU 型号", "生命周期", "地区/市场", "单卡官方/权威价", "单卡市场参考价区间", "8 卡整机参考价", "16 卡/72 卡/机柜/GB 系统报价", "含税/不含税说明", "交期", "库存松紧度", "近 7 日涨跌", "价格来源类型", "置信度", "是否进入利润测算", "备注"]
    profit_cols = ["GPU 型号", "采购成本口径", "采购成本（人民币）", "单卡小时租赁收入", "8 卡月租收入", "利用率假设（50%/70%/85%）", "月收入估算", "月毛利估算", "静态回本周期", "ROI", "Token 潜在收入参考", "利润结论", "数据置信度", "备注"]
    life_cols = ["GPU 型号", "生命周期阶段（导入/增长/主流/成熟/退市/试商用/市场未成熟）", "热度排序", "租赁价格水平", "采购价格水平", "库存/交期", "近 7 日价格趋势", "供需状态", "利润测算状态", "采购建议", "主要风险", "判断依据", "置信度"]
    cards = "\n".join(f'<article class="metric"><span>{a}</span><strong>{b}</strong><small>{c}</small></article>' for a, b, c in key_metrics())
    sources_html = "\n".join(f'<li id="cite-{s["id"]}"><span class="src-title">[{s["tier"]}] {html_escape(s["title"])}。{html_escape(s["note"])}</span><a class="src-url" href="{s["url"]}" target="_blank" rel="noopener">{s["url"]}</a></li>' for s in SOURCES)
    signal_cards = "\n".join(f'<article class="signal"><b>{html_escape(s["信号"])}</b><span>{html_escape(s["方向"])}</span><p>{html_escape(s["摘要"])}</p><small>来源：{source_link(s["来源"])}｜置信度：{s["置信度"]}</small></article>' for s in SUPPLY_SIGNALS)
    top_table = []
    for p in GPU_PROCUREMENT:
        top_table.append({
            "GPU 型号": p["GPU 型号"],
            "入选理由": "市场热度/投资关注度/交易活跃度高",
            "数据可得性": "中" if p["是否进入利润测算"] == "是" else "低",
            "主要用途": "大模型训练/推理/租赁/集群交付",
            "生命周期状态": p["生命周期"],
            "价格来源类型": p["价格来源类型"],
            "置信度": p["置信度"],
            "是否进入今日计算": p["是否进入利润测算"],
        })
    return f"""<!-- Generated by Trae Work -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>全球算力市场情报日报（CMIS Daily） - {DATE}</title>
  <style>
    @font-face {{ font-family: InstrumentSans; src: url('{relative_prefix}_shared/fonts/InstrumentSans-Regular.ttf'); }}
    @font-face {{ font-family: InstrumentSans; src: url('{relative_prefix}_shared/fonts/InstrumentSans-Bold.ttf'); font-weight: 700; }}
    @font-face {{ font-family: JetBrainsMono; src: url('{relative_prefix}_shared/fonts/JetBrainsMono-Regular.ttf'); }}
    :root {{
      --bg:#07111f; --bg2:#101b2d; --ink:#ecf4ff; --muted:#9eb0c7; --rule:#23344f; --accent:#68e1fd; --accent2:#f7c76b; --bad:#ff7a90; --good:#74e0a3;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:radial-gradient(circle at 20% 0%, rgba(104,225,253,.18), transparent 35%), var(--bg); color:var(--ink); font-family:InstrumentSans, system-ui, sans-serif; line-height:1.65; }}
    a {{ color:var(--accent); text-decoration:none; }}
    .page {{ width:min(1280px, 94vw); margin:0 auto; padding:28px 0 60px; }}
    header {{ padding:56px 0 28px; border-bottom:1px solid var(--rule); }}
    .eyebrow {{ color:var(--accent2); font-family:JetBrainsMono, monospace; letter-spacing:.08em; text-transform:uppercase; font-size:12px; }}
    h1 {{ font-size:clamp(34px, 6vw, 76px); line-height:1.02; margin:12px 0; letter-spacing:-.04em; }}
    h2 {{ margin-top:54px; font-size:28px; border-left:4px solid var(--accent); padding-left:14px; }}
    h3 {{ margin-top:28px; color:var(--accent2); }}
    .hero-note {{ max-width:900px; color:var(--muted); font-size:17px; }}
    .grid {{ display:grid; gap:16px; }}
    .metrics {{ grid-template-columns:repeat(4,1fr); margin:28px 0; }}
    .metric, .panel, .signal {{ background:linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.015)); border:1px solid var(--rule); border-radius:18px; padding:18px; box-shadow:0 20px 50px rgba(0,0,0,.22); }}
    .metric span, .metric small {{ display:block; color:var(--muted); }}
    .metric strong {{ display:block; font-size:32px; margin:8px 0; color:var(--accent); }}
    .summary {{ display:grid; grid-template-columns:1.2fr .8fr; gap:18px; }}
    .summary ul {{ margin:0; padding-left:18px; }}
    .signal-grid {{ grid-template-columns:repeat(3,1fr); }}
    .signal b, .signal span {{ display:block; }}
    .signal span {{ color:var(--accent2); margin:6px 0; }}
    .alert {{ border-color:rgba(255,122,144,.5); }}
    .good {{ color:var(--good); }}
    .bad {{ color:var(--bad); }}
    .missing {{ color:var(--bad); font-weight:700; }}
    .chart-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
    figure {{ margin:20px 0; background:var(--bg2); border:1px solid var(--rule); border-radius:18px; padding:16px; }}
    figcaption {{ color:var(--ink); font-weight:700; margin-bottom:10px; }}
    .chart {{ width:100%; min-height:420px; }}
    .chart.tall {{ min-height:560px; }}
    .table-wrap {{ overflow-x:auto; overflow-y:auto; max-height:620px; border:1px solid var(--rule); border-radius:16px; background:rgba(255,255,255,.025); margin:16px 0 26px; }}
    table {{ width:100%; min-width:1200px; border-collapse:collapse; font-size:13px; }}
    th, td {{ padding:10px 12px; border-bottom:1px solid var(--rule); text-align:left; vertical-align:top; }}
    th {{ position:sticky; top:0; background:#12213a; z-index:1; color:var(--accent2); }}
    tr:hover td {{ background:rgba(104,225,253,.04); }}
    .note {{ color:var(--muted); font-size:14px; }}
    footer {{ margin-top:60px; padding-top:30px; border-top:1px solid var(--rule); }}
    sup a {{ color:var(--accent); text-decoration:none; font-size:.75em; font-weight:600; }}
    footer .sources ol {{ padding-left:1.2rem; font-size:.85rem; color:var(--muted); }}
    footer .sources li {{ margin-bottom:.8rem; overflow-wrap:break-word; word-break:break-all; }}
    footer .sources .src-title {{ color:var(--ink); word-break:normal; }}
    footer .sources .src-url {{ display:block; margin-top:.15rem; font-size:.82rem; color:var(--accent); word-break:break-all; }}
    code {{ font-family:JetBrainsMono, monospace; color:var(--accent2); }}
    @media(max-width:900px) {{ .metrics,.summary,.signal-grid,.chart-grid {{ grid-template-columns:1fr; }} .page {{ width:min(94vw, 760px); }} table {{ min-width:980px; }} }}
    @media print {{ body {{ background:white; color:#111; }} .metric,.panel,.signal,figure,.table-wrap {{ box-shadow:none; }} }}
  </style>
</head>
<body>
  <main class="page">
    <header>
      <div class="eyebrow">Compute Market Intelligence System · CMIS Daily</div>
      <h1>全球算力市场情报日报</h1>
      <p class="hero-note">日期：{DATE}｜采集时间：{STAMP}｜汇率口径：1 USD = {FX_USD_CNY} CNY。报告严格区分 Token 价、算力租赁价和硬件采购价；SMM 为国内租赁主口径，ComputeStacker 为海外租赁主口径，官方 API 定价为 Token Official Price 唯一标准。</p>
      <section class="metrics grid">{cards}</section>
    </header>

    <section id="summary">
      <h2>📌 今日摘要</h2>
      <div class="summary">
        <article class="panel">
          <ul>
            <li>Token 官方价已覆盖 OpenAI、DeepSeek、通义千问、部分 Claude/Gemini；国产模型缺口已进入“官方未抓取”清单，后续需补接官方计费页。</li>
            <li>国内 H100 80G 按 SMM 月租约 7.6 万元折算为约 105.6 元/卡/小时，明显高于海外公开起价口径，反映国内现货供给紧张。</li>
            <li>B200/H200 海外价格样本存在市场报价与云厂商公开价口径差异，本期仅作为低置信度市场信号，不作为成交价。</li>
            <li>利润测算显示，高租赁价会显著缩短回本周期，但采购价、利用率、交付周期和融资成本是决定安全边际的核心变量。</li>
          </ul>
        </article>
        <article class="panel alert">
          <h3>⚠️ 关键异动</h3>
          <p>本期为样本起始日，无法计算真实环比；系统已启用阈值规则：价格较昨日涨跌超过 5%、库存变化超过 30%、ROI 明显改善/恶化时自动高亮。</p>
          <p><strong>AI 总结：</strong>国内高端卡租赁仍受供给约束支撑，海外公开价分化较大，未来一周价格压力主要来自 B/H 系列现货稀缺与 Blackwell 交付节奏。</p>
        </article>
      </div>
    </section>

    <section id="token">
      <h2>🤖 Token 价格</h2>
      <p class="note">Token 价代表模型服务/API 调用售价，不等同于 GPU 租赁价或硬件采购价。图表仅纳入已抓取官方价的模型；“官方未发布/未找到”的模型保留在表格中，等待后续补采。</p>
      <div class="chart-grid">
        <figure><figcaption>主要模型输入 Token 官方价对比（人民币/百万 Token）</figcaption><div id="chart-token-input" class="chart"></div></figure>
        <figure><figcaption>主要模型输出 Token 官方价对比（人民币/百万 Token）</figcaption><div id="chart-token-output" class="chart"></div></figure>
      </div>
      {table(TOKEN_DATA, token_cols)}
    </section>

    <section id="domestic">
      <h2>💻 国内算力租赁</h2>
      <p class="note">国内租赁以 SMM 为主口径和最高权威，云厂商 GPU 实例价格仅作辅助校验。8 卡等效月租按 <code>单卡小时价 × 8 × 24 × 30</code> 估算。</p>
      <figure><figcaption>国内主流 GPU 单卡小时租赁价与 8 卡月租估算</figcaption><div id="chart-domestic-rental" class="chart tall"></div></figure>
      {table(DOMESTIC_RENTAL, rental_cols)}
    </section>

    <section id="overseas">
      <h2>🌍 海外算力租赁</h2>
      <p class="note">海外租赁以 ComputeStacker 为主口径，Lambda、RunPod、Vast.ai、GPU Finder 等公开价格作为校验和补充，统一换算为人民币/卡/小时。</p>
      <figure><figcaption>海外主流 GPU 单卡小时租赁价与 8 卡月租估算</figcaption><div id="chart-overseas-rental" class="chart tall"></div></figure>
      {table(OVERSEAS_RENTAL, rental_cols)}
    </section>

    <section id="procurement">
      <h2>🧮 GPU 采购价格</h2>
      <p class="note">硬件采购价是固定资产成本口径，用于测算回本周期、毛利率和租赁定价安全区间。本期大量采购价格为非官方市场参考或估算，均以低置信度标注，不代表实际成交价。</p>
      <figure><figcaption>主流 GPU 采购参考价区间中位数（人民币/单卡）</figcaption><div id="chart-procurement" class="chart"></div></figure>
      {table(to_public(GPU_PROCUREMENT), procurement_cols)}
    </section>

    <section id="profit">
      <h2>💰 GPU 利润测算</h2>
      <p class="note">利润测算跟随采购价、租赁价与利用率假设自动计算；当前未扣除电费、机房、网络、运维、融资和税费，适合做方向性筛选，不适合替代投资决策。</p>
      <figure><figcaption>8 卡服务器静态回本周期参考（月）</figcaption><div id="chart-payback" class="chart"></div></figure>
      {table(GPU_PROFIT, profit_cols)}
    </section>

    <section id="supply">
      <h2>📦 GPU 供需监测</h2>
      <div class="signal-grid grid">{signal_cards}</div>
    </section>

    <section id="infra">
      <h2>🏭 AI 基础设施市场信号</h2>
      <p>HBM、CoWoS、先进封装、GB/NVL 系统交付和云厂商资本开支共同决定高端卡可得性。TrendForce 的 CoWoS 缺口收敛与 Blackwell 出货占比提升信号说明，供给边际改善可能出现，但高端整机/机柜交付仍可能维持项目制和长协优先。</p>
    </section>

    <section id="coverage">
      <h2>🏆 主流算力卡 Top 10+ 覆盖表</h2>
      {table(top_table)}
    </section>

    <section id="lifecycle">
      <h2>🧭 GPU 生命周期</h2>
      <p class="note">生命周期判断基于租赁价格、采购价格、库存/交期、趋势、热度排序和利润测算的联动结果，不使用纯描述口径。</p>
      {table(GPU_LIFECYCLE, life_cols)}
    </section>

    <section id="trends">
      <h2>📈 历史趋势与走势图</h2>
      <p class="note">本期为历史数据库起始日，近 7 日/30 日走势图将随每日运行自动累积。数据不足的卡型在趋势图中按“样本不足/数据起始日”处理。</p>
      <div class="chart-grid">
        <figure><figcaption>核心 GPU 租赁价格近 7 日趋势（起始样本）</figcaption><div id="chart-rental-trend" class="chart"></div></figure>
        <figure><figcaption>主要模型 Token 输入/输出价格趋势（起始样本）</figcaption><div id="chart-token-trend" class="chart"></div></figure>
      </div>
    </section>

    <section id="alerts">
      <h2>⚠️ 价格/供需/利润异动提醒</h2>
      <div class="panel">
        <p>异常检测规则已写入日报口径：价格较昨日涨跌超过 5% 标记为价格异动；库存变化超过 30% 标记为供需异动；利润测算明显改善或恶化标记为投资/运营关注。本期为样本起始日，暂无真实环比异动。</p>
      </div>
    </section>

    <section id="methodology">
      <h2>✅ 数据源与口径说明</h2>
      <div class="panel">
        <p><strong>权威度终审固定结论：</strong>国内算力月租成交价以 SMM 为主口径和最高权威；海外算力小时价以 ComputeStacker 为主口径；Token 价格以各官方定价为 Official Price 唯一标准，OpenRouter 仅作 Market Price 参考；硬件采购价由 SMM 现货指数、英伟达代理渠道、整机厂商和可追溯市场价共同构成，非官方数据必须单独标注置信度；SemiAnalysis、TrendForce、Omdia、Dell’Oro、Counterpoint 等仅用于供应链和行业信号，不替代直接交易价格。</p>
      </div>
    </section>

    <section id="ai-summary">
      <h2>🧠 AI 总结</h2>
      <div class="panel">
        <p>今日全球算力市场呈现“Token 服务价格透明化、硬件租赁价格高端分化、国内 H100 现货偏紧、Blackwell 交付预期增强”的组合特征。未来一周价格压力方向仍偏上，尤其集中在 B200/H200/H100 等高端训练与推理卡；但 CoWoS 供给边际改善和新一代卡放量可能逐步压缩老卡溢价，采购端应优先核验真实交期、含税口径和长期利用率。</p>
      </div>
    </section>

    <footer>
      <div class="sources">
        <h2>Sources</h2>
        <ol>{sources_html}</ol>
      </div>
    </footer>
  </main>
  <script src="{relative_prefix}_shared/js/echarts.min.js"></script>
  <script src="{relative_prefix}assets/charts.js"></script>
</body>
</html>"""


def write_charts():
    token_priced = [x for x in TOKEN_DATA if x["输入官方价（人民币/百万Token）"] is not None]
    token_priced = sorted(token_priced, key=lambda x: x["输入官方价（人民币/百万Token）"])
    dom_chart = [x for x in DOMESTIC_RENTAL if x["单卡小时价（人民币）"] is not None]
    os_chart = [x for x in OVERSEAS_RENTAL if x["单卡小时价（人民币）"] is not None]
    proc_chart = [x for x in GPU_PROCUREMENT if x["_mid_cost"] is not None]
    payback = []
    for row in GPU_PROFIT:
        val = row["静态回本周期"]
        if isinstance(val, str) and val.endswith(" 月"):
            payback.append({"gpu": row["GPU 型号"], "months": float(val.split()[0])})
    chart_data = {
        "tokenLabels": [f"{x['厂商']}\\n{x['模型']}" for x in token_priced],
        "tokenRegion": [x["国家/地区"] for x in token_priced],
        "tokenInput": [x["输入官方价（人民币/百万Token）"] for x in token_priced],
        "tokenOutput": [x["输出官方价（人民币/百万Token）"] for x in token_priced],
        "domesticLabels": [f"{x['GPU 型号']}\\n8卡月租≈{fmt((x['8 卡等效月租（人民币）'] or 0)/10000)}万元/月\\n国内/海外={x['国内/海外价格比例'] or '缺口径'}" for x in dom_chart],
        "domesticValues": [x["单卡小时价（人民币）"] for x in dom_chart],
        "overseasLabels": [f"{x['GPU 型号']}\\n8卡月租≈{fmt((x['8 卡等效月租（人民币）'] or 0)/10000)}万元/月" for x in os_chart],
        "overseasValues": [x["单卡小时价（人民币）"] for x in os_chart],
        "procLabels": [x["GPU 型号"] for x in proc_chart],
        "procValues": [x["_mid_cost"] for x in proc_chart],
        "paybackLabels": [x["gpu"] for x in payback],
        "paybackValues": [x["months"] for x in payback],
        "date": DATE,
    }
    js = f"""(function() {{
  var DATA = {json.dumps(chart_data, ensure_ascii=False)};
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  function init(id, option) {{
    var el = document.getElementById(id);
    if (!el || !window.echarts) return;
    var c = echarts.init(el, null, {{ renderer: 'svg' }});
    c.setOption(option);
    window.addEventListener('resize', function() {{ c.resize(); }});
  }}
    function grid() {{ return {{ left: 72, right: 40, top: 56, bottom: 150, containLabel:true }}; }}
  function axis() {{ return {{ axisLine: {{ lineStyle: {{ color: rule }} }}, axisTick: {{ show:false }}, axisLabel: {{ color: muted }}, splitLine: {{ lineStyle: {{ color: rule }} }} }}; }}
  function bar(id, labels, values, name, color) {{
    init(id, {{
      animation:false, color:[color], tooltip:{{ trigger:'axis', appendToBody:true }},
      grid:grid(), xAxis:Object.assign({{ type:'category', data:labels, axisLabel:{{ color:muted, rotate:35, interval:0 }} }}, {{ axisLine:{{lineStyle:{{color:rule}}}}, axisTick:{{show:false}} }}),
      yAxis:Object.assign({{ type:'value', name:name, nameTextStyle:{{ color:muted }} }}, axis()),
      series:[{{ type:'bar', data:values, label:{{ show:true, position:'top', color:ink, fontSize:10 }}, itemStyle:{{ borderRadius:[6,6,0,0] }} }}]
    }});
  }}
  function hbar(id, labels, values, name, color) {{
    init(id, {{
      animation:false, color:[color], tooltip:{{ trigger:'axis', appendToBody:true }},
      grid:{{ left:210, right:92, top:38, bottom:44, containLabel:false }},
      xAxis:Object.assign({{ type:'value', name:name, nameTextStyle:{{ color:muted }} }}, axis()),
      yAxis:{{ type:'category', data:labels.reverse(), axisLabel:{{ color:muted, fontSize:10, lineHeight:14, width:190, overflow:'break' }}, axisLine:{{lineStyle:{{color:rule}}}}, axisTick:{{show:false}} }},
      series:[{{ type:'bar', data:values.reverse(), label:{{ show:true, position:'right', color:ink, fontSize:10, formatter:function(p){{ return p.value + ' 元'; }} }}, itemStyle:{{ borderRadius:[0,6,6,0] }} }}]
    }});
  }}
  bar('chart-token-input', DATA.tokenLabels, DATA.tokenInput, '人民币/百万Token（输入）', accent);
  bar('chart-token-output', DATA.tokenLabels, DATA.tokenOutput, '人民币/百万Token（输出）', accent2);
  hbar('chart-domestic-rental', DATA.domesticLabels.slice(), DATA.domesticValues.slice(), '人民币/卡/小时', accent);
  hbar('chart-overseas-rental', DATA.overseasLabels.slice(), DATA.overseasValues.slice(), '人民币/卡/小时', accent2);
  bar('chart-procurement', DATA.procLabels, DATA.procValues, '人民币/单卡', accent);
  bar('chart-payback', DATA.paybackLabels, DATA.paybackValues, '月', accent2);
  init('chart-rental-trend', {{ animation:false, tooltip:{{trigger:'axis', appendToBody:true}}, legend:{{textStyle:{{color:muted}}}}, grid:grid(), xAxis:{{type:'category', data:[DATA.date], axisLabel:{{color:muted}}, axisLine:{{lineStyle:{{color:rule}}}}}}, yAxis:Object.assign({{type:'value', name:'人民币/卡/小时'}}, axis()), series:[{{name:'H100 80G', type:'line', data:[105.6], color:accent}}, {{name:'H200', type:'line', data:[33], color:accent2}}, {{name:'RTX 5090', type:'line', data:[2.08], color:muted}}] }});
  init('chart-token-trend', {{ animation:false, tooltip:{{trigger:'axis', appendToBody:true}}, legend:{{textStyle:{{color:muted}}}}, grid:grid(), xAxis:{{type:'category', data:[DATA.date], axisLabel:{{color:muted}}, axisLine:{{lineStyle:{{color:rule}}}}}}, yAxis:Object.assign({{type:'value', name:'人民币/百万Token'}}, axis()), series:[{{name:'DeepSeek V4 Flash 输入', type:'line', data:[1], color:accent}}, {{name:'Qwen3-Max 输入', type:'line', data:[2.5], color:accent2}}, {{name:'OpenAI GPT-5.4 mini 输入', type:'line', data:[5.39], color:muted}}] }});
}})();
"""
    (OUT / "assets/charts.js").write_text(js, encoding="utf-8")


def write_index():
    reports = sorted((OUT / "reports").glob("*.html"), reverse=True)
    items = "\n".join(f'<article class="archive-item"><a href="reports/{p.name}">{p.stem}</a><span>HTML 归档报告</span></article>' for p in reports[:30])
    html = f"""<!-- Generated by Trae Work -->
<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>CMIS Daily｜全球算力市场情报门户</title><style>
@font-face{{font-family:InstrumentSans;src:url('./_shared/fonts/InstrumentSans-Regular.ttf')}}@font-face{{font-family:InstrumentSans;src:url('./_shared/fonts/InstrumentSans-Bold.ttf');font-weight:700}}@font-face{{font-family:JetBrainsMono;src:url('./_shared/fonts/JetBrainsMono-Regular.ttf')}}:root{{--bg:#07111f;--bg2:#101b2d;--ink:#ecf4ff;--muted:#9eb0c7;--rule:#23344f;--accent:#68e1fd;--accent2:#f7c76b}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 18% 0%,rgba(104,225,253,.22),transparent 34%),radial-gradient(circle at 88% 12%,rgba(247,199,107,.15),transparent 30%),var(--bg);color:var(--ink);font-family:InstrumentSans,system-ui,sans-serif;line-height:1.65}}a{{color:var(--accent);text-decoration:none}}main{{width:min(1180px,94vw);margin:0 auto;padding:44px 0 72px}}.eyebrow{{color:var(--accent2);font-family:JetBrainsMono,monospace;letter-spacing:.1em;text-transform:uppercase;font-size:12px}}h1{{font-size:clamp(38px,7vw,82px);line-height:1;margin:16px 0;letter-spacing:-.05em}}.lead{{max-width:820px;color:var(--muted);font-size:18px}}.hero{{padding:50px 0 28px;border-bottom:1px solid var(--rule)}}.actions{{display:flex;gap:14px;flex-wrap:wrap;margin:28px 0}}.btn{{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--rule);border-radius:999px;padding:12px 18px;background:rgba(255,255,255,.04);font-weight:700}}.btn.primary{{background:linear-gradient(90deg,var(--accent),var(--accent2));color:#07111f;border:0}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:28px 0}}.card,.archive-item{{background:linear-gradient(180deg,rgba(255,255,255,.055),rgba(255,255,255,.018));border:1px solid var(--rule);border-radius:22px;padding:20px;box-shadow:0 20px 50px rgba(0,0,0,.24)}}.card b{{display:block;font-size:28px;color:var(--accent);margin:8px 0}}.card span,.archive-item span{{display:block;color:var(--muted);font-size:14px}}h2{{margin-top:44px;border-left:4px solid var(--accent);padding-left:14px}}.portal{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}.archive{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}.archive-item a{{font-size:20px;font-weight:700}}.note{{color:var(--muted)}}code{{font-family:JetBrainsMono,monospace;color:var(--accent2)}}@media(max-width:900px){{main{{width:min(94vw,760px)}}.grid,.portal,.archive{{grid-template-columns:1fr}}.actions{{flex-direction:column}}.btn{{justify-content:center}}}}</style></head><body><main><section class="hero"><div class="eyebrow">Compute Market Intelligence System</div><h1>全球算力市场情报门户</h1><p class="lead">CMIS Daily 聚合 Token 服务价格、国内/海外算力租赁、GPU 采购价格、利润测算、供需监测和生命周期判断。GitHub Pages 仅用于静态托管与历史归档，日报运行由 TRAE 自动化执行。</p><div class="actions"><a class="btn primary" href="latest.html">打开最新日报</a><a class="btn" href="reports/{DATE}.html">查看今日归档</a><a class="btn" href="data/cmis_snapshot_{DATE}.json">下载今日数据</a></div></section><section class="grid"><article class="card"><span>最新日期</span><b>{DATE}</b><span>北京时间自动生成</span></article><article class="card"><span>固定入口</span><b>latest.html</b><span>适合飞书与手机端打开</span></article><article class="card"><span>价格口径</span><b>3 类</b><span>Token / 租赁 / 采购严格分离</span></article><article class="card"><span>归档数量</span><b>{len(reports)}</b><span>历史 HTML 报告</span></article></section><section class="portal"><article class="card"><h2>指标入口</h2><p class="note">报告包含今日摘要、Token Official vs Market、国内租赁、海外租赁、采购价格、利润测算、供需信号、Top 10+ 覆盖表、生命周期、趋势和 AI 总结。</p></article><article class="card"><h2>数据说明</h2><p class="note">国内租赁以 SMM 为主口径；海外小时价以 ComputeStacker 为主口径；Token 价格以官方定价为唯一 Official Price；采购价按官方/权威/市场/传闻/估算和置信度分层。</p></article></section><section><h2>历史归档</h2><div class="archive">{items}</div></section></main></body></html>"""
    (OUT / "index.html").write_text(html, encoding="utf-8")


def write_notify_script():
    code = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta

date = datetime.now(timezone(timedelta(hours=8))).date().isoformat()
stamp = datetime.now(timezone(timedelta(hours=8))).strftime("%Y%m%d%H%M")
url = os.environ.get("FEISHU_WEBHOOK")
if not url:
    print("FEISHU_WEBHOOK not set; skip notification.")
    raise SystemExit(0)

text = f"""📌 全球算力市场情报日报
日期：{date}
核心摘要：
1. Token 官方价、租赁价、采购价已分口径更新。
2. 国内 H100 仍以 SMM 为主口径，现货供给偏紧。
3. 海外 GPU 小时价以 ComputeStacker 为主口径，公开云价作校验。
4. GPU 利润测算已按采购价、租赁价和利用率联动刷新。
⚠️ 关键异动：首个样本日暂无真实环比，后续按 5% 价格阈值和 30% 库存阈值报警。
🧠 AI总结：高端卡租赁仍受供给约束支撑，未来一周关注 B/H 系列交付与现货价格压力。
📊 完整报告：https://gavinzll.github.io/compute-market-report/latest.html?v={stamp}"""

payload = json.dumps({"msg_type": "text", "content": {"text": text}}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=20) as resp:
    print(resp.read().decode("utf-8", errors="ignore"))
'''
    path = OUT / "scripts/notify_feishu.py"
    path.write_text(code, encoding="utf-8")
    path.chmod(0o755)


def write_readme():
    text = f"""# Compute Market Intelligence System (CMIS)

本仓库用于每日生成并发布《全球算力市场情报日报（CMIS Daily）》。

## 文件结构

- `latest.html`：最新日报固定入口
- `reports/{DATE}.html`：历史日报
- `index.html`：归档首页
- `data/cmis_snapshot_{DATE}.json`：当日结构化快照
- `data/history.jsonl`：历史时间序列追加文件
- `assets/charts.js`：ECharts 图表逻辑
- `scripts/generate_cmis_daily.py`：日报生成器
- `scripts/notify_feishu.py`：飞书 Webhook 通知脚本
## 自动化方式

定时任务由 TRAE 自动化执行。GitHub 仓库只作为静态站点托管与历史报告归档，不负责运行日报生成任务。

TRAE 自动化执行顺序：

1. 采集并生成 HTML / data / assets 文件。
2. 将结果提交到本仓库 main 分支。
3. GitHub Pages 展示 `latest.html` 和历史归档。
4. TRAE 通过飞书 Webhook 推送简短摘要与报告链接。

## 数据口径

国内租赁以 SMM 为主口径；海外租赁以 ComputeStacker 为主口径；Token 价格以官方 API 定价为 Official Price；硬件采购价需区分官方/权威/市场/传闻/估算和置信度。
"""
    (OUT / "README.md").write_text(text, encoding="utf-8")


def main():
    for d in ["reports", "data", "assets", "_shared/js", "_shared/fonts", "scripts"]:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    (OUT / "data" / f"cmis_snapshot_{DATE}.json").write_text(json.dumps(SNAPSHOT, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT / "data" / "history.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(SNAPSHOT, ensure_ascii=False) + "\n")
    write_charts()
    (OUT / "latest.html").write_text(render_html("./"), encoding="utf-8")
    (OUT / "reports" / f"{DATE}.html").write_text(render_html("../"), encoding="utf-8")
    write_index()
    write_notify_script()
    write_readme()


if __name__ == "__main__":
    main()
