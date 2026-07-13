# 全球算力市场情报日报 (CMIS Daily)

[![CMIS Daily](https://img.shields.io/badge/CMIS-Daily-blue)](https://gavinzll.github.io/compute-market-report/)
[![Last Updated](https://img.shields.io/badge/Last%20Updated-2026--07--13-green)](https://gavinzll.github.io/compute-market-report/latest.html)

> 每日 08:45 自动采集、治理、校验并发布全球算力市场核心定价数据。

**在线报告**：https://gavinzll.github.io/compute-market-report/latest.html

---

## 什么是 CMIS Daily？

CMIS Daily（Compute Market Intelligence System Daily）是一份面向个人投资决策的全球算力市场情报日报，覆盖：

- **Token 价格**：主流大模型 API 官方价 vs 市场价
- **国内算力租赁**：以 SMM 为主口径的 8卡 HGX 整机月租
- **海外 GPU Cloud**：以 ComputeStacker 为主口径的美元/卡/小时
- **GPU 采购价格**：覆盖训练卡、推理卡、消费级和国产 GPU
- **利润测算**：基于校验通过数据的 ROI 与回本周期
- **供需监测**：库存、交期、生命周期判断
- **趋势走势**：近 7/30 日价格与指数变化

---

## 架构与治理

### 双文件 Prompt 结构

本系统采用"稳定治理底座 + 可变日报配置"的双文件设计：

| 文件 | 作用 | 修改频率 |
|------|------|----------|
| [`prompts/system_prompt.md`](prompts/system_prompt.md) | 数据治理、ETL、七层校验、审计、HTML 规范 | 原则上长期不改 |
| [`prompts/report_config.md`](prompts/report_config.md) | GPU 覆盖、Token 覆盖、模块、分类、飞书模板 | 经常调整 |

新增 GPU（如 B300、GB300）或调整报告模块时，只需修改 `report_config.md`，不触碰数据治理底座。

### ETL 数据治理流程

任何数据进入报告、指数、图表或 AI 总结之前，必须完成：

```
Collect → Classify → Normalize → Validate → Publish
```

**七层校验体系**：

1. **Confidence Score** — 来源可信度评分（0-100），< 70 不得进入主指数
2. **单位校验** — 小时/日/月/单卡/整机/集群严格区分
3. **GPU 数量校验** — 64卡集群必须先拆算到 8卡整机
4. **价格合理性校验** — 超过合理区间 2 倍立即 REJECT
5. **来源优先级校验** — 冲突时采用高优先级，不得平均
6. **Historical Validation** — 日环比 >30% REVIEW，>100% REJECT（除非多源确认）
7. **口径校验** — GPU Cloud 小时价不得进入国内租赁指数

### Source Consensus（来源共识）

每个 GPU 型号当日价格计算多源一致性：

- **High**（±15% 内多源一致）→ 正常进入指数
- **Medium**（有个别离群值）→ 可进入，AI 总结注明
- **Low**（差异 >30%）→ AI 总结不得做方向性判断，只能说"数据存在分歧，等待进一步确认"

### Data Freeze（数据冻结）

日报开始生成时记录 `freeze_time`（精确到分钟），所有数据采集时间必须 ≤ freeze_time。freeze_time 之后的新数据留待下一期，确保同一份日报内数据口径一致。

---

## 数据口径

### 国内算力租赁（Mandatory）

- **地区**：中国大陆
- **对象**：8 GPU HGX Server / 8卡整机
- **单位**：万元/台/月
- **包含**：IDC、机柜、电力、IB/网络、托管、运维
- **合同**：一年左右市场主流长租
- **来源优先级**：SMM > IDC 一手 > 运营商 > 招投标 > 媒体 > 云厂商 > 论坛 > 社区

** Sanity Check **：
- H100 80G：约 6.5-8.5 万元/月
- A100 80G：约 3.0-4.5 万元/月
- RTX 5090/4090：约 1.0-1.5 万元/月

### 海外算力租赁

- **口径**：美元/卡/小时 或 人民币/卡/小时
- **来源优先级**：ComputeStacker > RunPod > Lambda > Vast.ai > CoreWeave > 其它
- 等效 8卡月租仅作参考，**不得进入国内租赁指数**

### Token 价格

- **Official Price**：厂商官网/API 文档/计费页
- **Market Price**：OpenRouter / Artificial Analysis 等替代门户
- 市场价不得冒充官方价

### GPU 采购价格

覆盖 Training / Inference / Consumer / 国产 四大类：

- **Training**：GB300、GB200、B300、B200、H200、H100、H800、H20、A100、A800
- **Inference**：L40S、L20、L4
- **Consumer**：RTX 5090、RTX 4090
- **国产**：昇腾 910C/910B、寒武纪 MLU、海光 DCU、壁仞、摩尔线程

---

## 自动化执行

| 项目 | 说明 |
|------|------|
| **执行端** | TRAE 自动化（每日 08:45） |
| **托管端** | GitHub Pages（静态展示） |
| **通知** | 飞书 Webhook 推送摘要 + 报告链接 |
| **工作流** | 严禁使用 GitHub Actions，GitHub 仅做托管 |

执行流程：

1. `git fetch origin main` → `git pull --rebase origin main`
2. 记录 `freeze_time`
3. 读取 `prompts/system_prompt.md` + `prompts/report_config.md`
4. 采集 → Classify → Normalize → Validate（七层）→ Source Consensus → Publish
5. 生成 `latest.html`、`reports/{date}.html`、`index.html`、数据文件、审计文件
6. `git add` → `git commit` → `git push origin main`
7. 飞书推送固定模板通知

---

## 文件结构

```
├── latest.html                    # 最新日报固定入口
├── index.html                     # 归档首页/门户
├── reports/
│   └── {YYYY-MM-DD}.html          # 历史日报归档
├── data/
│   ├── cmis_snapshot_{date}.json  # 当日结构化快照
│   ├── history.jsonl              # 历史时间序列
│   ├── audit_{date}.json          # 数据审计记录
│   └── rejected_{date}.json       # 异常样本记录
├── assets/
│   └── charts.js                  # ECharts 图表逻辑
├── scripts/
│   ├── generate_cmis_daily.py     # 日报生成器
│   └── notify_feishu.py           # 飞书通知脚本
├── prompts/
│   ├── system_prompt.md           # 数据治理底座（长期不改）
│   └── report_config.md           # 日报配置（经常调整）
└── README.md                      # 本文件
```

---

## 版本信息

每份 HTML 报告页脚包含：

```
CMIS Daily v{Report Version} | Prompt {Git Commit} | Freeze {YYYY-MM-DD HH:MM}
```

- **Report Version**：日报版本号（semver）
- **Prompt Version**：当期执行时 prompts 目录的 Git commit 短哈希
- **Data Freeze**：当日数据冻结时间

---

## 免责声明

本报告仅供个人研究参考，不构成任何投资建议。数据来源于公开渠道，经过自动化采集与校验，但无法保证 100% 准确。所有结论基于 `Validate == PASS` 且 `Consensus != Low` 的数据，异常样本已在审计文件中标注。
