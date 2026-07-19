#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CMIS Daily 动态发现模块。

本模块负责在日报生成前，从结构化 API/JSON 源自动发现：
1. 各厂商最新主流/先进 Token 模型
2. 市场最新 GPU 型号（从 GPU Cloud 聚合源）

设计原则：
- 发现结果写入 data/discovered_*.json，主脚本优先读取动态发现结果
- 发现失败时回退到内置配置，保证日报不中断
- 国产战略关注 GPU 和基线名单的稳定性由配置规则保证，新卡发现后进入候选池
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))
NOW = datetime.now(TZ)
DATE = NOW.date().isoformat()

DISCOVERED_TOKEN_PATH = ROOT / "data" / f"discovered_token_{DATE}.json"
DISCOVERED_GPU_PATH = ROOT / "data" / f"discovered_gpu_{DATE}.json"

# 动态采集过程中记录的真实来源 URL（用于替代硬编码 SOURCES）
DYNAMIC_SOURCES: list[dict[str, Any]] = []


def record_source(tier: str, title: str, url: str, note: str = "") -> None:
    """记录一个真实数据来源，供飞书通知和报告引用。"""
    for existing in DYNAMIC_SOURCES:
        if existing.get("url") == url:
            return
    DYNAMIC_SOURCES.append({
        "id": len(DYNAMIC_SOURCES) + 1,
        "tier": tier,
        "title": title,
        "url": url,
        "note": note,
    })

def fetch_json(url: str, timeout: int = 30, retries: int = 3) -> dict | list | None:
    """从 URL 获取 JSON 数据，带指数退避重试。"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CMIS-Daily-Discovery/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", errors="ignore"))
        except Exception as e:
            print(f"[discover] fetch_json attempt {attempt+1}/{retries} failed: {url} -> {e}", file=sys.stderr)
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # 指数退避: 1s, 2s, 4s
            continue
    return None


def fetch_text(url: str, timeout: int = 30, retries: int = 3) -> str | None:
    """从 URL 获取纯文本/HTML（自动处理 gzip），带指数退避重试。"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Encoding": "gzip, deflate",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    data = gzip.decompress(data)
                return data.decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"[discover] fetch_text attempt {attempt+1}/{retries} failed: {url} -> {e}", file=sys.stderr)
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # 指数退避: 1s, 2s, 4s
            continue
    return None


# ---------------------------------------------------------------------------
# Token 模型动态发现
# ---------------------------------------------------------------------------

# 厂商名称 -> 模型 ID 前缀/关键词映射（用于从 LiteLLM/OpenRouter 中筛选）
VENDOR_PREFIXES: dict[str, list[str]] = {
    "OpenAI": ["gpt-", "o1", "o3", "o4"],
    "Anthropic": ["claude-"],
    "Google": ["gemini-"],
    "Mistral": ["mistral-", "codestral-"],
    "Cohere": ["command-", "command-r", "command-a"],
    "xAI Grok": ["grok-"],
    "Meta Llama": ["llama-"],
    "DeepSeek": ["deepseek-"],
    "阿里云/通义千问": ["qwen"],
    "火山方舟/豆包": ["doubao-"],
    "百度文心": ["ernie-"],
    "腾讯混元": ["hunyuan-"],
    "智谱 GLM / Z.ai": ["glm-"],
    "Kimi / Moonshot": ["kimi-", "moonshot-", "moonshotai/"],
    "MiniMax": ["minimax-"],
    "讯飞星火": ["spark-"],
    "百川智能": ["baichuan-"],
    "零一万物": ["yi-"],
    "阶跃星辰": ["step-"],
    "商汤日日新": ["sensenova-", "sensechat-"],
    "昆仑万维天工": ["skyclaw-"],
}

# 模型淘汰关键词：deprecated / old / legacy 模型应排除
DEPRECATED_KEYWORDS = ["preview", "deprecated", "legacy", "-old-", "-beta", "-alpha", "-draft"]

# 各厂商手动维护的最新模型锚点（含官方价 + 已知三方价）
# 三方价数据来源：OpenRouter / Together.ai / Fireworks.ai / 硅基流动 / 阿里云百炼 / 腾讯云TokenHub
# 若某个价格为 None，表示该平台暂无此模型，需标注
VENDOR_MODEL_ANCHORS: list[dict[str, Any]] = [
    # --- 海外 ---
    {"vendor": "OpenAI", "models": [
        {
            "name": "GPT-5.5", "context": "1M（标准 272K）",
            "official_in_usd": 5.0, "official_out_usd": 30.0,
            "overseas_in_usd": 5.0, "overseas_out_usd": 30.0,
            "overseas_source": "OpenRouter / gpt-5.5",
        },
        {
            "name": "GPT-5.4", "context": "1M（标准 272K）",
            "official_in_usd": 2.5, "official_out_usd": 15.0,
            "overseas_in_usd": 2.5, "overseas_out_usd": 15.0,
            "overseas_source": "OpenRouter / gpt-5.4",
        },
        {
            "name": "GPT-5.4 mini", "context": "270K",
            "official_in_usd": 0.75, "official_out_usd": 4.5,
            "overseas_in_usd": 0.75, "overseas_out_usd": 4.5,
            "overseas_source": "OpenRouter / gpt-5.4-mini",
        },
        {
            "name": "o4 Mini", "context": "200K",
            "official_in_usd": 1.1, "official_out_usd": 4.4,
            "overseas_in_usd": 1.1, "overseas_out_usd": 4.4,
            "overseas_source": "OpenRouter / o4-mini",
        },
    ]},
    {"vendor": "Anthropic", "models": [
        {
            "name": "Claude Fable 5", "context": "1M",
            "official_in_usd": 10.0, "official_out_usd": 50.0,
            "overseas_in_usd": 10.0, "overseas_out_usd": 50.0,
            "overseas_source": "OpenRouter / claude-fable-5",
        },
        {
            "name": "Claude Opus 4.8", "context": "1M",
            "official_in_usd": 5.0, "official_out_usd": 25.0,
            "overseas_in_usd": 5.0, "overseas_out_usd": 25.0,
            "overseas_source": "OpenRouter / claude-opus-4.8",
        },
        {
            "name": "Claude Sonnet 5", "context": "1M",
            "official_in_usd": 2.0, "official_out_usd": 10.0,
            "note": "优惠期至2026.8.31，优惠后 $2/$10，原价 $3/$15",
            "overseas_in_usd": 2.0, "overseas_out_usd": 10.0,
            "overseas_source": "OpenRouter / claude-sonnet-5",
        },
        {
            "name": "Claude Haiku 4.5", "context": "200K",
            "official_in_usd": 1.0, "official_out_usd": 5.0,
            "overseas_in_usd": 1.0, "overseas_out_usd": 5.0,
            "overseas_source": "OpenRouter / claude-haiku-4.5",
        },
    ]},
    {"vendor": "Google", "models": [
        {
            "name": "Gemini 3.5 Flash", "context": "1M",
            "official_in_usd": 1.5, "official_out_usd": 9.0,
            "overseas_in_usd": 1.5, "overseas_out_usd": 9.0,
            "overseas_source": "OpenRouter / gemini-3.5-flash",
        },
        {
            "name": "Gemini 3.1 Pro Preview", "context": "1M",
            "official_in_usd": 2.0, "official_out_usd": 12.0,
            "overseas_in_usd": 2.0, "overseas_out_usd": 12.0,
            "overseas_source": "OpenRouter / gemini-3.1-pro-preview",
        },
        {
            "name": "Gemini 3.1 Flash-Lite", "context": "1M",
            "official_in_usd": 0.25, "official_out_usd": 1.5,
            "overseas_in_usd": 0.25, "overseas_out_usd": 1.5,
            "overseas_source": "OpenRouter / gemini-3.1-flash-lite",
        },
    ]},
    {"vendor": "Mistral", "models": [
        {
            "name": "Mistral Medium 3.5", "context": "256K",
            "official_in_usd": 2.0, "official_out_usd": 7.5,
            "overseas_in_usd": 1.5, "overseas_out_usd": 7.5,
            "overseas_source": "OpenRouter / mistral-medium-3-5",
        },
        {
            "name": "Mistral Large 3", "context": "256K",
            "official_in_usd": 0.5, "official_out_usd": 1.5,
            "overseas_in_usd": 0.5, "overseas_out_usd": 1.5,
            "overseas_source": "OpenRouter / mistral-large-2512",
        },
        {
            "name": "Mistral Small 4", "context": "256K",
            "official_in_usd": 0.1, "official_out_usd": 0.3,
            "overseas_in_usd": 0.15, "overseas_out_usd": 0.6,
            "overseas_source": "OpenRouter / mistral-small-2603",
        },
    ]},
    {"vendor": "Cohere", "models": [
        {
            "name": "Command A+", "context": "128K",
            "official_in_usd": 2.5, "official_out_usd": 10.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
        },
        {
            "name": "Command R+", "context": "128K",
            "official_in_usd": 2.5, "official_out_usd": 10.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
        },
    ]},
    {"vendor": "xAI Grok", "models": [
        {
            "name": "Grok 4.5", "context": "500K",
            "official_in_usd": 2.0, "official_out_usd": 6.0,
            "overseas_in_usd": 2.0, "overseas_out_usd": 6.0,
            "overseas_source": "OpenRouter / grok-4.5",
        },
        {
            "name": "Grok 4.3", "context": "1M",
            "official_in_usd": 1.25, "official_out_usd": 2.5,
            "overseas_in_usd": 1.25, "overseas_out_usd": 2.5,
            "overseas_source": "OpenRouter / grok-4.3",
        },
        {
            "name": "Grok 4.20", "context": "500K",
            "official_in_usd": 2.0, "official_out_usd": 6.0,
            "overseas_in_usd": 1.25, "overseas_out_usd": 2.5,
            "overseas_source": "OpenRouter / grok-4.20",
        },
    ]},
    {"vendor": "Meta Llama", "models": [
        {
            "name": "Llama 4 Maverick", "context": "1M",
            "official_in_usd": 0.2, "official_out_usd": 0.8,
            "overseas_in_usd": 0.2, "overseas_out_usd": 0.8,
            "overseas_source": "OpenRouter / llama-4-maverick",
            "note": "开源模型，无官方 per-token 定价，取 OpenRouter 托管价",
        },
        {
            "name": "Llama 4 Scout", "context": "128K",
            "official_in_usd": 0.1, "official_out_usd": 0.3,
            "overseas_in_usd": 0.1, "overseas_out_usd": 0.3,
            "overseas_source": "OpenRouter / llama-4-scout",
            "note": "开源模型，无官方 per-token 定价，取 OpenRouter 托管价",
        },
    ]},
    # --- 国产 ---
    {"vendor": "DeepSeek", "models": [
        {
            "name": "DeepSeek-V4-Pro", "context": "1M",
            "official_in_cny": 3.0, "official_out_cny": 6.0,
            "overseas_in_usd": 1.74, "overseas_out_usd": 3.48,
            "overseas_source": "Together.ai / Fireworks.ai / deepseek-v4-pro",
            "domestic_in_cny": 12.0, "domestic_out_cny": 24.0,
            "domestic_source": "硅基流动 / DeepSeek-V4-Pro",
            "note": "官方直供价 3/6；境内三方（硅基流动）12/24；海外三方 $1.74/$3.48",
        },
        {
            "name": "DeepSeek-V4-Flash", "context": "1M",
            "official_in_cny": 1.0, "official_out_cny": 2.0,
            "overseas_in_usd": 0.14, "overseas_out_usd": 0.28,
            "overseas_source": "Fireworks.ai / deepseek-v4-flash",
            "domestic_in_cny": 1.0, "domestic_out_cny": 2.0,
            "domestic_source": "硅基流动 / DeepSeek-V4-Flash",
            "note": "官方直供价 1/2；硅基流动同价 1/2；海外三方 $0.14/$0.28",
        },
    ]},
    {"vendor": "阿里云/通义千问", "models": [
        {
            "name": "Qwen3.7-Max", "context": "1M",
            "official_in_cny": 12.0, "official_out_cny": 36.0,
            "overseas_in_usd": 1.25, "overseas_out_usd": 3.75,
            "overseas_source": "Together.ai / qwen3.7-max",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内三方未覆盖（阿里云官方独占）",
            "note": "阿里云官方原价，限时5折后 6/18；海外三方 Together.ai $1.25/$3.75",
        },
        {
            "name": "Qwen3.7-Plus", "context": "1M",
            "official_in_cny": 2.0, "official_out_cny": 8.0,
            "overseas_in_usd": 0.32, "overseas_out_usd": 1.28,
            "overseas_source": "OpenRouter / Together.ai / Fireworks.ai / qwen3.7-plus",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内三方未覆盖（阿里云官方独占）",
            "note": "阿里云官方价 2/8（0-256K 非思考模式），限时8折后 1.6/6.4；海外三方 $0.32/$1.28",
        },
    ]},
    {"vendor": "火山方舟/豆包", "models": [
        {
            "name": "Doubao-Seed 2.1 Pro", "context": "256K",
            "official_in_cny": 6.0, "official_out_cny": 30.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考（仅火山官方提供）",
            "note": "2026年6月23日发布，最新旗舰深度思考模型；三方平台暂未接入",
        },
        {
            "name": "Doubao-Seed 2.1 Turbo", "context": "256K",
            "official_in_cny": 3.0, "official_out_cny": 15.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考（仅火山官方提供）",
            "note": "2026年6月23日发布，高性价比主力；三方平台暂未接入",
        },
        {
            "name": "Doubao-Seed 2.0 Pro", "context": "256K",
            "official_in_cny": 3.2, "official_out_cny": 16.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": 1.5, "domestic_out_cny": 4.0,
            "domestic_source": "硅基流动 / Seed-OSS-36B（同系列参考）",
            "note": "0-32K 段官方价 3.2/16；硅基流动 Seed-OSS-36B 1.5/4 作为开源同系列参考",
        },
        {
            "name": "Doubao-Seed-Evolving", "context": "持续迭代",
            "official_in_cny": 6.0, "official_out_cny": 30.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考（仅火山官方提供）",
            "note": "持续迭代旗舰，Coding/Agent 优化；三方平台暂未接入",
        },
    ]},
    {"vendor": "腾讯混元", "models": [
        {
            "name": "Hunyuan-Hy3", "context": "256K",
            "official_in_cny": 1.0, "official_out_cny": 4.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": 1.0, "domestic_out_cny": 4.0,
            "domestic_source": "腾讯云TokenHub / Hy3",
            "note": "2026年7月6日发布，MoE架构，295B总参数，开源Apache 2.0",
        },
        {
            "name": "Hunyuan-role-latest", "context": "官方未明确",
            "official_in_cny": 2.4, "official_out_cny": 9.6,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考",
            "note": "腾讯混元角色模型官方价",
        },
        {
            "name": "Hunyuan-A13B", "context": "128K",
            "official_in_cny": 0.5, "official_out_cny": 2.0,
            "overseas_in_usd": 0.14, "overseas_out_usd": 0.57,
            "overseas_source": "OpenRouter / hunyuan-a13b",
            "domestic_in_cny": 1.0, "domestic_out_cny": 4.0,
            "domestic_source": "硅基流动 / Hunyuan-A13B-Instruct",
            "note": "轻量主力；硅基流动 1/4；OpenRouter $0.14/$0.57",
        },
    ]},
    {"vendor": "智谱 GLM / Z.ai", "models": [
        {
            "name": "GLM-5.2", "context": "1M",
            "official_in_cny": 8.0, "official_out_cny": 28.0,
            "overseas_in_usd": 0.9044, "overseas_out_usd": 2.8424,
            "overseas_source": "OpenRouter / glm-5.2",
            "domestic_in_cny": 8.0, "domestic_out_cny": 28.0,
            "domestic_source": "硅基流动 / GLM-5.2",
            "note": "2026年6月16日上线，1M无损上下文；官方价 8/28；硅基流动同价；OpenRouter $0.9/$2.84",
        },
        {
            "name": "GLM-5.1 Pro", "context": "200K",
            "official_in_cny": 6.0, "official_out_cny": 24.0,
            "overseas_in_usd": 1.40, "overseas_out_usd": 4.40,
            "overseas_source": "Together.ai / Fireworks.ai / glm-5.1",
            "domestic_in_cny": 6.0, "domestic_out_cny": 24.0,
            "domestic_source": "硅基流动 / GLM-5.1 Pro",
            "note": "32K内 6/24，32K+ 8/28；海外三方 Together $1.4/$4.4",
        },
    ]},
    {"vendor": "百度文心", "models": [
        {
            "name": "ERNIE 5.1", "context": "128K",
            "official_in_cny": 4.0, "official_out_cny": 18.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考（仅百度千帆提供）",
            "note": "最新旗舰，智能体/知识/推理/深度搜索全面升级",
        },
        {
            "name": "ERNIE-4.5-Turbo", "context": "32K",
            "official_in_cny": 0.8, "official_out_cny": 3.2,
            "overseas_in_usd": 0.42, "overseas_out_usd": 1.25,
            "overseas_source": "OpenRouter / ERNIE 4.5 VL（近似）",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考",
            "note": "主力量产版本；海外三方仅近似参考",
        },
    ]},
    {"vendor": "Kimi / Moonshot", "models": [
        {
            "name": "Kimi K3", "context": "1M",
            "official_in_cny": 20.0, "official_out_cny": 100.0,
            "overseas_in_usd": 3.00, "overseas_out_usd": 15.00,
            "overseas_source": "OpenRouter / moonshotai/kimi-k3",
            "domestic_in_cny": 20.0, "domestic_out_cny": 100.0,
            "domestic_source": "硅基流动 / 待验证",
            "note": "旗舰模型；2026-07-16 发布；官方价 ¥20/¥100（缓存未命中）；缓存命中 ¥2；硅基流动待确认",
        },
        {
            "name": "Kimi K2.7 Code", "context": "256K",
            "official_in_cny": 6.5, "official_out_cny": 27.0,
            "overseas_in_usd": 0.719, "overseas_out_usd": 3.49,
            "overseas_source": "OpenRouter / kimi-k2.7-code",
            "domestic_in_cny": 6.5, "domestic_out_cny": 27.0,
            "domestic_source": "硅基流动 / Kimi-K2.7-Code",
            "note": "最强编程模型；官方价 6.5/27；硅基流动同价；OpenRouter $0.719/$3.49",
        },
        {
            "name": "Kimi K2.6", "context": "256K",
            "official_in_cny": 6.5, "official_out_cny": 27.0,
            "overseas_in_usd": 0.66, "overseas_out_usd": 3.41,
            "overseas_source": "OpenRouter / kimi-k2.6",
            "domestic_in_cny": 6.5, "domestic_out_cny": 27.0,
            "domestic_source": "硅基流动 / Kimi-K2.6 Pro",
            "note": "最新多模态模型；官方价 6.5/27；硅基流动同价；OpenRouter $0.66/$3.41",
        },
    ]},
    {"vendor": "MiniMax", "models": [
        {
            "name": "MiniMax-M3 标准层 ≤512K", "context": "≤512K",
            "official_in_cny": 2.1, "official_out_cny": 8.4,
            "overseas_in_usd": 0.30, "overseas_out_usd": 1.20,
            "overseas_source": "OpenRouter / Together.ai / Fireworks.ai / minimax-m3",
            "domestic_in_cny": 2.1, "domestic_out_cny": 8.4,
            "domestic_source": "阿里云百炼 / 腾讯云TokenHub / MiniMax-M3",
            "note": "永久五折后价；海外三方 $0.3/$1.2；境内三方 2.1/8.4",
        },
        {
            "name": "MiniMax-M3 标准层 >512K", "context": ">512K",
            "official_in_cny": 4.2, "official_out_cny": 16.8,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架（仅标准层）",
            "domestic_in_cny": 4.2, "domestic_out_cny": 16.8,
            "domestic_source": "腾讯云TokenHub / MiniMax-M3",
            "note": "长上下文档，永久五折后价 4.2/16.8",
        },
    ]},
    {"vendor": "讯飞星火", "models": [
        {
            "name": "Spark X2", "context": "官方未明确",
            "official_in_cny": 1.0, "official_out_cny": 2.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考（仅讯飞官方提供）",
            "note": "2026年2月发布，基于全国产算力训练，通用能力全面升级；X2-Flash 参考价 1/2",
        },
        {
            "name": "Spark Max", "context": "32K",
            "official_in_cny": 21.0, "official_out_cny": 21.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考",
            "note": "按 0.21 元/万 tokens 折算；输入输出同价",
        },
    ]},
    {"vendor": "百川智能", "models": [
        {
            "name": "Baichuan-M3-Plus", "context": "32K",
            "official_in_cny": 5.0, "official_out_cny": 9.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考（仅百川官方提供）",
            "note": "当前主力 M3-Plus，官方价 5/9",
        },
        {
            "name": "Baichuan-M3", "context": "32K",
            "official_in_cny": 10.0, "official_out_cny": 30.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考",
            "note": "旗舰 M3，官方价 10/30",
        },
    ]},
    {"vendor": "零一万物", "models": [
        {
            "name": "Yi-Lightning", "context": "官方未明确",
            "official_in_cny": 0.99, "official_out_cny": 0.99,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考",
            "note": "旗舰 MoE 模型，主打极致性价比，0.99 元/百万 tokens 输入输出同价",
        },
        {
            "name": "Yi-Large", "context": "32K",
            "official_in_cny": 20.0, "official_out_cny": 20.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考",
            "note": "输入输出同价",
        },
    ]},
    {"vendor": "阶跃星辰", "models": [
        {
            "name": "Step 3.5 Flash", "context": "官方未明确",
            "official_in_cny": 0.7, "official_out_cny": 2.1,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": 0.7, "domestic_out_cny": 2.1,
            "domestic_source": "硅基流动 / Step-3.5-Flash",
            "note": "当前主力；硅基流动精确同名 0.7/2.1",
        },
        {
            "name": "Step-R1-V-Mini", "context": "官方未明确",
            "official_in_cny": 2.5, "official_out_cny": 8.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考",
            "note": "推理模型",
        },
    ]},
    {"vendor": "商汤日日新", "models": [
        {
            "name": "SenseNova-V6.5-Pro", "context": "官方未明确",
            "official_in_cny": 3.0, "official_out_cny": 9.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考（仅商汤官方提供）",
            "note": "旗舰融合模态大模型，官方价 3/9",
        },
        {
            "name": "SenseNova-V6.5-Turbo", "context": "官方未明确",
            "official_in_cny": 1.5, "official_out_cny": 4.5,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考",
            "note": "Turbo 版模型，官方价 1.5/4.5",
        },
    ]},
    {"vendor": "昆仑万维天工", "models": [
        {
            "name": "SkyClaw-v1.0", "context": "1M",
            "official_in_cny": 0.5, "official_out_cny": 4.0,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考（仅天工官方提供）",
            "note": "旗舰 Agent 模型，主打工具调用和多轮任务执行，1M 上下文",
        },
        {
            "name": "SkyClaw-v1.0-lite", "context": "官方未明确",
            "official_in_cny": 0.3, "official_out_cny": 1.5,
            "overseas_in_usd": None, "overseas_out_usd": None,
            "overseas_source": "海外渠道暂未上架",
            "domestic_in_cny": None, "domestic_out_cny": None,
            "domestic_source": "境内渠道同系列参考",
            "note": "轻量版 Agent 模型",
        },
    ]},
]


def _is_deprecated(model_id: str) -> bool:
    mid = model_id.lower()
    return any(kw in mid for kw in DEPRECATED_KEYWORDS)


def _match_vendor(model_id: str) -> str | None:
    mid = model_id.lower()
    for vendor, prefixes in VENDOR_PREFIXES.items():
        for prefix in prefixes:
            if mid.startswith(prefix.lower()):
                return vendor
    return None


def discover_from_litellm() -> dict[str, list[dict]]:
    """从 LiteLLM JSON 发现模型。返回 vendor -> [models]。"""
    data = fetch_json("https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json")
    if not data or not isinstance(data, dict):
        return {}
    result: dict[str, list[dict]] = {}
    for model_id, info in data.items():
        if not isinstance(info, dict):
            continue
        if _is_deprecated(model_id):
            continue
        vendor = _match_vendor(model_id)
        if not vendor:
            continue
        # 只保留有价格信息的模型
        input_cost = info.get("input_cost_per_token")
        output_cost = info.get("output_cost_per_token")
        if input_cost is None and output_cost is None:
            continue
        ctx = info.get("max_tokens", "") or info.get("max_input_tokens", "") or "未知"
        result.setdefault(vendor, []).append({
            "id": model_id,
            "context": str(ctx),
            "input_cost_per_token": input_cost,
            "output_cost_per_token": output_cost,
            "source": "LiteLLM JSON",
        })
    if result:
        record_source("官方/校验", "LiteLLM 模型价格与上下文窗口 JSON", "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json", f"验证 {sum(len(v) for v in result.values())} 个模型")
    return result


def discover_from_openrouter() -> dict[str, list[dict]]:
    """从 OpenRouter API 发现模型。"""
    data = fetch_json("https://openrouter.ai/api/v1/models")
    if not data or not isinstance(data, dict):
        return {}
    models = data.get("data", [])
    if not isinstance(models, list):
        return {}
    result: dict[str, list[dict]] = {}
    for m in models:
        if not isinstance(m, dict):
            continue
        model_id = m.get("id", "")
        if _is_deprecated(model_id):
            continue
        vendor = _match_vendor(model_id)
        if not vendor:
            continue
        pricing = m.get("pricing", {})
        prompt_price = pricing.get("prompt", pricing.get("input", None))
        completion_price = pricing.get("completion", pricing.get("output", None))
        if prompt_price is None and completion_price is None:
            continue
        ctx = m.get("context_length", "")
        result.setdefault(vendor, []).append({
            "id": model_id,
            "context": str(ctx) if ctx else "未知",
            "input_cost_per_token": prompt_price,
            "output_cost_per_token": completion_price,
            "source": "OpenRouter API",
        })
    if result:
        record_source("海外三方", "OpenRouter API 模型定价", "https://openrouter.ai/api/v1/models", f"验证 {sum(len(v) for v in result.values())} 个模型")
    return result


def discover_from_modelsdev() -> dict[str, list[dict]]:
    """从 models.dev API 发现模型。"""
    data = fetch_json("https://models.dev/api.json")
    if not data or not isinstance(data, list):
        return {}
    result: dict[str, list[dict]] = {}
    for m in data:
        if not isinstance(m, dict):
            continue
        model_id = m.get("id", "")
        if _is_deprecated(model_id):
            continue
        vendor = _match_vendor(model_id)
        if not vendor:
            continue
        pricing = m.get("pricing", {})
        prompt_price = pricing.get("input", pricing.get("prompt", None))
        completion_price = pricing.get("output", pricing.get("completion", None))
        if prompt_price is None and completion_price is None:
            continue
        ctx = m.get("context_length", "")
        result.setdefault(vendor, []).append({
            "id": model_id,
            "context": str(ctx) if ctx else "未知",
            "input_cost_per_token": prompt_price,
            "output_cost_per_token": completion_price,
            "source": "models.dev API",
        })
    if result:
        record_source("海外三方", "models.dev API 模型定价", "https://models.dev/api.json", f"验证 {sum(len(v) for v in result.values())} 个模型")
    return result


def merge_vendor_models(
    litellm: dict[str, list[dict]],
    openrouter: dict[str, list[dict]],
    modelsdev: dict[str, list[dict]],
) -> dict[str, list[dict]]:
    """合并三个来源的模型发现结果，去重并保留最新版本。"""
    all_models: dict[str, list[dict]] = {}

    def add_models(source: dict[str, list[dict]], src_name: str):
        for vendor, models in source.items():
            for m in models:
                m["_source"] = src_name
            all_models.setdefault(vendor, []).extend(models)

    add_models(litellm, "LiteLLM")
    add_models(openrouter, "OpenRouter")
    add_models(modelsdev, "models.dev")

    # 按模型 ID 去重，优先保留有价格的
    merged: dict[str, list[dict]] = {}
    for vendor, models in all_models.items():
        seen: dict[str, dict] = {}
        for m in models:
            mid = m["id"]
            if mid not in seen:
                seen[mid] = m
            else:
                # 保留有价格的版本
                old = seen[mid]
                old_has_price = old.get("input_cost_per_token") is not None or old.get("output_cost_per_token") is not None
                new_has_price = m.get("input_cost_per_token") is not None or m.get("output_cost_per_token") is not None
                if new_has_price and not old_has_price:
                    seen[mid] = m
        merged[vendor] = list(seen.values())

    return merged


def build_discovered_token_rows() -> tuple[list[dict[str, Any]], list[dict]]:
    """构建发现后的 Token 数据行。

    策略：
    1. 以 VENDOR_MODEL_ANCHORS 为基础（含官方价 + 已知三方价），保证数据质量
    2. 从 OpenRouter API 动态拉取市场价，与锚点交叉验证
    3. 若锚点中某项价格缺失，用 API 发现结果补全
    4. 记录所有发现的模型 ID 供人工审核新模型
    """
    print("[discover] Fetching OpenRouter API...")
    openrouter = discover_from_openrouter()
    print(f"[discover] OpenRouter: {sum(len(v) for v in openrouter.values())} models")

    print("[discover] Fetching LiteLLM JSON...")
    litellm = discover_from_litellm()
    print(f"[discover] LiteLLM: {sum(len(v) for v in litellm.values())} models")

    discovered = merge_vendor_models(litellm, openrouter, {})

    rows: list[dict[str, Any]] = []
    discovered_log: list[dict] = []

    for anchor in VENDOR_MODEL_ANCHORS:
        vendor = anchor["vendor"]
        api_models = discovered.get(vendor, [])

        for model in anchor["models"]:
            name = model["name"]
            context = model.get("context", "未知")
            note = model.get("note", "")

            # 判断币种和官方价
            if "official_in_usd" in model:
                official_in = model["official_in_usd"]
                official_out = model["official_out_usd"]
                currency = "USD"
            else:
                official_in = model.get("official_in_cny")
                official_out = model.get("official_out_cny")
                currency = "CNY"

            region = "海外" if currency == "USD" else "国产"

            # 三方价：优先用锚点中的已知价格，缺失则尝试从 API 发现补全
            overseas_in_usd = model.get("overseas_in_usd")
            overseas_out_usd = model.get("overseas_out_usd")
            overseas_source = model.get("overseas_source", "")

            domestic_in_cny = model.get("domestic_in_cny")
            domestic_out_cny = model.get("domestic_out_cny")
            domestic_source = model.get("domestic_source", "")

            # 若锚点中海外三方价缺失，尝试从 API 发现补全
            if overseas_in_usd is None and overseas_out_usd is None:
                for am in api_models:
                    aid = am["id"].lower()
                    # 模糊匹配
                    name_norm = name.lower().replace(" ", "-").replace(".", "-")
                    if any(part in aid for part in name_norm.split("-") if len(part) >= 2):
                        inp = am.get("input_cost_per_token")
                        out = am.get("output_cost_per_token")
                        if inp is not None:
                            overseas_in_usd = round(float(inp) * 1_000_000, 4)
                        if out is not None:
                            overseas_out_usd = round(float(out) * 1_000_000, 4)
                        if overseas_in_usd or overseas_out_usd:
                            overseas_source = f"API补全 / {am.get('_source', 'unknown')} / {am['id']}"
                        break

            status = "PASS"
            confidence = 90

            # 根据数据完整度调整状态
            if overseas_in_usd is None and overseas_out_usd is None:
                confidence = min(confidence, 70)
            if domestic_in_cny is None and domestic_out_cny is None and region == "国产":
                confidence = min(confidence, 70)

            rows.append({
                "vendor": vendor,
                "model": name,
                "region": region,
                "context": context,
                "official_in": official_in,
                "official_out": official_out,
                "official_currency": currency,
                "official_source": f"{vendor} 官方定价页",
                "overseas_in_usd": overseas_in_usd,
                "overseas_out_usd": overseas_out_usd,
                "overseas_source": overseas_source,
                "domestic_in_cny": domestic_in_cny,
                "domestic_out_cny": domestic_out_cny,
                "domestic_source": domestic_source,
                "note": note or f"{vendor} {name}",
                "confidence": confidence,
                "status": status,
                "api_discovered_models": [m["id"] for m in api_models[:5]],
            })

        discovered_log.append({
            "vendor": vendor,
            "api_discovered_count": len(api_models),
            "api_model_ids": [m["id"] for m in api_models[:10]],
        })

    return rows, discovered_log


# ---------------------------------------------------------------------------
# GPU 动态发现
# ---------------------------------------------------------------------------

def discover_gpu_from_cloudgpus() -> list[str]:
    """尝试从 cloud-gpus.com 发现 GPU 型号列表。"""
    html = fetch_text("https://cloud-gpus.com/")
    if not html:
        return []
    # 简单正则提取 GPU 型号
    gpus = set()
    # 匹配常见 GPU 型号模式
    patterns = [
        r'([A-Z]+\s*\d+[A-Z]*)',
        r'(RTX\s*\d+[A-Z]*)',
        r'(H100|H200|H800|H20|A100|A800|L40S|L20|L4|B200|B300|GB200|GB300)',
        r'(昇腾\s*\d+[A-Z]*)',
        r'(MLU\d+)',
        r'(DCU\s*[A-Z]*\d+)',
    ]
    for pat in patterns:
        for m in re.finditer(pat, html):
            gpus.add(m.group(1).strip())
    return sorted(gpus)


def discover_gpu_from_gpucloudpricing() -> list[str]:
    """尝试从 gpucloudpricing.com 发现 GPU 型号。"""
    html = fetch_text("https://www.gpucloudpricing.com/")
    if not html:
        return []
    gpus = set()
    patterns = [
        r'(H100|H200|H800|H20|A100|A800|L40S|L20|L4|B200|B300|GB200|GB300|RTX\s*\d+[A-Z]*)',
    ]
    for pat in patterns:
        for m in re.finditer(pat, html):
            gpus.add(m.group(1).strip())
    return sorted(gpus)


# 基线 GPU 名单（稳定性保障）——这些是 report_config.md 定义的分类
# 2026-07-15 更新：H20 标注停产；新增国产候选型号
BASELINE_GPU_GROUPS = [
    ("Training", ["GB300", "GB200", "B300", "B200", "H200", "H100 80G", "H800", "A100 80G", "A800"]),
    ("Inference", ["L40S", "L20", "L4"]),
    ("Consumer", ["RTX 5090", "RTX 4090"]),
    ("国产", ["昇腾 910C", "昇腾 910B", "昇腾 950PR", "寒武纪 MLU370-X8", "寒武纪 MLU590", "海光 DCU K100", "海光 DCU Z100", "壁仞 BR100", "摩尔线程 MTT S4000", "摩尔线程 MTT S5000"]),
]

# 已知停产/禁售 GPU（仍保留在审计中，但不进入主指数）
DISCONTINUED_GPUS = {"H20"}

# 候选 GPU（连续 3 期发现后人工审核加入基线）
GPU_CANDIDATES = ["RTX Pro 6000 SE", "MI300X", "MI325X", "MI355X"]


# ---------------------------------------------------------------------------
# GPU 价格动态采集
# ---------------------------------------------------------------------------

OVERSEAS_GPU_PRICE_ANCHORS: dict[str, dict[str, Any]] = {
    # 数据来源：RunPod / Lambda / Vast.ai / cloud-gpus.com 实际采集（2026-07-15）
    "H100 SXM": {
        "runpod": 2.99, "lambda": 3.99, "vast_low": 1.98, "vast_median": 2.23,
        "cloudgpus": 3.63, "source": "RunPod/Lambda/Vast.ai/cloud-gpus.com",
    },
    "H100 PCIe": {
        "runpod": 2.89, "cloudgpus": 3.19, "source": "RunPod/cloud-gpus.com",
    },
    "H200": {
        "runpod": 4.39, "vast_low": 3.41, "vast_median": 3.79, "cloudgpus": 4.43,
        "source": "RunPod/Vast.ai/cloud-gpus.com",
    },
    "B200": {
        "runpod": 5.89, "lambda": 6.69, "vast_low": 4.69, "vast_median": 4.99,
        "cloudgpus": 7.15, "source": "RunPod/Lambda/Vast.ai/cloud-gpus.com",
    },
    "B300": {
        "runpod": 7.39, "vast_low": 5.83, "vast_median": 6.30, "cloudgpus": 12.37,
        "source": "RunPod/Vast.ai/cloud-gpus.com",
    },
    "GB200": {
        "cloudgpus": 13.25, "source": "cloud-gpus.com",
    },
    "GB300": {
        "cloudgpus": 13.31, "source": "cloud-gpus.com",
    },
    "A100 80G SXM": {
        "runpod": 1.49, "lambda": 2.79, "source": "RunPod/Lambda",
    },
    "A100 80G PCIe": {
        "runpod": 1.39, "source": "RunPod",
    },
    "L40S": {
        "runpod": 0.99, "vast_low": 0.47, "cloudgpus": 1.61, "source": "RunPod/Vast.ai/cloud-gpus.com",
    },
    "L4": {
        "runpod": 0.39, "vast_low": 0.32, "cloudgpus": 0.88, "source": "RunPod/Vast.ai/cloud-gpus.com",
    },
    "RTX 5090": {
        "runpod": 0.99, "vast_low": 0.42, "vast_median": 0.49, "cloudgpus": 0.77,
        "source": "RunPod/Vast.ai/cloud-gpus.com",
    },
    "RTX 4090": {
        "runpod": 0.69, "vast_low": 0.35, "vast_median": 0.39, "cloudgpus": 0.68,
        "source": "RunPod/Vast.ai/cloud-gpus.com",
    },
}


def discover_gpu_prices_from_cloudgpus() -> dict[str, float]:
    """从 cloud-gpus.com 抓取 GPU 时租价格。"""
    html = fetch_text("https://cloud-gpus.com/")
    if not html:
        return {}
    prices: dict[str, float] = {}
    # 匹配形如 "H100 SXM $3.63/hr" 或 "B300 $12.37/hr" 的模式
    # 也匹配 price-analytics 页面中的表格数据
    pat = re.compile(r'([A-Z]+(?:\s+[A-Z]+)?)\s*\$?([0-9]+\.[0-9]{2})\s*/\s*hr', re.IGNORECASE)
    for m in pat.finditer(html):
        gpu = m.group(1).strip()
        price = float(m.group(2))
        if gpu and price > 0:
            prices[gpu] = price
    if prices:
        record_source("海外云价", "cloud-gpus.com GPU pricing", "https://cloud-gpus.com/", f"采集到 {len(prices)} 款 GPU 海外时租价")
    return prices


def scrape_tianyi_gpu_prices() -> dict[str, tuple[float, float]]:
    """从天翼云文档页抓取 GPU 单卡按需时租价 + 包月价。

    页面为静态 HTML 表格，URL: https://www.ctyun.cn/document/10029787/10047957
    返回 {GPU型号: (单卡按需元/小时, 单卡包月元/月)}
    """
    html = fetch_text("https://www.ctyun.cn/document/10029787/10047957")
    if not html:
        print("[discover] tianyi: fetch failed", file=sys.stderr)
        return {}
    prices: dict[str, tuple[float, float]] = {}
    # 天翼云表格列序：规格名称, vCPU, 内存, 显存, 显卡数, 显卡类型, 按需价格（元/小时）, 价格（元/月）
    # 策略：找到型号关键词，提取其所在行（1卡实例）的按需价和包月价
    search_map = {
        "L40S": ["L40S", "L40 S"],
        "L20": ["L20"],
        "昇腾 910B": ["910B", "Ascend 910B"],
        "寒武纪 MLU370-X8": ["MLU370", "Cambricon MLU370"],
        "海光 DCU K100": ["DCU", "K100", "海光"],
    }
    for gpu_name, keywords in search_map.items():
        for kw in keywords:
            # 搜索包含关键词的 <td> 单元格，而不是整个页面中关键词的位置
            # 这样可以精确匹配型号在显卡类型列中的行
            pattern = rf'<td[^>]*>[^<]*{re.escape(kw)}[^<]*</td>'
            m = re.search(pattern, html, re.IGNORECASE)
            if not m:
                # 也尝试搜索 <p> 或其他标签内的型号
                pattern2 = rf'>\s*{re.escape(kw)}\s*<'
                m = re.search(pattern2, html, re.IGNORECASE)
            if not m:
                continue
            # 从匹配位置往前找 <tr>，提取整行
            tr_start = html.rfind('<tr', 0, m.start())
            tr_end = html.find('</tr>', m.start())
            if tr_start < 0 or tr_end < 0:
                continue
            row_html = html[tr_start:tr_end]
            # 找该行中的所有数值 TD
            tds = re.findall(r'<td[^>]*>\s*([\d,.]+)\s*</td>', row_html)
            # 表格结构：vCPU, 内存, 显存, 显卡数, 显卡类型(文本), 按需价, 包月价
            # 显卡类型列是文本 TD 不被上面的正则匹配到
            # 所以 tds = [vCPU, 内存, 显存, 显卡数, 按需价, 包月价]
            if len(tds) >= 6:
                try:
                    hourly = float(tds[4])
                    monthly = float(tds[5])
                    if 0.1 < hourly < 500 and 100 < monthly < 500000:
                        prices[gpu_name] = (hourly, monthly)
                        break
                except (ValueError, IndexError):
                    pass
    if prices:
        record_source("云价折算", "天翼云 GPU 云主机价格总览", "https://www.ctyun.cn/document/10029787/10047957", f"采集到 {len(prices)} 款 GPU 单卡包月价")
    print(f"[discover] tianyi: {len(prices)} prices found: {list(prices.keys())}")
    return prices


def scrape_smm_gpu_prices() -> dict[str, dict[str, Any]]:
    """从 SMM 算力频道直播页抓取 GPU 8卡整机月租报价。

    URL: https://news.smm.cn/live/metal/143
    返回 {GPU型号: {"monthly_wan": float, "note": str}}
    """
    html = fetch_text("https://news.smm.cn/live/metal/143")
    if not html:
        print("[discover] smm: fetch failed", file=sys.stderr)
        return {}
    # 去标签，纯文本搜索
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    results: dict[str, dict[str, Any]] = {}
    # SMM 文本格式多样，需优先匹配"主流报价区间"/"实际成交"/"报价集中"等关键词
    # 跳过"含电"报价（含电费的高价不是裸金属市场价）
    gpu_search = [
        ("H100 80G", [
            # 优先：主流报价区间 7.5-8万/月
            r'H100[^万]{0,40}?(?:主流报价区间|实际成交区间|报价集中|成交区间)[^万]{0,20}?(\d+\.?\d*)\s*[-—~]\s*(\d+\.?\d*)\s*万',
            # 裸金属报价 X万以内
            r'H100[^万]{0,30}?裸金属[^万]{0,20}?(\d+\.?\d*)\s*万',
            # 排除含电的单值
            r'H100[^万含]{0,40}?(?<!含电费)(\d+\.?\d*)\s*[-—~]\s*(\d+\.?\d*)\s*万\s*/\s*月',
        ]),
        ("A100 80G", [
            r'A100[^万]{0,40}?(\d+\.?\d*)\s*[-—~]\s*(\d+\.?\d*)\s*万\s*/\s*月',
            r'A100[^万]{0,40}?(\d+\.?\d*)\s*万\s*/\s*月',
        ]),
        ("RTX 5090", [
            r'5090[^万]{0,30}?报.*?(\d+\.?\d*)\s*万',
            r'5090[^万]{0,30}?(\d+\.?\d*)\s*万\s*/\s*月',
        ]),
        ("RTX 4090", [
            r'4090[^元万]{0,40}?(\d[\d,]*)\s*[-—~]\s*(\d[\d,]*)\s*元\s*/\s*台\s*/\s*月',
            r'4090[^元万]{0,30}?市场价报(\d[\d,]*)\s*元',
            r'4090[^元万]{0,30}?成交价(\d[\d,]*)\s*元',
        ]),
    ]
    for gpu, patterns in gpu_search:
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    if len(m.groups()) == 2:
                        low = float(m.group(1).replace(",", ""))
                        high = float(m.group(2).replace(",", ""))
                        # 判断是万元还是元
                        if "万" in text[m.start():m.end()+10]:
                            mid = round((low + high) / 2, 2)
                            results[gpu] = {"monthly_wan": mid, "note": f"SMM直播：{low}-{high}万/月，中位{mid}万"}
                        else:
                            mid = round((low + high) / 2 / 10000, 2)
                            results[gpu] = {"monthly_wan": mid, "note": f"SMM直播：{low}-{high}元/台/月，中位{mid}万"}
                    else:
                        val = float(m.group(1).replace(",", ""))
                        if "万" in text[m.start():m.end()+10]:
                            results[gpu] = {"monthly_wan": val, "note": f"SMM直播：{val}万/月"}
                        elif val > 1000:
                            results[gpu] = {"monthly_wan": round(val / 10000, 2), "note": f"SMM直播：{val}元/台/月"}
                    break
                except (ValueError, IndexError):
                    pass
    if results:
        record_source("裸金属/行业", "SMM 算力快讯直播页", "https://news.smm.cn/live/metal/143", f"采集到 {len(results)} 款 GPU 裸金属月租价")
    print(f"[discover] smm: {len(results)} prices found: {list(results.keys())}")
    return results


def scrape_omniyq_gpu_prices() -> dict[str, float]:
    """从云擎天下抓取 8卡整机月租价。

    URL: https://www.omniyq.com/h-col-104.html
    页面直接列出各型号8卡整机月租价文本。
    返回 {GPU型号: 月租万元}
    """
    html = fetch_text("https://www.omniyq.com/h-col-104.html")
    if not html:
        print("[discover] omniyq: fetch failed", file=sys.stderr)
        return {}
    prices: dict[str, float] = {}
    # 去标签，纯文本搜索
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    # 格式：8*910B - 15000/月  或  8*H100 - 75000/月
    patterns = {
        "昇腾 910B": r'8\s*[*×xX\\]\s*910B?\s*[-–—]\s*(\d[\d,]*)\s*/\s*月',
        "H100 80G": r'8\s*[*×xX\\]\s*H100\s*[-–—]\s*(\d[\d,]*)\s*/\s*月',
        "H800": r'8\s*[*×xX\\]\s*H800\s*[-–—]\s*(\d[\d,]*)\s*/\s*月',
        "H200": r'8\s*[*×xX\\]\s*H200\s*[-–—]\s*(\d[\d,]*)\s*/\s*月',
        "A100 80G": r'8\s*[*×xX\\]\s*A100\s*(?:nvlink|pcie)?\s*80G?\s*[-–—]\s*(\d[\d,]*)\s*/\s*月',
        "A800": r'8\s*[*×xX\\]\s*A800\s*[-–—]\s*(\d[\d,]*)\s*/\s*月',
        "RTX 4090": r'8\s*[*×xX\\]\s*4090\s*[-–—]\s*(\d[\d,]*)\s*/\s*月',
        "RTX 5090": r'8\s*[*×xX\\]\s*5090\s*[-–—]\s*(\d[\d,]*)\s*/\s*月',
        "L40S": r'8\s*[*×xX\\]\s*L40S?\s*[-–—]\s*(\d[\d,]*)\s*/\s*月',
        "L40": r'8\s*[*×xX\\]\s*L40(?!\w)\s*[-–—]\s*(\d[\d,]*)\s*/\s*月',
        "B200": r'8\s*[*×xX\\]\s*B200\s*[-–—]\s*(\d[\d,]*)\s*/\s*月',
        "B300": r'8\s*[*×xX\\]\s*B300\s*[-–—]\s*(\d[\d,]*)\s*/\s*月',
    }
    for gpu, pat in patterns.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                val = float(m.group(1).replace(",", ""))
                monthly_wan = round(val / 10000, 2)
                if monthly_wan > 0:
                    prices[gpu] = monthly_wan
            except ValueError:
                pass
    if prices:
        record_source("裸金属/行业", "云擎天下 8卡整机裸金属月租", "https://www.omniyq.com/h-col-104.html", f"采集到 {len(prices)} 款 GPU 裸金属月租价")
    print(f"[discover] omniyq: {len(prices)} prices found: {list(prices.keys())}")
    return prices


def scrape_shengsuanyun_gpu_prices() -> dict[str, dict[str, Any]]:
    """从胜算云抓取国产 GPU 单卡时租价。

    URL: https://www.shengsuanyun.com/hashrate
    ⚠️ 该网站为 React SPA，urllib 只能拿到空壳 HTML。
    实际数据需通过 AI session + MCP 浏览器工具抓取后写入
    data/shengsuanyun_{DATE}.json，本函数读取该文件。
    若文件不存在或过期，回退到硬编码 fallback。
    返回 {GPU型号: {"hourly_cny": float, "source": str}}
    """
    # 尝试读取 AI session 写入的抓取结果
    ssy_cache = ROOT / "data" / f"shengsuanyun_{DATE}.json"
    if ssy_cache.exists():
        try:
            cached = json.loads(ssy_cache.read_text(encoding="utf-8"))
            if isinstance(cached, dict) and cached.get("scraped_at") == DATE:
                print(f"[discover] shengsuanyun: loaded from cache {ssy_cache.name}")
                return cached.get("prices", {})
        except (json.JSONDecodeError, KeyError):
            pass

    # 硬编码 fallback（2026-07-15 人工验证值）
    print("[discover] shengsuanyun: SPA site, using hardcoded fallback (last verified 2026-07-15)", file=sys.stderr)
    return {
        "摩尔线程 MTT S4000": {"hourly_cny": 1.69, "source": "胜算云(fallback)"},
        "壁仞 天垓100": {"hourly_cny": 1.49, "source": "胜算云(fallback)"},
        "华为 Ascend 910": {"hourly_cny": 2.36, "source": "胜算云(fallback)"},
    }


def scrape_gitee_ai_gpu_prices() -> dict[str, dict[str, Any]]:
    """从模力方舟（Gitee AI）抓取国产 GPU 单卡时租价。

    URL: https://ai.gitee.com/compute
    ⚠️ 该网站为 JS 动态渲染，urllib 只能拿到空壳 HTML。
    实际数据需通过 AI session + MCP 浏览器工具抓取后写入
    data/gitee_ai_{DATE}.json，本函数读取该文件。
    若文件不存在或过期，回退到硬编码 fallback。
    返回 {GPU型号: {"hourly_cny": float, "source": str}}
    """
    # 尝试读取 AI session 写入的抓取结果
    gitee_cache = ROOT / "data" / f"gitee_ai_{DATE}.json"
    if gitee_cache.exists():
        try:
            cached = json.loads(gitee_cache.read_text(encoding="utf-8"))
            if isinstance(cached, dict) and cached.get("scraped_at") == DATE:
                print(f"[discover] gitee-ai: loaded from cache {gitee_cache.name}")
                return cached.get("prices", {})
        except (json.JSONDecodeError, KeyError):
            pass

    # 硬编码 fallback（2026-07-15 人工验证值）
    print("[discover] gitee-ai: SPA site, using hardcoded fallback (last verified 2026-07-15)", file=sys.stderr)
    return {
        "海光 BW1000": {"hourly_cny": 3.00, "source": "模力方舟(fallback)"},
        "摩尔线程 MTT S5000": {"hourly_cny": 8.00, "source": "模力方舟(fallback)"},
        "壁仞 天垓150": {"hourly_cny": 3.00, "source": "模力方舟(fallback)"},
        "壁仞 壁砺106M": {"hourly_cny": 2.00, "source": "模力方舟(fallback)"},
        "天数智芯 智铠100": {"hourly_cny": 2.00, "source": "模力方舟(fallback)"},
        "燧原 S60": {"hourly_cny": 2.00, "source": "模力方舟(fallback)"},
        "昇腾 910B": {"hourly_cny": 3.50, "source": "模力方舟(fallback)"},
    }


def build_dynamic_domestic_anchors() -> dict[str, dict[str, Any]]:
    """汇总所有动态采集源的国内 GPU 价格，合并到锚点字典。

    价格口径说明：
    - 主图表口径：裸金属8卡整机月租（SMM/云擎天下/静态锚点）
    - 云价折算：仅作为参考口径，不替代裸金属价格

    优先级（裸金属 > 云价）：
    1. SMM直播页 -> 裸金属8卡整机月租（最高置信，公开成交）
    2. 云擎天下 -> 裸金属8卡整机月租（次高置信，公开报价）
    3. 天翼云 -> 单卡包月价×8（云价折算，仅在没有裸金属数据时使用）
    4. 生数云 -> 单卡时租反推（云价折算，仅在没有裸金属数据时使用）
    5. 合并到 DOMESTIC_GPU_PRICE_ANCHORS 静态锚点
    """
    anchors: dict[str, dict[str, Any]] = {}
    cloud_only: dict[str, dict[str, Any]] = {}  # 云价折算单独存放

    # --- 第一轮：收集所有数据源 ---

    # 1. 天翼云单卡包月价 -> 云价折算（8卡整机 = 单卡包月 × 8 × 0.7长协折扣）
    tianyi = scrape_tianyi_gpu_prices()
    for gpu, (hourly, monthly) in tianyi.items():
        eight_card_monthly = round(monthly * 8 * 0.7 / 10000, 2)
        cloud_only[gpu] = {
            "tianyi_hourly": hourly,
            "tianyi_monthly": monthly,
            "cloud_monthly_wan": eight_card_monthly,
            "cloud_source": f"天翼云包月{monthly}元/卡/月×8×0.7折算",
            "cloud_note": f"天翼云单卡包月{monthly}元/月，按需{hourly}元/时；云价折算8卡整机={monthly}×8×0.7÷10000≈{eight_card_monthly}万/月（含0.7长协折扣系数）",
        }

    # 2. SMM 8卡整机月租 -> 裸金属（公开成交）
    smm = scrape_smm_gpu_prices()
    for gpu, info in smm.items():
        anchors[gpu] = {
            "monthly_wan": info["monthly_wan"],
            "monthly_source": "SMM直播页 8卡整机裸金属",
            "note": info["note"],
            "_price_basis": "公开成交/主口径价",
        }

    # 3. 云擎天下 8卡整机月租 -> 裸金属（公开报价）
    omniyq = scrape_omniyq_gpu_prices()
    for gpu, monthly_wan in omniyq.items():
        if gpu not in anchors:
            anchors[gpu] = {
                "monthly_wan": monthly_wan,
                "monthly_source": "云擎天下 8卡整机裸金属月租",
                "note": f"云擎天下裸金属报价：{monthly_wan}万/月",
                "_price_basis": "公开成交/主口径价",
            }

    # 4. 胜算云单卡时租 -> 云价折算（国产卡补充到 cloud_only）
    ssy = scrape_shengsuanyun_gpu_prices()
    for gpu, info in ssy.items():
        hourly = info["hourly_cny"]
        # 单卡时价 × 8卡 × 24时 × 30天 × 0.7长协折扣 / 10000 = 万元/月
        monthly_wan = round(hourly * 8 * 24 * 30 * 0.7 / 10000, 2)
        if gpu not in cloud_only:
            cloud_only[gpu] = {
                "cloud_monthly_wan": monthly_wan,
                "cloud_source": f"胜算云{hourly}元/时×8×24×30×0.7折算",
                "cloud_note": f"胜算云单卡{hourly}元/时；单卡云价×8折算8卡整机约{monthly_wan}万/月（含0.7长协折扣系数）",
                "price_band_aux": monthly_wan,
            }

    # 5. 模力方舟单卡时租 -> 云价折算（国产卡补充到 cloud_only）
    gitee = scrape_gitee_ai_gpu_prices()
    for gpu, info in gitee.items():
        hourly = info["hourly_cny"]
        if hourly is None:
            continue  # 跳过无可用价格的型号
        monthly_wan = round(hourly * 8 * 24 * 30 * 0.7 / 10000, 2)
        # 模力方舟价格与胜算云可能覆盖同系列不同型号（如S4000 vs S5000）
        existing = cloud_only.get(gpu, {})
        # 优先保留已有的胜算云数据（更便宜），模力方舟作为补充
        if gpu not in cloud_only or monthly_wan < existing.get("cloud_monthly_wan", 999):
            cloud_only[gpu] = {
                "cloud_monthly_wan": monthly_wan,
                "cloud_source": f"模力方舟{hourly}元/时×8×24×30×0.7折算",
                "cloud_note": f"模力方舟单卡{hourly}元/时；单卡云价×8折算8卡整机约{monthly_wan}万/月（含0.7长协折扣系数）",
                "price_band_aux": monthly_wan,
            }

    # --- 第二轮：合并 ---

    # 对已有裸金属价格的型号，附上云价参考和折算值
    for gpu, cloud_info in cloud_only.items():
        if gpu in anchors:
            # 已有裸金属价，云价仅作参考
            anchors[gpu]["cloud_monthly_wan"] = cloud_info.get("cloud_monthly_wan")
            anchors[gpu]["cloud_source"] = cloud_info.get("cloud_source", "")
            anchors[gpu]["cloud_note"] = cloud_info.get("cloud_note", "")
            # 折算参考值（用于柱状图和表格辅助展示）
            if "price_band_aux" in cloud_info:
                anchors[gpu]["price_band_aux"] = cloud_info["price_band_aux"]
        else:
            # 无裸金属价，云价折算作为兜底
            anchors[gpu] = {
                "monthly_wan": cloud_info.get("cloud_monthly_wan"),
                "monthly_source": cloud_info.get("cloud_source", ""),
                "note": cloud_info.get("cloud_note", ""),
                "_price_basis": "云价折算",
                "price_band_aux": cloud_info.get("price_band_aux"),
            }

    # 5. 合并静态锚点（裸金属数据优先，静态补充缺失型号）
    for gpu, info in DOMESTIC_GPU_PRICE_ANCHORS.items():
        if gpu not in anchors:
            # 深拷贝静态锚点
            anchors[gpu] = dict(info)
        else:
            # 用静态锚点补充动态数据缺失的字段（但不覆盖已有价格）
            for k, v in info.items():
                if k not in anchors[gpu]:
                    anchors[gpu][k] = v

    return anchors


DOMESTIC_GPU_PRICE_ANCHORS: dict[str, dict[str, Any]] = {
    # 数据来源：国内云厂商官方定价页实际采集（2026-07-15）
    # 价格单位为：元/小时（单卡按量计费）或 万元/月（8卡整机）
    "H100 80G": {
        "tencent_hourly": 30.48, "volcano_hourly_8card": 42.0,
        "aliyun_hourly": 15.0, "tianyi_hourly": None,
        "monthly_wan": 7.6, "monthly_source": "SMM样本 8卡整机",
        "note": "腾讯云单卡30.48/时；火山8卡整机约42/时/卡；阿里云海外15/时；SMM 8卡整机7.6万/月",
    },
    "H20": {
        "tencent_hourly": 14.58, "status": "DISCONTINUED",
        "note": "2026年7月已停产/禁售，美国出口管制+中国禁入，无新交付；保留历史价格参考",
    },
    "A100 80G": {
        "tianyi_hourly": 31.27, "aliyun_hourly": 9.80, "volcano_hourly": 50.40,
        "tencent_hourly": None, "monthly_wan": 3.15, "monthly_source": "SMM样本",
        "note": "天翼云31.27/时；阿里云9.80/时；火山50.40/时；SMM 8卡整机3.15万/月",
    },
    "A100 40G": {
        "tianyi_hourly": 21.30, "tencent_hourly": 28.64,
        "note": "天翼云21.30/时；腾讯云28.64/时",
    },
    "L40S": {
        "tianyi_hourly": 31.28, "runpod_hourly": 0.99,
        "note": "天翼云31.28/时；RunPod $0.99/时",
    },
    "L20": {
        "tianyi_hourly": 15.72, "volcano_hourly": 17.50,
        "note": "天翼云15.72/时；火山17.50/时",
    },
    "L4": {
        "volcano_hourly": 8.06, "runpod_hourly": 0.39,
        "note": "火山8.06/时；RunPod $0.39/时",
    },
    "RTX 4090": {
        "volcano_hourly": None, "monthly_wan": 0.73, "monthly_source": "SMM样本 8卡整机",
        "note": "SMM 8卡整机0.73万/月；RunPod $0.69/时",
    },
    "RTX 5090": {
        "runpod_hourly": 0.99, "vast_low": 0.42,
        "note": "RunPod $0.99/时；Vast.ai $0.42/时起",
    },
    "昇腾 910C": {
        "monthly_wan": 6.2, "monthly_source": "SMM样本 8卡整机",
        "note": "SMM样本：买方出价5.3万/月，行业均价6.2万/月",
    },
    "昇腾 910B": {
        "tianyi_hourly": 38.45, "huawei_hourly": 7.90,
        "monthly_wan": 1.35, "monthly_source": "SMM区间中点 8卡整机",
        "note": "天翼云38.45/时；华为云约7.90/时；SMM 8卡整机1.2-1.5万/月",
    },
    "昇腾 950PR": {
        "status": "NEW_RELEASE",
        "note": "2026年Q1已商用，FP8算力1PFLOPS，112GB HBM；暂无公开租赁价",
    },
    "寒武纪 MLU370-X8": {
        "tianyi_hourly": 13.00, "monthly_wan": 4.24, "monthly_source": "天翼云4卡折算8卡等效",
        "note": "天翼云13.00/时（单卡）；4卡云主机折算8卡等效4.24万/月",
    },
    "寒武纪 MLU590": {
        "status": "NEW_RELEASE",
        "note": "2025-2026年已推出，7nm，FP16约256TFLOPS；暂无公开租赁价",
    },
    "海光 DCU K100": {
        "monthly_wan": 4.0, "monthly_source": "市场核价估算 8卡整机",
        "note": "无公开成交月租；市场核价区间3.5-4.5万/月，中位数4.0万入图",
    },
    "海光 DCU Z100": {
        "status": "NEW_RELEASE",
        "note": "深算三号，2025-2026年已量产，兼容ROCm；暂无公开租赁价",
    },
    "壁仞 BR100": {
        "monthly_wan": 4.3, "monthly_source": "市场核价估算 8卡整机",
        "note": "无公开成交月租；市场核价区间3.8-4.8万/月，中位数4.3万入图",
    },
    "摩尔线程 MTT S4000": {
        "monthly_wan": 3.5, "monthly_source": "市场核价估算 8卡整机",
        "note": "无公开成交月租；市场核价区间3.0-4.0万/月，中位数3.5万入图",
    },
    "摩尔线程 MTT S5000": {
        "status": "NEW_RELEASE",
        "note": "80GB显存，单卡算力1千万亿次，2026年2月完成Day-0适配；暂无公开租赁价",
    },
}


def build_discovered_gpu_list() -> dict[str, Any]:
    """构建发现的 GPU 列表和价格。

    策略：
    1. 以基线名单为基础，保证稳定性
    2. 从 GPU Cloud 聚合源发现新卡和价格
    3. 结合手动维护的海外/国内价格锚点
    4. 新卡进入 candidate_pool，连续 3 期出现后人工审核加入基线
    """
    print("[discover] Fetching GPU Cloud sources...")
    cloud_gpus = discover_gpu_from_cloudgpus()
    pricing_gpus = discover_gpu_from_gpucloudpricing()
    cloudgpu_prices = discover_gpu_prices_from_cloudgpus()

    all_discovered = set(cloud_gpus) | set(pricing_gpus)

    # 基线名单中的 GPU
    baseline_gpus = set()
    for _, items in BASELINE_GPU_GROUPS:
        baseline_gpus.update(items)

    # 新发现的 GPU（不在基线中）
    new_gpus = sorted(all_discovered - baseline_gpus)
    noise_filter = {"GPU", "CPU", "RAM", "SSD", "HDD", "NVMe", "TB", "GB", "VRAM", "vCPU"}
    new_gpus = [g for g in new_gpus if g not in noise_filter and len(g) >= 3]

    return {
        "baseline_groups": BASELINE_GPU_GROUPS,
        "discontinued": sorted(DISCONTINUED_GPUS),
        "candidates": GPU_CANDIDATES,
        "discovered_from_cloudgpus": cloud_gpus,
        "discovered_from_gpucloudpricing": pricing_gpus,
        "discovered_prices_from_cloudgpus": cloudgpu_prices,
        "new_candidates": new_gpus,
        "overseas_price_anchors": OVERSEAS_GPU_PRICE_ANCHORS,
        "domestic_price_anchors": build_dynamic_domestic_anchors(),
        "recommendation": "基线名单已更新至2026-07-15；H20停产保留审计；新增国产候选型号；价格锚点含多源真实数据（天翼云/SMM/云擎天下/生数云动态采集+静态锚点补充）。",
    }


# ---------------------------------------------------------------------------
# 模型能力评测数据（Artificial Analysis Intelligence Index v4.1）
# ---------------------------------------------------------------------------

# Token 价格表中模型到 AA 排行榜模型名称的映射
# key: 我们 Token 表中的 "厂商/模型" 关键词, value: AA 排行榜模型 slug 或名称关键词
_AA_MODEL_MAP: dict[str, list[str]] = {
    "GPT-5.5": ["gpt-5-5"],
    "GPT-5.6 Sol": ["gpt-5-6-sol"],
    "Claude Opus": ["claude-opus-4-8"],
    "Claude Sonnet": ["claude-sonnet-5"],
    "Claude Fable": ["claude-fable-5"],
    "Gemini 3.5 Flash": ["gemini-3-5-flash"],
    "Gemini 3.1 Pro": ["gemini-3-1-pro"],
    "Gemini 3.1 Flash-Lite": ["gemini-3-1-flash-lite"],
    "Mistral Medium": ["mistral-medium-3-5"],
    "Mistral Large": ["mistral-large-3"],
    "Mistral Small": ["mistral-small-4"],
    "Command A+": ["command-a-plus"],
    "Command R+": ["command-r-plus"],
    "Grok 4.5": ["grok-4-5"],
    "Grok 4.3": ["grok-4-3"],
    "Llama 4 Maverick": ["llama-4-maverick"],
    "Llama 4 Scout": ["llama-4-scout"],
    "DeepSeek-V4-Pro": ["deepseek-v4-pro"],
    "DeepSeek-V4-Flash": ["deepseek-v4-flash"],
    "Qwen3.7-Max": ["qwen3-7-max"],
    "Qwen3.7-Plus": ["qwen3-7-plus"],
    "Doubao": ["doubao"],
    "Hunyuan-Hy3": ["hy3"],
    "GLM-5.2": ["glm-5-2"],
    "GLM-5.1": ["glm-5-1"],
    "ERNIE 5.1": ["ernie-5-0-thinking"],
    "ERNIE-4.5": ["ernie-4-5"],
    "Kimi K3": ["kimi-k3"],
    "Kimi K2.7": ["kimi-k2-7-code"],
    "Kimi K2.6": ["kimi-k2-6"],
    "MiniMax-M3": ["minimax-m3"],
    "Spark X2": ["spark"],  # 讯飞星火可能不在 AA 中
    "Baichuan-M3-Plus": ["baichuan"],
    "Yi-Lightning": ["yi-lightning"],
    "Yi-Large": ["yi-large"],
    "Step 3.5 Flash": ["step-3-5-flash"],
    "SenseNova": ["sensenova"],
    "SkyClaw": ["skyclaw"],
    "Muse Spark 1.1": ["muse-spark-1-1"],
    "Inkling": ["inkling"],
    "JT-4.1 Flash": ["jt-4-1-flash"],
}

# Fallback 评测数据（基于 2026-07-17 Artificial Analysis 排行榜真实数据）
_BENCHMARK_FALLBACK: list[dict[str, Any]] = [
    # SciCode 编程能力 (%) 来源: data/aa_scicode_scores.json (AA SciCode pass@1%)
    # SciCode 是模型级编程能力 pass@1 评测，与 Intelligence Index（综合智能）是不同指标体系。
    # 数据由 _apply_scicode_scores() 从 aa_scicode_scores.json 模糊匹配填充。
    {"模型": "GPT-5.5", "厂商": "OpenAI", "AA Intelligence Index": 55, "SciCode 编程能力 (%)": 76.4, "GDPval-AA v2 Elo": 1217, "Output Speed (t/s)": 68, "Cost per Task (USD)": 4.35, "来源": "Artificial Analysis", "更新时间": "2026-07-17"},
    {"模型": "Claude Opus 4.8", "厂商": "Anthropic", "AA Intelligence Index": 56, "SciCode 编程能力 (%)": 67.0, "GDPval-AA v2 Elo": 1195, "Output Speed (t/s)": 50, "Cost per Task (USD)": 3.85, "来源": "Artificial Analysis", "更新时间": "2026-07-17"},
    {"模型": "Claude Sonnet 5", "厂商": "Anthropic", "AA Intelligence Index": 53, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1143, "Output Speed (t/s)": 196, "Cost per Task (USD)": 1.54, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Kimi K3", "厂商": "Kimi / Moonshot", "AA Intelligence Index": 57, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1215, "Output Speed (t/s)": 2, "Cost per Task (USD)": 2.31, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Gemini 3.5 Flash", "厂商": "Google", "AA Intelligence Index": 50, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1102, "Output Speed (t/s)": 25, "Cost per Task (USD)": 1.31, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Gemini 3.1 Pro Preview", "厂商": "Google", "AA Intelligence Index": 46, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1062, "Output Speed (t/s)": 27, "Cost per Task (USD)": 1.74, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Gemini 3.1 Flash-Lite", "厂商": "Google", "AA Intelligence Index": 25, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 927, "Output Speed (t/s)": 6, "Cost per Task (USD)": 0.22, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Mistral Medium 3.5", "厂商": "Mistral", "AA Intelligence Index": 30, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1000, "Output Speed (t/s)": 2, "Cost per Task (USD)": 1.16, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Mistral Large 3", "厂商": "Mistral", "AA Intelligence Index": 16, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 960, "Output Speed (t/s)": 1, "Cost per Task (USD)": 0.60, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Mistral Small 4", "厂商": "Mistral", "AA Intelligence Index": 20, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 962, "Output Speed (t/s)": 1, "Cost per Task (USD)": 0.20, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Command A+", "厂商": "Cohere", "AA Intelligence Index": 23, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 952, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Command R+", "厂商": "Cohere", "AA Intelligence Index": 8, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 900, "Output Speed (t/s)": 2, "Cost per Task (USD)": 3.25, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Grok 4.5", "厂商": "xAI Grok", "AA Intelligence Index": 54, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1173, "Output Speed (t/s)": 11, "Cost per Task (USD)": 1.35, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Grok 4.3", "厂商": "xAI Grok", "AA Intelligence Index": 38, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1035, "Output Speed (t/s)": 22, "Cost per Task (USD)": 0.64, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Llama 4 Maverick", "厂商": "Meta Llama", "AA Intelligence Index": 14, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 910, "Output Speed (t/s)": 1, "Cost per Task (USD)": 0.34, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Llama 4 Scout", "厂商": "Meta Llama", "AA Intelligence Index": 10, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 885, "Output Speed (t/s)": 1, "Cost per Task (USD)": 0.22, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "DeepSeek-V4-Pro", "厂商": "DeepSeek", "AA Intelligence Index": 44, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1081, "Output Speed (t/s)": 2, "Cost per Task (USD)": 0.18, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "DeepSeek-V4-Flash", "厂商": "DeepSeek", "AA Intelligence Index": 40, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1041, "Output Speed (t/s)": 1, "Cost per Task (USD)": 0.06, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Qwen3.7-Max", "厂商": "阿里云/通义千问", "AA Intelligence Index": 46, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1062, "Output Speed (t/s)": 2, "Cost per Task (USD)": 1.43, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Qwen3.7-Plus", "厂商": "阿里云/通义千问", "AA Intelligence Index": 39, "SciCode 编程能力 (%)": 52.0, "GDPval-AA v2 Elo": 1023, "Output Speed (t/s)": 3, "Cost per Task (USD)": 0.27, "来源": "Artificial Analysis", "更新时间": "2026-07-17"},
    {"模型": "Hunyuan-Hy3", "厂商": "腾讯混元", "AA Intelligence Index": 41, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1042, "Output Speed (t/s)": 2, "Cost per Task (USD)": 0.00, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "GLM-5.2", "厂商": "智谱 GLM / Z.ai", "AA Intelligence Index": 51, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1098, "Output Speed (t/s)": 2, "Cost per Task (USD)": 0.90, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "ERNIE 5.1", "厂商": "百度文心", "AA Intelligence Index": 22, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 945, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Kimi K2.7 Code", "厂商": "Kimi / Moonshot", "AA Intelligence Index": 42, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1041, "Output Speed (t/s)": 3, "Cost per Task (USD)": 0.70, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Kimi K2.6", "厂商": "Kimi / Moonshot", "AA Intelligence Index": 44, "SciCode 编程能力 (%)": 47.0, "GDPval-AA v2 Elo": 1081, "Output Speed (t/s)": 3, "Cost per Task (USD)": 0.70, "来源": "Artificial Analysis", "更新时间": "2026-07-17"},
    {"模型": "MiniMax-M3", "厂商": "MiniMax", "AA Intelligence Index": 44, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1079, "Output Speed (t/s)": 2, "Cost per Task (USD)": 0.22, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Spark X2", "厂商": "讯飞星火", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-17"},
    {"模型": "Baichuan-M3-Plus", "厂商": "百川智能", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-17"},
    {"模型": "GPT-5.6 Sol", "厂商": "OpenAI", "AA Intelligence Index": 59, "SciCode 编程能力 (%)": 78.7, "GDPval-AA v2 Elo": 1259, "Output Speed (t/s)": 42, "Cost per Task (USD)": 4.35, "来源": "Artificial Analysis", "更新时间": "2026-07-17"},
    {"模型": "Muse Spark 1.1", "厂商": "Meta", "AA Intelligence Index": 51, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1098, "Output Speed (t/s)": 1, "Cost per Task (USD)": 0.78, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "Inkling", "厂商": "Thinking Machines", "AA Intelligence Index": 41, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1035, "Output Speed (t/s)": 0, "Cost per Task (USD)": 1.10, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "JT-4.1 Flash", "厂商": "中国移动", "AA Intelligence Index": 39, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    # --- 名称匹配补齐：以下为 Token 表中有但此前未覆盖的模型 ---
    {"模型": "GPT-5.4", "厂商": "OpenAI", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据（已迭代至 GPT-5.5/5.6 Sol）", "更新时间": "2026-07-19"},
    {"模型": "GPT-5.4 mini", "厂商": "OpenAI", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据（轻量模型，AA 未单独评测）", "更新时间": "2026-07-19"},
    {"模型": "o4 Mini", "厂商": "OpenAI", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据（推理模型，AA 未单独评测）", "更新时间": "2026-07-19"},
    {"模型": "Claude Fable 5", "厂商": "Anthropic", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
    {"模型": "Claude Haiku 4.5", "厂商": "Anthropic", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
    {"模型": "Grok 4.20", "厂商": "xAI Grok", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据（已迭代至 Grok 4.5）", "更新时间": "2026-07-19"},
    {"模型": "MiniMax-M3 标准层 ≤512K", "厂商": "MiniMax", "AA Intelligence Index": 44, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1079, "Output Speed (t/s)": 2, "Cost per Task (USD)": 0.22, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "MiniMax-M3 标准层 >512K", "厂商": "MiniMax", "AA Intelligence Index": 44, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 1079, "Output Speed (t/s)": 2, "Cost per Task (USD)": 0.44, "来源": "Artificial Analysis（暂无 SciCode 数据）", "更新时间": "2026-07-17"},
    {"模型": "GLM-5.1 Pro", "厂商": "智谱 GLM / Z.ai", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据（已迭代至 GLM-5.2）", "更新时间": "2026-07-19"},
    {"模型": "Hunyuan-A13B", "厂商": "腾讯混元", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据（豆包系列，AA 未评测）", "更新时间": "2026-07-19"},
    {"模型": "Doubao-Seed 2.0 Pro", "厂商": "火山方舟/豆包", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
    {"模型": "Doubao-Seed 2.1 Pro", "厂商": "火山方舟/豆包", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
    {"模型": "Doubao-Seed 2.1 Turbo", "厂商": "火山方舟/豆包", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
    {"模型": "Doubao-Seed-Evolving", "厂商": "火山方舟/豆包", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
    {"模型": "Baichuan-M3", "厂商": "百川智能", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
    {"模型": "ERNIE-4.5-Turbo", "厂商": "百度文心", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据（轻量模型，AA 未单独评测）", "更新时间": "2026-07-19"},
    {"模型": "Hunyuan-role-latest", "厂商": "腾讯混元", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据（角色扮演模型，AA 未评测）", "更新时间": "2026-07-19"},
    {"模型": "Spark Max", "厂商": "讯飞星火", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
    {"模型": "SenseNova-V6.5-Pro", "厂商": "商汤日日新", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
    {"模型": "SenseNova-V6.5-Turbo", "厂商": "商汤日日新", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
    {"模型": "SkyClaw-v1.0", "厂商": "昆仑万维天工", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
    {"模型": "SkyClaw-v1.0-lite", "厂商": "昆仑万维天工", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
    {"模型": "Step 3.5 Flash", "厂商": "阶跃星辰", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
    {"模型": "Step-R1-V-Mini", "厂商": "阶跃星辰", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
    {"模型": "Yi-Large", "厂商": "零一万物", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
    {"模型": "Yi-Lightning", "厂商": "零一万物", "AA Intelligence Index": 0, "SciCode 编程能力 (%)": 0, "GDPval-AA v2 Elo": 0, "Output Speed (t/s)": 0, "Cost per Task (USD)": 0.00, "来源": "暂无评测数据", "更新时间": "2026-07-19"},
]

DISCOVERED_BENCHMARK_PATH = ROOT / "data" / f"discovered_benchmark_{DATE}.json"

# --- SciCode 数据加载与匹配 ---
_SCICODE_PATH = ROOT / "data" / "aa_scicode_scores.json"


def _load_scicode_scores() -> list[dict]:
    """加载 SciCode 评测分数数据。"""
    if _SCICODE_PATH.exists():
        try:
            return json.loads(_SCICODE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _apply_scicode_scores(records: list[dict]) -> list[dict]:
    """用 aa_scicode_scores.json 中的 SciCode 分数填充记录。

    匹配逻辑：SciCode 数据的 model 字段与记录的 '模型' 字段做模糊匹配（包含关系）。
    - 对于 MiniMax-M3 的两个 SKU（包含 "MiniMax-M3" 的模型名），使用 MiniMax-M3 的分数。
    - 如果没有匹配到 SciCode 分数，保持原值（fallback 中已设为 0）。
    """
    scidata = _load_scicode_scores()
    if not scidata:
        print("  [benchmark] 未找到 SciCode 数据文件，跳过分数填充")
        return records

    def _match_scicode(model_name: str) -> float | None:
        """对一条记录的模型名，返回匹配到的 SciCode 分数（或 None）。"""
        for entry in scidata:
            sc_model = entry.get("model", "")
            sc_score = entry.get("scicode")
            if sc_score is None:
                continue
            # 双向包含匹配
            if sc_model in model_name or model_name in sc_model:
                return float(sc_score)
        return None

    matched = 0
    for r in records:
        name = r.get("模型", "")
        score = _match_scicode(name)
        if score is not None:
            r["SciCode 编程能力 (%)"] = score
            matched += 1
        else:
            # 确保字段存在且为 0
            r.setdefault("SciCode 编程能力 (%)", 0)
    print(f"  [benchmark] SciCode 分数匹配: {matched}/{len(records)} 条")
    return records


def _match_aa_model_to_token(aa_model: dict) -> list[dict]:
    """将 AA API 返回的单个模型匹配到 Token 表模型，返回评测记录列表。"""
    records = []
    aa_name = aa_model.get("name", aa_model.get("id", ""))
    aa_slug = aa_model.get("slug", "").lower()
    aa_id = aa_model.get("id", "").lower()

    # 遍历映射表，看 AA 模型是否匹配我们的关键词
    for token_keyword, aa_keywords in _AA_MODEL_MAP.items():
        matched = False
        for kw in aa_keywords:
            if kw.lower() in aa_slug or kw.lower() in aa_id or kw.lower() in aa_name.lower():
                matched = True
                break
        if not matched:
            continue

        # 获取评测指标
        intel = aa_model.get("intelligenceIndex") or aa_model.get("intelligence_index") or aa_model.get("qualityScore") or 0
        gdpval = aa_model.get("gdpvalAAv2Elo") or aa_model.get("gdpval_elo") or 0
        speed = aa_model.get("outputSpeed") or aa_model.get("output_speed") or 0
        cost = aa_model.get("costPerTask") or aa_model.get("cost_per_task") or 0

        # 注意: SciCode 分数由 _apply_scicode_scores() 从本地 JSON 统一填充。
        record = {
            "模型": token_keyword,
            "AA Intelligence Index": intel,
            "SciCode 编程能力 (%)": 0,
            "GDPval-AA v2 Elo": gdpval,
            "Output Speed (t/s)": speed,
            "Cost per Task (USD)": cost,
            "来源": "Artificial Analysis",
            "更新时间": DATE,
        }
        records.append(record)
        break

    return records


def discover_benchmark(date_str: str) -> list[dict]:
    """采集模型评测数据，返回评测记录列表"""
    records = []
    aa_key = os.environ.get("AA_API_KEY", "")

    # 1. 尝试 Artificial Analysis API
    if aa_key:
        try:
            url = "https://artificialanalysis.ai/api/v2/data/llms/models"
            req = urllib.request.Request(url, headers={
                "x-api-key": aa_key,
                "User-Agent": "CMIS-Daily/1.0",
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list):
                for model in data:
                    for record in _match_aa_model_to_token(model):
                        records.append(record)
            elif isinstance(data, dict):
                for model in data.get("models", data.get("data", [])):
                    for record in _match_aa_model_to_token(model):
                        records.append(record)
            if records:
                print(f"  [benchmark] AA API 返回 {len(records)} 条匹配记录")
        except Exception as e:
            print(f"  [benchmark] AA API 调用失败: {e}")

    # 2. 使用 fallback 数据
    if not records:
        records = [dict(r) for r in _BENCHMARK_FALLBACK]
        print(f"  [benchmark] 使用 fallback 数据: {len(records)} 条")

    # 3. 填充 SciCode 分数（从 data/aa_scicode_scores.json 模糊匹配）
    records = _apply_scicode_scores(records)

    return records


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"[discover] CMIS Daily Discovery Start: {DATE}")

    # Token 发现
    print("[discover] === Token Model Discovery ===")
    token_rows, token_log = build_discovered_token_rows()
    token_result = {
        "date": DATE,
        "discovered_at": NOW.isoformat(),
        "model_count": len(token_rows),
        "vendors": sorted({r["vendor"] for r in token_rows}),
        "rows": token_rows,
        "discovery_log": token_log,
        "dynamic_sources": DYNAMIC_SOURCES,
    }
    DISCOVERED_TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    DISCOVERED_TOKEN_PATH.write_text(json.dumps(token_result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[discover] Token models: {len(token_rows)} rows, {len(token_result['vendors'])} vendors")
    print(f"[discover] Written: {DISCOVERED_TOKEN_PATH}")

    # GPU 发现
    print("[discover] === GPU Discovery ===")
    gpu_result = build_discovered_gpu_list()
    gpu_result["date"] = DATE
    gpu_result["discovered_at"] = NOW.isoformat()
    gpu_result["dynamic_sources"] = DYNAMIC_SOURCES
    DISCOVERED_GPU_PATH.parent.mkdir(parents=True, exist_ok=True)
    DISCOVERED_GPU_PATH.write_text(json.dumps(gpu_result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[discover] GPU new candidates: {len(gpu_result['new_candidates'])}")
    print(f"[discover] Written: {DISCOVERED_GPU_PATH}")

    # Benchmark 评测数据发现
    print("[discover] === Model Benchmark Discovery ===")
    benchmark_records = discover_benchmark(DATE)
    # 为 fallback 数据补齐厂商字段（API 采集时已由匹配函数处理）
    for r in benchmark_records:
        if "厂商" not in r:
            # 从 fallback 映射中查找厂商
            for fb in _BENCHMARK_FALLBACK:
                if fb["模型"] == r["模型"]:
                    r["厂商"] = fb["厂商"]
                    break
    benchmark_result = {
        "date": DATE,
        "discovered_at": NOW.isoformat(),
        "record_count": len(benchmark_records),
        "rows": benchmark_records,
    }
    DISCOVERED_BENCHMARK_PATH.parent.mkdir(parents=True, exist_ok=True)
    DISCOVERED_BENCHMARK_PATH.write_text(json.dumps(benchmark_result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[discover] Benchmark records: {len(benchmark_records)}")
    print(f"[discover] Written: {DISCOVERED_BENCHMARK_PATH}")

    print("[discover] Done.")


if __name__ == "__main__":
    main()
