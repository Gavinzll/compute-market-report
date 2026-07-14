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
📅 日期：{date}

📈 GPU 租赁：
国内 H100 8卡整机月租采用 SMM 主口径；低置信度卡型仅作待复核观察。

💰 GPU 采购：
采购价以低置信度和协议价缺口为主，本期不进入投资结论。

🪙 Token 价格：
OpenAI、Anthropic、Google 与主流国产模型 Token 表已补齐官方、海外三方、境内三方六个核心价格字段。

⚡ 关键异动：
样本起始/延续日按七层校验写入审计；共识 Low 的数据不做方向性判断。

🧠 AI 一句话：
通过校验的数据支持 H100 长租口径仍处高位，其它分歧样本等待进一步确认。

📊 完整报告：https://gavinzll.github.io/compute-market-report/latest.html?v={stamp}"""

payload = json.dumps({"msg_type": "text", "content": {"text": text}}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=20) as resp:
    print(resp.read().decode("utf-8", errors="ignore"))
