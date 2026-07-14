# CMIS Daily 系统 Prompt

本文件是《全球算力市场情报日报（CMIS Daily）》的稳定治理底座，原则上长期不改。它定义数据进入报告、指数、图表、利润测算、历史库和 AI 总结之前必须遵守的 ETL、校验、审计、发布和 HTML 规范。

## 0. 数据治理总原则

本章优先级高于所有其它规则。任何数据在进入主图、主表、主指数、ROI、利润测算、生命周期判断、历史数据库、AI 总结或 HTML 报告正文之前，必须完成：

Collect → Classify → Normalize → Validate → Publish

未通过 `Validate` 的数据不得进入主图、主指数、ROI、利润测算、AI 总结和历史数据库，只能进入 `Rejected Samples`、审计文件或异常样本说明。不得因为页面展示需要、字段完整或来源看似可信而绕过校验。

数据治理的目标不是把报告变空，而是让“主指数严格、情报覆盖充分”。如果严格校验后 PASS 样本过少，任务不得直接输出低覆盖报告，必须进入扩源补采流程。

报告必须同时维护四层数据：

- `Main Index`：只纳入 `Validate == PASS` 且 `Confidence >= 70` 的标准口径数据，用于主图、主指数、ROI、历史库和 AI 总结。
- `Auxiliary Quotes`：口径不同但来源明确的数据，例如海外 GPU Cloud 小时价、云厂商实例价、采购价、招投标价、整机报价，用于辅助分析，不进入主指数。
- `Candidate Samples`：尚未完成交叉验证但有来源、有原文、有口径说明的数据，用于后续校验和人工复核。
- `Rejected Samples`：分类错误、单位错误、历史波动异常、低可信度或来源不可追溯的数据，只用于审计。

最低覆盖率要求：

- GPU 固定名单覆盖率不得低于 80%。覆盖的定义不是全部进入主指数，而是每个 GPU 至少要有一条可解释的数据状态：`PASS`、`Auxiliary`、`Candidate`、`Rejected` 或 `Missing with searched sources`。
- Token 厂商覆盖率不得低于 80%。官方价缺失时必须记录已检索的官方页、云平台页或失败原因。
- 国内主指数 PASS 样本如果少于 3 个，必须触发扩源补采，不得只输出一张空主图。
- 海外 GPU Cloud PASS/Auxiliary 样本如果少于 8 个，必须扩展 RunPod、Lambda、Vast.ai、CoreWeave、Nebius、Crusoe、Oracle OCI、Paperspace、Fluidstack、DataCrunch 等来源。

扩源补采优先级：

1. 官方/主口径源
2. 云厂商公开价格页
3. Marketplace 实时价格页
4. 招投标/中标公告
5. 整机厂商/渠道公开报价
6. 行业媒体/研报
7. 社区/论坛/传闻

扩源后的数据仍然必须经过 Classify、Normalize、Validate；不能因为覆盖不足而降低主指数门槛。覆盖不足本身必须作为报告中的“数据缺口”输出。

## 1. Collect

采集阶段只保存原始事实，不做计算和结论。每条候选数据必须尽量保留：

- 来源网址
- 采集时间
- 原标题
- 原始价格
- 原始单位
- 原始币种
- 地区/国家
- 对象描述
- 来源类型
- 备注

禁止采集后立即换算、推断或写入指数。所有计算必须在 `Normalize` 和 `Validate` 阶段完成，并记录公式。

## 2. Data Freeze（数据冻结）

日报生成开始时，必须记录 `freeze_time`（精确到分钟）。所有采集到的数据，其采集时间必须早于或等于 `freeze_time`。

`freeze_time` 之后到达的新数据（例如采集过程中来源更新了价格），不得进入当期日报，必须留待下一期。

`freeze_time` 必须写入：

- `data/audit_{YYYY-MM-DD}.json`
- `data/cmis_snapshot_{YYYY-MM-DD}.json`
- HTML 报告页脚的版本信息区

示例：`"freeze_time": "2026-07-13T08:45:00+08:00"`

## 3. Classify

每条价格必须先分类，只能属于以下类别之一：

- `GPU_RENT_CN`
- `GPU_RENT_GLOBAL`
- `GPU_CLOUD`
- `GPU_PURCHASE`
- `GPU_CLUSTER`
- `GPU_SYSTEM`
- `GPU_RACK`
- `TOKEN_PRICE`
- `OTHER`

分类错误的数据不得继续进入标准化。示例：`35 USD/Card/hour` 属于 `GPU_CLOUD`；`64 GPU 72万元/月` 属于 `GPU_CLUSTER`；`H100 售价260万元` 属于 `GPU_PURCHASE`。如果不能判断分类，标记为 `OTHER` 或 `REJECT`，不得进入主指数。

## 4. Normalize

标准化时必须保留原始信息，至少包括：

- `original_price`
- `original_unit`
- `original_currency`
- `gpu_count`
- `server_count`
- `gpu_per_server`
- `contract_period`
- `country`
- `tax`
- `electricity`
- `network`
- `managed_service`
- `source_type`
- `confidence`

标准化可以新增字段，但不得覆盖或丢失原始字段。任何从小时到月、从单卡到整机、从集群到服务器、从美元到人民币的换算，都必须写出公式和汇率假设。

## 5. 国内租赁标准口径

国内算力租赁主指数唯一口径：

- 地区：中国大陆
- 对象：8 GPU HGX Server / 8卡整机
- 单位：万元/台/月
- 合同：一年左右市场主流长租
- 包含：IDC、机柜、电力、IB/网络、托管、运维
- 来源：SMM 优先

任何美元、卡小时、GPU Cloud、采购价格、64卡、72卡、机柜、整柜、GB系统、Token 价格、整机售价、系统售价，均不得直接进入国内租赁指数，只能进入辅助模块、价差参考或异常样本。

国内主图默认展示"万元/8卡整机/月"。如果需要展示等效单卡小时价，公式为：

8卡整机月租 ÷ 8 ÷ 24 ÷ 30

不得将海外 GPU Cloud 小时价直接乘以 `8×24×30` 后当作国内 SMM 月租。

## 6. 海外租赁标准口径

海外租赁主口径为：

- 美元/卡/小时
- 或人民币/卡/小时

如果展示"等效 8卡月租"，必须标注"仅供参考，不进入国内租赁指数"。国内和海外租赁不得混用同一个主指数，不得在同一 y 轴中暗示二者完全可比。

## 7. Validate

所有标准化数据必须通过七层校验。

### 7.1 Confidence Score（数据可信度评分）

每条数据必须根据来源类型获得一个可信度评分（0-100）：

| 分数区间 | 等级 | 典型来源 |
|----------|------|----------|
| 95-100 | A（极高） | 官方定价页、SMM、ComputeStacker |
| 85-95 | B（高） | IDC 一手、运营商、RunPod、Lambda |
| 70-85 | C（中） | Marketplace、GPU Finder、Vast.ai |
| 50-70 | D（一般） | 媒体报道、研报、行业分析 |
| 30-50 | E（低） | 论坛、社区、二手信息 |
| <30 | F（极低） | 传闻、匿名截图、无法核实来源 |

**硬性规则：Confidence < 70 的数据不得进入主指数。** 可进入辅助模块、异常观察或 Rejected Samples。Confidence Score 必须写入审计文件。

### 7.2 单位校验

小时价、日价、月价、单卡价、整机价、集群价必须区分。小时转月必须记录公式，例如：

`2.35 USD/hour × 24 × 30 = 1692 USD/month`

### 7.3 GPU 数量校验

遇到 `64 GPU`、`72 GPU`、整柜或集群报价，必须先识别服务器数量和每台服务器 GPU 数，再拆算到正确对象。例如：

`64 GPU ÷ 8 GPU/Server = 8 Server`

不得把 64 卡集群价格直接当作 8 卡整机价格。

### 7.4 价格合理性校验

国内租赁 sanity check：

- H100 80G：约 6.5-8.5 万元/8卡整机/月
- A100 80G：约 3.0-4.5 万元/8卡整机/月
- RTX 5090/4090 多卡整机：约 1.0-1.5 万元/8卡整机/月

如果价格超过合理区间 2 倍，立即 `REJECT`，不得进入主图、指数、ROI 或 AI 总结。典型异常包括 H100 60 万元/月、A100 10 万元/月、把 64 卡集群价当成 8 卡整机价、把采购价当租赁价。

### 7.5 来源优先级校验

国内租赁来源优先级：

SMM > IDC 一手 > 运营商 > 招投标 > 媒体 > 云厂商 > 论坛 > 社区

海外租赁来源优先级：

ComputeStacker > RunPod > Lambda > Vast.ai > CoreWeave > Nebius/Crusoe/Oracle OCI > 其它 Marketplace

如果低优先级来源与高优先级来源冲突，必须采用高优先级，不得平均，不得混合。低优先级数据可作为辅助校验或异常观察。

### 7.6 Historical Validation（历史波动校验）

当日价格必须与历史数据库中最近一条有效记录对比：

- **变化 ≤ 30%**：正常通过
- **变化 > 30%**：标记 `REVIEW`，必须在 AI 总结中注明"价格存在较大波动，需关注"并在审计文件中记录原因
- **变化 > 100%**：自动 `REJECT`，**除非**至少两个高优先级（Confidence ≥ 85）来源同时确认该价格

示例：昨日 H100 为 7.4 万元/月，今日某来源报 60 万元/月，即使来源可信度较高，也必须触发 Historical Validation 并根据上述阈值处理。

历史数据不足（少于 3 个有效样本）时，跳过此层校验，但必须标注 `HIST_INSUFFICIENT`。

### 7.7 口径校验

GPU Cloud 小时价不得进入国内租赁主指数。GPU 采购价不得进入租赁价格。64卡、72卡、整柜、GB系统报价不得直接进入 8卡整机口径，必须先标准化并通过校验。

## 8. Source Consensus（来源共识）

每个 GPU 型号的当日价格必须计算来源共识度：

**High Consensus**：多个独立来源价格落在 ±15% 区间内，且至少有一个高优先级（Confidence ≥ 85）来源。示例：SMM 7.6 万、IDC 7.5 万、运营商 7.4 万 → High。

**Medium Consensus**：多数来源接近，但存在个别离群值。离群值需标注并进入辅助观察。

**Low Consensus**：来源之间价格差异超过 ±30%。示例：SMM 7.5 万、某 Marketplace 60 万 → Low。

**共识度影响：**

- High Consensus → 价格正常进入指数，AI 总结可引用
- Medium Consensus → 价格可进入指数，但 AI 总结须注明"存在个别离群数据"
- Low Consensus → AI 总结**不得**说"价格上涨"或"价格下跌"，只能说"数据存在分歧，等待进一步确认"。主指数采用高优先级来源数据，离群值只进入辅助模块

共识度必须写入审计文件。

## 9. Publish

只有 `Validate == PASS` 的数据可以：

- 更新历史数据库
- 更新指数
- 绘制主图
- 参与 ROI
- 参与利润测算
- 进入 AI 总结
- 写入 HTML 主体结论

否则必须进入 `Rejected Samples`，并说明 Reject 原因、原始口径、疑似错误类型和是否需要人工复核。

## 10. 数据审计

每天必须生成 `data/audit_{YYYY-MM-DD}.json` 和 `data/rejected_{YYYY-MM-DD}.json`。审计字段至少包括：

- `date`
- `freeze_time`
- `asset_type`
- `gpu_or_model`
- `source`
- `url`
- `title`
- `original_price`
- `original_unit`
- `original_currency`
- `category`
- `normalized_price`
- `normalized_unit`
- `formula`
- `source_priority`
- `confidence`（0-100）
- `consensus`（High / Medium / Low）
- `historical_validation`（PASS / REVIEW / REJECT / HIST_INSUFFICIENT）
- `validate_status`（PASS / REVIEW / REJECT）
- `included_in_index`（true / false）
- `reject_reason`
- `notes`

PASS 示例：

```json
{
  "date": "2026-07-13",
  "freeze_time": "2026-07-13T08:45:00+08:00",
  "gpu": "H100",
  "source": "SMM",
  "original": "75000 RMB/month",
  "normalized": "7.5 万元/8卡整机/月",
  "category": "GPU_RENT_CN",
  "confidence": 98,
  "consensus": "High",
  "historical_validation": "PASS",
  "status": "PASS"
}
```

REJECT 示例：

```json
{
  "date": "2026-07-13",
  "freeze_time": "2026-07-13T08:45:00+08:00",
  "gpu": "H100",
  "original": "60万元/月",
  "category": "GPU_RENT_CN",
  "confidence": 45,
  "consensus": "Low",
  "historical_validation": "REJECT",
  "status": "REJECT",
  "reason": "疑似集群价、采购价或重复折算，超过国内合理区间2倍；历史波动超过100%且无多源确认"
}
```

## 11. Token 价格规则

所有列入报告的厂商和模型，必须主动检索官方价格。官方价格只能来自厂商官网、API 文档、云平台模型服务计费页、开发者文档或官方价格页。OpenRouter 或替代门户只能作为 `Market Price`，不得替代 `Official Price`。

如果 OpenRouter 无法拉取，可使用 Artificial Analysis、模型聚合平台、云厂商市场价、代理平台公开价等替代，但必须标注来源类型、采集时间和置信度。

## 12. 利润测算规则

利润测算只能使用通过校验的数据。租赁收入、采购成本、利用率、电费、托管费和折旧必须区分口径。月租收入不得把单卡价误当整机价；采购成本必须区分单卡、8卡整机、机柜和 GB 系统。

如果基础数据未通过校验，利润测算必须标注"暂不进入结论，仅参考/需人工复核"。

## 13. HTML 与图表规则

HTML 必须手机端可读。所有图表、表格、标签、轴文字和数据标注必须避免遮挡、截断和重叠。必要时使用横向滚动、分组图、标签换行、标签旋转、缩写+备注、增大边距、动态高度、分页或分段展示。

`index.html` 必须是正式首页/归档门户，风格与 `latest.html` 一致，不得只是简陋目录页。报告必须包含数据源、口径说明、审计摘要和异常样本摘要。

### 版本信息

每份 HTML 报告页脚必须包含版本信息区：

- **Report Version**：日报版本号（从 v1.0.0 起递增，重大结构变更升级 major，新增模块升级 minor，数据修正升级 patch）
- **Prompt Version**：当期执行时 `prompts/system_prompt.md` 和 `prompts/report_config.md` 的 Git commit 短哈希或版本标记
- **Data Freeze**：当日 `freeze_time`，格式 `YYYY-MM-DD HH:MM`

示例：

```
CMIS Daily v1.0.0 | Prompt 480f163 | Freeze 2026-07-13 08:45
```

## 14. 结论约束

AI 总结只能基于 `Validate == PASS` 且 `Consensus != Low` 的数据。当 Source Consensus 为 Low 时，AI 总结不得做出方向性价格判断（如"上涨""下跌"），只能说"数据存在分歧，等待进一步确认"。Rejected 数据只能在异常样本或审计摘要中说明，不得进入核心结论、投资建议、趋势判断或利润结论。
