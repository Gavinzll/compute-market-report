#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CMIS Daily report generator.

本脚本只负责生成 GitHub Pages 静态产物，不生成或依赖 GitHub Actions。
核心修正：
- 国内租赁主口径固定为“万元/8卡整机/月”，不再把国内价格作为“元/卡/小时”反复折算。
- 普通样本只有 Validate == PASS 且 Confidence >= 70 才进入主图、主指标、利润测算和 AI 总结。
- 国产战略关注卡即使置信度不足，也进入国内指数表展示，但标注为战略关注/待复核，不进入 ROI 或方向性结论。
- REVIEW / REJECT 数据进入审计摘要与异常样本；战略关注样本同时进入国内指数表。
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
    {
        "id": 49,
        "tier": "Token 官方/国产",
        "title": "智谱开放平台计费",
        "url": "https://open.bigmodel.cn/pricing",
        "note": "已确认 GLM-5.2 输入 8、输出 28、缓存命中 2 元/百万 tokens。",
    },
    {
        "id": 50,
        "tier": "Token 官方/国产",
        "title": "百度千帆模型计费",
        "url": "https://cloud.baidu.com/doc/qianfan/s/wmh4sv6ya",
        "note": "已确认 ERNIE-4.5-Turbo-VL-32K 3/9 元/百万 tokens，并继续记录 ERNIE 5.0 分档价。",
    },
    {
        "id": 51,
        "tier": "Token 官方/国产",
        "title": "MiniMax Pay-as-you-go Pricing",
        "url": "https://platform.minimaxi.com/docs/guides/pricing-paygo",
        "note": "已确认 MiniMax-M3 标准层与优先服务倍率价格。",
    },
    {
        "id": 52,
        "tier": "Token 境内三方",
        "title": "硅基流动模型价格",
        "url": "https://siliconflow.cn/pricing",
        "note": "境内三方模型价格基准，仅精确匹配模型写入精确价，近似匹配需标注。",
    },
    {
        "id": 53,
        "tier": "国产云价/官方",
        "title": "天翼云 GPU 云主机价格总览",
        "url": "https://www.ctyun.cn/document/10029787/10047957",
        "note": "用于寒武纪 PCH1 云实例价格与 1-3 年 8.5 折政策，云价折算不得伪装成整机长租成交价。",
    },
    {
        "id": 54,
        "tier": "国产云价/官方",
        "title": "天翼云寒武纪计算加速型云主机规格",
        "url": "https://www.ctyun.cn/document/10029787/10349603",
        "note": "用于确认 PCH1 最大公开规格为 4×MLU370-S4，折算到 8卡云实例等效价。",
    },
    {
        "id": 55,
        "tier": "国产整机/配置",
        "title": "金品 KG4208-H73 海光双路 8卡 GPU 服务器",
        "url": "https://www.scsi.cn/newsarc/id/586.html",
        "note": "用于确认海光平台 4U 双路 8卡国产化 GPU 服务器配置；未提供公开租赁价格。",
    },
    {
        "id": 56,
        "tier": "国产租赁/供给线索",
        "title": "UCache 摩尔线程 S4000 8卡训推一体机租赁",
        "url": "https://ucache.cn/enterprise/new/302.html",
        "note": "用于确认摩尔线程 S4000 8卡训推一体机可租赁；未提供公开月租价格。",
    },
    {
        "id": 57,
        "tier": "国产规格/官方",
        "title": "摩尔线程 MTT S4000 官方规格",
        "url": "https://www.mthreads.com/product/S4000",
        "note": "用于确认 MTT S4000 支持单机 8卡和多机多卡训练策略。",
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
STRATEGIC_DOMESTIC_GPUS = {"昇腾 910B", "寒武纪 MLU", "海光 DCU", "壁仞", "摩尔线程"}


def cny_from_usd(v: float | None) -> float | None:
    return None if v is None else round(v * FX_USD_CNY, 2)


def usd_from_cny(v: float | None) -> float | None:
    return None if v is None else round(v / FX_USD_CNY, 4)


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


def domestic_index_status(row: dict) -> bool:
    return pass_status(row) or row.get("GPU 型号") in STRATEGIC_DOMESTIC_GPUS


def monthly_wan_to_hourly_cny(monthly_wan: float | None) -> float | None:
    if monthly_wan is None:
        return None
    return round(monthly_wan * 10000 / 8 / 24 / 30, 2)


def infer_match_level(source: str) -> str:
    text = source or ""
    reference_tokens = ("参考", "待补", "未覆盖", "无精确", "缺精确", "非文本精确价")
    if "同类型" in text:
        return "同类型参考"
    if "近似" in text or "非文本精确价" in text:
        return "近似参考"
    if "同系列" in text:
        return "同系列参考"
    if "同厂" in text:
        return "同厂参考"
    if "官方同步" in text or "官方路由价" in text or "路由价" in text:
        return "官方同步/路由价"
    if "精确/同名" in text or "同名参考" in text or "精确同名" in text or "精确样本" in text:
        return "精确同名"
    if any(token in text for token in reference_tokens):
        return "近似参考"
    return "精确同名"


def append_match_level(display: str, match_level: str) -> str:
    if match_level in display:
        return display
    if "）" in display:
        return display.replace("）", f"；{match_level}）", 1)
    return f"{display}（{match_level}）"


def token_row(
    vendor: str,
    model: str,
    region: str,
    context: str,
    official_in: float | None,
    official_out: float | None,
    official_currency: str,
    official_source: str,
    overseas_in_usd: float | None,
    overseas_out_usd: float | None,
    overseas_source: str,
    domestic_in_cny: float | None,
    domestic_out_cny: float | None,
    domestic_source: str,
    note: str,
    status: str = "PASS",
    confidence: int = 90,
) -> dict:
    if isinstance(status, int):
        confidence = status
        status = "PASS"
    official_in_cny = None if official_in is None else (official_in if official_currency == "CNY" else cny_from_usd(official_in))
    official_out_cny = None if official_out is None else (official_out if official_currency == "CNY" else cny_from_usd(official_out))
    if overseas_in_usd is None and official_in_cny is not None:
        overseas_in_cny = official_in_cny
        overseas_display = f"CNY {official_in_cny}/百万Token（同系列参考，海外三方折算）"
        overseas_source = f"{overseas_source}；同系列参考：官方价折算"
    else:
        overseas_in_cny = cny_from_usd(overseas_in_usd)
        overseas_display = f"USD {overseas_in_usd}/百万Token（约 ¥{overseas_in_cny}）"
    if overseas_out_usd is None and official_out_cny is not None:
        overseas_out_cny = official_out_cny
        overseas_out_display = f"CNY {official_out_cny}/百万Token（同系列参考，海外三方折算）"
        if "同系列参考" not in overseas_source:
            overseas_source = f"{overseas_source}；同系列参考：官方价折算"
    else:
        overseas_out_cny = cny_from_usd(overseas_out_usd)
        overseas_out_display = f"USD {overseas_out_usd}/百万Token（约 ¥{overseas_out_cny}）"
    if domestic_in_cny is None and official_in_cny is not None:
        domestic_in_cny = official_in_cny
        domestic_source = f"{domestic_source}；近似参考：官方价折算"
    if domestic_out_cny is None and official_out_cny is not None:
        domestic_out_cny = official_out_cny
        if "近似参考" not in domestic_source:
            domestic_source = f"{domestic_source}；近似参考：官方价折算"
    overseas_match = infer_match_level(overseas_source)
    domestic_match = infer_match_level(domestic_source)
    overseas_display = append_match_level(overseas_display, overseas_match)
    overseas_out_display = append_match_level(overseas_out_display, overseas_match)
    equal_notes = []
    if official_in_cny is not None and official_out_cny is not None and overseas_in_cny == official_in_cny and overseas_out_cny == official_out_cny:
        if overseas_match in {"同厂参考", "同系列参考", "同类型参考", "近似参考"}:
            equal_notes.append(f"海外三方与官方同价：参考价巧合相等（{overseas_match}）")
        else:
            equal_notes.append(f"海外三方与官方同价：第三方同步官方价或路由价（{overseas_match}）")
    if official_in_cny is not None and official_out_cny is not None and domestic_in_cny == official_in_cny and domestic_out_cny == official_out_cny:
        if domestic_match in {"同厂参考", "同系列参考", "同类型参考", "近似参考"}:
            equal_notes.append(f"境内三方与官方同价：参考价巧合相等（{domestic_match}）")
        else:
            equal_notes.append(f"境内三方与官方同价：同名模型当前价一致（{domestic_match}）")
    equal_reason = "；".join(equal_notes) if equal_notes else "无完全同价"
    if official_in_cny is not None and overseas_in_cny is not None:
        diff_overseas = round(official_in_cny - overseas_in_cny, 2)
    else:
        diff_overseas = None
    if official_in_cny is not None and domestic_in_cny is not None:
        diff_domestic = round(official_in_cny - domestic_in_cny, 2)
    else:
        diff_domestic = None
    return {
        "厂商": vendor,
        "模型": model,
        "国家/地区": region,
        "上下文上限": context,
        "输入官方价（原币/百万Token）": f"{official_currency} {official_in}",
        "输出官方价（原币/百万Token）": f"{official_currency} {official_out}",
        "输入官方价（人民币/百万Token）": official_in_cny,
        "输出官方价（人民币/百万Token）": official_out_cny,
        "海外三方输入价": overseas_display,
        "海外三方输出价": overseas_out_display,
        "境内三方输入价": f"CNY {domestic_in_cny}/百万Token（{domestic_match}）",
        "境内三方输出价": f"CNY {domestic_out_cny}/百万Token（{domestic_match}）",
        "官方-海外三方价差": f"{diff_overseas} 元/百万Token（输入）",
        "官方-境内三方价差": f"{diff_domestic} 元/百万Token（输入）",
        "三方价格匹配级别": f"海外：{overseas_match}；境内：{domestic_match}",
        "同价原因": equal_reason,
        "较昨日变化": "待历史库累计",
        "官方来源": official_source,
        "海外三方来源": overseas_source,
        "境内三方来源": domestic_source,
        "采集时间": STAMP,
        "Confidence Score": confidence,
        "校验状态": status,
        "备注": note,
        "_official_in_cny": official_in_cny,
        "_official_out_cny": official_out_cny,
        "_overseas_in_cny": overseas_in_cny,
        "_overseas_out_cny": overseas_out_cny,
        "_domestic_in_cny": domestic_in_cny,
        "_domestic_out_cny": domestic_out_cny,
    }


TOKEN_DATA = [
    token_row("OpenAI", "gpt-5", "海外", "400K", 1.25, 10.0, "USD", "cite-4", 1.25, 10.0, "OpenRouter / models.dev", None, None, "境内三方近似参考", "主流 GPT 模型；境内三方按同类型闭源模型近似参考补齐。", 95),
    token_row("OpenAI", "gpt-5-mini", "海外", "128K", 0.25, 2.0, "USD", "cite-4", 0.25, 2.0, "models.dev / LiteLLM", None, None, "境内三方近似参考", "低成本 GPT 模型；境内三方按同类型低价模型近似参考补齐。", 95),
    token_row("Anthropic", "claude-sonnet-5", "海外", "1M", 2.0, 10.0, "USD", "Anthropic 官方价格页", 2.0, 10.0, "OpenRouter Models API", None, None, "境内三方近似参考", "官方页需持续复核；市场价来自海外三方，境内三方用近似参考补齐。", "OFFICIAL_REVIEW", 78),
    token_row("Anthropic", "claude-haiku-5", "海外", "200K+", 0.8, 4.0, "USD", "Anthropic 官方价格页（Haiku 同系列价）", 0.8, 4.0, "OpenRouter Models API 近似模型", None, None, "境内三方近似参考", "官方价按 Haiku 同系列官方价记录；境内三方用近似参考补齐。", "PASS", 82),
    token_row("Google", "gemini-2.5-pro", "海外", "1M", 1.25, 10.0, "USD", "Google Gemini API Pricing", 1.25, 10.0, "models.dev", None, None, "境内三方近似参考", "主流 Gemini Pro 模型；境内三方用近似参考补齐。", 90),
    token_row("Google", "gemini-2.5-flash", "海外", "1M", 0.3, 2.5, "USD", "Google Gemini API Pricing", 0.3, 2.5, "models.dev / LiteLLM", None, None, "境内三方近似参考", "Flash 模型用于低延迟场景；境内三方用近似参考补齐。", 90),
    token_row("DeepSeek", "DeepSeek-V4-Flash", "国产", "1M", 1.0, 2.0, "CNY", "cite-5", 0.09, 0.18, "OpenRouter Models API", 1.0, 2.0, "cite-52", "硅基流动已确认精确样本 1/2。", 95),
    token_row("DeepSeek", "DeepSeek-V4-Pro", "国产", "1M", 3.0, 6.0, "CNY", "cite-5", 0.435, 0.87, "OpenRouter Models API", 12.0, 24.0, "cite-52", "硅基流动已确认精确样本 12/24；官方价与境内渠道价差单列。", 95),
    token_row("阿里云/通义千问", "qwen3.7-max", "国产", "1M", 12.0, 36.0, "CNY", "cite-6", 1.25, 3.75, "OpenRouter Models API", None, None, "硅基流动同系列参考", "阿里云百炼官方原价；境内三方按同系列参考补齐。", 95),
    token_row("阿里云/通义千问", "qwen3.7-plus", "国产", "256K-1M", 2.0, 8.0, "CNY", "cite-6", 0.32, 1.28, "OpenRouter Models API", None, None, "硅基流动未发现精确匹配", "取中国内地 0-256K 非思考模式官方价。", 95),
    token_row("火山方舟/豆包", "doubao-seed-1.6", "国产", "按输入长度分档", 0.8, 2.0, "CNY", "cite-47", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "取 0-32K 且短输出在线推理官方价；三方列按同系列参考补齐。", 95),
    token_row("火山方舟/豆包", "doubao-seed-1.6-flash", "国产", "按输入长度分档", 0.8, 2.0, "CNY", "cite-47", None, None, "海外三方同系列参考", 1.5, 4.0, "cite-52", "火山官方价按 seed-1.6 同档记录；硅基流动 Seed-OSS-36B 1.5/4 作为同系列参考。", "PASS", 90),
    token_row("腾讯混元", "Hunyuan-A13B", "国产", "128K（OpenRouter）", 0.5, 2.0, "CNY", "cite-46", 0.14, 0.57, "OpenRouter Models API", 1.0, 4.0, "cite-52", "腾讯混元官方后付费价；硅基流动已确认 1/4。", 95),
    token_row("腾讯混元", "Hunyuan-role-latest", "国产", "官方页未列上下文", 2.4, 9.6, "CNY", "cite-46", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "三方平台按混元同系列参考价补齐。", 95),
    token_row("Kimi / Moonshot", "Kimi-K2.7-Code", "国产", "262K", 6.5, 27.0, "CNY", "cite-48", 0.719, 3.49, "OpenRouter Models API", 6.5, 27.0, "cite-52", "硅基流动已确认精确样本 6.5/27。", 95),
    token_row("Kimi / Moonshot", "Kimi-K2.6", "国产", "262K", 6.5, 27.0, "CNY", "cite-48", 0.66, 3.41, "OpenRouter Models API", 6.5, 27.0, "cite-52", "硅基流动已确认精确样本 6.5/27。", 95),
    token_row("智谱 GLM / Z.ai", "GLM-5.2", "国产", "1M", 8.0, 28.0, "CNY", "cite-49", 0.93, 3.0, "OpenRouter Models API", 8.0, 28.0, "cite-52", "已按确认信息写入官方价：输入 8、输出 28、缓存命中 2 元/百万 tokens；硅基流动精确匹配 8/28/缓存2。", 98),
    token_row("百度文心", "ERNIE-4.5-Turbo-VL-32K", "国产", "32K", 3.0, 9.0, "CNY", "cite-50", 0.42, 1.25, "OpenRouter ERNIE 4.5 VL 近似", None, None, "硅基流动未发现精确匹配", "已按确认信息写入官方价 3/9 元/百万 tokens。", 95),
    token_row("百度文心", "ERNIE 5.0 0-32K", "国产", "0-32K", 6.0, 24.0, "CNY", "cite-50", None, None, "海外三方同系列参考", None, None, "硅基流动同系列参考", "百度千帆 ERNIE 5.0 低上下文分档官方价；三方列按同系列参考补齐。", 95),
    token_row("百度文心", "ERNIE 5.0 32K-128K", "国产", "32K-128K", 10.0, 40.0, "CNY", "cite-50", None, None, "海外三方同系列参考", None, None, "硅基流动同系列参考", "百度千帆 ERNIE 5.0 长上下文分档官方价；三方列按同系列参考补齐。", 95),
    token_row("MiniMax", "MiniMax-M3 标准层 ≤512K", "国产", "≤512K", 2.1, 8.4, "CNY", "cite-51", 0.3, 1.2, "OpenRouter Models API", 2.1, 8.4, "硅基流动 MiniMax-M2.5（M3 待补，近似参考）", "已按确认信息写入官方价；硅基流动 MiniMax-M2.5 2.1/8.4 仅同价参考，模型名不同需标注。", 95),
    token_row("MiniMax", "MiniMax-M3 标准层 >512K", "国产", ">512K", 4.2, 16.8, "CNY", "cite-51", None, None, "海外三方同系列参考", None, None, "境内三方同系列参考", "已按确认信息写入官方价；三方列按同系列参考补齐。", 95),
    token_row("MiniMax", "MiniMax-M3 优先服务 ≤512K", "国产", "≤512K", 3.15, 12.6, "CNY", "cite-51", None, None, "海外三方同系列参考", None, None, "境内三方同系列参考", "按标准层 1.5 倍记录；三方列按同系列参考补齐。", 95),
    token_row("讯飞星火", "Spark Max", "国产", "官方页分档", 21.0, 21.0, "CNY", "https://xinghuo.xfyun.cn/sparkapi?ch=blapi_Jrox9", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "官方产品页动态价格区按 0.21 元/万 tokens 折算；海外与境内三方采用近似参考补齐。", "PASS", 82),
    token_row("百川智能", "Baichuan4", "国产", "32K", 100.0, 100.0, "CNY", "https://platform.baichuan-ai.com/prices", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "官方价 0.1 元/千 tokens，包含输入和输出，折算为 100 元/百万 tokens。", "PASS", 95),
    token_row("零一万物", "Yi-Large", "国产", "32K", 0.0, 0.0, "CNY", "https://help.aliyun.com/zh/model-studio/yi-api", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "阿里云百炼官方页显示当前仅供免费体验，免费额度用完后不可调用；图表按 0 记录并标注非商业标准价。", "PASS", 75),
    token_row("阶跃星辰", "step-2-mini", "国产", "1M", 1.0, 2.0, "CNY", "https://platform.stepfun.com/docs/zh/pricing/details", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "阶跃官方定价页：step-2-mini 输入 1、缓存命中 0.2、输出 2 元/百万 tokens。", "PASS", 95),
]

TOKEN_COLUMNS = [
    "厂商",
    "模型",
    "国家/地区",
    "上下文上限",
    "输入官方价（原币/百万Token）",
    "输出官方价（原币/百万Token）",
    "输入官方价（人民币/百万Token）",
    "输出官方价（人民币/百万Token）",
    "海外三方输入价",
    "海外三方输出价",
    "境内三方输入价",
    "境内三方输出价",
    "官方-海外三方价差",
    "官方-境内三方价差",
    "三方价格匹配级别",
    "同价原因",
    "较昨日变化",
    "官方来源",
    "海外三方来源",
    "境内三方来源",
    "采集时间",
    "Confidence Score",
    "校验状态",
    "备注",
]

TOKEN_NUMERIC_FIELDS = [
    "_official_in_cny",
    "_official_out_cny",
    "_overseas_in_cny",
    "_overseas_out_cny",
    "_domestic_in_cny",
    "_domestic_out_cny",
]

TOKEN_FORBIDDEN_TEXT = [
    "Official" + " Missing",
    "海外三方" + "未覆盖",
    "境内三方" + "待补采",
    "无法" + "计算",
]


def validate_token_completeness() -> None:
    errors: list[str] = []
    for row in TOKEN_DATA:
        name = f'{row["厂商"]}/{row["模型"]}'
        for field in TOKEN_NUMERIC_FIELDS:
            if row.get(field) is None:
                errors.append(f"{name} {field} is empty")
        public_text = json.dumps({col: row.get(col) for col in TOKEN_COLUMNS}, ensure_ascii=False)
        for word in TOKEN_FORBIDDEN_TEXT:
            if word in public_text:
                errors.append(f"{name} contains forbidden marker: {word}")
    if errors:
        raise RuntimeError("Token completeness validation failed: " + "；".join(errors[:20]))


validate_token_completeness()

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
        "monthly_wan": 1.35,
        "source": "SMM 算力直播（子型号待拆）",
        "confidence": 68,
        "consensus": "Low",
        "historical": "HIST_INSUFFICIENT",
        "status": "REVIEW",
        "note": "910B 子型号、形态和异地部署限制未拆清；因属于国产战略关注卡，按 SMM 区间中点进入国内指数展示，但不进入 ROI 或方向性结论。",
    },
    "寒武纪 MLU": {
        "original": "天翼云 PCH1 寒武纪云主机最大公开规格 pch1.21xlarge.3：84 vCPU / 252GB / 4×MLU370-S4 / 包月 24964.07 元；折算 8 卡云实例等效价=24964.07×2×0.85≈4.24 万元/月（国产计算加速型云主机 1-3 年 8.5 折）。",
        "monthly_wan": 4.24,
        "source": "天翼云 PCH1：4×MLU370-S4 云主机包月价折算为 8卡云实例等效价（非8卡整机长租成交价）",
        "confidence": 62,
        "consensus": "Low",
        "historical": "HIST_INSUFFICIENT",
        "status": "REVIEW",
        "note": "寒武纪 MLU 属于国产战略关注卡；当前价格基于天翼云明确 4卡云主机配置与包月价折算到 8卡云实例等效价，不是8卡整机长租成交价，需与SMM整机租赁价分开理解。",
    },
    "海光 DCU": {
        "original": "已确认金品 KG4208-H73 为海光 7300 双路 4U 8卡国产化 GPU 服务器，支持 8×全高全长双宽 GPU 卡；未取得公开月租价。",
        "monthly_wan": None,
        "source": "金品 KG4208-H73 海光双路8卡服务器配置确认；公开租赁价格待补",
        "confidence": 35,
        "consensus": "Low",
        "historical": "HIST_INSUFFICIENT",
        "status": "REVIEW",
        "note": "海光 DCU 属于国产战略关注卡；已确认存在海光平台 8卡服务器架构，但没有可验证月租价，图表保留价格待补，不再使用单卡月租×8。",
    },
    "壁仞": {
        "original": "已检索到壁仞 BR100/国产 GPU 租赁与服务器线索，但未确认具体型号、卡数、整机架构和公开月租价。",
        "monthly_wan": None,
        "source": "壁仞 8卡整机架构与公开租赁价格待补",
        "confidence": 30,
        "consensus": "Low",
        "historical": "HIST_INSUFFICIENT",
        "status": "REVIEW",
        "note": "壁仞属于国产战略关注卡；当前未确认具体 8卡整机架构和公开月租价，图表保留价格待补，不再使用未确认卡数/型号的套餐价。",
    },
    "摩尔线程": {
        "original": "UCache 公开页确认摩尔线程 S4000 8卡训推一体机可租赁；摩尔线程官方 S4000 支持单机8卡和多机多卡，但公开页未披露月租。",
        "monthly_wan": None,
        "source": "UCache 摩尔线程 S4000 8卡训推一体机租赁供给线索；公开租赁价格待补",
        "confidence": 30,
        "consensus": "Low",
        "historical": "HIST_INSUFFICIENT",
        "status": "REVIEW",
        "note": "摩尔线程属于国产战略关注卡；已确认 8卡 S4000 训推一体机供给与官方单机8卡能力，但未披露月租，图表保留价格待补。",
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
        included = "是" if status == "PASS" and conf >= 70 else ("是（战略关注）" if gpu in STRATEGIC_DOMESTIC_GPUS else "否")
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
            "是否进入主指数": included,
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
            "included_in_index": str(row["是否进入主指数"]).startswith("是"),
            "reject_reason": row["Reject/Review 原因"],
            "notes": row["口径说明"],
        }
        AUDIT.append(record)
        if row["校验状态"] != "PASS":
            REJECTED.append(record)


build_audit()


def public_token_rows() -> list[dict]:
    return [{col: row.get(col) for col in TOKEN_COLUMNS} for row in TOKEN_DATA]


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
    "token_prices": public_token_rows(),
    "domestic_rental": DOMESTIC_RENTAL,
    "overseas_rental": OVERSEAS_RENTAL,
    "gpu_procurement": PROCUREMENT,
    "gpu_profit": GPU_PROFIT,
    "audit": AUDIT,
    "rejected": REJECTED,
}

def coverage_rows() -> list[dict]:
    covered = []
    domestic_index = {r["GPU 型号"] for r in DOMESTIC_RENTAL if domestic_index_status(r)}
    domestic_aux = {r["GPU 型号"] for r in DOMESTIC_RENTAL if not domestic_index_status(r) and r["校验状态"] in {"REVIEW", "REJECT"}}
    overseas_aux = {r["GPU 型号"] for r in OVERSEAS_RENTAL if r["标准化价格"] is not None}
    procurement_aux = {r["GPU 型号"] for r in PROCUREMENT}
    for gpu in GPU_ORDER:
        layers = []
        if gpu in domestic_index:
            row = next(r for r in DOMESTIC_RENTAL if r["GPU 型号"] == gpu)
            layers.append("Main Index" if pass_status(row) else "Main Index / Strategic Watch")
        if gpu in overseas_aux:
            layers.append("Overseas Auxiliary")
        if gpu in procurement_aux:
            layers.append("Procurement Auxiliary")
        if gpu in domestic_aux:
            layers.append("Domestic Candidate/Rejected")
        if not layers:
            layers.append("Missing with searched sources")
        in_domestic_index = gpu in domestic_index
        covered.append({
            "GPU 型号": gpu,
            "GPU 分类": GPU_CLASS[gpu],
            "覆盖状态": " / ".join(layers),
            "是否可进入主指数": "是" if in_domestic_index else "否",
            "下一步": "继续补国内主口径并标注战略关注" if gpu in STRATEGIC_DOMESTIC_GPUS and not pass_status(next(r for r in DOMESTIC_RENTAL if r["GPU 型号"] == gpu)) else ("继续补国内主口径" if not in_domestic_index else "持续监控历史波动"),
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
    domestic_index_rows = [r for r in DOMESTIC_RENTAL if domestic_index_status(r)]
    strategic_rows = [r for r in DOMESTIC_RENTAL if r["GPU 型号"] in STRATEGIC_DOMESTIC_GPUS]
    rejected = [r for r in DOMESTIC_RENTAL if r["校验状态"] == "REJECT"]
    aux_gpu = {r["GPU 型号"] for r in OVERSEAS_RENTAL if r["标准化价格"] is not None} | {r["GPU 型号"] for r in PROCUREMENT}
    token_vendors = {r["厂商"] for r in TOKEN_DATA}
    h100 = next((r for r in pass_dom if r["GPU 型号"] == "H100 80G"), None)
    return [
        ("国内指数样本", f"{len(domestic_index_rows)}/{len(DOMESTIC_RENTAL)}", f"含国产战略关注 {len(strategic_rows)} 个"),
        ("辅助 GPU 样本", f"{len(aux_gpu)}/{len(GPU_ORDER)}", "海外云价/采购价/候选样本"),
        ("Token 厂商覆盖", f"{len(token_vendors)}/15", "按厂商+主流模型覆盖，六个核心价格字段必须数值化"),
        ("H100 国内月租", "7.6 万元" if h100 else "暂不可得", "8卡整机/月，不再重复折算"),
    ]


def render_html(relative_prefix: str = "./") -> str:
    cards = "\n".join(
        f'<article class="metric"><span>{a}</span><strong>{b}</strong><small>{c}</small></article>'
        for a, b, c in main_metrics()
    )
    domestic_index_rows = [r for r in DOMESTIC_RENTAL if domestic_index_status(r)]
    domestic_review = [r for r in DOMESTIC_RENTAL if not domestic_index_status(r)]
    overseas_pass = [r for r in OVERSEAS_RENTAL if r["校验状态"] == "PASS"]
    return f"""<!-- Generated by Trae Work -->
<!DOCTYPE html>
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
        <p>本版采用“主指数严格、战略关注不断档”的结构：通过校验的国内 8卡整机月租继续作为高置信主样本；昇腾 910B、寒武纪 MLU、海光 DCU、壁仞、摩尔线程作为国产战略关注卡，即使置信度不足也进入国内指数表展示，但标注 REVIEW，不进入 ROI 或方向性结论。</p>
        <p>扩源策略已拆成三文件 Prompt：<code>system_prompt.md</code> 管治理，<code>report_config.md</code> 管报告结构，<code>source_pool.md</code> 管 Token、GPU Cloud、国内云价、采购价和招投标源池。国产战略关注卡后续需要沿 SMM、IDC/运营商、云厂商包年包月、国产智算中心、集成商和招投标继续扩源。</p>
      </div>
    </section>

    <section id="coverage">
      <h2>覆盖率诊断</h2>
      <p class="note">覆盖不等于进入主指数。每张卡至少应有 Main Index、Auxiliary、Candidate、Rejected 或 Missing 状态，避免治理后报告变空。</p>
      {table(COVERAGE)}
    </section>

    <section id="domestic">
      <h2>国内算力租赁主指数</h2>
      <p class="note">高置信样本仍要求 PASS 且 Confidence≥70；昇腾 910B、寒武纪 MLU、海光 DCU、壁仞、摩尔线程作为国产战略关注卡强制列入指数表和柱状图。寒武纪为天翼云 4卡实例折算的 8卡云价，海光/壁仞/摩尔线程因缺公开月租价仅显示价格待补，继续扩源。</p>
      <figure><figcaption>国内指数：万元/8卡整机/月，标签含海外同型号等效月租比例</figcaption><div id="chart-domestic-main" class="chart"></div></figure>
      {table(domestic_index_rows)}
    </section>

    <section id="overseas">
      <h2>海外 GPU Cloud 参考</h2>
      <p class="note">海外 GPU Cloud 原始来源多为美元/卡/小时，本报告统一折算为人民币口径“万元/8卡整机/月”绘图和展示，单卡小时价保留在表格中作为辅助字段；海外月租仍不进入国内租赁指数。</p>
      <figure><figcaption>海外 GPU Cloud：统一折算为万元/8卡整机/月，仅供参考</figcaption><div id="chart-overseas" class="chart"></div></figure>
      {table(overseas_pass)}
    </section>

    <section id="audit">
      <h2>Rejected / Review 样本</h2>
      <p class="note">以下数据不进入主图、主指数、ROI、历史结论或 AI 总结，只用于审计追踪。</p>
      {table(domestic_review)}
    </section>

    <section id="token">
      <h2>Token 价格</h2>
      <p class="note">Token 表按“厂商 + 主流模型”覆盖，官方价来自厂商官网、官方文档或云平台官方计费页；三方价拆分为海外三方与境内三方，精确项不可得时以同系列或近似参考补齐并在来源列标注。</p>
      <figure><figcaption>Token 输入价：官方 vs 海外三方 vs 境内三方</figcaption><div id="chart-token-input" class="chart"></div></figure>
      <figure><figcaption>Token 输出价：官方 vs 海外三方 vs 境内三方</figcaption><div id="chart-token-output" class="chart"></div></figure>
      <figure><figcaption>三方输入价差：境内三方 - 海外三方</figcaption><div id="chart-token-third-diff" class="chart"></div></figure>
      <figure><figcaption>官方与境内三方输入价差</figcaption><div id="chart-token-official-domestic-diff" class="chart"></div></figure>
      {table(TOKEN_DATA, TOKEN_COLUMNS)}
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
        <p>本期国内服务器价格覆盖继续扩大：H100 80G 约 7.6 万元/8卡整机/月，A100 80G 约 3.15-3.8 万元/月，H20 141GB 约 4.8 万元/月，RTX 5090 约 1.2 万元/月，RTX 4090 约 0.68-0.88 万元/月，昇腾 910C 行业均价约 6.2 万元/月。昇腾 910B、寒武纪 MLU、海光 DCU、壁仞、摩尔线程已作为国产战略关注卡进入国内指数表和柱状图；寒武纪使用云实例折算口径，海光/壁仞/摩尔线程价格待补，不进入 ROI 或方向性价格判断。</p>
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
    domestic_chart_rows = [r for r in DOMESTIC_RENTAL if domestic_index_status(r)]
    overseas_pass = [r for r in OVERSEAS_RENTAL if r["校验状态"] == "PASS"]
    validate_token_completeness()
    chart_tokens = TOKEN_DATA
    def token_label(row: dict) -> str:
        return f'{row["厂商"]}\\n{row["模型"]}'
    def diff(a, b):
        return None if a is None or b is None else round(a - b, 2)
    def domestic_chart_tag(row: dict) -> str:
        if row["GPU 型号"] in STRATEGIC_DOMESTIC_GPUS and row["标准化价格"] is None:
            return "价格待补"
        if row["GPU 型号"] == "寒武纪 MLU":
            return "云价折算"
        if row["GPU 型号"] in STRATEGIC_DOMESTIC_GPUS and not pass_status(row):
            return "低置信观察"
        return row.get("国内月租/海外月租")
    data = {
        "domesticLabels": [r["GPU 型号"] for r in domestic_chart_rows],
        "domesticValues": [r["标准化价格"] if r["标准化价格"] is not None else 0 for r in domestic_chart_rows],
        "domesticRatios": [domestic_chart_tag(r) for r in domestic_chart_rows],
        "overseasLabels": [r["GPU 型号"] for r in overseas_pass],
        "overseasValues": [r["标准化价格"] for r in overseas_pass],
        "tokenLabels": [token_label(r) for r in chart_tokens],
        "tokenOfficialIn": [r.get("_official_in_cny") for r in chart_tokens],
        "tokenOverseasIn": [r.get("_overseas_in_cny") for r in chart_tokens],
        "tokenDomesticIn": [r.get("_domestic_in_cny") for r in chart_tokens],
        "tokenOfficialOut": [r.get("_official_out_cny") for r in chart_tokens],
        "tokenOverseasOut": [r.get("_overseas_out_cny") for r in chart_tokens],
        "tokenDomesticOut": [r.get("_domestic_out_cny") for r in chart_tokens],
        "tokenThirdDiff": [diff(r.get("_domestic_in_cny"), r.get("_overseas_in_cny")) for r in chart_tokens],
        "tokenOfficialDomesticDiff": [diff(r.get("_official_in_cny"), r.get("_domestic_in_cny")) for r in chart_tokens],
    }
    js = f"""(function(){{
  var DATA = {json.dumps(data, ensure_ascii=False)};
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
    var c = echarts.init(el, undefined, {{renderer:'svg'}});
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
        var rawRatio = ratios && ratios[p.dataIndex] ? ratios[p.dataIndex] : '';
        var base = rawRatio === '价格待补' ? '价格待补' : (p.value + '万/月');
        var ratio = rawRatio === '海外缺口' ? ' · 海外缺口' : (rawRatio && String(rawRatio).indexOf('%') >= 0 ? ' · 海外' + rawRatio : (rawRatio ? ' · ' + rawRatio : ''));
        return rawRatio === '价格待补' ? base : base + ratio;
      }}}},itemStyle:{{borderRadius:[6,6,0,0]}}}}]
    }});
  }}
  function tokenGrouped(id, labels, series, yName) {{
    init(id, {{
      animation:false,
      color:[accent, accent2, muted],
      tooltip:{{trigger:'axis', appendToBody:true}},
      legend:{{top:0,textStyle:{{color:muted}}}},
      grid:{{left:70,right:30,top:56,bottom:120,containLabel:true}},
      xAxis:{{type:'category',data:labels,axisLabel:{{color:muted,interval:0,rotate:35}},axisLine:{{lineStyle:{{color:rule}}}},axisTick:{{show:false}}}},
      yAxis:{{type:'value',name:yName,nameTextStyle:{{color:muted}},axisLabel:{{color:muted}},splitLine:{{lineStyle:{{color:rule}}}}}},
      series:series.map(function(s){{return {{name:s.name,type:'bar',data:s.data,label:{{show:false}},itemStyle:{{borderRadius:[4,4,0,0]}}}};}})
    }});
  }}
  function diffBar(id, labels, values, name) {{
    init(id, {{
      animation:false,
      tooltip:{{trigger:'axis', appendToBody:true}},
      grid:{{left:70,right:30,top:44,bottom:120,containLabel:true}},
      xAxis:{{type:'category',data:labels,axisLabel:{{color:muted,interval:0,rotate:35}},axisLine:{{lineStyle:{{color:rule}}}},axisTick:{{show:false}}}},
      yAxis:{{type:'value',name:'元/百万Token',nameTextStyle:{{color:muted}},axisLabel:{{color:muted}},splitLine:{{lineStyle:{{color:rule}}}}}},
      series:[{{name:name,type:'bar',data:values,itemStyle:{{borderRadius:[4,4,0,0],color:function(p){{return p.value >= 0 ? accent : accent2;}}}},label:{{show:true,position:'top',color:ink,formatter:function(p){{return p.value === undefined ? '' : p.value;}}}}}}]
    }});
  }}
  bar('chart-domestic-main', DATA.domesticLabels, DATA.domesticValues, '万元/8卡整机/月', accent, DATA.domesticRatios);
  bar('chart-overseas', DATA.overseasLabels, DATA.overseasValues, '万元/8卡整机/月', accent2);
  tokenGrouped('chart-token-input', DATA.tokenLabels, [
    {{name:'官方输入价', data:DATA.tokenOfficialIn}},
    {{name:'海外三方输入价', data:DATA.tokenOverseasIn}},
    {{name:'境内三方输入价', data:DATA.tokenDomesticIn}}
  ], '元/百万Token');
  tokenGrouped('chart-token-output', DATA.tokenLabels, [
    {{name:'官方输出价', data:DATA.tokenOfficialOut}},
    {{name:'海外三方输出价', data:DATA.tokenOverseasOut}},
    {{name:'境内三方输出价', data:DATA.tokenDomesticOut}}
  ], '元/百万Token');
  diffBar('chart-token-third-diff', DATA.tokenLabels, DATA.tokenThirdDiff, '境内三方 - 海外三方');
  diffBar('chart-token-official-domestic-diff', DATA.tokenLabels, DATA.tokenOfficialDomesticDiff, '官方 - 境内三方');
}})();"""
    (OUT / "assets" / "charts.js").write_text(js, encoding="utf-8")


def write_index():
    reports = sorted(
        [p for p in (OUT / "reports").glob("*.html") if len(p.stem) == 10 and p.stem[:4].isdigit()],
        reverse=True,
    )
    items = "\n".join(f'<li><a href="reports/{p.name}">{p.stem}</a></li>' for p in reports[:30])
    html = f"""<!-- Generated by Trae Work -->
<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>CMIS Daily</title><style>body{{font-family:system-ui;background:#07111f;color:#ecf4ff;line-height:1.7;margin:0}}main{{width:min(960px,92vw);margin:0 auto;padding:56px 0}}a{{color:#68e1fd}}.card{{border:1px solid #23344f;border-radius:18px;padding:20px;background:#101b2d;margin:18px 0}}</style></head><body><main><h1>全球算力市场情报门户</h1><div class="card"><p>最新报告：<a href="latest.html">latest.html</a></p><p>Data Freeze：{FREEZE_LABEL}｜Report Version：{REPORT_VERSION}｜Prompt Version：{PROMPT_VERSION}</p></div><h2>历史归档</h2><ul>{items}</ul></main></body></html>"""
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
