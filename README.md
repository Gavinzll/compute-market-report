# Compute Market Intelligence System (CMIS)

本仓库用于每日生成并发布《全球算力市场情报日报（CMIS Daily）》。

## 文件结构

- `latest.html`：最新日报固定入口
- `reports/2026-07-14.html`：历史日报
- `index.html`：归档首页
- `data/cmis_snapshot_2026-07-14.json`：当日结构化快照
- `data/history.jsonl`：历史时间序列追加文件
- `assets/charts.js`：ECharts 图表逻辑
- `scripts/generate_cmis_daily.py`：日报生成器
- `scripts/notify_feishu.py`：飞书 Webhook 通知脚本
- `prompts/system_prompt.md`：稳定数据治理底座
- `prompts/report_config.md`：报告模块、字段和发布配置
- `prompts/source_pool.md`：Token、GPU Cloud、国内租赁、采购价、招投标和规格校验扩源清单
## 自动化方式

定时任务由 TRAE 自动化执行。GitHub 仓库只作为静态站点托管与历史报告归档，不负责运行日报生成任务。

TRAE 自动化执行顺序：

1. 采集并生成 HTML / data / assets 文件。
2. 将结果提交到本仓库 main 分支。
3. GitHub Pages 展示 `latest.html` 和历史归档。
4. TRAE 通过飞书 Webhook 推送简短摘要与报告链接。

## 数据口径

国内租赁以 SMM / IDC / 运营商等 8卡整机月租为主口径；海外 GPU Cloud 以 RunPod、Lambda、Vast.ai、Cloud-GPUs、GPUCloudPricing、TensorDock、DataCrunch、CUDO 等公开小时价为辅助；Token 价格以厂商官方 API 定价为 Official Price，LiteLLM、OpenRouter、models.dev、BenchLM、llmpricing、morph-llm 等只作为结构化市场辅助；硬件采购价需区分官方规格、整机渠道、招投标成交、市场报价和估算置信度。

扩源治理目标不是减少报告内容，而是做到“主指数严格、情报覆盖充分”。未通过国内主口径的数据不得进入主图、主指数、ROI 或 AI 总结，但必须进入辅助样本、候选样本、Rejected 样本或缺口清单。

服务器租赁价格必须对 SMM 做深扒：同时检索算力直播、移动详情页、news.metal.com 镜像和站内关键词结果；若仍缺失，再扩展到 IDC 门户、个人站、指数站、公众号、抖音、视频号、B站、知乎、CSDN、掘金、墨天轮、东方财富财富号等低置信线索层，并保留为 Candidate / Lead。
