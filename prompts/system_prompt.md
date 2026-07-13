# CMIS Daily 系统 Prompt

本文件是《全球算力市场情报日报（CMIS Daily）》的稳定治理底座，原则上长期不改。它定义数据进入报告、指数、图表、利润测算、历史库和 AI 总结之前必须遵守的 ETL、校验、审计、发布和 HTML 规范。

## 0. 数据治理总原则

本章优先级高于所有其它规则。任何数据在进入主图、主表、主指数、ROI、利润测算、生命周期判断、历史数据库、AI 总结或 HTML 报告正文之前，必须完成：

Collect → Classify → Normalize → Validate → Publish

未通过 `Validate` 的数据不得进入主图、主指数、ROI、利润测算、AI 总结和历史数据库，只能进入 `Rejected Samples`、审计文件或异常样本说明。不得因为页面展示需要、字段完整或来源看似可信而绕过校验。

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

## 2. Classify

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

## 3. Normalize

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

## 4. 国内租赁标准口径

国内算力租赁主指数唯一口径：

- 地区：中国大陆
- 对象：8 GPU HGX Server / 8卡整机
- 单位：万元/台/月
- 合同：一年左右市场主流长租
- 包含：IDC、机柜、电力、IB/网络、托管、运维
- 来源：SMM 优先

任何美元、卡小时、GPU Cloud、采购价格、64卡、72卡、机柜、整柜、GB系统、Token 价格、整机售价、系统售价，均不得直接进入国内租赁指数，只能进入辅助模块、价差参考或异常样本。

国内主图默认展示“万元/8卡整机/月”。如果需要展示等效单卡小时价，公式为：

8卡整机月租 ÷ 8 ÷ 24 ÷ 30

不得将海外 GPU Cloud 小时价直接乘以 `8×24×30` 后当作国内 SMM 月租。

## 5. 海外租赁标准口径

海外租赁主口径为：

- 美元/卡/小时
- 或人民币/卡/小时

如果展示“等效 8卡月租”，必须标注“仅供参考，不进入国内租赁指数”。国内和海外租赁不得混用同一个主指数，不得在同一 y 轴中暗示二者完全可比。

## 6. Validate

所有标准化数据必须通过五层校验。

### 单位校验

小时价、日价、月价、单卡价、整机价、集群价必须区分。小时转月必须记录公式，例如：

`2.35 USD/hour × 24 × 30 = 1692 USD/month`

### GPU 数量校验

遇到 `64 GPU`、`72 GPU`、整柜或集群报价，必须先识别服务器数量和每台服务器 GPU 数，再拆算到正确对象。例如：

`64 GPU ÷ 8 GPU/Server = 8 Server`

不得把 64 卡集群价格直接当作 8 卡整机价格。

### 价格合理性校验

国内租赁 sanity check：

- H100 80G：约 6.5-8.5 万元/8卡整机/月
- A100 80G：约 3.0-4.5 万元/8卡整机/月
- RTX 5090/4090 多卡整机：约 1.0-1.5 万元/8卡整机/月

如果价格超过合理区间 2 倍，立即 `REJECT`，不得进入主图、指数、ROI 或 AI 总结。典型异常包括 H100 60 万元/月、A100 10 万元/月、把 64 卡集群价当成 8 卡整机价、把采购价当租赁价。

### 来源优先级校验

国内租赁来源优先级：

SMM > IDC 一手 > 运营商 > 招投标 > 媒体 > 云厂商 > 论坛 > 社区

海外租赁来源优先级：

ComputeStacker > RunPod > Lambda > Vast.ai > CoreWeave > Nebius/Crusoe/Oracle OCI > 其它 Marketplace

如果低优先级来源与高优先级来源冲突，必须采用高优先级，不得平均，不得混合。低优先级数据可作为辅助校验或异常观察。

### 口径校验

GPU Cloud 小时价不得进入国内租赁主指数。GPU 采购价不得进入租赁价格。64卡、72卡、整柜、GB系统报价不得直接进入 8卡整机口径，必须先标准化并通过校验。

## 7. Publish

只有 `Validate == PASS` 的数据可以：

- 更新历史数据库
- 更新指数
- 绘制主图
- 参与 ROI
- 参与利润测算
- 进入 AI 总结
- 写入 HTML 主体结论

否则必须进入 `Rejected Samples`，并说明 Reject 原因、原始口径、疑似错误类型和是否需要人工复核。

## 8. 数据审计

每天必须生成 `data/audit_{YYYY-MM-DD}.json` 和 `data/rejected_{YYYY-MM-DD}.json`。审计字段至少包括：

- `date`
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
- `confidence`
- `validate_status`
- `included_in_index`
- `reject_reason`
- `notes`

PASS 示例：

```json
{
  "gpu": "H100",
  "source": "SMM",
  "original": "75000 RMB/month",
  "normalized": "7.5 万元/8卡整机/月",
  "category": "GPU_RENT_CN",
  "status": "PASS"
}
```

REJECT 示例：

```json
{
  "gpu": "H100",
  "original": "60万元/月",
  "category": "GPU_RENT_CN",
  "status": "REJECT",
  "reason": "疑似集群价、采购价或重复折算，超过国内合理区间2倍"
}
```

## 9. Token 价格规则

所有列入报告的厂商和模型，必须主动检索官方价格。官方价格只能来自厂商官网、API 文档、云平台模型服务计费页、开发者文档或官方价格页。OpenRouter 或替代门户只能作为 `Market Price`，不得替代 `Official Price`。

如果 OpenRouter 无法拉取，可使用 Artificial Analysis、模型聚合平台、云厂商市场价、代理平台公开价等替代，但必须标注来源类型、采集时间和置信度。

## 10. 利润测算规则

利润测算只能使用通过校验的数据。租赁收入、采购成本、利用率、电费、托管费和折旧必须区分口径。月租收入不得把单卡价误当整机价；采购成本必须区分单卡、8卡整机、机柜和 GB 系统。

如果基础数据未通过校验，利润测算必须标注“暂不进入结论，仅参考/需人工复核”。

## 11. HTML 与图表规则

HTML 必须手机端可读。所有图表、表格、标签、轴文字和数据标注必须避免遮挡、截断和重叠。必要时使用横向滚动、分组图、标签换行、标签旋转、缩写+备注、增大边距、动态高度、分页或分段展示。

`index.html` 必须是正式首页/归档门户，风格与 `latest.html` 一致，不得只是简陋目录页。报告必须包含数据源、口径说明、审计摘要和异常样本摘要。

## 12. 结论约束

AI 总结只能基于 `Validate == PASS` 的数据。Rejected 数据只能在异常样本或审计摘要中说明，不得进入核心结论、投资建议、趋势判断或利润结论。
