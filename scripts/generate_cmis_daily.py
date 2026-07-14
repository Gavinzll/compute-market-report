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
REPORT_VERSION = "v1.2.0"


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
    {
        "id": 17,
        "tier": "Token 结构化/开源",
        "title": "LiteLLM model_prices_and_context_window.json",
        "url": "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json",
        "note": "机器可读模型价格、上下文窗口和 provider 映射源；只作 Market / Structured Auxiliary，不替代官方价。",
    },
    {
        "id": 18,
        "tier": "Token 市场价/API",
        "title": "OpenRouter Models API",
        "url": "https://openrouter.ai/api/v1/models",
        "note": "机器可读模型、上下文和市场路由价格源；官方价缺失时只能标注为市场价。",
    },
    {
        "id": 19,
        "tier": "Token 结构化/目录",
        "title": "models.dev API",
        "url": "https://models.dev/api.json",
        "note": "多 provider 模型目录和价格结构化源，用于发现缺失模型和交叉校验。",
    },
    {
        "id": 20,
        "tier": "Token 结构化/辅助",
        "title": "BenchLM pricing JSON",
        "url": "https://www.benchlm.ai/data/pricing.json",
        "note": "模型价格矩阵辅助源，用于补充 Token 市场价和冲突审计。",
    },
    {
        "id": 21,
        "tier": "Token 性能/市场辅助",
        "title": "Artificial Analysis",
        "url": "https://artificialanalysis.ai/",
        "note": "可提供模型价格、速度、质量、上下文等市场对比信息；不替代官方价格页。",
    },
    {
        "id": 22,
        "tier": "海外云价/API",
        "title": "TensorDock Hostnodes API",
        "url": "https://dashboard.tensordock.com/api/docs/fetch-hostnodes",
        "note": "可抓取节点级 GPU price_per_hr、availableCount、vCPU/RAM/storage 单价，用于海外 GPU Cloud 辅助样本。",
    },
    {
        "id": 23,
        "tier": "海外云价",
        "title": "DataCrunch Pricing",
        "url": "https://datacrunch.io/pricing",
        "note": "可抓取海外 GPU 实例价、GPU 数和区域，用于 GPU_CLOUD 标准化。",
    },
    {
        "id": 24,
        "tier": "海外云价/Marketplace",
        "title": "CUDO Compute Pricing",
        "url": "https://www.cudocompute.com/pricing",
        "note": "GPU Marketplace 价格和可用性辅助源，进入海外 GPU Cloud 模块。",
    },
    {
        "id": 25,
        "tier": "海外云价/企业云",
        "title": "CoreWeave GPU Cloud",
        "url": "https://www.coreweave.com/products/gpu-cloud",
        "note": "企业 GPU 云产品源；公开价缺失时记录为 Price Missing，不推断。",
    },
    {
        "id": 26,
        "tier": "海外云价/官方",
        "title": "Nebius AI Cloud Prices",
        "url": "https://nebius.com/prices",
        "note": "海外 GPU 云实例价、区域和 GPU 数来源，用于 GPU_CLOUD 辅助校验。",
    },
    {
        "id": 27,
        "tier": "海外云价/官方",
        "title": "Oracle Cloud Infrastructure Price List",
        "url": "https://www.oracle.com/cloud/price-list/",
        "note": "OCI GPU 实例公开价；必须解析实例 GPU 数后再标准化。",
    },
    {
        "id": 28,
        "tier": "海外云价/Serverless",
        "title": "Modal Pricing",
        "url": "https://modal.com/pricing",
        "note": "Serverless GPU 价格源；按 GPU 秒/小时归类为海外辅助，不进入国内租赁指数。",
    },
    {
        "id": 29,
        "tier": "国内云价/辅助",
        "title": "阿里云 GPU 云服务器价格",
        "url": "https://www.aliyun.com/price/product?productCode=ecs",
        "note": "国内云厂商实例价，只进入 Auxiliary Quotes，不进入国内 8卡整机主指数。",
    },
    {
        "id": 30,
        "tier": "国内云价/辅助",
        "title": "腾讯云 GPU 云服务器",
        "url": "https://cloud.tencent.com/product/gpu",
        "note": "国内 GPU 云实例辅助源；包月、按量和竞价需分列。",
    },
    {
        "id": 31,
        "tier": "国内云价/辅助",
        "title": "华为云 GPU 加速型云服务器",
        "url": "https://www.huaweicloud.com/product/gpu.html",
        "note": "国内 GPU 云实例辅助源；不得直接进入国内租赁主口径。",
    },
    {
        "id": 32,
        "tier": "国内云价/辅助",
        "title": "AutoDL 价格",
        "url": "https://www.autodl.com/price",
        "note": "国内 GPU 租赁平台单卡/容器价，进入辅助样本和覆盖率诊断。",
    },
    {
        "id": 33,
        "tier": "国内云价/辅助",
        "title": "矩池云主机市场",
        "url": "https://matpool.com/host-market",
        "note": "国内 GPU 租赁平台市场价，作为辅助线索和候选样本。",
    },
    {
        "id": 34,
        "tier": "采购/招投标",
        "title": "高校采购与公共资源交易中心",
        "url": "https://www.ccgp.gov.cn/cggg/dfgg/",
        "note": "检索高校、科研院所和地方公共资源 AI 服务器中标公告，进入采购价或候选样本。",
    },
    {
        "id": 35,
        "tier": "官方规格/OEM",
        "title": "NVIDIA Data Center GPUs",
        "url": "https://www.nvidia.com/en-us/data-center/",
        "note": "用于 GPU 型号、显存、系统形态和生命周期校验，不提供成交价。",
    },
    {
        "id": 36,
        "tier": "整机规格/OEM",
        "title": "Supermicro GPU Systems",
        "url": "https://www.supermicro.com/en/products/gpu",
        "note": "用于确认 4卡/8卡/多卡服务器形态，价格需另行验证。",
    },
    {
        "id": 37,
        "tier": "采购/整机辅助",
        "title": "Exxact GPU Systems",
        "url": "https://www.exxactcorp.com/",
        "note": "整机配置价辅助源；需区分工作站、服务器、GPU 数和税费。",
    },
    {
        "id": 38,
        "tier": "采购/整机辅助",
        "title": "Thinkmate GPU Servers",
        "url": "https://www.thinkmate.com/",
        "note": "GPU 服务器配置价辅助源；单一渠道最多进入 Auxiliary 或 Candidate。",
    },
    {
        "id": 39,
        "tier": "国内租赁/SMM 深扒",
        "title": "SMM 算力金属直播",
        "url": "https://news.smm.cn/live/metal/143",
        "note": "国内服务器租赁价格深扒主入口，需按近 7 日快讯抽取 H100/H200/H20/A100/4090/5090/昇腾等价格和供需信号。",
    },
    {
        "id": 40,
        "tier": "国内租赁/SMM 移动页",
        "title": "SMM 移动详情页：H100/A100/5090 月租",
        "url": "https://m.smm.cn/news/detail/103972174",
        "note": "SMM 原文移动页，用于校验 H100 7.6 万、A100 40G 1.3 万、八卡 5090 1.2 万/月等原始样本。",
    },
    {
        "id": 41,
        "tier": "国内租赁/SMM 镜像",
        "title": "SMM news.metal.com 镜像：H100/A100/5090 月租",
        "url": "https://news.metal.com/about-us.html/newscontent/103972175-smm-computing-power-flash-an-intelligent-computing-company-quoted-monthly-rental-prices-for-multiple-gpu-models-includin",
        "note": "SMM 多语言镜像，用于补全文本和跨页面校验，不作为独立来源重复计数。",
    },
    {
        "id": 42,
        "tier": "国内租赁/门户线索",
        "title": "GoGPU / 捷智算 H100 租赁线索",
        "url": "https://gogpu.cn/news/detail/596.html",
        "note": "国内 H100 服务器租赁价格线索，仅进入 Candidate / Lead，需与 SMM/IDC/运营商交叉验证。",
    },
    {
        "id": 43,
        "tier": "国内租赁/门户线索",
        "title": "墨天轮 H100 租用榜单",
        "url": "https://www.modb.pro/db/2068888499013640192",
        "note": "H100 租赁榜单和平台特性线索，低置信辅助，不进入主指数。",
    },
    {
        "id": 44,
        "tier": "国内租赁/个人站线索",
        "title": "OmniYQ GPU 算力租赁平台",
        "url": "https://www.omniyq.com/",
        "note": "国内外裸金属八卡机报价线索，作为 Candidate / Lead 保存，需逐条复核。",
    },
    {
        "id": 45,
        "tier": "国内租赁/自媒体线索",
        "title": "东方财富财富号 GPU 租金走势线索",
        "url": "https://caifuhao.eastmoney.com/news/1739405719",
        "note": "自媒体价格走势线索，仅用于发现缺口和候选样本，不进入主指数或 AI 总结。",
    },
    {
        "id": 46,
        "tier": "Token 官方/国产",
        "title": "腾讯混元生文计费概述",
        "url": "https://cloud.tencent.com/document/product/1729/97731",
        "note": "腾讯混元官方 Token 计费来源，需抓取 Hunyuan-a13b、Hunyuan-role-latest 等模型。",
    },
    {
        "id": 47,
        "tier": "Token 官方/国产",
        "title": "火山方舟模型服务价格",
        "url": "https://www.volcengine.com/docs/82379/1099320",
        "note": "豆包、火山方舟和部分托管模型官方价格来源，需按输入长度区间分列。",
    },
    {
        "id": 48,
        "tier": "Token 官方/国产",
        "title": "Kimi / Moonshot 模型推理定价",
        "url": "https://platform.kimi.com/docs/pricing/chat",
        "note": "Kimi K2.7 Code、Kimi K2.6、Moonshot V1 等官方价格来源。",
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


def token_row(
    vendor: str,
    model: str,
    region: str,
    context: str,
    official_in: float | None,
    official_out: float | None,
    official_currency: str,
    official_source: str,
    market_in_usd: float | None,
    market_out_usd: float | None,
    market_source: str,
    note: str,
    status: str = "PASS",
    confidence: int = 90,
) -> dict:
    if isinstance(status, int):
        confidence = status
        status = "PASS"
    market_in_cny = cny_from_usd(market_in_usd) if market_in_usd is not None else None
    market_out_cny = cny_from_usd(market_out_usd) if market_out_usd is not None else None
    if official_in is not None and market_in_cny is not None:
        diff = round(official_in - market_in_cny, 2)
    else:
        diff = None
    return {
        "厂商": vendor,
        "模型": model,
        "国家/地区": region,
        "上下文上限": context,
        "输入官方价（原币/百万Token）": None if official_in is None else f"{official_currency} {official_in}",
        "输出官方价（原币/百万Token）": None if official_out is None else f"{official_currency} {official_out}",
        "输入官方价（人民币/百万Token）": official_in if official_currency == "CNY" else cny_from_usd(official_in),
        "输出官方价（人民币/百万Token）": official_out if official_currency == "CNY" else cny_from_usd(official_out),
        "OpenRouter/替代市场输入价": None if market_in_usd is None else f"USD {market_in_usd}/百万Token（约 ¥{market_in_cny}）",
        "OpenRouter/替代市场输出价": None if market_out_usd is None else f"USD {market_out_usd}/百万Token（约 ¥{market_out_cny}）",
        "官方-市场价差": None if diff is None else f"{diff} 元/百万Token（输入）",
        "较昨日变化": "待历史库累计",
        "官方来源": official_source,
        "市场来源": market_source,
        "采集时间": STAMP,
        "Confidence Score": confidence,
        "校验状态": status,
        "备注": note,
    }


TOKEN_DATA = [
    token_row("OpenAI", "gpt-5", "海外", "400K", 1.25, 10.0, "USD", "cite-4", 1.25, 10.0, "models.dev / OpenRouter", "主流 GPT 模型，官方价与三方市场价分列。", 95),
    token_row("OpenAI", "gpt-5-mini", "海外", "128K", 0.25, 2.0, "USD", "cite-4", 0.25, 2.0, "models.dev / LiteLLM", "低成本 GPT 模型。", 95),
    token_row("Anthropic", "claude-sonnet-5", "海外", "1M", 2.0, 10.0, "USD", "Anthropic 官方价格页待补采", 2.0, 10.0, "OpenRouter Models API", "官方页需补采；市场价来自 OpenRouter。", "OFFICIAL_REVIEW", 78),
    token_row("Google", "gemini-2.5-pro", "海外", "1M", 1.25, 10.0, "USD", "Google Gemini API Pricing", 1.25, 10.0, "models.dev", "主流 Gemini Pro 模型。", 90),
    token_row("DeepSeek", "deepseek-v4-flash", "国产", "1M", 1.0, 2.0, "CNY", "cite-5", None, None, "OpenRouter / LiteLLM 待匹配", "官方价已从 DeepSeek 价格页抓取；Cache Hit 另列不混入标准输入价。", 95),
    token_row("DeepSeek", "deepseek-v4-pro", "国产", "1M", 3.0, 6.0, "CNY", "cite-5", None, None, "OpenRouter / LiteLLM 待匹配", "官方价已从 DeepSeek 价格页抓取。", 95),
    token_row("阿里云/通义千问", "qwen3.7-max", "国产", "1M", 12.0, 36.0, "CNY", "cite-6", None, None, "OpenRouter / models.dev 待匹配", "阿里云百炼官方原价；限时折扣另列不混入标准价。", 95),
    token_row("阿里云/通义千问", "qwen-plus-latest", "国产", "128K-1M", 0.8, 2.0, "CNY", "cite-6", None, None, "OpenRouter / models.dev 待匹配", "取中国内地 0-128K 非思考模式官方价。", 95),
    token_row("火山方舟/豆包", "doubao-seed-1.6", "国产", "按输入长度分档", 0.8, 2.0, "CNY", "cite-47", None, None, "OpenRouter / LiteLLM 待匹配", "取 0-32K 且短输出在线推理官方价；长上下文需分档展示。", 95),
    token_row("火山方舟/豆包", "doubao-seed-1.6-flash", "国产", "按输入长度分档", 0.15, 1.5, "CNY", "cite-47", None, None, "OpenRouter / LiteLLM 待匹配", "取 0-32K 在线推理官方价。", 95),
    token_row("腾讯混元", "Hunyuan-a13b", "国产", "官方页未列上下文", 0.5, 2.0, "CNY", "cite-46", None, None, "OpenRouter / LiteLLM 待匹配", "腾讯混元官方后付费 Token 价格。", 95),
    token_row("腾讯混元", "Hunyuan-role-latest", "国产", "官方页未列上下文", 2.4, 9.6, "CNY", "cite-46", None, None, "OpenRouter / LiteLLM 待匹配", "腾讯混元官方后付费 Token 价格。", 95),
    token_row("Kimi / Moonshot", "kimi-k2.7-code", "国产", "262K", 6.5, 27.0, "CNY", "cite-48", 0.74, 3.5, "OpenRouter Models API", "Kimi 官方未命中缓存输入价；市场价来自 OpenRouter Kimi K2.7 Code。", 95),
    token_row("Kimi / Moonshot", "kimi-k2.6", "国产", "262K", 6.5, 27.0, "CNY", "cite-48", None, None, "OpenRouter / LiteLLM 待匹配", "Kimi 官方未命中缓存输入价。", 95),
    token_row("Kimi / Moonshot", "moonshot-v1-128k", "国产", "128K", 10.0, 30.0, "CNY", "cite-48", None, None, "OpenRouter / LiteLLM 待匹配", "Moonshot V1 官方价格。", 95),
    token_row("智谱 GLM / Z.ai", "glm-5.2", "国产", "1M", None, None, "CNY", "智谱开放平台官方价页访问受限，需继续补采控制台/文档价", 0.93, 3.0, "OpenRouter Models API", "市场价已抓取，官方价不能用市场价冒充。", "OFFICIAL_MISSING", 65),
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
        "original": "SMM 样本：江苏 32 台 A100 80G IB 组网整租约 3.15-3.8 万元/台/月",
        "monthly_wan": 3.15,
        "source": "SMM 算力直播（主口径候选）",
        "confidence": 86,
        "consensus": "Medium",
        "historical": "HIST_INSUFFICIENT",
        "status": "PASS",
        "note": "同日 SMM 存在 3.15 万与 3.8 万两个报价，保守采用低端成交/供给价进入主指数，区间保留在审计备注。",
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
    "H20": {
        "original": "SMM 样本：华东某大型城市 141GB H20 八卡服务器单台月租报价 4.8 万元",
        "monthly_wan": 4.8,
        "source": "SMM 算力直播（主口径候选）",
        "confidence": 85,
        "consensus": "Medium",
        "historical": "HIST_INSUFFICIENT",
        "status": "PASS",
        "note": "H20 141GB 八卡服务器，SMM 报价且有上线即锁定的供需信号。",
    },
    "RTX 4090": {
        "original": "SMM 样本：4090 八卡服务器市场报价约 0.68-0.88 万元/台/月，批量报价约 0.73 万元/月",
        "monthly_wan": 0.73,
        "source": "SMM 算力直播（辅助主口径）",
        "confidence": 82,
        "consensus": "Medium",
        "historical": "HIST_INSUFFICIENT",
        "status": "PASS",
        "note": "消费级八卡服务器租赁价，按 SMM 多路渠道报价区间保守取中部参考。",
    },
    "昇腾 910C": {
        "original": "SMM 样本：华南 910C 服务器买方出价 5.3 万/月，当前行业均价约 6.2 万/月上下",
        "monthly_wan": 6.2,
        "source": "SMM 算力直播（国产候选）",
        "confidence": 78,
        "consensus": "Medium",
        "historical": "HIST_INSUFFICIENT",
        "status": "PASS",
        "note": "国产算力服务器价格，样本含买方出价与行业均价，需继续扩源校验。",
    },
    "昇腾 910B": {
        "original": "SMM 样本：910B2 月租约 1.2-1.5 万元，但存在 B2/B3/B4 子型号和搬迁限制差异",
        "monthly_wan": None,
        "source": "SMM 算力直播（子型号待拆）",
        "confidence": 68,
        "consensus": "Low",
        "historical": "HIST_INSUFFICIENT",
        "status": "REVIEW",
        "note": "910B 子型号、形态和异地部署限制未拆清，暂不进入主指数。",
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


def overseas_monthly_wan(gpu: str) -> float | None:
    item = OVERSEAS_HOURLY_USD.get(gpu)
    if not item:
        return None
    usd = item[0]
    cny = cny_from_usd(usd)
    return None if cny is None else round(cny * 8 * 24 * 30 / 10000, 2)


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
        overseas_monthly = overseas_monthly_wan(gpu)
        overseas_ratio = None
        if monthly is not None and overseas_monthly:
            overseas_ratio = round(monthly / overseas_monthly * 100, 1)
        overseas_ratio_label = None
        if monthly is not None:
            overseas_ratio_label = f"{overseas_ratio}%" if overseas_ratio is not None else "海外缺口"
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
            "海外同型号等效8卡月租（万元）": overseas_monthly,
            "国内月租/海外月租": overseas_ratio_label,
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
            "标准化价格": monthly_ref,
            "标准化单位": "万元/8卡整机/月",
            "单卡小时价（人民币）": cny,
            "等效8卡月租（万元）": monthly_ref,
            "Confidence Score": conf,
            "Source Consensus": consensus,
            "校验状态": status,
            "备注": "海外 GPU Cloud 已统一折算为 8卡整机月租，仍只进入海外参考，不进入国内租赁指数。" if cny is not None else note,
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
    "prompt_files": [
        "prompts/system_prompt.md",
        "prompts/report_config.md",
        "prompts/source_pool.md",
    ],
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
        <p>扩源策略已拆成三文件 Prompt：<code>system_prompt.md</code> 管治理，<code>report_config.md</code> 管报告结构，<code>source_pool.md</code> 管 Token、GPU Cloud、国内云价、采购价和招投标源池。H800 当前没有通过国内主口径校验，因此不进入国内主指数；但它仍保留在覆盖率诊断和缺口清单中，后续通过云厂商、招投标、渠道报价继续补采。</p>
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
      <p class="note">海外 GPU Cloud 原始来源多为美元/卡/小时，本报告统一折算为人民币口径“万元/8卡整机/月”绘图和展示，单卡小时价保留在表格中作为辅助字段；海外月租仍不进入国内租赁指数。</p>
      <figure><div id="chart-overseas" class="chart"></div></figure>
      {table(overseas_pass)}
    </section>

    <section id="token">
      <h2>Token 价格</h2>
      <p class="note">Token 表按“每个厂商主流模型”覆盖，官方价来自厂商官网或官方文档，市场价来自 OpenRouter、LiteLLM、models.dev 等三方平台；官方价和市场价必须分列，不得互相替代。</p>
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
        <p>本期 SMM 深扒后，国内服务器价格覆盖明显扩大：H100 80G 约 7.6 万元/8卡整机/月，A100 80G 约 3.15-3.8 万元/月，H20 141GB 约 4.8 万元/月，RTX 5090 约 1.2 万元/月，RTX 4090 约 0.68-0.88 万元/月，昇腾 910C 行业均价约 6.2 万元/月。H800 和昇腾 910B 因当前口径或子型号未拆清，仍不进入主指数；后续需继续沿 SMM、IDC、运营商、门户和自媒体线索扩源。</p>
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
        "domesticRatios": [r.get("国内月租/海外月租") for r in domestic_pass],
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
  function bar(id, labels, values, name, color, ratios) {{
    init(id, {{
      animation:false,
      color:[color],
      tooltip:{{trigger:'axis', appendToBody:true}},
      grid:{{left:70,right:40,top:44,bottom:80,containLabel:true}},
      xAxis:{{type:'category',data:labels,axisLabel:{{color:muted,interval:0}},axisLine:{{lineStyle:{{color:rule}}}},axisTick:{{show:false}}}},
      yAxis:{{type:'value',name:name,nameTextStyle:{{color:muted}},axisLabel:{{color:muted}},splitLine:{{lineStyle:{{color:rule}}}}}},
      series:[{{type:'bar',data:values,label:{{show:true,position:'top',color:ink,formatter:function(p){{
        var base = p.value + '万/月';
        var rawRatio = ratios && ratios[p.dataIndex] ? ratios[p.dataIndex] : '';
        var ratio = rawRatio === '海外缺口' ? ' · 海外缺口' : (rawRatio ? ' · 海外' + rawRatio : '');
        return base + ratio;
      }}}},itemStyle:{{borderRadius:[6,6,0,0]}}}}]
    }});
  }}
  bar('chart-domestic-main', DATA.domesticLabels, DATA.domesticValues, '万元/8卡整机/月', accent, DATA.domesticRatios);
  bar('chart-overseas', DATA.overseasLabels, DATA.overseasValues, '万元/8卡整机/月', accent2);
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
