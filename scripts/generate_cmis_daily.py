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
ASSET_VERSION = NOW.strftime("%Y%m%d%H%M%S")
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
        "note": "用于确认摩尔线程 MTT S4000 8卡训推一体机可租赁；未提供公开月租价格。",
    },
    {
        "id": 57,
        "tier": "国产规格/官方",
        "title": "摩尔线程 MTT S4000 官方规格",
        "url": "https://www.mthreads.com/product/S4000",
        "note": "用于确认 MTT S4000 支持单机 8卡和多机多卡训练策略。",
    },
    {
        "id": 58,
        "tier": "国产规格/媒体转发",
        "title": "壁仞 BR100 / BR104 技术与 8卡 OAM 服务器形态",
        "url": "https://ex.chinadaily.com.cn/exchange/partners/82/rss/channel/cn/columns/snl9a7/stories/WS62fb45eca3101c3ee7ae3ff6.html",
        "note": "用于确认壁仞 BR100/BR104、OAM/PCIe 板卡、8个 OAM 模组 UBB 全互联、海玄 OAM 服务器 8PFLOPS / 512GB HBM2e / 7kW 等规格线索；不提供租赁成交价。",
    },
    {
        "id": 59,
        "tier": "国产规格/平台文档",
        "title": "Gitee AI 摩尔线程 MTT S5000 集群文档",
        "url": "https://ai.gitee.com/docs/compute/clusters_gpu/moore_gpu",
        "note": "用于确认 MTT S5000 面向大模型训练推理、80GB 显存、Dense 1000 TFlops、MTLink 8卡全连接拓扑和 784GB/s 卡间互联；不提供租赁成交价。",
    },
    {
        "id": 60,
        "tier": "行业研报/租赁模型",
        "title": "天风证券：国内算力需求方兴未艾，重视算力租赁及 AI 基建投资机遇",
        "url": "https://pdf.dfcfw.com/pdf/H3_AP202504111654883638_1.pdf",
        "note": "用于校验算力租赁按“每台服务器（含8张GPU）/台/月”计租的行业模型，并以 8卡 H100 设备五年租期月租 7万元作为租赁核价锚点之一。",
    },
    {
        "id": 61,
        "tier": "采购/招投标",
        "title": "郑州大学第一附属医院 8卡 GPU 服务器项目",
        "url": "http://hnsggzyjy.henan.gov.cn/jyxx/002002/002002003/20260310/e8d630b0-3bb4-4760-875c-6742753deb55.html",
        "note": "公开资源交易结果显示 8卡 GPU 服务器项目成交单价 149 万元，用于国产/通用 8卡服务器采购价低端锚点；需结合具体 GPU 型号使用。",
    },
    {
        "id": 62,
        "tier": "采购/招投标",
        "title": "中国海洋大学八卡 GPU 服务器采购项目中标公告",
        "url": "http://www.ccgp.gov.cn/cggg/zygg/zbgg/202501/t20250115_24069441.htm",
        "note": "中标金额 119 万元，用于 8卡 GPU 服务器采购价低端样本；需解析具体 GPU 型号后才可提高置信度。",
    },
    {
        "id": 63,
        "tier": "采购/渠道报价",
        "title": "超聚变 8U AI 8卡 H20 GPU 服务器渠道价",
        "url": "https://pingjia.taobao.com/dHpXeXM5NmFwbjFqTklUZStWZ291Zz09.html",
        "note": "公开渠道页显示 8卡 H20 96G/141G 服务器约 109 万元，用于 H20 采购价候选；电商渠道需降级为 Candidate。",
    },
    {
        "id": 64,
        "tier": "采购/渠道报价",
        "title": "ZOL RTX 4090 8卡 AI 服务器报价",
        "url": "https://detail.zol.com.cn/server/index2121071.shtml",
        "note": "公开渠道页显示 RTX 4090 8卡服务器参考报价约 26 万元，用于消费级 8卡整机采购价锚点。",
    },
    {
        "id": 65,
        "tier": "采购/渠道报价",
        "title": "1688 4090/5090 8卡 GPU 服务器报价",
        "url": "http://m.1688.com/offer/919018240266.html",
        "note": "公开渠道页显示 4090/5090 8卡一体机约 37-37.94 万元，用于消费级采购价上沿候选。",
    },
    {
        "id": 66,
        "tier": "采购/框架协议线索",
        "title": "农业发展银行国产 GPU 服务器框架协议线索",
        "url": "https://xueqiu.com/7686006657/337516792",
        "note": "公开转述显示昇腾 910B 推理服务器 154.5 万元/台、训练服务器 212.2 万元/台、配件约 9.7 万元；用于 910B/910C 采购价候选，需继续追溯原始公告。",
    },
    {
        "id": 67,
        "tier": "采购/国产卡渠道",
        "title": "海光 K100 GPU 卡采购价格线索",
        "url": "https://jsj.nwpu.edu.cn/info/1599/25675.htm",
        "note": "高校采购结果显示海光 K100 64GB GPU 卡单价 4.6 万元；另有公开渠道显示 8.4 万元/张，整机采购价需加服务器、网络、维保和集成费用。",
    },
    {
        "id": 68,
        "tier": "采购/国产卡渠道",
        "title": "摩尔线程 MTT S4000 显卡报价",
        "url": "http://detail.xa.zol.com.cn/detail/2161613/price/",
        "note": "ZOL 公开报价显示 MTT S4000 参考价约 8.64 万元/张；需加服务器底座、网络、电源、维保形成 8卡整机采购价。",
    },
    {
        "id": 69,
        "tier": "采购/国产卡渠道",
        "title": "摩尔线程 MTT S4000 公开渠道价线索",
        "url": "https://mobile-phone.taobao.com/chanpin/1ca179511e98d3df4d1359ff998a7792.html",
        "note": "公开渠道页显示 MTT S4000 48GB 算力卡约 5.9-7.0 万元/张，用于摩尔线程 MTT S4000 8卡整机采购价区间低端锚点。",
    },
]

def _load_discovered_gpu() -> list[tuple[str, list[str]]] | None:
    """尝试加载动态发现的 GPU 列表；失败或不存在时返回 None，回退到硬编码。"""
    path = ROOT / "data" / f"discovered_gpu_{DATE}.json"
    try:
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        baseline = data.get("baseline_groups")
        if baseline and isinstance(baseline, list):
            return [(group[0], group[1]) for group in baseline]
    except Exception as e:
        print(f"[warn] failed to load discovered GPU: {e}")
    return None


_GPU_GROUPS_FALLBACK = [
    ("Training", ["GB300", "GB200", "B300", "B200", "H200", "H100 80G", "H800", "A100 80G", "A800"]),
    ("Inference", ["L40S", "L20", "L4"]),
    ("Consumer", ["RTX 5090", "RTX 4090"]),
    ("国产", ["昇腾 910C", "昇腾 910B", "昇腾 950PR", "寒武纪 MLU370-X8", "寒武纪 MLU590", "海光 DCU K100", "海光 DCU Z100", "壁仞 BR100", "摩尔线程 MTT S4000", "摩尔线程 MTT S5000"]),
]

GPU_GROUPS = _load_discovered_gpu() or _GPU_GROUPS_FALLBACK
GPU_ORDER = [gpu for _, items in GPU_GROUPS for gpu in items]
GPU_CLASS = {gpu: group for group, items in GPU_GROUPS for gpu in items}
STRATEGIC_DOMESTIC_GPUS = {"昇腾 910B", "昇腾 950PR", "寒武纪 MLU370-X8", "寒武纪 MLU590", "海光 DCU K100", "海光 DCU Z100", "壁仞 BR100", "摩尔线程 MTT S4000", "摩尔线程 MTT S5000"}


def _load_discovered_gpu_prices() -> tuple[dict[str, dict], dict[str, dict]]:
    """加载动态发现的 GPU 价格锚点；失败时返回空字典，回退到硬编码。"""
    path = ROOT / "data" / f"discovered_gpu_{DATE}.json"
    domestic: dict[str, dict] = {}
    overseas: dict[str, tuple] = {}
    try:
        if not path.exists():
            return domestic, overseas
        data = json.loads(path.read_text(encoding="utf-8"))
        d_anchors = data.get("domestic_price_anchors", {})
        o_anchors = data.get("overseas_price_anchors", {})

        # 海外名称映射：基线名称 -> 锚点名称
        o_name_map = {
            "H100 80G": "H100 SXM",
            "A100 80G": "A100 80G SXM",
        }

        # 处理国内锚点 -> DOMESTIC_RENTAL_INPUT 格式
        for gpu, info in d_anchors.items():
            if info.get("status") == "DISCONTINUED":
                continue
            monthly = info.get("monthly_wan")
            source = info.get("monthly_source") or info.get("note", "动态采集")[:40]
            note = info.get("note", "")
            # 优先使用动态数据自带的 _price_basis，否则按来源推断
            dynamic_basis = info.get("_price_basis")
            if dynamic_basis:
                price_basis = dynamic_basis
            elif info.get("status") == "NEW_RELEASE":
                price_basis = None  # 新发布无公开价
            elif "市场核价" in source or "市场核价" in note:
                price_basis = "市场核价区间（估算）"
            elif "折算" in source or "折算" in note or "小时价反推" in source:
                price_basis = "云价折算"
            elif "SMM区间中点" in source or "低置信" in note:
                price_basis = "低置信观察"
            else:
                price_basis = "公开成交/主口径价"
            # 若没给月租但有小时价，反推月租（单卡小时 -> 8卡整机月）
            if monthly is None:
                hourly = info.get("tencent_hourly") or info.get("aliyun_hourly") or info.get("volcano_hourly") or info.get("tianyi_hourly")
                if hourly is not None:
                    monthly = round(hourly * 8 * 24 * 30 / 10000, 2)
                    source = f"{source} 小时价反推"
                    price_basis = "云价折算"
            if monthly is not None:
                conf = 85 if "SMM" in note or "样本" in note else 75
                domestic[gpu] = {
                    "original": note or f"动态采集 {gpu}",
                    "monthly_wan": monthly,
                    "price_basis": price_basis,
                    "source": source,
                    "confidence": conf,
                    "consensus": "Medium",
                    "historical": "HIST_INSUFFICIENT",
                    "status": "PASS",
                    "note": note,
                }

        # 处理海外锚点 -> dict 格式 (usd, conf, consensus, note, source)
        for gpu_base, anchor_name in o_name_map.items():
            if anchor_name in o_anchors:
                o_anchors[gpu_base] = o_anchors.pop(anchor_name)
        for gpu, info in o_anchors.items():
            prices = []
            src_labels = []
            for k in ("runpod", "lambda", "cloudgpus", "vast_median"):
                v = info.get(k)
                if v is not None:
                    prices.append(v)
                    src_labels.append(k)
            if not prices:
                continue
            usd = round(sum(prices) / len(prices), 2)
            src_cnt = len(prices)
            conf = 90 if src_cnt >= 3 else (85 if src_cnt == 2 else 80)
            consensus = "High" if src_cnt >= 3 else ("Medium" if src_cnt == 2 else "Low")
            note = f"动态采集 {gpu}：{'/'.join(src_labels)} 均价"
            source = f"海外动态采集：{'/'.join(src_labels)}"
            overseas[gpu] = {"usd": usd, "conf": conf, "consensus": consensus, "note": note, "source": source}

    except Exception as e:
        print(f"[warn] failed to load discovered GPU prices: {e}")
    return domestic, overseas


_DYNAMIC_DOMESTIC, _DYNAMIC_OVERSEAS = _load_discovered_gpu_prices()


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


def _load_discovered_token() -> list[dict] | None:
    """尝试加载动态发现的 Token 模型列表；失败时返回 None，回退到硬编码锚点。"""
    path = ROOT / "data" / f"discovered_token_{DATE}.json"
    try:
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data.get("rows", [])
        if not rows:
            return None
        result = []
        for r in rows:
            result.append(token_row(
                vendor=r["vendor"],
                model=r["model"],
                region=r["region"],
                context=r["context"],
                official_in=r.get("official_in"),
                official_out=r.get("official_out"),
                official_currency=r.get("official_currency", "USD"),
                official_source=r.get("official_source", ""),
                overseas_in_usd=r.get("overseas_in_usd"),
                overseas_out_usd=r.get("overseas_out_usd"),
                overseas_source=r.get("overseas_source", ""),
                domestic_in_cny=r.get("domestic_in_cny"),
                domestic_out_cny=r.get("domestic_out_cny"),
                domestic_source=r.get("domestic_source", ""),
                note=r.get("note", ""),
                status=r.get("status", "PASS"),
                confidence=r.get("confidence", 90),
            ))
        return result
    except Exception as e:
        print(f"[warn] failed to load discovered token: {e}")
    return None


_TOKEN_DATA_FALLBACK = [
    # —— 海外厂商 ——
    token_row("OpenAI", "GPT-5.5", "海外", "1M（标准 272K）", 5.0, 30.0, "USD", "OpenAI API 官方定价页", 5.0, 30.0, "OpenRouter / models.dev", None, None, "境内三方近似参考", "OpenAI 当前旗舰模型，编码和专业工作优化；境内三方按同类型闭源模型近似参考补齐。", 95),
    token_row("OpenAI", "GPT-5.4", "海外", "1M（标准 272K）", 2.5, 15.0, "USD", "OpenAI API 官方定价页", 2.5, 15.0, "OpenRouter / models.dev", None, None, "境内三方近似参考", "更实惠的编码/专业工作模型；境内三方用近似参考补齐。", 95),
    token_row("OpenAI", "GPT-5.4 mini", "海外", "270K", 0.75, 4.5, "USD", "OpenAI API 官方定价页", 0.75, 4.5, "models.dev / LiteLLM", None, None, "境内三方近似参考", "最强 mini 模型，适用于编码、计算机使用和子代理。", 95),
    token_row("OpenAI", "o4 Mini", "海外", "200K", 1.1, 4.4, "USD", "OpenAI API 官方定价页", 1.1, 4.4, "OpenRouter / LiteLLM", None, None, "境内三方近似参考", "o 系列深度推理轻量版；境内三方用近似参考补齐。", 90),
    token_row("Anthropic", "Claude Opus 4.8", "海外", "1M", 5.0, 25.0, "USD", "Anthropic Claude Platform 官方定价", 5.0, 25.0, "OpenRouter Models API", None, None, "境内三方近似参考", "Anthropic 旗舰模型，Opus 4.7/4.6/4.5 同价；境内三方用近似参考补齐。", 95),
    token_row("Anthropic", "Claude Sonnet 4.6", "海外", "1M", 3.0, 15.0, "USD", "Anthropic Claude Platform 官方定价", 3.0, 15.0, "OpenRouter Models API", None, None, "境内三方近似参考", "主力平衡型模型，Sonnet 4.5 同价；境内三方用近似参考补齐。", 95),
    token_row("Anthropic", "Claude Haiku 4.5", "海外", "200K", 1.0, 5.0, "USD", "Anthropic Claude Platform 官方定价", 1.0, 5.0, "OpenRouter Models API", None, None, "境内三方近似参考", "快速轻量模型；境内三方用近似参考补齐。", 90),
    token_row("Google", "Gemini 3.1 Pro", "海外", "1M", 2.0, 12.0, "USD", "Google Gemini API 官方定价", 2.0, 12.0, "models.dev", None, None, "境内三方近似参考", "Gemini 当前旗舰 Pro 模型，200K 内标准价；境内三方用近似参考补齐。", 95),
    token_row("Google", "Gemini 3.5 Flash", "海外", "1M", 1.5, 9.0, "USD", "Google Gemini API 官方定价", 1.5, 9.0, "models.dev / LiteLLM", None, None, "境内三方近似参考", "2026年5月发布，性能接近 Pro，速度提升4倍；境内三方用近似参考补齐。", 90),
    token_row("Google", "Gemini 3.1 Flash-Lite", "海外", "1M", 0.25, 1.5, "USD", "Google Gemini API 官方定价", 0.25, 1.5, "models.dev / LiteLLM", None, None, "境内三方近似参考", "轻量经济型模型；境内三方用近似参考补齐。", 88),
    token_row("Mistral", "Mistral Medium 3.5", "海外", "256K", 2.0, 7.5, "USD", "Mistral La Plateforme 官方定价", 2.0, 7.5, "海外三方同系列参考", None, None, "境内三方近似参考", "Mistral 旗舰合并模型，密集 128B 参数；三方列按同系列参考补齐。", 85),
    token_row("Mistral", "Mistral Large 3", "海外", "256K", 0.5, 1.5, "USD", "Mistral La Plateforme 官方定价", 0.5, 1.5, "海外三方同系列参考", None, None, "境内三方近似参考", "主力大模型，2025年12月发布，大幅降价 75%；三方列按同系列参考补齐。", 85),
    token_row("Mistral", "Mistral Small 4", "海外", "256K", 0.1, 0.3, "USD", "Mistral La Plateforme 官方定价", 0.1, 0.3, "海外三方同系列参考", None, None, "境内三方近似参考", "统一前沿小模型，MoE 架构；三方列按同系列参考补齐。", 82),
    token_row("Cohere", "Command A+", "海外", "128K", 2.5, 10.0, "USD", "Cohere 官方定价页", 2.5, 10.0, "海外三方同系列参考", None, None, "境内三方近似参考", "Cohere 最新旗舰 MoE 模型，218B 总/25B 活跃，多模态；三方列按同系列参考补齐。", 85),
    token_row("Cohere", "Command R+", "海外", "128K", 2.5, 10.0, "USD", "Cohere 官方定价页", 2.5, 10.0, "海外三方同系列参考", None, None, "境内三方近似参考", "上一代旗舰，优化于 RAG 与多步工具调用；三方列按同系列参考补齐。", 82),
    token_row("xAI Grok", "Grok 4.3", "海外", "1M", 1.25, 2.5, "USD", "xAI 官方文档", 1.25, 2.5, "OpenRouter / models.dev", None, None, "境内三方近似参考", "xAI 当前旗舰，2026年4月发布，价格大幅下调，196 token/s 高速输出。", 90),
    token_row("xAI Grok", "Grok 4 Fast", "海外", "256K", 0.2, 0.5, "USD", "xAI 官方文档", 0.2, 0.5, "OpenRouter / models.dev", None, None, "境内三方近似参考", "快速经济型模型，日常对话/内容创作；境内三方用近似参考补齐。", 85),
    token_row("Meta Llama", "Llama 4 Maverick", "海外", "1M", 0.3, 0.6, "USD", "主流托管平台代表性价格（Together/Fireworks）", 0.3, 0.6, "Together.ai / Fireworks.ai", None, None, "境内三方近似参考", "Meta 旗舰 MoE 模型（400B 总参数），开源模型，无官方 per-token 定价，取主流托管平台中位价。", 80),
    token_row("Meta Llama", "Llama 4 Scout", "海外", "128K", 0.15, 0.35, "USD", "主流托管平台代表性价格（Together/Fireworks）", 0.15, 0.35, "Together.ai / Fireworks.ai", None, None, "境内三方近似参考", "小型高性能 MoE（109B 总/17B 活跃），开源模型，取主流托管平台代表性价格。", 78),
    # —— 国产厂商 ——
    token_row("DeepSeek", "DeepSeek-V4-Pro", "国产", "1M", 3.0, 6.0, "CNY", "DeepSeek API 官方定价", 0.435, 0.87, "OpenRouter / Together.ai", 12.0, 24.0, "硅基流动精确同名", "DeepSeek 当前旗舰；硅基流动精确匹配 12/24；官方价与境内渠道价差单列。", 95),
    token_row("DeepSeek", "DeepSeek-V4-Flash", "国产", "1M", 1.0, 2.0, "CNY", "DeepSeek API 官方定价", 0.09, 0.18, "OpenRouter / Together.ai", 1.0, 2.0, "硅基流动精确同名", "DeepSeek 高性价比主力；硅基流动精确匹配 1/2。", 95),
    token_row("阿里云/通义千问", "Qwen3.7-Max", "国产", "1M", 12.0, 36.0, "CNY", "阿里云百炼官方定价", 1.25, 3.75, "OpenRouter / Together.ai", None, None, "硅基流动同系列参考", "阿里旗舰模型；境内三方按同系列参考补齐。", 95),
    token_row("阿里云/通义千问", "Qwen3.7-Plus", "国产", "1M", 2.0, 8.0, "CNY", "阿里云百炼官方定价", 0.32, 1.28, "OpenRouter / Together.ai", None, None, "硅基流动同系列参考", "阿里主力平衡模型，0-256K 非思考模式官方价；三方按同系列参考补齐。", 95),
    token_row("火山方舟/豆包", "Doubao-Seed-1.6", "国产", "256K", 0.8, 2.0, "CNY", "火山方舟官方定价", None, None, "海外三方同系列参考", None, None, "境内三方同系列参考", "豆包当前主力模型，0-32K 短输出在线推理官方价；三方列按同系列参考补齐。", 95),
    token_row("火山方舟/豆包", "Doubao-Seed-1.6-Flash", "国产", "256K", 0.15, 1.5, "CNY", "火山方舟官方定价", None, None, "海外三方同系列参考", 1.5, 4.0, "硅基流动 Seed-OSS-36B（同系列参考）", "火山 Flash 版官方价；硅基流动 Seed-OSS-36B 1.5/4 作为同系列参考。", "PASS", 90),
    token_row("火山方舟/豆包", "Doubao-Seed-1.6-Thinking", "国产", "256K", 0.8, 8.0, "CNY", "火山方舟官方定价", None, None, "海外三方同系列参考", None, None, "境内三方同系列参考", "豆包思考版模型，0-32K 档思考模式；三方列按同系列参考补齐。", 90),
    token_row("腾讯混元", "Hunyuan-Hy3", "国产", "256K", 1.0, 4.0, "CNY", "腾讯云混元官方定价（Hy3 2026.7.6 发布）", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "腾讯混元最新旗舰 Hy3，MoE 架构，295B 总参数，256K 上下文，开源 Apache 2.0；三方列按同系列参考补齐。", 95),
    token_row("腾讯混元", "Hunyuan-role-latest", "国产", "官方未明确", 2.4, 9.6, "CNY", "腾讯云混元官方定价", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "腾讯混元角色模型官方价；三方平台按混元同系列参考价补齐。", 92),
    token_row("腾讯混元", "Hunyuan-A13B", "国产", "128K", 0.5, 2.0, "CNY", "腾讯云混元官方定价", 0.14, 0.57, "OpenRouter Models API", 1.0, 4.0, "硅基流动同系列参考", "腾讯混元轻量主力；硅基流动 Hunyuan-A13B 1/4 作为同系列参考。", 92),
    token_row("智谱 GLM / Z.ai", "GLM-5.2", "国产", "1M", 8.0, 28.0, "CNY", "智谱开放平台官方定价", 0.93, 3.0, "OpenRouter Models API", 8.0, 28.0, "硅基流动精确同名", "智谱当前旗舰，官方价输入 8、输出 28；硅基流动精确匹配 8/28。", 98),
    token_row("智谱 GLM / Z.ai", "GLM-5.1 Pro", "国产", "200K", 6.0, 24.0, "CNY", "智谱开放平台官方定价", 1.4, 4.4, "Together.ai / Fireworks.ai", 6.0, 24.0, "硅基流动同系列参考", "智谱上一代旗舰，32K 内 6/24；三方列按同系列参考补齐。", 95),
    token_row("百度文心", "ERNIE 5.1", "国产", "128K", 4.0, 18.0, "CNY", "百度千帆官方定价", None, None, "海外三方同系列参考", None, None, "硅基流动同系列参考", "百度千帆 ERNIE 5.1 最新旗舰，智能体、知识、推理、深度搜索全面升级；三方列按同系列参考补齐。", 92),
    token_row("百度文心", "ERNIE-4.5-Turbo", "国产", "32K", 0.8, 3.2, "CNY", "百度千帆官方定价", 0.42, 1.25, "OpenRouter 近似模型", None, None, "硅基流动同系列参考", "ERNIE 4.5 Turbo 主力量产版本；三方列按同系列参考补齐。", 90),
    token_row("Kimi / Moonshot", "Kimi K2.7 Code", "国产", "256K", 6.5, 27.0, "CNY", "Kimi 开放平台官方定价", 0.719, 3.49, "OpenRouter / Together.ai", 6.5, 27.0, "硅基流动精确同名", "Kimi 最强编程模型；硅基流动精确匹配 6.5/27。", 95),
    token_row("Kimi / Moonshot", "Kimi K2.6", "国产", "256K", 6.5, 27.0, "CNY", "Kimi 开放平台官方定价", 0.66, 3.41, "OpenRouter / Together.ai", 6.5, 27.0, "硅基流动精确同名", "Kimi 最新最智能多模态模型；硅基流动精确匹配 6.5/27。", 95),
    token_row("MiniMax", "MiniMax-M3 标准层 ≤512K", "国产", "≤512K", 2.1, 8.4, "CNY", "MiniMax 开放平台官方定价", 0.3, 1.2, "OpenRouter / Together.ai", 2.1, 8.4, "硅基流动 MiniMax-M2.5（同系列参考）", "MiniMax 当前主力，永久五折后价；硅基流动 M2.5 2.1/8.4 作为同系列参考。", 95),
    token_row("MiniMax", "MiniMax-M3 标准层 >512K", "国产", ">512K", 4.2, 16.8, "CNY", "MiniMax 开放平台官方定价", None, None, "海外三方同系列参考", None, None, "境内三方同系列参考", "MiniMax M3 长上下文档，永久五折后价；三方列按同系列参考补齐。", 92),
    token_row("讯飞星火", "Spark X2", "国产", "官方未明确", 1.0, 2.0, "CNY", "讯飞星火官方定价页", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "讯飞星火当前旗舰 X2-Flash 参考价；海外与境内三方采用近似参考补齐。", "PASS", 78),
    token_row("讯飞星火", "Spark Max", "国产", "32K", 21.0, 21.0, "CNY", "讯飞星火官方定价页", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "讯飞星火 Max 版，按 0.21 元/万 tokens 折算；三方采用近似参考补齐。", "PASS", 78),
    token_row("百川智能", "Baichuan-M3-Plus", "国产", "32K", 5.0, 9.0, "CNY", "百川智能官方定价页", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "百川当前主力 M3-Plus，官方价 5/9 元/百万 tokens；三方采用近似参考补齐。", 90),
    token_row("百川智能", "Baichuan-M3", "国产", "32K", 10.0, 30.0, "CNY", "百川智能官方定价页", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "百川旗舰 M3，官方价 10/30 元/百万 tokens；三方采用近似参考补齐。", 90),
    token_row("零一万物", "Yi-Lightning", "国产", "官方未明确", 0.99, 0.99, "CNY", "零一万物官方公开定价", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "零一万物旗舰 MoE 模型，主打极致性价比，0.99 元/百万 tokens 输入输出同价。", 82),
    token_row("零一万物", "Yi-Large", "国产", "32K", 20.0, 20.0, "CNY", "零一万物官方公开定价", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "零一万物 Yi-Large，输入输出同价；三方采用近似参考补齐。", 80),
    token_row("阶跃星辰", "Step 3.5 Flash", "国产", "官方未明确", 0.7, 2.1, "CNY", "阶跃星辰官方定价", None, None, "海外三方同系列参考", 0.7, 2.1, "硅基流动 Step-3.5-Flash（精确同名）", "阶跃当前主力；硅基流动精确匹配 Step-3.5-Flash 0.7/2.1。", 92),
    token_row("阶跃星辰", "Step-R1-V-Mini", "国产", "官方未明确", 2.5, 8.0, "CNY", "阶跃星辰官方定价", None, None, "海外三方同系列参考", None, None, "境内三方同系列参考", "阶跃推理模型；三方列按同系列参考补齐。", 88),
    token_row("商汤日日新", "SenseNova-V6.5-Pro", "国产", "官方未明确", 3.0, 9.0, "CNY", "商汤日日新官方定价", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "商汤旗舰融合模态大模型，官方价 3/9 元/百万 tokens；三方采用近似参考补齐。", 85),
    token_row("商汤日日新", "SenseNova-V6.5-Turbo", "国产", "官方未明确", 1.5, 4.5, "CNY", "商汤日日新官方定价", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "商汤 Turbo 版模型，官方价 1.5/4.5 元/百万 tokens；三方采用近似参考补齐。", 82),
    token_row("昆仑万维天工", "SkyClaw-v1.0", "国产", "1M", 0.5, 4.0, "CNY", "昆仑万维天工官方发布", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "天工旗舰 Agent 模型，主打工具调用和多轮任务执行，1M 上下文；三方采用近似参考补齐。", 80),
    token_row("昆仑万维天工", "SkyClaw-v1.0-lite", "国产", "官方未明确", 0.3, 1.5, "CNY", "昆仑万维天工官方发布", None, None, "海外三方同系列参考", None, None, "境内三方近似参考", "天工轻量版 Agent 模型；三方采用近似参考补齐。", 78),
]

TOKEN_DATA = _load_discovered_token() or _TOKEN_DATA_FALLBACK

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
        "price_basis": "低置信观察",
        "price_band": "1.2-1.5",
        "price_refresh_rule": "每日优先检索 SMM、运营商、IDC、集成商和国产智算中心明确 8卡整机月租；若出现更高置信公开价，替换当前 SMM 区间中位数；否则沿用低置信观察价并保持 REVIEW。",
        "source": "SMM 算力直播（子型号待拆）",
        "confidence": 68,
        "consensus": "Low",
        "historical": "HIST_INSUFFICIENT",
        "status": "REVIEW",
        "note": "910B 子型号、形态和异地部署限制未拆清；因属于国产战略关注卡，按 SMM 区间中点进入国内指数展示，但不进入 ROI 或方向性结论。",
    },
    "寒武纪 MLU370-X8": {
        "original": "天翼云 PCH1 寒武纪云主机最大公开规格 pch1.21xlarge.3：84 vCPU / 252GB / 4×MLU370-S4 / 包月 24964.07 元；折算 8 卡云实例等效价=24964.07×2×0.85≈4.24 万元/月（国产计算加速型云主机 1-3 年 8.5 折）。另按国产8卡整机供给、云价溢价和可比租赁模型给出裸机市场核价区间 2.8-3.8 万元/月，仅作估算。",
        "monthly_wan": 4.24,
        "price_basis": "云价折算",
        "price_band": "云价折算 4.24；裸机市场核价 2.8-3.8",
        "price_refresh_rule": "每日优先检索寒武纪 MLU 8卡整机/裸机长租公开价；若找到明确市场价，用公开市场价替代云价折算；若未找到，继续使用天翼云 4卡云实例折算价，并保留裸机市场核价区间作参考。",
        "source": "天翼云 PCH1：4×MLU370-S4 云主机包月价折算为 8卡云实例等效价（非8卡整机长租成交价）",
        "confidence": 62,
        "consensus": "Low",
        "historical": "HIST_INSUFFICIENT",
        "status": "REVIEW",
        "note": "寒武纪 MLU 属于国产战略关注卡；当前入图价格基于天翼云明确 4卡云主机配置与包月价折算到 8卡云实例等效价，不是8卡整机长租成交价。裸机市场核价区间 2.8-3.8 万元/月仅用于价格带判断，不进入 ROI。",
    },
    "海光 DCU K100": {
        "original": "已确认金品 KG4208-H73 为海光 7300 双路 4U 8卡国产化 GPU 服务器，支持 8×全高全长双宽 GPU 卡。未取得公开成交月租价；按已确认 8卡服务器形态、国产智算供给线索、H100 8卡租赁研报锚点和可比国产裸机租赁带，市场核价区间估为 3.5-4.5 万元/月，中位数 4.0 万元入图。",
        "monthly_wan": 4.0,
        "price_basis": "市场核价区间（估算）",
        "price_band": "3.5-4.5",
        "price_refresh_rule": "每日优先检索海光 DCU 8卡整机、裸机、智算中心或集成商明确月租；若找到公开市场价，按来源置信度更新价格口径和标准化价格；若未找到，沿用 3.5-4.5 万元/月市场核价区间，中位数入图。",
        "source": "金品 KG4208-H73 海光双路8卡服务器配置确认；行业租赁模型与国产裸机可比区间核价（非公开成交价）",
        "confidence": 48,
        "consensus": "Low",
        "historical": "HIST_INSUFFICIENT",
        "status": "REVIEW",
        "note": "海光 DCU 属于国产战略关注卡；已确认 8卡服务器架构，但未取得公开成交月租。本期不是单卡价×8，也不是 910B 系数价，而是按 8卡形态、行业按台/月计租模型和可比国产供给做市场核价区间；需继续寻找 SMM、运营商或集成商公开报价复核，不进入 ROI。",
    },
    "壁仞 BR100": {
        "original": "已确认壁仞 BR100/BR104 具备 OAM/PCIe 板卡形态，8个 OAM 模组可置于 UBB 形成单节点8卡全互联；海玄 OAM 服务器为 8PFLOPS / 512GB HBM2e / 最大功耗 7kW。未取得公开成交月租价；按 8卡 OAM 整机形态、H100 8卡租赁研报锚点和国产高端训练卡折价，市场核价区间估为 3.8-4.8 万元/月，中位数 4.3 万元入图。",
        "monthly_wan": 4.3,
        "price_basis": "市场核价区间（估算）",
        "price_band": "3.8-4.8",
        "price_refresh_rule": "每日优先检索壁仞 BR100/BR104 8卡 OAM 整机、裸机或智算中心明确月租；若找到公开市场价，替换估算区间中位数；若未找到，沿用 3.8-4.8 万元/月市场核价区间，中位数入图。",
        "source": "壁仞 BR100/BR104 8卡 OAM 服务器形态确认；行业租赁模型与国产高端训练卡可比区间核价（非公开成交价）",
        "confidence": 48,
        "consensus": "Low",
        "historical": "HIST_INSUFFICIENT",
        "status": "REVIEW",
        "note": "壁仞 BR100 属于国产战略关注卡；已补充 BR100/BR104 8卡 OAM 服务器形态依据，但未取得公开成交月租。本期按市场核价区间展示，不使用未确认卡数/型号的套餐价，不进入 ROI。",
    },
    "摩尔线程 MTT S4000": {
        "original": "UCache 公开页确认摩尔线程 S4000 8卡训推一体机可租赁；摩尔线程官方 S4000 支持单机8卡和多机多卡，Gitee AI 文档显示 MTT S5000 面向大模型训练推理，80GB 显存、Dense 1000 TFlops、MTLink 8卡全连接拓扑。未取得公开成交月租价；按已确认 8卡供给、S5000 规格提升和国产租赁可比带，市场核价区间估为 3.0-4.0 万元/月，中位数 3.5 万元入图。",
        "monthly_wan": 3.5,
        "price_basis": "市场核价区间（估算）",
        "price_band": "3.0-4.0",
        "price_refresh_rule": "每日优先检索摩尔线程 S4000/S5000 8卡训推一体机、裸机或智算中心明确月租；若找到公开市场价，替换估算区间中位数；若未找到，沿用 3.0-4.0 万元/月市场核价区间，中位数入图。",
        "source": "UCache S4000 8卡训推一体机租赁供给、摩尔线程 S4000 官方单机8卡能力、Gitee AI S5000 8卡互联规格；市场核价区间（非公开成交价）",
        "confidence": 50,
        "consensus": "Low",
        "historical": "HIST_INSUFFICIENT",
        "status": "REVIEW",
        "note": "摩尔线程 MTT S4000 属于国产战略关注卡；已确认 8卡 S4000 租赁供给、官方单机8卡能力，并补充 S5000 8卡互联规格。本期按市场核价区间展示，不把小模型项目费用或单卡价折成整机月租，不进入 ROI。",
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
        # 优先使用动态发现的价格，回退到硬编码
        item = _DYNAMIC_DOMESTIC.get(gpu) or DOMESTIC_RENTAL_INPUT.get(gpu)
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
        _basis = item.get("price_basis", "公开成交/主口径价" if status == "PASS" else "待复核")
        _note = item["note"]
        _src = item["source"]
        # 根据口径类型重写口径说明，只保留增量信息
        if "云价折算" in _basis:
            brief_note = f"{_note[:80]}..." if len(_note) > 80 else _note
        elif "市场核价" in _basis or "低置信" in _basis:
            brief_note = f"{_note[:80]}..." if len(_note) > 80 else _note
        else:
            brief_note = _src
        rows.append({
            "GPU 型号": gpu,
            "GPU 分类": GPU_CLASS[gpu],
            "热度排序": idx,
            "地区/市场": "中国大陆",
            "category": "GPU_RENT_CN",
            "主数据源": item["source"],
            "原始价格": item["original"],
            "价格口径": _basis,
            "核价区间（万元/月）": item.get("price_band", ""),
            "价格更新规则": item.get("price_refresh_rule", "每日优先检索更高置信的新报价；若无新来源，沿用当前主口径样本并保留审计备注。"),
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
            "口径说明": _note,
            "数据来源与口径": brief_note,
        })
    return rows


def overseas_rows() -> list[dict]:
    rows = []
    for idx, gpu in enumerate(GPU_ORDER, 1):
        dynamic = _DYNAMIC_OVERSEAS.get(gpu)
        fallback = OVERSEAS_HOURLY_USD.get(gpu)
        if dynamic:
            usd = dynamic["usd"]
            conf = dynamic["conf"]
            consensus = dynamic["consensus"]
            note = dynamic["note"]
            source = dynamic.get("source", "海外动态采集")
            cny = cny_from_usd(usd)
            monthly_ref = round(cny * 8 * 24 * 30 / 10000, 2)
            status = "PASS" if conf >= 70 else "REVIEW"
        elif fallback:
            usd, conf, consensus, note = fallback
            source = "硬编码锚点（待动态更新）"
            cny = cny_from_usd(usd)
            monthly_ref = round(cny * 8 * 24 * 30 / 10000, 2)
            status = "PASS" if conf >= 70 else "REVIEW"
        else:
            usd = cny = monthly_ref = None
            conf = 50
            consensus = "Low"
            note = "海外公开小时价暂不可得。"
            source = "暂无公开来源"
            status = "REVIEW"
        rows.append({
            "GPU 型号": gpu,
            "GPU 分类": GPU_CLASS[gpu],
            "热度排序": idx,
            "地区/市场": "海外",
            "category": "GPU_CLOUD",
            "主数据源": source,
            "原始价格": None if usd is None else f"USD {usd}/卡/小时",
            "标准化价格": monthly_ref,
            "标准化单位": "万元/8卡整机/月",
            "单卡小时价（人民币）": cny,
            "等效8卡月租（万元）": monthly_ref,
            "Confidence Score": conf,
            "Source Consensus": consensus,
            "校验状态": status,
        })
    return rows


DOMESTIC_RENTAL = domestic_rows()
OVERSEAS_RENTAL = overseas_rows()

PROCUREMENT_INPUT = {
    "H100 80G": {"purchase_min_wan": 230, "purchase_mid_wan": 275, "purchase_max_wan": 320, "basis": "市场核价区间（估算）", "source": "BIZON H100/H200 配置价、公开 8卡 GPU 服务器中标样本、国内渠道核价", "confidence": 58, "status": "REVIEW", "note": "H100 8卡 HGX 国内采购价公开成交样本稀缺；本期按海外整机配置价、国内招投标通用 8卡服务器样本和渠道核价给出 230-320 万元区间。"},
    "H20": {"purchase_min_wan": 100, "purchase_mid_wan": 120, "purchase_max_wan": 140, "basis": "三方渠道价/市场核价", "source": "超聚变 8U AI 8卡 H20 服务器渠道价约 109 万元；结合 H20 141GB 供需溢价核价", "confidence": 55, "status": "REVIEW", "note": "H20 8卡整机存在公开渠道价线索，但非政府中标或厂商官方报价；按 100-140 万元区间进入参考测算。"},
    "A100 80G": {"purchase_min_wan": 90, "purchase_mid_wan": 115, "purchase_max_wan": 140, "basis": "市场核价区间（估算）", "source": "BIZON A100 80GB 配置价、国内 8卡 GPU 服务器中标样本、存量卡渠道价", "confidence": 55, "status": "REVIEW", "note": "A100 80G 已进入存量/二级市场，公开 8卡整机成交价分散；按 90-140 万元区间做采购成本参考。"},
    "RTX 5090": {"purchase_min_wan": 28, "purchase_mid_wan": 34, "purchase_max_wan": 40, "basis": "三方渠道价", "source": "1688 4090/5090 8卡一体机约 37-37.94 万元，结合 RTX 5090 单卡溢价和整机集成成本核价", "confidence": 60, "status": "REVIEW", "note": "消费级 8卡整机渠道价波动大，需持续跟踪显卡现货与整机集成商报价。"},
    "RTX 4090": {"purchase_min_wan": 18, "purchase_mid_wan": 23, "purchase_max_wan": 28, "basis": "三方渠道价", "source": "ZOL RTX 4090 8卡服务器约 26 万元、1688 4090/5090 一体机区间作交叉参考", "confidence": 62, "status": "REVIEW", "note": "RTX 4090 单卡与整机渠道充足，但税费、保修、供电散热和品牌差异明显；按 18-28 万元做参考测算。"},
    "昇腾 910C": {"purchase_min_wan": 170, "purchase_mid_wan": 220, "purchase_max_wan": 270, "basis": "市场核价区间（估算）", "source": "昇腾 910B 框架协议价、910C 供需溢价和国产高端训练服务器市场核价", "confidence": 48, "status": "REVIEW", "note": "910C 明确 8卡整机采购成交价仍少；按 910B 框架协议训练服务器价格带上修估算，需继续追踪运营商和银行集采。"},
    "昇腾 910B": {"purchase_min_wan": 155, "purchase_mid_wan": 190, "purchase_max_wan": 225, "basis": "框架协议线索/市场核价", "source": "农业发展银行国产 GPU 服务器框架协议线索：910B 推理服务器 154.5 万元/台、训练服务器 212.2 万元/台、配件约 9.7 万元", "confidence": 52, "status": "REVIEW", "note": "910B 采购价有框架协议线索，但原始公告仍需追溯；租赁端价格受 B2/B3/B4 子型号、库存和生态迁移影响，毛回本仅作风险观察。"},
    "寒武纪 MLU370-X8": {"purchase_min_wan": 20, "purchase_mid_wan": 30, "purchase_max_wan": 40, "basis": "三方渠道价/市场核价", "source": "MLU370-S4/X8 公开卡价与国产 8卡整机渠道核价", "confidence": 40, "status": "REVIEW", "note": "寒武纪 MLU370-X8 当前租赁价为云价折算，采购价按 MLU370 卡价和整机集成成本估算；二者口径不同，毛回本不进入 ROI 结论。"},
    "海光 DCU K100": {"purchase_min_wan": 60, "purchase_mid_wan": 78, "purchase_max_wan": 95, "basis": "公开卡价/市场核价", "source": "海光 K100 64GB GPU 卡高校采购单价 4.6 万元、公开渠道 8.4 万元/张，加服务器底座和集成成本核价", "confidence": 56, "status": "REVIEW", "note": "海光 DCU K100 采购价按单卡公开价×8加整机底座、网络、电源、维保和集成成本估算；需继续补 8卡整机中标价。"},
    "壁仞 BR100": {"purchase_min_wan": 60, "purchase_mid_wan": 80, "purchase_max_wan": 100, "basis": "市场核价区间（估算）", "source": "壁仞 BR100/BR104 8卡 OAM 服务器形态、国产高端训练卡可比价格、渠道核价", "confidence": 35, "status": "REVIEW", "note": "未取得壁仞 BR100 8卡整机公开采购价；按已确认 8卡 OAM 服务器形态和国产训练卡可比区间估算，需重点扩源。"},
    "摩尔线程 MTT S4000": {"purchase_min_wan": 65, "purchase_mid_wan": 80, "purchase_max_wan": 95, "basis": "公开卡价/市场核价", "source": "MTT S4000 公开报价约 5.9-8.64 万元/张，叠加 8卡服务器底座、网络、供电和维保核价", "confidence": 52, "status": "REVIEW", "note": "摩尔线程 MTT S4000 8卡整机采购价按公开单卡价和整机集成成本估算；S5000/SGX5000 需继续查官方和集成商报价。"},
}


def procurement_rows() -> list[dict]:
    rows = []
    for rent in [r for r in DOMESTIC_RENTAL if domestic_index_status(r)]:
        gpu = rent["GPU 型号"]
        item = PROCUREMENT_INPUT.get(gpu, {"purchase_min_wan": None, "purchase_mid_wan": None, "purchase_max_wan": None, "basis": "待补", "source": "未采集到采购价来源", "confidence": 20, "status": "REVIEW", "note": "采购价待补，不能进入利润测算。"})
        band = "暂不可得" if item["purchase_min_wan"] is None or item["purchase_max_wan"] is None else f'{fmt(item["purchase_min_wan"])}-{fmt(item["purchase_max_wan"])}'
        rows.append({
            "GPU 型号": gpu,
            "GPU 分类": rent["GPU 分类"],
            "采购价口径": item["basis"],
            "采购价区间（万元/8卡整机）": band,
            "采购价中位数（万元）": item["purchase_mid_wan"],
            "采购数据源": item["source"],
            "采购 Confidence": item["confidence"],
            "采购校验状态": item["status"],
            "采购备注": item["note"],
        })
    return rows


PROCUREMENT = procurement_rows()


def profit_rows() -> list[dict]:
    rows = []
    domestic = {r["GPU 型号"]: r for r in DOMESTIC_RENTAL if domestic_index_status(r)}
    procurement = {r["GPU 型号"]: r for r in PROCUREMENT}
    for gpu in [r["GPU 型号"] for r in DOMESTIC_RENTAL if domestic_index_status(r)]:
        rent = domestic.get(gpu)
        p = procurement.get(gpu)
        rent_monthly = rent.get("标准化价格") if rent else None
        purchase_mid = p.get("采购价中位数（万元）") if p else None
        monthly_yield = None if rent_monthly is None or purchase_mid in (None, 0) else round(rent_monthly / purchase_mid * 100, 2)
        payback = None if rent_monthly in (None, 0) or purchase_mid is None else round(purchase_mid / rent_monthly, 1)
        strong_roi = bool(rent and p and pass_status(rent) and p["采购校验状态"] == "PASS" and p["采购 Confidence"] >= 70)
        if strong_roi:
            roi_status = "可进入 ROI"
            conclusion = "租赁价与采购价均通过校验，可用于正式 ROI。"
        else:
            roi_status = "参考测算"
            conclusion = "租赁价或采购价仍含 REVIEW/估算口径，仅展示毛回本，不进入方向性利润结论。"
        rows.append({
            "GPU 型号": gpu,
            "租赁价格（万元/月）": rent_monthly,
            "租赁价格口径": rent.get("价格口径") if rent else "无",
            "采购价区间（万元）": p.get("采购价区间（万元/8卡整机）") if p else "暂不可得",
            "采购价中位数（万元）": purchase_mid,
            "采购价口径": p.get("采购价口径") if p else "待补",
            "月租/采购价中位数": None if monthly_yield is None else f"{monthly_yield}%",
            "毛回本（月）": payback,
            "ROI 状态": roi_status,
            "测算说明": conclusion,
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


def _load_dynamic_sources() -> list[dict]:
    """从 discover_latest.py 生成的 JSON 中读取当天实际采集的来源。"""
    sources: list[dict] = []
    for path in (ROOT / "data" / f"discovered_token_{DATE}.json", ROOT / "data" / f"discovered_gpu_{DATE}.json"):
        try:
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                for s in data.get("dynamic_sources", []):
                    if not any(existing.get("url") == s.get("url") for existing in sources):
                        sources.append(s)
        except Exception as e:
            print(f"[warn] failed to load dynamic sources from {path}: {e}")
    return sources


# 合并动态来源到 SNAPSHOT（动态优先，静态补充）
_dynamic_sources = _load_dynamic_sources()
if _dynamic_sources:
    seen_urls = {s["url"] for s in _dynamic_sources}
    for s in SOURCES:
        if s.get("url") not in seen_urls:
            _dynamic_sources.append(s)
    SNAPSHOT["sources"] = _dynamic_sources


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


def pill(label: str, value) -> str:
    return f'<span class="pill"><b>{html_escape(label)}</b>{html_escape(fmt(value) if isinstance(value, (int, float)) else value)}</span>'


def mobile_gpu_cards(rows: list[dict]) -> str:
    cards = []
    for row in rows:
        status = row.get("校验状态", "")
        price = fmt(row.get("标准化价格"))
        cards.append(f"""
        <article class="m-card compact">
          <div class="m-card-head"><h3>{html_escape(row.get("GPU 型号"))}</h3><span class="status {'ok' if status == 'PASS' else 'warn'}">{html_escape(status)}</span></div>
          <div class="pill-row">
            {pill("月租", f'{price} 万')}
            {pill("口径", row.get("价格口径", row.get("category", "—")))}
            {pill("置信度", row.get("Confidence Score"))}
          </div>
        </article>""")
    return "\n".join(cards)


def mobile_overseas_cards(rows: list[dict]) -> str:
    cards = []
    for row in rows:
        status = row.get("校验状态", "")
        cards.append(f"""
        <article class="m-card compact">
          <div class="m-card-head"><h3>{html_escape(row.get("GPU 型号"))}</h3><span class="status {'ok' if status == 'PASS' else 'warn'}">{html_escape(status)}</span></div>
          <div class="pill-row">
            {pill("等效月租", f'{fmt(row.get("等效8卡月租（万元）"))} 万')}
            {pill("单卡小时", f'{fmt(row.get("单卡小时价（人民币）"))} 元')}
            {pill("置信度", row.get("Confidence Score"))}
          </div>
        </article>""")
    return "\n".join(cards)


def mobile_profit_cards(rows: list[dict]) -> str:
    cards = []
    for row in rows:
        cards.append(f"""
        <article class="m-card compact">
          <div class="m-card-head"><h3>{html_escape(row.get("GPU 型号"))}</h3><span>{html_escape(row.get("ROI 状态"))}</span></div>
          <div class="pill-row">
            {pill("月租", f'{fmt(row.get("租赁价格（万元/月）"))} 万')}
            {pill("采购中位", f'{fmt(row.get("采购价中位数（万元）"))} 万')}
            {pill("毛回本", f'{fmt(row.get("毛回本（月）"))} 月')}
          </div>
          <p>{html_escape(row.get("测算说明"))}</p>
        </article>""")
    return "\n".join(cards)


def mobile_token_cards(rows: list[dict]) -> str:
    cards = []
    for row in rows:
        cards.append(f"""
        <article class="m-card compact">
          <div class="m-card-head"><div><h3>{html_escape(row.get("厂商"))}</h3><small>{html_escape(row.get("模型"))}</small></div><span>{html_escape(row.get("校验状态"))}</span></div>
          <div class="pill-row">
            {pill("官方输入", row.get("输入官方价（人民币/百万Token）"))}
            {pill("官方输出", row.get("输出官方价（人民币/百万Token）"))}
            {pill("海外三方", row.get("海外三方输入价"))}
            {pill("境内三方", row.get("境内三方输入价"))}
          </div>
        </article>""")
    return "\n".join(cards)


def source_list() -> str:
    # 直接读取 SNAPSHOT 中的 sources（已由 _load_dynamic_sources 动态合并）
    srcs = SNAPSHOT.get("sources", SOURCES)
    return "\n".join(
        f'<li id="cite-{s["id"]}"><b>[{s["tier"]}] {html_escape(s["title"])}</b><br>'
        f'<a href="{s["url"]}" target="_blank" rel="noopener">{s["url"]}</a><br>'
        f'<span>{html_escape(s["note"])}</span></li>'
        for s in srcs
    )



def main_metrics() -> list[tuple[str, str, str]]:
    pass_dom = [r for r in DOMESTIC_RENTAL if pass_status(r)]
    domestic_index_rows = [r for r in DOMESTIC_RENTAL if domestic_index_status(r)]
    strategic_rows = [r for r in DOMESTIC_RENTAL if r["GPU 型号"] in STRATEGIC_DOMESTIC_GPUS]
    review_rows = [r for r in DOMESTIC_RENTAL if r["校验状态"] in {"REVIEW", "REJECT"}]
    aux_gpu = {r["GPU 型号"] for r in OVERSEAS_RENTAL if r["标准化价格"] is not None} | {r["GPU 型号"] for r in PROCUREMENT}
    token_vendors = {r["厂商"] for r in TOKEN_DATA}
    return [
        ("国内指数样本", f"{len(domestic_index_rows)}/{len(DOMESTIC_RENTAL)}", f"含国产战略关注 {len(strategic_rows)} 个"),
        ("辅助 GPU 样本", f"{len(aux_gpu)}/{len(GPU_ORDER)}", "海外云价/采购价/候选样本"),
        ("Token 厂商覆盖", f"{len(token_vendors)}/15", "按厂商+主流模型覆盖，六个核心价格字段必须数值化"),
        ("待复核样本", f"{len(review_rows)} 条", "REVIEW/REJECT 只进审计，不进方向性结论"),
    ]


def market_summary_html() -> str:
    domestic_index_rows = [r for r in DOMESTIC_RENTAL if domestic_index_status(r)]
    pass_rows = [r for r in domestic_index_rows if pass_status(r)]
    strategic_review = [r for r in domestic_index_rows if r["GPU 型号"] in STRATEGIC_DOMESTIC_GPUS and not pass_status(r)]
    h100 = next((r for r in domestic_index_rows if r["GPU 型号"] == "H100 80G"), None)
    h100_text = f'H100 80G 国内 8卡整机月租为 {fmt(h100.get("标准化价格"))} 万元' if h100 else "H100 80G 当期主口径价格暂不可得"
    token_vendors = len({r["厂商"] for r in TOKEN_DATA})
    return (
        f"<p>本期国内算力租赁指数共展示 {len(domestic_index_rows)} 个型号，其中 {len(pass_rows)} 个为 PASS 主口径样本，{h100_text}；国产战略关注卡继续保留在指数和图表中，但低置信、云价折算和市场核价样本均标注为观察口径。</p>"
        f"<p>海外 GPU Cloud 继续作为辅助参考，不与国内长租指数混用；采购覆盖和毛回本测算只跟随国内指数型号展开。Token 价格覆盖 {token_vendors} 家厂商，展示官方价、海外三方价和境内三方价，用于观察模型 API 市场价差。</p>"
        f"<p>当前需要重点复核的是 {len(strategic_review)} 个国产战略关注样本：若后续采集到明确 8卡整机/裸机/月租或采购价，应优先用新公开价格替换市场核价区间；未取得新价前，不进入 ROI 或方向性市场结论。</p>"
    )


def render_html(relative_prefix: str = "./") -> str:
    cards = "\n".join(
        f'<article class="metric"><span>{a}</span><strong>{b}</strong><small>{c}</small></article>'
        for a, b, c in main_metrics()
    )
    domestic_index_rows = [r for r in DOMESTIC_RENTAL if domestic_index_status(r)]
    domestic_review = [r for r in DOMESTIC_RENTAL if not domestic_index_status(r)]
    overseas_pass = [r for r in OVERSEAS_RENTAL if r["校验状态"] == "PASS"]
    mobile_href = "latest-mobile.html" if relative_prefix == "./" else f"{DATE}-mobile.html"
    return f"""<!-- Generated by Trae Work -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>全球算力市场情报日报（CMIS Daily） - {DATE}</title>
  <script>
    (function(){{
      if (window.innerWidth <= 768 && !new URLSearchParams(location.search).has('desktop')) {{
        location.replace('{mobile_href}');
      }}
    }})();
  </script>
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
    .table-wrap{{overflow:auto;max-height:640px;border:1px solid var(--rule);border-radius:16px;background:rgba(255,255,255,.025);margin:16px 0 26px;box-shadow:0 12px 40px rgba(0,0,0,.18)}}
    table{{width:100%;min-width:1180px;border-collapse:collapse;font-size:13px}} th,td{{padding:10px 12px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top}}
    th{{position:sticky;top:0;background:#12213a;color:var(--accent2);z-index:1;font-weight:600;letter-spacing:.02em}}
    tr:nth-child(even){{background:rgba(255,255,255,.02)}}
    tbody tr:hover{{background:rgba(104,225,253,.06);transition:background .15s}}
    .chart{{width:100%;min-height:420px}} footer{{margin-top:60px;padding-top:28px;border-top:1px solid var(--rule)}}
    @media(max-width:768px){{h1{{font-size:28px}} h2{{margin-top:32px;font-size:20px}} .page{{padding:16px 0 40px}} header{{padding:28px 0 18px}} .metric strong{{font-size:24px}} .chart{{min-height:320px}} table{{min-width:800px;font-size:12px}} th,td{{padding:8px 10px}} figcaption{{font-size:12px}}}}
    @media(max-width:900px){{.metrics{{grid-template-columns:1fr}} .page{{width:min(98vw,760px)}}}}
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
        {market_summary_html()}
      </div>
    </section>

    <section id="coverage">
      <h2>覆盖率诊断</h2>
      <p class="note">覆盖不等于进入主指数。每张卡至少应有 Main Index、Auxiliary、Candidate、Rejected 或 Missing 状态，避免治理后报告变空。</p>
      {table(COVERAGE)}
    </section>

    <section id="domestic">
      <h2>国内算力租赁主指数</h2>
      <p class="note">高置信样本仍要求 PASS 且 Confidence≥70；昇腾 910B、寒武纪 MLU370-X8、海光 DCU K100、壁仞 BR100、摩尔线程 MTT S4000 作为国产战略关注卡强制列入指数表和柱状图。寒武纪为天翼云 4卡实例折算的 8卡云价；海光/壁仞/摩尔线程采用市场核价区间中位数入图，并在表格中显示区间和依据。柱状图按价格口径分色：主口径、低置信观察、云价折算、市场核价和价格待补分别展示。</p>
      <figure><figcaption>国内指数：万元/8卡整机/月；颜色区分主口径、低置信观察、云价折算与市场核价</figcaption><div id="chart-domestic-main" class="chart"></div></figure>
      {table(domestic_index_rows, ["GPU 型号", "GPU 分类", "价格口径", "标准化价格（万/月）", "国内月租/海外月租", "Confidence Score", "校验状态", "口径说明"] if domestic_index_rows else None)}
    </section>

    <section id="overseas">
      <h2>海外 GPU Cloud 参考</h2>
      <p class="note">海外 GPU Cloud 原始来源多为美元/卡/小时，已统一折算为人民币口径"万元/8卡整机/月"绘图和展示，单卡小时价保留在表格中作为辅助字段；海外月租仍只进入海外参考，不进入国内租赁指数。</p>
      <figure><figcaption>海外 GPU Cloud：统一折算为万元/8卡整机/月，仅供参考</figcaption><div id="chart-overseas" class="chart"></div></figure>
      {table(overseas_pass, ["GPU 型号", "主数据源", "原始价格", "标准化价格（万/月）", "单卡小时价（人民币）", "Confidence Score", "校验状态"] if overseas_pass else None)}
    </section>

    <section id="audit">
      <h2>Rejected / Review 样本</h2>
      <p class="note">以下数据不进入主图、主指数、ROI、历史结论或 AI 总结，只用于审计追踪。每日运行时应优先检索更高置信的新报价；若无新来源，沿用当前主口径样本并保留审计备注。</p>
      {table(domestic_review, [c for c in domestic_review[0].keys() if c not in ("category", "价格更新规则")] if domestic_review else None)}
    </section>

    <section id="token">
      <h2>Token 价格</h2>
      <p class="note">Token 表按"厂商 + 主流模型"覆盖，官方价来自厂商官网、官方文档或云平台官方计费页；三方价拆分为海外三方与境内三方，精确项不可得时以同系列或近似参考补齐并在来源列标注。<br><b>同价原则：</b>当官方价与三方价完全相等时，通常系第三方同步官方定价、同名模型当前标价一致，或参考价巧合重合；不等同于市场溢价或折扣缺失。</p>
      <figure><figcaption>Token 输入价：官方 vs 海外三方 vs 境内三方</figcaption><div id="chart-token-input" class="chart"></div></figure>
      <figure><figcaption>Token 输出价：官方 vs 海外三方 vs 境内三方</figcaption><div id="chart-token-output" class="chart"></div></figure>
      <figure><figcaption>三方输入价差：境内三方 - 海外三方</figcaption><div id="chart-token-third-diff" class="chart"></div></figure>
      <figure><figcaption>官方与境内三方输入价差</figcaption><div id="chart-token-official-domestic-diff" class="chart"></div></figure>
      {table(TOKEN_DATA, TOKEN_COLUMNS)}
    </section>

    <section id="profit">
      <h2>利润测算</h2>
      <p class="note">利润测算覆盖范围与国内算力租赁指数保持一致。采购价按公开招投标/框架协议、三方渠道、自媒体线索和市场核价区间分层；本期先展示月租收入 ÷ 采购价中位数和毛回本月数，不含电力、机柜、网络、维保、资金成本、税费和空置率。凡租赁价或采购价仍为 REVIEW/估算口径的样本，仅作参考测算，不进入方向性 ROI 结论。</p>
      <h3>采购价覆盖</h3>
      {table(PROCUREMENT)}
      <h3>毛回本参考</h3>
      {table(GPU_PROFIT)}
    </section>

    <section id="sources">
      <h2>数据源与口径</h2>
      <ol>{source_list()}</ol>
    </section>

    <section id="ai-summary">
      <h2>AI 总结</h2>
      <div class="panel">
        <p>本期国内服务器价格覆盖继续扩大：H100 80G 约 7.6 万元/8卡整机/月，A100 80G 约 3.15-3.8 万元/月，H20 141GB 约 4.8 万元/月，RTX 5090 约 1.2 万元/月，RTX 4090 约 0.68-0.88 万元/月，昇腾 910C 行业均价约 6.2 万元/月。昇腾 910B、寒武纪 MLU370-X8、海光 DCU K100、壁仞 BR100、摩尔线程 MTT S4000已作为国产战略关注卡进入国内指数表和柱状图；寒武纪使用云实例折算口径，海光/壁仞/摩尔线程使用市场核价区间中位数展示，均不进入 ROI。</p>
      </div>
    </section>

    <footer>
      <p class="muted">CMIS Daily {REPORT_VERSION} | Prompt {PROMPT_VERSION} | Freeze {FREEZE_LABEL}</p>
      <p class="muted" style="margin-top:8px;font-size:12px">© Gavin YszY · 算力市场情报日报</p>
    </footer>
  </main>
  <script src="{relative_prefix}_shared/js/echarts.min.js"></script>
  <script src="{relative_prefix}assets/charts.js?v={ASSET_VERSION}-{REPORT_VERSION}"></script>
</body>
</html>"""


def render_mobile_html(relative_prefix: str = "./", desktop_href: str = "latest.html") -> str:
    metrics = "\n".join(
        f'<article class="metric"><span>{a}</span><strong>{b}</strong><small>{c}</small></article>'
        for a, b, c in main_metrics()
    )
    domestic_index_rows = [r for r in DOMESTIC_RENTAL if domestic_index_status(r)]
    overseas_pass = [r for r in OVERSEAS_RENTAL if r["校验状态"] == "PASS"]
    domestic_review = [r for r in DOMESTIC_RENTAL if not domestic_index_status(r)]
    return f"""<!-- Generated by Trae Work -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <title>全球算力市场情报日报 · 手机版 - {DATE}</title>
  <style>
    :root{{--bg:#07111f;--bg2:#101b2d;--ink:#ecf4ff;--muted:#9eb0c7;--rule:#23344f;--accent:#68e1fd;--accent2:#f7c76b;--bad:#ff7a90;--good:#74e0a3;}}
    *{{box-sizing:border-box}}
    html{{scroll-behavior:smooth}}
    body{{margin:0;background:linear-gradient(180deg,#07111f 0%,#0b1424 45%,#07111f 100%);color:var(--ink);font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55;-webkit-text-size-adjust:100%}}
    a{{color:var(--accent);text-decoration:none}}
    .mobile-page{{width:min(100%,520px);margin:0 auto;padding:env(safe-area-inset-top) 8px 76px}}
    .hero{{position:sticky;top:0;z-index:10;margin:0 -8px 18px;padding:18px 8px 14px;background:linear-gradient(180deg,rgba(7,17,31,.98),rgba(7,17,31,.88));backdrop-filter:blur(12px);border-bottom:1px solid var(--rule)}}
    .eyebrow{{font-size:11px;color:var(--accent2);letter-spacing:.08em;text-transform:uppercase}}
    h1{{font-size:28px;line-height:1.08;margin:8px 0 8px;letter-spacing:-.03em}}
    h2{{font-size:20px;margin:26px 0 10px;border-left:3px solid var(--accent);padding-left:10px}}
    h3{{font-size:16px;margin:0}}
    p{{margin:8px 0;color:#dce8f8}} .note,small{{color:var(--muted)}}
    .desktop-link{{display:inline-flex;margin-top:8px;padding:6px 10px;border:1px solid var(--rule);border-radius:999px;background:rgba(255,255,255,.04);font-size:12px}}
    .metrics{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:16px 0}}
    .metric,.m-card,figure,details{{background:linear-gradient(180deg,rgba(255,255,255,.07),rgba(255,255,255,.025));border:1px solid var(--rule);border-radius:18px;box-shadow:0 12px 36px rgba(0,0,0,.22)}}
    .metric{{padding:12px}} .metric span,.metric small{{display:block;color:var(--muted);font-size:11px}} .metric strong{{display:block;color:var(--accent);font-size:22px;margin:4px 0}}
    .m-card{{padding:14px;margin:10px 0;border:1px solid rgba(255,255,255,.08);box-shadow:0 8px 24px rgba(0,0,0,.28)}} .m-card.compact{{padding:12px}}
    .m-card-head{{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:8px}}
    .m-card-head span,.status{{white-space:nowrap;border:1px solid rgba(255,255,255,.12);border-radius:999px;padding:4px 10px;font-size:11px;color:var(--muted);background:rgba(255,255,255,.04)}}
    .status.ok{{color:var(--good);border-color:rgba(116,224,163,.45);background:rgba(116,224,163,.08)}} .status.warn{{color:var(--accent2);border-color:rgba(247,199,107,.45);background:rgba(247,199,107,.08)}}
    .m-price{{font-size:30px;color:var(--accent);font-weight:800;letter-spacing:-.03em}} .m-price em{{display:block;font-size:11px;font-style:normal;color:var(--muted);font-weight:500;letter-spacing:0}}
    .pill-row{{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}}
    .pill{{display:inline-flex;gap:5px;align-items:center;padding:5px 10px;border:1px solid rgba(255,255,255,.08);border-radius:999px;background:rgba(255,255,255,.045);font-size:11px;color:var(--ink)}}
    .pill b{{color:var(--muted);font-weight:600}}
    figure{{padding:8px 0;margin:12px 0 18px}} figcaption{{font-size:13px;color:var(--accent2);font-weight:650;margin-bottom:8px;padding:0 8px}}
    .chart{{width:100%;min-height:320px}} #chart-domestic-main,#chart-overseas{{min-height:380px}} #chart-token-input,#chart-token-output,#chart-token-third-diff,#chart-token-official-domestic-diff{{min-height:600px}}
    details{{padding:0;margin:10px 0}} summary{{cursor:pointer;padding:14px;font-weight:700;color:var(--accent2)}} details[open] summary{{border-bottom:1px solid var(--rule)}}
    .details-body{{padding:8px 12px 12px}}
    .quick-nav{{position:fixed;left:0;right:0;bottom:0;z-index:20;display:flex;gap:6px;overflow:auto;padding:8px 12px calc(8px + env(safe-area-inset-bottom));background:rgba(7,17,31,.95);border-top:1px solid var(--rule);backdrop-filter:blur(12px)}}
    .quick-nav a{{flex:0 0 auto;padding:7px 10px;border:1px solid var(--rule);border-radius:999px;background:var(--bg2);font-size:12px;color:var(--ink)}}
    .missing{{color:var(--bad);font-weight:700}}
  </style>
</head>
<body>
  <main class="mobile-page">
    <header class="hero">
      <div class="eyebrow">CMIS Daily · Mobile</div>
      <h1>全球算力市场情报日报</h1>
      <p class="note">日期：{DATE}｜Freeze：{FREEZE_LABEL}｜版本：{REPORT_VERSION}</p>
      <a class="desktop-link" href="{desktop_href}?desktop=1">切换电脑版</a>
    </header>

    <section class="metrics">{metrics}</section>

    <section id="summary">
      <h2>今日结论</h2>
      <article class="m-card">
        {market_summary_html()}
      </article>
    </section>

    <section id="domestic">
      <h2>国内租赁指数</h2>
      <figure><figcaption>国内指数：手机端横向条形图</figcaption><div id="chart-domestic-main" class="chart"></div></figure>
      <details open><summary>国内租赁卡片</summary><div class="details-body">{mobile_gpu_cards(domestic_index_rows)}</div></details>
    </section>

    <section id="overseas">
      <h2>海外 GPU Cloud</h2>
      <figure><figcaption>海外参考：统一折算万元/8卡整机/月</figcaption><div id="chart-overseas" class="chart"></div></figure>
      <details open><summary>海外参考卡片</summary><div class="details-body">{mobile_overseas_cards(overseas_pass)}</div></details>
    </section>

    <section id="token">
      <h2>Token 价格</h2>
      <figure><figcaption>Token 输入价：官方 vs 海外三方 vs 境内三方</figcaption><div id="chart-token-input" class="chart"></div></figure>
      <figure><figcaption>Token 输出价：官方 vs 海外三方 vs 境内三方</figcaption><div id="chart-token-output" class="chart"></div></figure>
      <details><summary>模型价格卡片</summary><div class="details-body">{mobile_token_cards(TOKEN_DATA)}</div></details>
    </section>

    <section id="profit">
      <h2>利润测算</h2>
      <details open><summary>毛回本参考</summary><div class="details-body">{mobile_profit_cards(GPU_PROFIT)}</div></details>
    </section>

    <section id="audit">
      <h2>异常与待复核</h2>
      <details><summary>Rejected / Review 样本（{len(domestic_review)} 条）</summary><div class="details-body">{mobile_gpu_cards(domestic_review)}</div></details>
    </section>
    <footer style="text-align:center;padding:20px 0 8px;font-size:11px;color:var(--muted)">
      © Gavin YszY · 算力市场情报日报
    </footer>
  </main>
  <nav class="quick-nav">
    <a href="#summary">结论</a><a href="#domestic">国内</a><a href="#overseas">海外</a><a href="#token">Token</a><a href="#profit">利润</a><a href="#audit">审计</a>
  </nav>
  <script src="{relative_prefix}_shared/js/echarts.min.js"></script>
  <script src="{relative_prefix}assets/charts.js?v={ASSET_VERSION}-{REPORT_VERSION}"></script>
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
        if row.get("价格口径") == "市场核价区间（估算）":
            return "市场核价"
        if row["GPU 型号"] == "寒武纪 MLU370-X8":
            return "云价折算"
        if row["GPU 型号"] in STRATEGIC_DOMESTIC_GPUS and not pass_status(row):
            return "低置信观察"
        return row.get("国内月租/海外月租")
    def domestic_chart_kind(row: dict) -> str:
        if row["标准化价格"] is None:
            return "价格待补"
        kind = row.get("价格口径", "")
        if "市场核价" in kind:
            return "市场核价"
        if "云价折算" in kind:
            return "云价折算"
        if "低置信" in kind or (row["GPU 型号"] in STRATEGIC_DOMESTIC_GPUS and not pass_status(row)):
            return "低置信观察"
        return "公开成交/主口径价"
    data = {
        "domesticLabels": [r["GPU 型号"] for r in domestic_chart_rows],
        "domesticValues": [r["标准化价格"] if r["标准化价格"] is not None else 0 for r in domestic_chart_rows],
        "domesticRatios": [domestic_chart_tag(r) for r in domestic_chart_rows],
        "domesticKinds": [domestic_chart_kind(r) for r in domestic_chart_rows],
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
  var domesticPalette = {{
    '公开成交/主口径价': '#22c55e',
    '低置信观察': '#f97316',
    '云价折算': '#8b5cf6',
    '市场核价': '#38bdf8',
    '价格待补': '#64748b'
  }};
  function legendForKinds(kinds) {{
    if (!kinds) return undefined;
    var seen = {{}};
    return kinds.filter(function(k){{ if (seen[k]) return false; seen[k] = true; return true; }});
  }}
  function formatBarLabel(p, ratios) {{
    if (p.value === null || p.value === undefined || p.value === '') return '';
    var rawRatio = ratios && ratios[p.dataIndex] ? ratios[p.dataIndex] : '';
    if (isMobile) {{
      var short = '';
      if (rawRatio === '价格待补') short = '待补';
      else if (rawRatio === '海外缺口') short = '缺口';
      else if (rawRatio && String(rawRatio).indexOf('%') >= 0) short = rawRatio.replace('海外', '');
      else if (rawRatio) short = rawRatio.substring(0, 2);
      return short ? (p.value + '万·' + short) : (p.value + '万');
    }}
    var tagMap = {{'海外缺口':'缺口','云价折算':'云折','市场核价':'市核','价格待补':'待补'}};
    var tag = tagMap[rawRatio] || (rawRatio && String(rawRatio).indexOf('%') >= 0 ? rawRatio : '');
    return tag ? (p.value + '\\n' + tag) : String(p.value);
  }}
  var isMobile = window.innerWidth <= 768;
  function bar(id, labels, values, name, color, ratios, kinds) {{
    var maxVal = Math.max.apply(null, values.filter(function(v){{return v > 0;}}));
    var yMax = maxVal > 0 ? Math.ceil((maxVal * 1.3) / 5) * 5 : undefined;
    var seriesData = values.map(function(v, i) {{
      var kind = kinds && kinds[i] ? kinds[i] : '';
      var radius = isMobile ? [0,6,6,0] : [6,6,0,0];
      return {{value:v, itemStyle:{{color:domesticPalette[kind] || color, borderRadius:radius}}}};
    }});
    var series = [];
    var legend = legendForKinds(kinds);
    var labelPos = isMobile ? 'right' : 'top';
    if (legend) {{
      series = legend.map(function(kind) {{
        return {{name:kind,type:'bar',data:seriesData.map(function(d, i){{return kinds[i] === kind ? d : null;}}),barGap:'-100%',label:{{show:true,position:labelPos,color:ink,fontSize:isMobile?11:12,formatter:function(p){{return formatBarLabel(p, ratios);}}}},itemStyle:{{borderRadius:isMobile?[0,6,6,0]:[6,6,0,0]}}}};
      }});
    }} else {{
      series = [{{type:'bar',data:seriesData,label:{{show:true,position:labelPos,color:ink,fontSize:isMobile?11:12,formatter:function(p){{
        return formatBarLabel(p, ratios);
      }}}},itemStyle:{{borderRadius:isMobile?[0,6,6,0]:[6,6,0,0]}}}}];
    }}
    if (isMobile) {{
      init(id, {{
        animation:false,
        color:legend ? legend.map(function(k){{return domesticPalette[k] || color;}}) : [color],
        tooltip:{{trigger:'axis', appendToBody:true}},
        legend:legend ? {{top:0,textStyle:{{color:muted}}}} : undefined,
        grid:{{left:2,right:65,top:legend?62:36,bottom:20,containLabel:true}},
        yAxis:{{type:'category',data:labels,axisLabel:{{color:muted,interval:0,fontSize:10,width:70,overflow:'truncate',align:'right'}},axisLine:{{lineStyle:{{color:rule}}}},axisTick:{{show:false}},inverse:true}},
        xAxis:{{type:'value',name:'',max:yMax,axisLabel:{{color:muted,fontSize:10}},splitLine:{{lineStyle:{{color:rule}}}}}},
        series:series
      }});
    }} else {{
      init(id, {{
        animation:false,
        color:legend ? legend.map(function(k){{return domesticPalette[k] || color;}}) : [color],
        tooltip:{{trigger:'axis', appendToBody:true}},
        legend:legend ? {{top:0,textStyle:{{color:muted}}}} : undefined,
        grid:{{left:70,right:40,top:legend ? 80 : 52,bottom:100,containLabel:true}},
        xAxis:{{type:'category',data:labels,axisLabel:{{color:muted,interval:0,rotate:35,fontSize:11}},axisLine:{{lineStyle:{{color:rule}}}},axisTick:{{show:false}}}},
        yAxis:{{type:'value',name:name,max:yMax,nameTextStyle:{{color:muted}},axisLabel:{{color:muted}},splitLine:{{lineStyle:{{color:rule}}}}}},
        series:series
      }});
    }}
  }}
  function tokenGrouped(id, labels, series, yName) {{
    var s = series.map(function(s){{return {{name:s.name,type:'bar',data:s.data,label:{{show:false}},itemStyle:{{borderRadius:isMobile?[0,4,4,0]:[4,4,0,0]}}}};}});
    if (isMobile) {{
      init(id, {{
        animation:false,
        color:[accent, accent2, muted],
        tooltip:{{trigger:'axis', appendToBody:true}},
        legend:{{top:0,textStyle:{{color:muted}}}},
        grid:{{left:2,right:65,top:50,bottom:28,containLabel:true}},
        yAxis:{{type:'category',data:labels,axisLabel:{{color:muted,interval:0,fontSize:10,width:70,overflow:'truncate',align:'right'}},axisLine:{{lineStyle:{{color:rule}}}},axisTick:{{show:false}},inverse:true}},
        xAxis:{{type:'value',name:'',axisLabel:{{color:muted,fontSize:10}},splitLine:{{lineStyle:{{color:rule}}}}}},
        series:s
      }});
    }} else {{
      init(id, {{
        animation:false,
        color:[accent, accent2, muted],
        tooltip:{{trigger:'axis', appendToBody:true}},
        legend:{{top:0,textStyle:{{color:muted}}}},
        grid:{{left:70,right:30,top:56,bottom:120,containLabel:true}},
        xAxis:{{type:'category',data:labels,axisLabel:{{color:muted,interval:0,rotate:35}},axisLine:{{lineStyle:{{color:rule}}}},axisTick:{{show:false}}}},
        yAxis:{{type:'value',name:yName,nameTextStyle:{{color:muted}},axisLabel:{{color:muted}},splitLine:{{lineStyle:{{color:rule}}}}}},
        series:s
      }});
    }}
  }}
  function diffBar(id, labels, values, name) {{
    if (isMobile) {{
      init(id, {{
        animation:false,
        tooltip:{{trigger:'axis', appendToBody:true}},
        grid:{{left:2,right:65,top:40,bottom:28,containLabel:true}},
        yAxis:{{type:'category',data:labels,axisLabel:{{color:muted,interval:0,fontSize:10,width:70,overflow:'truncate',align:'right'}},axisLine:{{lineStyle:{{color:rule}}}},axisTick:{{show:false}},inverse:true}},
        xAxis:{{type:'value',name:'',axisLabel:{{color:muted,fontSize:10}},splitLine:{{lineStyle:{{color:rule}}}}}},
        series:[{{name:name,type:'bar',data:values,itemStyle:{{borderRadius:[0,4,4,0],color:function(p){{return p.value >= 0 ? accent : accent2;}}}},label:{{show:true,position:'right',color:ink,fontSize:10,formatter:function(p){{return p.value === undefined ? '' : p.value;}}}}}}]
      }});
    }} else {{
      init(id, {{
        animation:false,
        tooltip:{{trigger:'axis', appendToBody:true}},
        grid:{{left:70,right:30,top:44,bottom:120,containLabel:true}},
        xAxis:{{type:'category',data:labels,axisLabel:{{color:muted,interval:0,rotate:35}},axisLine:{{lineStyle:{{color:rule}}}},axisTick:{{show:false}}}},
        yAxis:{{type:'value',name:'元/百万Token',nameTextStyle:{{color:muted}},axisLabel:{{color:muted}},splitLine:{{lineStyle:{{color:rule}}}}}},
        series:[{{name:name,type:'bar',data:values,itemStyle:{{borderRadius:[4,4,0,0],color:function(p){{return p.value >= 0 ? accent : accent2;}}}},label:{{show:true,position:'top',color:ink,formatter:function(p){{return p.value === undefined ? '' : p.value;}}}}}}]
      }});
    }}
  }}
  bar('chart-domestic-main', DATA.domesticLabels, DATA.domesticValues, '万元/8卡整机/月', accent, DATA.domesticRatios, DATA.domesticKinds);
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
<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>CMIS Daily</title><style>body{{font-family:system-ui;background:#07111f;color:#ecf4ff;line-height:1.7;margin:0}}main{{width:min(960px,92vw);margin:0 auto;padding:56px 0}}a{{color:#68e1fd}}.card{{border:1px solid #23344f;border-radius:18px;padding:20px;background:#101b2d;margin:18px 0}}</style></head><body><main><h1>全球算力市场情报门户</h1><div class="card"><p>最新报告：<a href="latest.html">电脑版</a>｜<a href="latest-mobile.html">手机版</a></p><p>Data Freeze：{FREEZE_LABEL}｜Report Version：{REPORT_VERSION}｜Prompt Version：{PROMPT_VERSION}</p></div><h2>历史归档</h2><ul>{items}</ul></main></body></html>"""
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
    (OUT / "latest-mobile.html").write_text(render_mobile_html("./", "latest.html"), encoding="utf-8")
    (OUT / "reports" / f"{DATE}.html").write_text(render_html("../"), encoding="utf-8")
    (OUT / "reports" / f"{DATE}-mobile.html").write_text(render_mobile_html("../", f"{DATE}.html"), encoding="utf-8")
    write_index()


if __name__ == "__main__":
    main()
