# Compute Market Intelligence System (CMIS)

本仓库用于每日生成并发布《全球算力市场情报日报（CMIS Daily）》。

## 文件结构

- `latest.html`：最新日报固定入口
- `reports/2026-07-13.html`：历史日报
- `index.html`：归档首页
- `data/cmis_snapshot_2026-07-13.json`：当日结构化快照
- `data/history.jsonl`：历史时间序列追加文件
- `assets/charts.js`：ECharts 图表逻辑
- `scripts/generate_cmis_daily.py`：日报生成器
- `scripts/notify_feishu.py`：飞书 Webhook 通知脚本
- `scripts/` 可用于后续接入每日 08:45 自动运行；当前专用 Token 缺少 GitHub workflow 写入权限，因此工作流文件未随本次发布推送。

## Secrets

请在 GitHub 仓库 Settings → Secrets and variables → Actions 中配置：

- `CMIS_FEISHU_WEBHOOK`：飞书机器人 Webhook

如需启用 GitHub Actions 自动运行，请使用具备 `workflow` 权限的凭据添加工作流，并将飞书 Webhook 配置为 Secret，不要写入仓库文件。

## 数据口径

国内租赁以 SMM 为主口径；海外租赁以 ComputeStacker 为主口径；Token 价格以官方 API 定价为 Official Price；硬件采购价需区分官方/权威/市场/传闻/估算和置信度。
