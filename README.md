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
## 自动化方式

定时任务由 TRAE 自动化执行。GitHub 仓库只作为静态站点托管与历史报告归档，不负责运行日报生成任务。

TRAE 自动化执行顺序：

1. 采集并生成 HTML / data / assets 文件。
2. 将结果提交到本仓库 main 分支。
3. GitHub Pages 展示 `latest.html` 和历史归档。
4. TRAE 通过飞书 Webhook 推送简短摘要与报告链接。

## 数据口径

国内租赁以 SMM 为主口径；海外租赁以 ComputeStacker 为主口径；Token 价格以官方 API 定价为 Official Price；硬件采购价需区分官方/权威/市场/传闻/估算和置信度。
