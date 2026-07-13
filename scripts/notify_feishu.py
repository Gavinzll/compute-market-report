#!/usr/bin/env python3
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
