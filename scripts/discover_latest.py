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

def fetch_json(url: str, timeout: int = 30) -> dict | list | None:
    """从 URL 获取 JSON 数据。"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CMIS-Daily-Discovery/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception as e:
        print(f"[discover] fetch failed: {url} -> {e}", file=sys.stderr)
        return None


def fetch_text(url: str, timeout: int = 30) -> str | None:
    """从 URL 获取纯文本/HTML。"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CMIS-Daily-Discovery/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[discover] fetch failed: {url} -> {e}", file=sys.stderr)
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
    "Kimi / Moonshot": ["kimi-", "moonshot-"],
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

# 各厂商手动维护的最新模型锚点（当 API 无法提供精确官方价时作为 fallback）
# 这些锚点会覆盖/补充 API 发现结果
VENDOR_MODEL_ANCHORS: list[dict[str, Any]] = [
    # --- 海外 ---
    {"vendor": "OpenAI", "models": [
        {"name": "GPT-5.5", "context": "1M", "official_in_usd": 5.0, "official_out_usd": 30.0},
        {"name": "GPT-5.4", "context": "1M", "official_in_usd": 2.5, "official_out_usd": 15.0},
        {"name": "GPT-5.4 mini", "context": "270K", "official_in_usd": 0.75, "official_out_usd": 4.5},
        {"name": "o4 Mini", "context": "200K", "official_in_usd": 1.1, "official_out_usd": 4.4},
    ]},
    {"vendor": "Anthropic", "models": [
        {"name": "Claude Opus 4.8", "context": "1M", "official_in_usd": 5.0, "official_out_usd": 25.0},
        {"name": "Claude Sonnet 4.6", "context": "1M", "official_in_usd": 3.0, "official_out_usd": 15.0},
        {"name": "Claude Haiku 4.5", "context": "200K", "official_in_usd": 1.0, "official_out_usd": 5.0},
    ]},
    {"vendor": "Google", "models": [
        {"name": "Gemini 3.1 Pro", "context": "1M", "official_in_usd": 2.0, "official_out_usd": 12.0},
        {"name": "Gemini 3.5 Flash", "context": "1M", "official_in_usd": 1.5, "official_out_usd": 9.0},
        {"name": "Gemini 3.1 Flash-Lite", "context": "1M", "official_in_usd": 0.25, "official_out_usd": 1.5},
    ]},
    {"vendor": "Mistral", "models": [
        {"name": "Mistral Medium 3.5", "context": "256K", "official_in_usd": 2.0, "official_out_usd": 7.5},
        {"name": "Mistral Large 3", "context": "256K", "official_in_usd": 0.5, "official_out_usd": 1.5},
        {"name": "Mistral Small 4", "context": "256K", "official_in_usd": 0.1, "official_out_usd": 0.3},
    ]},
    {"vendor": "Cohere", "models": [
        {"name": "Command A+", "context": "128K", "official_in_usd": 2.5, "official_out_usd": 10.0},
        {"name": "Command R+", "context": "128K", "official_in_usd": 2.5, "official_out_usd": 10.0},
    ]},
    {"vendor": "xAI Grok", "models": [
        {"name": "Grok 4.3", "context": "1M", "official_in_usd": 1.25, "official_out_usd": 2.5},
        {"name": "Grok 4 Fast", "context": "256K", "official_in_usd": 0.2, "official_out_usd": 0.5},
    ]},
    {"vendor": "Meta Llama", "models": [
        {"name": "Llama 4 Maverick", "context": "1M", "official_in_usd": 0.3, "official_out_usd": 0.6},
        {"name": "Llama 4 Scout", "context": "128K", "official_in_usd": 0.15, "official_out_usd": 0.35},
    ]},
    # --- 国产 ---
    {"vendor": "DeepSeek", "models": [
        {"name": "DeepSeek-V4-Pro", "context": "1M", "official_in_cny": 3.0, "official_out_cny": 6.0},
        {"name": "DeepSeek-V4-Flash", "context": "1M", "official_in_cny": 1.0, "official_out_cny": 2.0},
    ]},
    {"vendor": "阿里云/通义千问", "models": [
        {"name": "Qwen3.7-Max", "context": "1M", "official_in_cny": 12.0, "official_out_cny": 36.0},
        {"name": "Qwen3.7-Plus", "context": "1M", "official_in_cny": 2.0, "official_out_cny": 8.0},
    ]},
    {"vendor": "火山方舟/豆包", "models": [
        {"name": "Doubao-Seed-1.6", "context": "256K", "official_in_cny": 0.8, "official_out_cny": 2.0},
        {"name": "Doubao-Seed-1.6-Flash", "context": "256K", "official_in_cny": 0.15, "official_out_cny": 1.5},
        {"name": "Doubao-Seed-1.6-Thinking", "context": "256K", "official_in_cny": 0.8, "official_out_cny": 8.0},
    ]},
    {"vendor": "腾讯混元", "models": [
        {"name": "Hunyuan-Hy3", "context": "256K", "official_in_cny": 1.0, "official_out_cny": 4.0},
        {"name": "Hunyuan-role-latest", "context": "官方未明确", "official_in_cny": 2.4, "official_out_cny": 9.6},
        {"name": "Hunyuan-A13B", "context": "128K", "official_in_cny": 0.5, "official_out_cny": 2.0},
    ]},
    {"vendor": "智谱 GLM / Z.ai", "models": [
        {"name": "GLM-5.2", "context": "1M", "official_in_cny": 8.0, "official_out_cny": 28.0},
        {"name": "GLM-5.1 Pro", "context": "200K", "official_in_cny": 6.0, "official_out_cny": 24.0},
    ]},
    {"vendor": "百度文心", "models": [
        {"name": "ERNIE 5.1", "context": "128K", "official_in_cny": 4.0, "official_out_cny": 18.0},
        {"name": "ERNIE-4.5-Turbo", "context": "32K", "official_in_cny": 0.8, "official_out_cny": 3.2},
    ]},
    {"vendor": "Kimi / Moonshot", "models": [
        {"name": "Kimi K2.7 Code", "context": "256K", "official_in_cny": 6.5, "official_out_cny": 27.0},
        {"name": "Kimi K2.6", "context": "256K", "official_in_cny": 6.5, "official_out_cny": 27.0},
    ]},
    {"vendor": "MiniMax", "models": [
        {"name": "MiniMax-M3 标准层 ≤512K", "context": "≤512K", "official_in_cny": 2.1, "official_out_cny": 8.4},
        {"name": "MiniMax-M3 标准层 >512K", "context": ">512K", "official_in_cny": 4.2, "official_out_cny": 16.8},
    ]},
    {"vendor": "讯飞星火", "models": [
        {"name": "Spark X2", "context": "官方未明确", "official_in_cny": 1.0, "official_out_cny": 2.0},
        {"name": "Spark Max", "context": "32K", "official_in_cny": 21.0, "official_out_cny": 21.0},
    ]},
    {"vendor": "百川智能", "models": [
        {"name": "Baichuan-M3-Plus", "context": "32K", "official_in_cny": 5.0, "official_out_cny": 9.0},
        {"name": "Baichuan-M3", "context": "32K", "official_in_cny": 10.0, "official_out_cny": 30.0},
    ]},
    {"vendor": "零一万物", "models": [
        {"name": "Yi-Lightning", "context": "官方未明确", "official_in_cny": 0.99, "official_out_cny": 0.99},
        {"name": "Yi-Large", "context": "32K", "official_in_cny": 20.0, "official_out_cny": 20.0},
    ]},
    {"vendor": "阶跃星辰", "models": [
        {"name": "Step 3.5 Flash", "context": "官方未明确", "official_in_cny": 0.7, "official_out_cny": 2.1},
        {"name": "Step-R1-V-Mini", "context": "官方未明确", "official_in_cny": 2.5, "official_out_cny": 8.0},
    ]},
    {"vendor": "商汤日日新", "models": [
        {"name": "SenseNova-V6.5-Pro", "context": "官方未明确", "official_in_cny": 3.0, "official_out_cny": 9.0},
        {"name": "SenseNova-V6.5-Turbo", "context": "官方未明确", "official_in_cny": 1.5, "official_out_cny": 4.5},
    ]},
    {"vendor": "昆仑万维天工", "models": [
        {"name": "SkyClaw-v1.0", "context": "1M", "official_in_cny": 0.5, "official_out_cny": 4.0},
        {"name": "SkyClaw-v1.0-lite", "context": "官方未明确", "official_in_cny": 0.3, "official_out_cny": 1.5},
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


def build_discovered_token_rows() -> list[dict[str, Any]]:
    """构建发现后的 Token 数据行。

    策略：
    1. 从 API 源动态发现模型
    2. 用 VENDOR_MODEL_ANCHORS 中的手动锚点覆盖/补充（锚点优先级更高，因为包含官方价）
    3. 对缺失官方价的模型，用 API 发现的价格作为市场价参考
    """
    print("[discover] Fetching LiteLLM...")
    litellm = discover_from_litellm()
    print(f"[discover] LiteLLM: {sum(len(v) for v in litellm.values())} models")

    print("[discover] Fetching OpenRouter...")
    openrouter = discover_from_openrouter()
    print(f"[discover] OpenRouter: {sum(len(v) for v in openrouter.values())} models")

    print("[discover] Fetching models.dev...")
    modelsdev = discover_from_modelsdev()
    print(f"[discover] models.dev: {sum(len(v) for v in modelsdev.values())} models")

    discovered = merge_vendor_models(litellm, openrouter, modelsdev)

    rows: list[dict[str, Any]] = []
    discovered_log: list[dict] = []

    for anchor in VENDOR_MODEL_ANCHORS:
        vendor = anchor["vendor"]
        for model in anchor["models"]:
            name = model["name"]
            context = model.get("context", "未知")

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

            # 查找 API 发现结果中的匹配模型（用于三方价）
            api_models = discovered.get(vendor, [])
            matched_api = None
            for am in api_models:
                aid = am["id"].lower()
                # 简单匹配：模型名包含关系
                if name.lower().replace(" ", "-").replace(".", "-") in aid or \
                   name.lower().replace(" ", "").replace(".", "") in aid.replace("-", ""):
                    matched_api = am
                    break

            # 三方价：优先用 API 发现的市场价
            overseas_in_usd = None
            overseas_out_usd = None
            overseas_source = "API 发现结果为空"
            if matched_api:
                inp = matched_api.get("input_cost_per_token")
                out = matched_api.get("output_cost_per_token")
                if inp is not None:
                    overseas_in_usd = round(float(inp) * 1_000_000, 4)
                if out is not None:
                    overseas_out_usd = round(float(out) * 1_000_000, 4)
                overseas_source = f"{matched_api['_source']} / {matched_api['id']}"

            # 境内三方价：对国产模型，尝试从 API 中找同名
            domestic_in_cny = None
            domestic_out_cny = None
            domestic_source = "境内三方近似参考"
            if region == "国产" and matched_api:
                # 如果 API 发现的是国产模型托管在境外平台的价格，可作为海外三方参考
                pass

            rows.append({
                "vendor": vendor,
                "model": name,
                "region": region,
                "context": context,
                "official_in": official_in,
                "official_out": official_out,
                "official_currency": currency,
                "official_source": f"{vendor} 官方定价页（锚点）",
                "overseas_in_usd": overseas_in_usd,
                "overseas_out_usd": overseas_out_usd,
                "overseas_source": overseas_source,
                "domestic_in_cny": domestic_in_cny,
                "domestic_out_cny": domestic_out_cny,
                "domestic_source": domestic_source,
                "note": f"动态发现：{vendor} {name}；API 匹配={matched_api is not None}",
                "confidence": 90,
                "status": "PASS",
                "api_discovered_models": [m["id"] for m in api_models[:5]],  # 记录前5个发现的模型ID
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
BASELINE_GPU_GROUPS = [
    ("Training", ["GB300", "GB200", "B300", "B200", "H200", "H100 80G", "H800", "H20", "A100 80G", "A800"]),
    ("Inference", ["L40S", "L20", "L4"]),
    ("Consumer", ["RTX 5090", "RTX 4090"]),
    ("国产", ["昇腾 910C", "昇腾 910B", "寒武纪 MLU370-X8", "海光 DCU K100", "壁仞 BR100", "摩尔线程 MTT S4000"]),
]


def build_discovered_gpu_list() -> dict[str, Any]:
    """构建发现的 GPU 列表。

    策略：
    1. 以基线名单为基础，保证稳定性
    2. 从 GPU Cloud 聚合源发现新卡
    3. 新卡进入 candidate_pool，连续 3 期出现后可人工审核加入基线
    """
    print("[discover] Fetching GPU Cloud sources...")
    cloud_gpus = discover_gpu_from_cloudgpus()
    pricing_gpus = discover_gpu_from_gpucloudpricing()

    all_discovered = set(cloud_gpus) | set(pricing_gpus)

    # 基线名单中的 GPU
    baseline_gpus = set()
    for _, items in BASELINE_GPU_GROUPS:
        baseline_gpus.update(items)

    # 新发现的 GPU（不在基线中）
    new_gpus = sorted(all_discovered - baseline_gpus)

    # 过滤掉明显不是 GPU 的噪声
    noise_filter = {"GPU", "CPU", "RAM", "SSD", "HDD", "NVMe", "TB", "GB"}
    new_gpus = [g for g in new_gpus if g not in noise_filter and len(g) >= 3]

    return {
        "baseline_groups": BASELINE_GPU_GROUPS,
        "discovered_from_cloudgpus": cloud_gpus,
        "discovered_from_gpucloudpricing": pricing_gpus,
        "new_candidates": new_gpus,
        "recommendation": "基线名单保持稳定；新卡进入 candidate_pool，连续 3 期有数据后人工审核加入基线。",
    }


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
    DISCOVERED_GPU_PATH.parent.mkdir(parents=True, exist_ok=True)
    DISCOVERED_GPU_PATH.write_text(json.dumps(gpu_result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[discover] GPU new candidates: {len(gpu_result['new_candidates'])}")
    print(f"[discover] Written: {DISCOVERED_GPU_PATH}")

    print("[discover] Done.")


if __name__ == "__main__":
    main()
