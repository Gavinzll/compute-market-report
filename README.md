# Compute Market Intelligence System

CMIS（Compute Market Intelligence System）用于生成和发布《全球算力市场情报日报》。报告覆盖国内算力租赁、海外 GPU Cloud、Token API 价格、GPU 采购价格、毛回本测算、异常样本审计和数据源追踪。

本仓库只承担静态页面托管、报告归档和规则存储。日报的实际执行由 TRAE 定时任务完成，GitHub 不负责运行采集任务，也不使用 GitHub Actions。

## 在线入口

- 最新桌面版报告：`https://gavinzll.github.io/compute-market-report/latest.html`
- 最新手机版报告：`https://gavinzll.github.io/compute-market-report/latest-mobile.html`
- 报告归档首页：`https://gavinzll.github.io/compute-market-report/`
- 历史桌面版报告：`https://gavinzll.github.io/compute-market-report/reports/{YYYY-MM-DD}.html`
- 历史手机版报告：`https://gavinzll.github.io/compute-market-report/reports/{YYYY-MM-DD}-mobile.html`

## 报告覆盖范围

CMIS Daily 主要关注三类市场信号：

- 国内算力租赁：以中国大陆 8 GPU HGX Server / 8卡整机月租为主口径，单位统一为万元/台/月。
- 海外 GPU Cloud：以海外公开 GPU Cloud 小时价为辅助参考，统一折算为人民币万元/8卡整机/月，但不进入国内主指数。
- Token 价格：覆盖国内外主流模型厂商，区分官方价、海外三方价和境内三方价。

报告还包含 GPU 采购价、毛回本参考、Rejected / Review 样本、覆盖率诊断、数据源索引和历史数据快照。

## 数据治理原则

数据进入主图、主指数、ROI、历史库和 AI 总结前，必须经过：

`Collect → Classify → Normalize → Validate → Publish`

未通过校验的数据不得进入主图、主指数、ROI 或方向性结论，只能进入辅助样本、候选样本、Rejected / Review 样本或审计文件。治理目标是“主指数严格、情报覆盖充分”：主指数不放松门槛，辅助层保留足够线索。

## 动态目录

GPU 和 Token 模型目录不是静态清单。

- GPU 基线名单是最低覆盖要求，不是上限。新卡出现后先进入 Candidate Samples；连续多期有可追溯价格后，再升级为基线名单。
- 展示目录优先保留当前主流、先进和战略关注型号。历史型号可保留在覆盖率诊断中，但不应长期占据主图。
- Token 模型目录每次运行前应更新，只保留各厂商当前主流、核心或先进模型。已 deprecated、长期无价格或非文本模型不进入主表。

## 自动化运行

TRAE 定时任务每天执行一次，流程为：

1. 拉取 GitHub main 分支最新代码。
2. 读取 `prompts/` 下的规则文件。
3. 采集、补采并校验数据。
4. 运行 `scripts/generate_cmis_daily.py` 生成报告。
5. 校验图表脚本和关键输出文件。
6. 提交并推送生成结果。
7. 通过飞书 Webhook 发送成功或失败通知。

定时任务的详细执行边界见 `prompts/automation_runbook.md`。

## 目录结构

```text
.
├── assets/
│   └── charts.js
├── data/
│   ├── audit_{YYYY-MM-DD}.json
│   ├── cmis_snapshot_{YYYY-MM-DD}.json
│   ├── history.jsonl
│   └── rejected_{YYYY-MM-DD}.json
├── prompts/
│   ├── automation_runbook.md
│   ├── report_config.md
│   ├── source_pool.md
│   └── system_prompt.md
├── reports/
│   ├── {YYYY-MM-DD}.html
│   └── {YYYY-MM-DD}-mobile.html
├── scripts/
│   ├── generate_cmis_daily.py
│   └── notify_feishu.py
├── index.html
├── latest.html
├── latest-mobile.html
└── README.md
```

## 关键文件

- `prompts/system_prompt.md`：长期稳定的数据治理底座。
- `prompts/report_config.md`：报告模块、展示顺序、字段和发布配置。
- `prompts/source_pool.md`：数据来源、补采顺序和扩源规则。
- `prompts/automation_runbook.md`：定时任务运行说明。
- `scripts/generate_cmis_daily.py`：日报生成入口。
- `scripts/notify_feishu.py`：飞书通知脚本。
- `assets/charts.js`：ECharts 图表逻辑。

## 维护边界

- 不创建 `.github/workflows`，不使用 GitHub Actions 跑日报。
- 不把 GitHub Token、飞书 Webhook 或其它敏感凭据写入仓库文件、HTML、数据文件、日志或报告正文。
- 不让 `null`、`Official Missing`、`海外三方未覆盖`、`境内三方待补采`、`无法计算` 进入 Token 表或图表数组。
- README 是人工维护文件。本次更新后，除非 Gavin YszY 明确下达人工命令，否则自动化任务和后续常规日报更新不得修改 `README.md`。

## 版权

© Gavin YszY · 算力市场情报日报
