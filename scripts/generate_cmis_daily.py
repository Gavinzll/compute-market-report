#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CMIS Daily report generator.

本脚本只负责生成 GitHub Pages 静态产物，不生成或依赖 GitHub Actions。
核心修正：
- 国内租赁主口径固定为“万元/8卡整机/月”，不再把国内价格作为“元/卡/小时”反复折算。
- 只有 Validate == PASS 且 Confidence >= 70 的数据进入主图、主指标、利润测算和 AI 总结。
- REVIEW / REJECT 数据只进入审计摘要与异常样本。
- 不再回写 README，避免覆盖仓库说明文档。
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("CMIS_OUT", ROOT))
TZ = timezone(timedelta(hours=8))
NOW = datetime.now(TZ)
DATE = NOW.date().isoformat()
FREEZE_TIME = NOW.replace(second=0, microsecond=0).isoformat()
FREEZE_LABEL = NOW.strftime("%Y-%m-%d %H:%M")
STAMP = NOW.strftime("%Y-%m-%d %H:%M:%S UTC+08:00")
FX_USD_CNY = 7.18
REPORT_VERSION = "v1.1.0"


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


PROMPT_VERSION = git_commit()

SOURCES = [
    {
        "id": 1,
        "tier": "主口径/行业",
        "title": "SMM 算力快讯：H100/A100/RTX 5090 月租报价",
        "url": "https://news.metal.com/featured-category.html/newscontent/103972175-smm-computing-power-flash-an-intelligent-computing-company-quoted-monthly-rental-prices-for-multiple-gpu-models-includin",
        "note": "国内租赁主口径，仅在对象、单位和合理性校验通过后进入指数。",
    },
    {
        "id": 2,
        "tier": "主口径/行业",
        "title": "ComputeStacker GPU cloud pricing guide",
        "url": "https://computestacker.com/insights/gpu-cloud-pricing-guide-2026/",
        "note": "海外 GPU Cloud 小时价参考，不进入国内租赁指数。",
    },
    {
        "id": 3,
        "tier": "官方/校验",
        "title": "Lambda GPU cloud pricing",
        "url": "https://lambda.ai/pricing",
        "note": "海外公开云价辅助校验。",
    },
    {
        "id": 4,
        "tier": "官方",
        "title": "OpenAI API Pricing",
        "url": "https://openai.com/api/pricing/",
        "note": "Token Official Price 来源之一。",
    },
    {
        "id": 5,
        "tier": "官方",
        "title": "DeepSeek API Pricing",
        "url": "https://api-docs.deepseek.com/zh-cn/quick_start/pricing",
        "note": "Token Official Price 来源之一。",
    },
    {
        "id": 6,
        "tier": "官方",
        "title": "阿里云百炼模型价格",
        "url": "https://help.aliyun.com/zh/model-studio/model-pricing",
        "note": "Token Official Price 来源之一。",
    },
    {
        "id": 7,
        "tier": "海外云价",
        "title": "RunPod GPU Cloud Pricing",
        "url": "https://www.runpod.io/pricing",
        "note": "可抓取 B300、B200、H200、H100、A100、L40S、RTX 5090、L4 等 GPU 小时价。",
    },
    {
        "id": 8,
        "tier": "海外云价",
        "title": "Lambda AI Cloud Pricing",
        "url": "https://lambda.ai/pricing",
        "note": "可抓取 B200、H100、A100 以及 1-Click Cluster 的 B200/H100 多 GPU 价格。",
    },
    {
        "id": 9,
        "tier": "海外云价/Marketplace",
        "title": "Vast.ai GPU Pricing",
        "url": "https://vast.ai/pricing",
        "note": "可抓取 p25、median、p90 等 Marketplace 实时价格分布，用于 Source Consensus。",
    },
    {
        "id": 10,
        "tier": "采购/整机辅助",
        "title": "BIZON ZX9000 GPU Server",
        "url": "https://bizon-tech.com/bizon-zx9000.html",
        "note": "可抓取 2 卡工作站/服务器配置价，用于采购辅助，不直接进入 8 卡 HGX 主口径。",
    },
    {
        "id": 11,
        "tier": "官方规格",
        "title": "NVIDIA H200 GPU",
        "url": "https://www.nvidia.com/en-us/data-center/h200/",
        "note": "用于确认 H200 SXM/NVL 规格、显存、服务器形态，不提供采购成交价。",
    },
    {
        "id": 12,
        "tier": "采购/招投标",
        "title": "中国政府采购网",
        "url": "http://www.ccgp.gov.cn/",
        "note": "用于检索 8卡 AI 训练/推理服务器中标公告和采购价。",
    },
    {
        "id": 13,
        "tier": "海外云价/聚合源",
        "title": "Cloud-GPUs.com",
        "url": "https://cloud-gpus.com/",
        "note": "覆盖 30+ providers、75+ GPU models、5000+ instance configurations，适合补齐海外 GPU Cloud 覆盖率和中位价。",
    },
    {
        "id": 14,
        "tier": "海外云价/聚合源",
        "title": "GPUCloudPricing",
        "url": "https://www.gpucloudpricing.com/",
        "note": "提供 GPU 云厂商特性和价格横向对比，适合作为 RunPod、Vast.ai、Novita、Salad 等平台的辅助参考。",
    },
    {
        "id": 15,
        "tier": "Token 市场价/性价比",
        "title": "llmpricing",
        "url": "https://sanand0.github.io/llmpricing/",
        "note": "提供 LLM 输入价格与 LMSYS/LMArena Elo 的性价比视图，适合做 Token 市场参考，不替代官方价。",
    },
    {
        "id": 16,
        "tier": "Token 市场价/辅助矩阵",
        "title": "morph-llm LLM Cost Calculator",
        "url": "https://www.morphllm.com/llm-cost-calculator",
        "note": "可作为模型价格、上下文窗口和限流信息的辅助源，需标注为 Market / Reference。",
    },
]

GPU_GROUPS = [
    ("Training", ["GB300", "GB200", "B300", "B200", "H200", "H100 80G", "H800", "H20", "A100 80G", "A800"]),
    ("Inference", ["L40S", "L20", "L4"]),
    ("Consumer", ["RTX 5090", "RTX 4090"]),
    ("国产", ["昇腾 910C", "昇腾 910B", "寒武纪 MLU", "海光 DCU", "壁仞", "摩尔线程"]),
]
GPU_ORDER = [gpu for _, items in GPU_GROUPS for gpu in items]
GPU_CLASS = {gpu: group for group, items in GPU_GROUPS for gpu in items}


def cny_from_usd(v: float | None) -> float | None:
    return None if v is None else round(v * FX_USD_CNY, 2)


def fmt(v, suffix: str = "") -> str:
    if v is None:
        return "暂不可得"
    if isinstance(v, float):
        if abs(v) >= 10000:
            return f"{v:,.0f}{suffix}"
        return f"{v:,.2f}{suffix}".rstrip("0").rstrip(".")
    if isinstance(v, int):
        return f"{v:,}{suffix}"
    return f"{v}{suffix}"


def pass_status(row: dict) -> bool:
    return row.get("校验状态") == "PASS" and (row.get("Confidence Score") or 0) >= 70


def monthly_wan_to_hourly_cny(monthly_wan: float | None) -> float | None:
    if monthly_wan is None:
        return None
    return round(monthly_wan * 10000 / 8 / 24 / 30, 2)


TOKEN_DATA = [
    {
        "厂商": "OpenAI",
        "模型": "GPT-5.5",
        "国家/地区": "海外",
        "输入官方价（原币/百万Token）": "USD 5.00",
        "输出官方价（原币/百万Token）": "USD 30.00",
        "输入官方价（人民币/百万Token）": cny_from_usd(5.0),
        "输出官方价（人民币/百万Token）": cny_from_usd(30.0),
        "官方来源": "cite-4",
        "市场来源": "OpenRouter/替代市场待抓取",
        "采集时间": STAMP,
        "Confidence Score": 95,
        "校验状态": "PASS",
        "备注": "OpenAI 官方价格页；缓存输入价单列，不混入标准输入价。",
    },
    {
        "厂商": "OpenAI",
        "模型": "GPT-5.4 mini",
        "国家/地区": "海外",
        "输入官方价（原币/百万Token）": "USD 0.75",
        "输出官方价（原币/百万Token）": "USD 4.50",
        "输入官方价（人民币/百万Token）": cny_from_usd(0.75),
        "输出官方价（人民币/百万Token）": cny_from_usd(4.5),
        "官方来源": "cite-4",
        "市场来源": "OpenRouter/替代市场待抓取",
        "采集时间": STAMP,
        "Confidence Score": 95,
        "校验状态": "PASS",
        "备注": "OpenAI 官方价格页。",
    },
    {
        "厂商": "DeepSeek",
        "模型": "deepseek-v4-flash",
        "国家/地区": "国产",
        "输入官方价（原币/百万Token）": "USD 0.14（Cache Miss）",
        "输出官方价（原币/百万Token）": "USD 0.28",
        "输入官方价（人民币/百万Token）": cny_from_usd(0.14),
        "输出官方价（人民币/百万Token）": cny_from_usd(0.28),
        "官方来源": "cite-5",
        "市场来源": "OpenRouter/替代市场待抓取",
        "采集时间": STAMP,
        "Confidence Score": 95,
        "校验状态": "PASS",
        "备注": "DeepSeek 官方页；Cache Hit 另列，不替代标准输入价。",
    },
    {
        "厂商": "阿里云/通义千问",
        "模型": "qwen3.7-max",
        "国家/地区": "国产",
        "输入官方价（原币/百万Token）": "CNY 12",
        "输出官方价（原币/百万Token）": "CNY 36",
        "输入官方价（人民币/百万Token）": 12.0,
        "输出官方价（人民币/百万Token）": 36.0,
        "官方来源": "cite-6",
        "市场来源": "OpenRouter/替代市场待抓取",
        "采集时间": STAMP,
        "Confidence Score": 95,
        "校验状态": "PASS",
        "备注": "阿里云百炼官方标准价，限时折扣另列不混入标准价。",
    },
    {
        "厂商": "阿里云/通义千问",
        "模型": "qwen-plus-latest",
        "国家/地区": "国产",
        "输入官方价（原币/百万Token）": "CNY 0.8",
        "输出官方价（原币/百万Token）": "CNY 2",
        "输入官方价（人民币/百万Token）": 0.8,
        "输出官方价（人民币/百万Token）": 2.0,
        "官方来源": "cite-6",
        "市场来源": "OpenRouter/替代市场待抓取",
        "采集时间": STAMP,
        "Confidence Score": 95,
        "校验状态": "PASS",
        "备注": "阿里云百炼官方标准价。",
    },
]

DOMESTIC_RENTAL_INPUT = {
    "H100 80G": {
        "original": "SMM 样本：约 7.5-8.0 万元/8卡整机/月",
        "monthly_wan": 7.6,
        "source": "SMM（主口径）",
        "confidence": 98,
        "consensus": "High",
        "historical": "HIST_INSUFFICIENT",
        "status": "PASS",
        "note": "符合国内 8卡 HGX 整机月租口径；等效单卡小时价仅由月租反推。",
    },
    "RTX 5090": {
        "original": "SMM 样本：约 1.2 万元/8卡整机/月",
        "monthly_wan": 1.2,
        "source": "SMM（主口径）",
        "confidence": 75,
        "consensus": "Medium",
        "historical": "HIST_INSUFFICIENT",
        "status": "PASS",
        "note": "消费级多卡整机口径，进入辅助指数，不与 HGX 训练卡混为同一价格层级。",
    },
    "A100 80G": {
        "original": "旧样本：约 1.3 万元/月，口径疑似非 A100 80G 8卡 HGX",
        "monthly_wan": None,
        "source": "待复核",
        "confidence": 55,
        "consensus": "Low",
        "historical": "HIST_INSUFFICIENT",
        "status": "REJECT",
        "note": "低于 A100 80G 国内合理区间，口径不明，不进入主图和利润测算。",
    },
    "H800": {
        "original": "旧估算：58 元/卡/小时",
        "monthly_wan": None,
        "source": "估算/待复核",
        "confidence": 55,
        "consensus": "Low",
        "historical": "HIST_INSUFFICIENT",
        "status": "REJECT",
        "note": "旧脚本把估算小时价误混入国内租赁主口径，已剔除。",
    },
}

OVERSEAS_HOURLY_USD = {
    "B300": (7.39, 85, "Medium", "RunPod 官方公开价，Vast.ai median 约 6.30 美元/小时作辅助。"),
    "B200": (6.69, 90, "High", "Lambda 官方 B200 8x 实例价；RunPod 5.89、Vast.ai median 4.99 作共识校验。"),
    "H200": (4.39, 90, "High", "RunPod 官方 H200 价格；Vast.ai median 3.79、Lambda cluster 4.31 作共识校验。"),
    "H100 80G": (2.99, 90, "High", "RunPod H100 SXM 价格；Lambda H100 SXM 3.99、Vast.ai H100 SXM median 2.23 作共识校验。"),
    "A100 80G": (1.49, 85, "Medium", "RunPod A100 SXM 80GB 价格；Lambda A100 SXM 2.79 作辅助。"),
    "L40S": (0.99, 85, "Medium", "RunPod 官方 L40S 价格。"),
    "RTX 5090": (0.99, 80, "Medium", "RunPod 官方 RTX 5090 价格；Vast.ai median 0.49 显示 marketplace 低价。"),
    "RTX 4090": (0.69, 80, "Medium", "RunPod 官方 RTX 4090 价格；Vast.ai median 0.39 作辅助。"),
    "L4": (0.39, 85, "Medium", "RunPod 官方 L4 价格。"),
}


def domestic_rows() -> list[dict]:
    rows = []
    for idx, gpu in enumerate(GPU_ORDER, 1):
        item = DOMESTIC_RENTAL_INPUT.get(gpu)
        if item:
            monthly = item["monthly_wan"]
            hourly = monthly_wan_to_hourly_cny(monthly)
            status = item["status"]
            conf = item["confidence"]
            reason = "" if status == "PASS" else item["note"]
        else:
            monthly = None
            hourly = None
            status = "REVIEW"
            conf = 50
            reason = "当日未获得符合国内主口径的可信样本。"
            item = {
                "original": "暂不可得",
                "source": "未采集到合格来源",
                "consensus": "Low",
                "historical": "HIST_INSUFFICIENT",
                "note": reason,
            }
        rows.append({
            "GPU 型号": gpu,
            "GPU 分类": GPU_CLASS[gpu],
            "热度排序": idx,
            "地区/市场": "中国大陆",
            "category": "GPU_RENT_CN",
            "主数据源": item["source"],
            "原始价格": item["original"],
            "标准化价格": None if monthly is None else monthly,
            "标准化单位": "万元/8卡整机/月",
            "等效单卡小时价（人民币）": hourly,
            "Confidence Score": conf,
            "Source Consensus": item["consensus"],
            "Historical Validation": item["historical"],
            "校验状态": status,
            "是否进入主指数": "是" if status == "PASS" and conf >= 70 else "否",
            "Reject/Review 原因": reason,
            "口径说明": item["note"],
        })
    return rows


def overseas_rows() -> list[dict]:
    rows = []
    for idx, gpu in enumerate(GPU_ORDER, 1):
        item = OVERSEAS_HOURLY_USD.get(gpu)
        if item:
            usd, conf, consensus, note = item
            cny = cny_from_usd(usd)
            monthly_ref = round(cny * 8 * 24 * 30 / 10000, 2)
            status = "PASS" if conf >= 70 else "REVIEW"
        else:
            usd = cny = monthly_ref = None
            conf = 50
            consensus = "Low"
            note = "海外公开小时价暂不可得。"
            status = "REVIEW"
        rows.append({
            "GPU 型号": gpu,
            "GPU 分类": GPU_CLASS[gpu],
            "热度排序": idx,
            "地区/市场": "海外",
            "category": "GPU_CLOUD",
            "主数据源": "ComputeStacker/Lambda/RunPod 辅助",
            "原始价格": None if usd is None else f"USD {usd}/卡/小时",
            "标准化价格": cny,
            "标准化单位": "人民币/卡/小时",
            "等效8卡月租（万元，仅参考）": monthly_ref,
            "Confidence Score": conf,
            "Source Consensus": consensus,
            "校验状态": status,
            "备注": "仅供海外 GPU Cloud 参考，不进入国内租赁指数。" if cny is not None else note,
        })
    return rows


DOMESTIC_RENTAL = domestic_rows()
OVERSEAS_RENTAL = overseas_rows()

PROCUREMENT = [
    {"GPU 型号": "H200", "GPU 分类": "Training", "采购成本口径": "BIZON 2卡水冷配置价", "8卡整机参考价": "不可直接折算；2x H200 NVL 加价 USD 99,000", "Confidence Score": 70, "校验状态": "AUXILIARY", "备注": "采购辅助报价，非 8卡 HGX 成交价，不进入 ROI。"},
    {"GPU 型号": "H100 80G", "GPU 分类": "Training", "采购成本口径": "BIZON 2卡水冷配置价 + 国内招投标待补", "8卡整机参考价": "不可直接折算；2x H100 NVL 加价 USD 79,500", "Confidence Score": 70, "校验状态": "AUXILIARY", "备注": "采购辅助报价，需与国内招投标/整机渠道交叉。"},
    {"GPU 型号": "A100 80G", "GPU 分类": "Training", "采购成本口径": "BIZON 2卡水冷配置价", "8卡整机参考价": "不可直接折算；2x A100 80GB 加价 USD 55,726", "Confidence Score": 70, "校验状态": "AUXILIARY", "备注": "采购辅助报价，非国内 8卡 HGX 主口径。"},
    {"GPU 型号": "8卡 AI 服务器", "GPU 分类": "Training", "采购成本口径": "中国政府采购网/高校招投标", "8卡整机参考价": "需按中标公告逐条解析", "Confidence Score": 85, "校验状态": "CANDIDATE", "备注": "招投标可提高采购价覆盖率，但需解析具体 GPU 型号和数量。"},
    {"GPU 型号": "RTX 5090", "GPU 分类": "Consumer", "采购成本口径": "公开渠道/电商/整机厂商待补", "8卡整机参考价": "需补采", "Confidence Score": 55, "校验状态": "CANDIDATE", "备注": "消费级价格波动大，必须单独标注渠道和税费。"},
]


def profit_rows() -> list[dict]:
    rows = []
    domestic = {r["GPU 型号"]: r for r in DOMESTIC_RENTAL if pass_status(r)}
    for p in PROCUREMENT:
        gpu = p["GPU 型号"]
        rent = domestic.get(gpu)
        if not rent or p["校验状态"] != "PASS":
            rows.append({
                "GPU 型号": gpu,
                "租赁数据状态": rent["校验状态"] if rent else "无 PASS 租赁价",
                "采购数据状态": p["校验状态"],
                "是否进入 ROI": "否",
                "结论": "采购价或租赁价未完全通过校验，仅保留为观察项。",
            })
    return rows


GPU_PROFIT = profit_rows()


AUDIT = []
REJECTED = []


def build_audit():
    for row in DOMESTIC_RENTAL:
        record = {
            "date": DATE,
            "freeze_time": FREEZE_TIME,
            "asset_type": "GPU_RENT_CN",
            "gpu_or_model": row["GPU 型号"],
            "source": row["主数据源"],
            "original_price": row["原始价格"],
            "category": row["category"],
            "normalized_price": row["标准化价格"],
            "normalized_unit": row["标准化单位"],
            "formula": "国内主口径直接采用万元/8卡整机/月；等效单卡小时价=月租×10000÷8÷24÷30",
            "confidence": row["Confidence Score"],
            "consensus": row["Source Consensus"],
            "historical_validation": row["Historical Validation"],
            "validate_status": row["校验状态"],
            "included_in_index": row["是否进入主指数"] == "是",
            "reject_reason": row["Reject/Review 原因"],
            "notes": row["口径说明"],
        }
        AUDIT.append(record)
        if row["校验状态"] != "PASS":
            REJECTED.append(record)


build_audit()

SNAPSHOT = {
    "date": DATE,
    "freeze_time": FREEZE_TIME,
    "report_version": REPORT_VERSION,
    "prompt_version": PROMPT_VERSION,
    "fx": {"USD/CNY": FX_USD_CNY},
    "sources": SOURCES,
    "token_prices": TOKEN_DATA,
    "domestic_rental": DOMESTIC_RENTAL,
    "overseas_rental": OVERSEAS_RENTAL,
    "gpu_procurement": PROCUREMENT,
    "gpu_profit": GPU_PROFIT,
    "audit": AUDIT,
    "rejected": REJECTED,
}


def coverage_rows() -> list[dict]:
    covered = []
    domestic_pass = {r["GPU 型号"] for r in DOMESTIC_RENTAL if pass_status(r)}
    domestic_aux = {r["GPU 型号"] for r in DOMESTIC_RENTAL if not pass_status(r) and r["校验状态"] in {"REVIEW", "REJECT"}}
    overseas_aux = {r["GPU 型号"] for r in OVERSEAS_RENTAL if r["标准化价格"] is not None}
    procurement_aux = {r["GPU 型号"] for r in PROCUREMENT}
    for gpu in GPU_ORDER:
        layers = []
        if gpu in domestic_pass:
            layers.append("Main Index")
        if gpu in overseas_aux:
            layers.append("Overseas Auxiliary")
        if gpu in procurement_aux:
            layers.append("Procurement Auxiliary")
        if gpu in domestic_aux:
            layers.append("Domestic Candidate/Rejected")
        if not layers:
            layers.append("Missing with searched sources")
        covered.append({
            "GPU 型号": gpu,
            "GPU 分类": GPU_CLASS[gpu],
            "覆盖状态": " / ".join(layers),
            "是否可进入主指数": "是" if gpu in domestic_pass else "否",
            "下一步": "继续补国内主口径" if gpu not in domestic_pass else "持续监控历史波动",
        })
    return covered


COVERAGE = coverage_rows()
SNAPSHOT["coverage"] = COVERAGE


def html_escape(x) -> str:
    if x is None:
        return '<span class="missing">暂不可得</span>'
    return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def table(rows: list[dict], cols: list[str] | None = None) -> str:
    if not rows:
        return "<p>暂无数据。</p>"
    cols = cols or list(rows[0].keys())
    trs = []
    for row in rows:
        cells = []
        for col in cols:
            value = row.get(col)
            cells.append(f"<td>{html_escape(fmt(value) if isinstance(value, (int, float)) else value)}</td>")
        trs.append("<tr>" + "".join(cells) + "</tr>")
    return (
        '<div class="table-wrap"><table><thead><tr>'
        + "".join(f"<th>{html_escape(c)}</th>" for c in cols)
        + "</tr></thead><tbody>"
        + "\n".join(trs)
        + "</tbody></table></div>"
    )


def source_list() -> str:
    return "\n".join(
        f'<li id="cite-{s["id"]}"><b>[{s["tier"]}] {html_escape(s["title"])}</b><br>'
        f'<a href="{s["url"]}" target="_blank" rel="noopener">{s["url"]}</a><br>'
        f'<span>{html_escape(s["note"])}</span></li>'
        for s in SOURCES
    )


def main_metrics() -> list[tuple[str, str, str]]:
    pass_dom = [r for r in DOMESTIC_RENTAL if pass_status(r)]
    rejected = [r for r in DOMESTIC_RENTAL if r["校验状态"] == "REJECT"]
    aux_gpu = {r["GPU 型号"] for r in OVERSEAS_RENTAL if r["标准化价格"] is not None} | {r["GPU 型号"] for r in PROCUREMENT}
    token_pass = [r for r in TOKEN_DATA if r["校验状态"] == "PASS"]
    h100 = next((r for r in pass_dom if r["GPU 型号"] == "H100 80G"), None)
    return [
        ("国内主指数样本", f"{len(pass_dom)}/{len(DOMESTIC_RENTAL)}", "仅 PASS 且 Confidence≥70"),
        ("辅助 GPU 样本", f"{len(aux_gpu)}/{len(GPU_ORDER)}", "海外云价/采购价/候选样本"),
        ("Token 官方价", f"{len(token_pass)}/{len(TOKEN_DATA)}", "官方页可追溯"),
        ("H100 国内月租", "7.6 万元" if h100 else "暂不可得", "8卡整机/月，不再重复折算"),
    ]


def render_html(relative_prefix: str = "./") -> str:
    cards = "\n".join(
        f'<article class="metric"><span>{a}</span><strong>{b}</strong><small>{c}</small></article>'
        for a, b, c in main_metrics()
    )
    domestic_pass = [r for r in DOMESTIC_RENTAL if pass_status(r)]
    domestic_review = [r for r in DOMESTIC_RENTAL if not pass_status(r)]
    overseas_pass = [r for r in OVERSEAS_RENTAL if r["校验状态"] == "PASS"]
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>全球算力市场情报日报（CMIS Daily） - {DATE}</title>
  <style>
    :root {{--bg:#07111f;--bg2:#101b2d;--ink:#ecf4ff;--muted:#9eb0c7;--rule:#23344f;--accent:#68e1fd;--accent2:#f7c76b;--bad:#ff7a90;--good:#74e0a3;}}
    *{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at 18% 0%,rgba(104,225,253,.18),transparent 34%),var(--bg);color:var(--ink);font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.7}}
    a{{color:var(--accent);text-decoration:none}} .page{{width:min(1280px,94vw);margin:0 auto;padding:32px 0 70px}}
    header{{padding:50px 0 26px;border-bottom:1px solid var(--rule)}} .eyebrow{{color:var(--accent2);font-size:12px;letter-spacing:.1em;text-transform:uppercase}}
    h1{{font-size:clamp(34px,6vw,76px);line-height:1.02;margin:12px 0;letter-spacing:-.04em}} h2{{margin-top:50px;border-left:4px solid var(--accent);padding-left:14px}}
    .note,.muted{{color:var(--muted)}} .grid{{display:grid;gap:16px}} .metrics{{grid-template-columns:repeat(4,1fr);margin:28px 0}}
    .metric,.panel,figure{{background:linear-gradient(180deg,rgba(255,255,255,.05),rgba(255,255,255,.015));border:1px solid var(--rule);border-radius:18px;padding:18px;box-shadow:0 20px 50px rgba(0,0,0,.22)}}
    .metric span,.metric small{{display:block;color:var(--muted)}} .metric strong{{display:block;font-size:30px;color:var(--accent);margin:8px 0}}
    .status-pass{{color:var(--good)}} .status-reject{{color:var(--bad)}} .missing{{color:var(--bad);font-weight:700}}
    .table-wrap{{overflow:auto;max-height:640px;border:1px solid var(--rule);border-radius:16px;background:rgba(255,255,255,.025);margin:16px 0 26px}}
    table{{width:100%;min-width:1180px;border-collapse:collapse;font-size:13px}} th,td{{padding:10px 12px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top}}
    th{{position:sticky;top:0;background:#12213a;color:var(--accent2);z-index:1}} .chart{{width:100%;min-height:420px}} footer{{margin-top:60px;padding-top:28px;border-top:1px solid var(--rule)}}
    @media(max-width:900px){{.metrics{{grid-template-columns:1fr}} .page{{width:min(94vw,760px)}} table{{min-width:980px}}}}
  </style>
</head>
<body>
  <main class="page">
    <header>
      <div class="eyebrow">Compute Market Intelligence System · CMIS Daily</div>
      <h1>全球算力市场情报日报</h1>
      <p class="note">日期：{DATE}｜Data Freeze：{FREEZE_LABEL}｜Report Version：{REPORT_VERSION}｜Prompt Version：{PROMPT_VERSION}。本页已按最新数据治理规范重生成，国内租赁主口径为“万元/8卡整机/月”。</p>
      <section class="metrics grid">{cards}</section>
    </header>

    <section>
      <h2>今日结论</h2>
      <div class="panel">
        <p>本版采用“主指数严格、情报覆盖充分”的结构：国内主指数只收通过校验的 8卡整机月租；海外 GPU Cloud、采购价、招投标、整机渠道报价进入辅助模块，不再被错误混入国内主指数。</p>
        <p>H800 当前没有通过国内主口径校验，因此不进入国内主指数；但它仍保留在覆盖率诊断和缺口清单中，后续通过云厂商、招投标、渠道报价继续补采。</p>
      </div>
    </section>

    <section id="coverage">
      <h2>覆盖率诊断</h2>
      <p class="note">覆盖不等于进入主指数。每张卡至少应有 Main Index、Auxiliary、Candidate、Rejected 或 Missing 状态，避免治理后报告变空。</p>
      {table(COVERAGE)}
    </section>

    <section id="domestic">
      <h2>国内算力租赁主指数</h2>
      <p class="note">只纳入 Validate == PASS 且 Confidence Score ≥ 70 的国内 8卡整机月租样本。</p>
      <figure><div id="chart-domestic-main" class="chart"></div></figure>
      {table(domestic_pass)}
    </section>

    <section id="audit">
      <h2>Rejected / Review 样本</h2>
      <p class="note">以下数据不进入主图、主指数、ROI、历史结论或 AI 总结，只用于审计追踪。</p>
      {table(domestic_review)}
    </section>

    <section id="overseas">
      <h2>海外 GPU Cloud 参考</h2>
      <p class="note">海外口径为人民币/卡/小时；等效 8卡月租只作参考，不进入国内租赁指数。</p>
      <figure><div id="chart-overseas" class="chart"></div></figure>
      {table(overseas_pass)}
    </section>

    <section id="token">
      <h2>Token 价格</h2>
      <p class="note">Token 官方价来自厂商官方价格页，市场价后续由 OpenRouter / Artificial Analysis 等补充，官方价和市场价分列展示。</p>
      {table(TOKEN_DATA)}
    </section>

    <section id="profit">
      <h2>利润测算</h2>
      <p class="note">利润测算必须同时满足租赁价格和采购价格通过校验。本期采购价未完成多源校验，因此 ROI 不生成方向性结论。</p>
      {table(GPU_PROFIT)}
    </section>

    <section id="sources">
      <h2>数据源与口径</h2>
      <ol>{source_list()}</ol>
    </section>

    <section id="ai-summary">
      <h2>AI 总结</h2>
      <div class="panel">
        <p>本期可进入结论的数据非常有限：H100 80G 国内 8卡整机月租约 7.6 万元，RTX 5090 多卡整机约 1.2 万元/月。其余国内卡型因口径、可信度或来源共识不足，只保留为 Review / Rejected 样本。当前不能据此判断 H800 或其它卡型存在夸张的国内外倍数差。</p>
      </div>
    </section>

    <footer>
      <p class="muted">CMIS Daily {REPORT_VERSION} | Prompt {PROMPT_VERSION} | Freeze {FREEZE_LABEL}</p>
    </footer>
  </main>
  <script src="{relative_prefix}_shared/js/echarts.min.js"></script>
  <script src="{relative_prefix}assets/charts.js?v={DATE.replace('-', '')}"></script>
</body>
</html>"""


def write_charts():
    domestic_pass = [r for r in DOMESTIC_RENTAL if pass_status(r)]
    overseas_pass = [r for r in OVERSEAS_RENTAL if r["校验状态"] == "PASS"]
    data = {
        "domesticLabels": [r["GPU 型号"] for r in domestic_pass],
        "domesticValues": [r["标准化价格"] for r in domestic_pass],
        "overseasLabels": [r["GPU 型号"] for r in overseas_pass],
        "overseasValues": [r["标准化价格"] for r in overseas_pass],
    }
    js = f"""(function(){{
  var DATA = {json.dumps(data, ensure_ascii=False)};
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  function init(id, option) {{
    var el = document.getElementById(id);
    if (!el || !window.echarts) return;
    var c = echarts.init(el, null, {{renderer:'svg'}});
    c.setOption(option);
    window.addEventListener('resize', function(){{c.resize();}});
  }}
  function bar(id, labels, values, name, color) {{
    init(id, {{
      animation:false,
      color:[color],
      tooltip:{{trigger:'axis', appendToBody:true}},
      grid:{{left:70,right:40,top:44,bottom:80,containLabel:true}},
      xAxis:{{type:'category',data:labels,axisLabel:{{color:muted,interval:0}},axisLine:{{lineStyle:{{color:rule}}}},axisTick:{{show:false}}}},
      yAxis:{{type:'value',name:name,nameTextStyle:{{color:muted}},axisLabel:{{color:muted}},splitLine:{{lineStyle:{{color:rule}}}}}},
      series:[{{type:'bar',data:values,label:{{show:true,position:'top',color:ink}},itemStyle:{{borderRadius:[6,6,0,0]}}}}]
    }});
  }}
  bar('chart-domestic-main', DATA.domesticLabels, DATA.domesticValues, '万元/8卡整机/月', accent);
  bar('chart-overseas', DATA.overseasLabels, DATA.overseasValues, '人民币/卡/小时', accent2);
}})();"""
    (OUT / "assets" / "charts.js").write_text(js, encoding="utf-8")


def write_index():
    reports = sorted(
        [p for p in (OUT / "reports").glob("*.html") if len(p.stem) == 10 and p.stem[:4].isdigit()],
        reverse=True,
    )
    items = "\n".join(f'<li><a href="reports/{p.name}">{p.stem}</a></li>' for p in reports[:30])
    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>CMIS Daily</title><style>body{{font-family:system-ui;background:#07111f;color:#ecf4ff;line-height:1.7;margin:0}}main{{width:min(960px,92vw);margin:0 auto;padding:56px 0}}a{{color:#68e1fd}}.card{{border:1px solid #23344f;border-radius:18px;padding:20px;background:#101b2d;margin:18px 0}}</style></head><body><main><h1>全球算力市场情报门户</h1><div class="card"><p>最新报告：<a href="latest.html">latest.html</a></p><p>Data Freeze：{FREEZE_LABEL}｜Report Version：{REPORT_VERSION}｜Prompt Version：{PROMPT_VERSION}</p></div><h2>历史归档</h2><ul>{items}</ul></main></body></html>"""
    (OUT / "index.html").write_text(html, encoding="utf-8")


def main():
    for d in ["reports", "data", "assets", "_shared/js", "_shared/fonts"]:
        (OUT / d).mkdir(parents=True, exist_ok=True)
    (OUT / "data" / f"cmis_snapshot_{DATE}.json").write_text(json.dumps(SNAPSHOT, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "data" / f"audit_{DATE}.json").write_text(json.dumps(AUDIT, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "data" / f"rejected_{DATE}.json").write_text(json.dumps(REJECTED, ensure_ascii=False, indent=2), encoding="utf-8")
    history_path = OUT / "data" / "history.jsonl"
    rows = []
    if history_path.exists():
        for line in history_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("date") != DATE:
                rows.append(row)
    rows.append(SNAPSHOT)
    history_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    write_charts()
    (OUT / "latest.html").write_text(render_html("./"), encoding="utf-8")
    (OUT / "reports" / f"{DATE}.html").write_text(render_html("../"), encoding="utf-8")
    write_index()


if __name__ == "__main__":
    main()
