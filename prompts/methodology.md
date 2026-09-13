# CMIS 指数方法论（Methodology）

本文件是《全球算力市场情报日报（CMIS Daily）》的指数方法论披露文档，对标 Silicon Data（silicondata.com）公开方法论的组织方式：让读者能独立判断"这个数是怎么来的、覆盖了多少、哪些不能比"。执行 Agent 每次运行时与 `system_prompt.md`、`report_config.md`、`source_pool.md` 一并读取；**两者冲突时以 `system_prompt.md` 的数据治理底座为准**。

实现载体：`scripts/cmis_index.py`（指数计算）、`scripts/generate_cmis_daily.py`（指数看板渲染）。

## 0. 为什么对标 Silicon Data

Silicon Data 是按金融指数标准构建的 GPU 价格基准（发布于 Bloomberg / Refinitiv，自称 350 万+ 数据点），其方法论公开且结构清晰。CMIS 借鉴的是**结构**，不是数据：

- 每个 GPU 型号一条标准化指数（one index per GPU），而非单一供应商价目表；
- 指数值 = 多源聚合的结果，而非单一报价；
- 覆盖率披露（neo-cloud / hyperscaler 覆盖比例）独立于指数本身；
- 方法论单独成文，读者可独立审计。

CMIS 与 Silicon Data 的本质差异：CMIS 是面向个人决策的情报日报，非机构结算基准；国内主口径是 8 卡整机月租（Silicon Data 为单卡小时价）；数据获取以公开可验证来源为限，不做付费数据接入。

## 1. 指数家族与代码（Ticker）

| 代码 | 含义 | 单位 | 对标 |
|------|------|------|------|
| CMIS-{GPU}-CN | 国内 GPU 租赁指数 | 万元/8卡整机/月 | SDH100RT 等 per-GPU 指数 |
| CMIS-{GPU}-US | 海外 GPU Cloud 指数 | 美元/卡/小时 | 同上（Silicon Data 主口径） |
| CMIS-TOKEN-INDEX | LLM Token 综合价格指数 | 美元/百万输入 token | SDLLMTK（LLM Token Expenditure Index） |

- 代码映射维护在 `cmis_index.py` 的 `GPU_TICKER_MAP`；新增 GPU 进 `GPU_ORDER` 时必须同步补映射。
- 每个指数发布当日值 + 7 日 / 30 日涨跌幅（±3 天容错取最近可用快照）。

## 2. 方法论五步（对标 Silicon Data Raw Data to Benchmark）

Silicon Data 的链路是：**单位标准化 → 多级过滤 → 基差调整 → 供应商级聚合 → 加权平均**。CMIS 对应实现：

### 2.1 单位标准化（Unit Standardization）

- 海外：每条记录先折算为"美元/卡/小时"，单位价 = 总租价 ÷ 卡数 ÷ 时长（与 Silicon Data 完全一致）。
- 国内：折算为"万元/8卡整机/月"；等效单卡小时价 = 月租 ÷ 8 ÷ 24 ÷ 30（仅辅助展示）。
- 所有换算必须保留 `original_price / original_unit / gpu_count / contract_period / country / tax` 等原始字段与公式（`system_prompt.md` 第 4 节）。

### 2.2 多级过滤（Multi-stage Filtering）

对应 `system_prompt.md` 第 7 节七层校验：Confidence Score、单位校验、GPU 数量校验、价格合理性 + 偏差率硬拦截、来源优先级、历史波动校验、口径校验。只有 `Validate == PASS` 的样本才能形成指数值（国产战略关注卡按底座规则进入展示但不进 PASS 指数）。

### 2.3 基差调整（Basis Adjustment）

Silicon Data 将每条记录标准化到 benchmark-equivalent contract（租赁类型 / 地域 / CPU 平台 / GPU 变体）。CMIS 对应做法：

- **口径基差**：国内指数只收"8 卡 HGX 整机 · 一年左右长租 · 含 IDC/电力/网络/托管"口径，其余口径（云实例、采购、集群、整柜、Token）一律不混入。
- **云价折算**：国产卡缺公开整机月租时，单卡云时价 × 8 × 24 × 30 × **0.7 长协折扣系数** 折算为占位值，显著标注"云价折算"，只作主图占位，不进指数 / ROI / 方向性结论。0.7 系数是用户业务参数（2026-07-19 确认），调整时只改 `system_prompt.md` 5.1 节。
- **期限基差（记录要求）**：采集海外报价时必须保留 `contract_period`（on-demand / 1mo / 6mo / 12mo / 24mo 等）。云厂商预留价（reserved / committed）与按需价（on-demand）是不同期限基差，**不得**混合成单一读数；具备 3 个以上期限点后可构建期限结构（Term Structure），详见第 6 节路线图。

### 2.4 供应商级聚合（Provider-level Aggregation）

Silicon Data 先按供应商聚合、再加权平均，避免日度配置组合变化导致指数漂移。CMIS 实现于 `cmis_index.aggregate_quotes()`：

- 同型号存在多条 PASS 供应商报价时：**按 Confidence 加权平均**，同时计算中位数交叉核对；加权均值与中位数偏差 > 20% 时置 `needs_review`，提示离群值。
- 单源时直接采用（`single-source`），并在指数卡上披露源数量。
- 聚合只发生在"同口径、同分段"的报价之间；跨口径（月租 vs 云实例）与跨分段（NeoCloud vs Hyperscaler）**不聚合**。

### 2.5 加权平均与权重

- GPU 指数：权重 = 来源 Confidence（见 2.4）。
- Token 指数：主流模型按市场重要性加权（权重表在 `cmis_index.calc_token_index`），单位为美元/百万输入 token。

## 3. 市场分段披露（Segment Disclosure）

Silicon Data 将 neo-cloud 与 hyperscaler 读数**分开发布**，让读者看到价差及其变动。CMIS 对应规则：

- 海外来源按 `segment_of()` 分为 **NeoCloud**（RunPod / Lambda / Vast.ai / CoreWeave / Nebius / Crusoe 等）、**Hyperscaler**（Oracle OCI / AWS / Azure / GCP / Paperspace 等）、**Aggregator**（Cloud-GPUs / GPUCloudPricing / ComputeStacker 等）、**Marketplace**、**Other**。
- 海外指数卡必须标注所属分段；**禁止**把两段价格平均成一个"全市场价"冒充单一读数。
- 采集端（`discover_latest.py` 动态发现）在同一 GPU 抓到多个供应商报价时，应以 `provider_quotes: [{"provider": ..., "usd": ...}]` 逐条保留，不得只留一个数；生成端据此计算分段中位价与价差（`calc_segment_spread()`），在报告"海外市场分段价差"表中展示 Hyperscaler 相对 NeoCloud 的价差百分比。
- 分供应商报价不足时该表**不展示**，不编造、不用聚合价替代。

## 4. 指数覆盖率披露（Coverage Disclosure）

Silicon Data 公开宣传"95% neo-cloud 覆盖 / 100% hyperscalers / 全球可租市场 80%"。CMIS 对应披露**真实覆盖率**（`index_coverage()`，写入 snapshot `cmis_indices.coverage` 与报告指数区）：

- 国内指数覆盖 = 基线 GPU 中存在 PASS 标准化价格的比例；
- 海外指数覆盖 = 基线 GPU 中存在 PASS 单卡小时价的比例；
- 海外数据源数 = PASS 样本主数据源去重个数（多源拼接按 "+" 拆分）；
- Token 模型覆盖 = PASS 模型 / 全部在列模型。

规则：覆盖率只报实算值，**不得**为了好看而把 REVIEW / 云价折算样本计入；覆盖率不足触发 `source_pool.md` 扩源补采流程。

## 5. 发布与趋势（Publication）

- 每日一更（business day 概念从宽：本日报每天发布），Data Freeze 时间戳入快照与页脚。
- 7 日 / 30 日涨跌幅基于历史快照（`data/cmis_snapshot_*.json`）对比，±3 天容错。
- 变化 ≤ 0.5% 记 flat；Source Consensus 为 Low 时指数卡照常展示，但 AI 总结不得做方向性判断（`system_prompt.md` 第 14 节）。
- 版本管理：指数看板结构性变更升级 minor（当前 v1.6.0 引入海外指数卡 / 覆盖率 / 分段价差）。

## 6. 路线图与边界（不做的事）

对标 Silicon Data 产品族，以下能力**列为方向、禁止无数据硬做**：

- **GPU Forward Curve（远期曲线）**：需要 1–36 个月期限结构的真实报价（云厂商 reserved/committed 价是可用素材）。在具备 ≥3 个期限点之前**不得**发布任何"远期价"；期限数据先按 2.3 节要求入库积累。
- **PriceIQ 类预测**：CMIS 只做已发生价格的指数化，不做价格预测；AI 总结只能描述已验证的变动与分歧。
- **SiliconMark 类性能基准**：性价比（价格/性能）需要独立 benchmark 数据；在此之前只展示价格，不得用厂商标称算力冒充实测性能。
- **SiteIQ 类容量测算**：超出本项目范围。

## 7. 与 Silicon Data 的口径差异对照

| 维度 | Silicon Data | CMIS |
|------|--------------|------|
| 主口径（海外） | 美元/卡/小时 | 一致 |
| 主口径（国内） | 不覆盖中国整机租赁 | 万元/8卡整机/月（SMM 优先） |
| 指数构造 | 基差调整后供应商级加权 | PASS 样本 + Confidence 加权聚合（单源常见） |
| 分段 | neo-cloud / hyperscaler 分开发布 | 一致（NeoCloud / Hyperscaler / Aggregator…） |
| 覆盖披露 | 95% neo-cloud 等宣传值 | 每期实算覆盖率 |
| 发布渠道 | Bloomberg / Refinitiv / API | GitHub Pages + 飞书卡片 |
| 预测产品 | Forward Curve / PriceIQ | 不做（见第 6 节） |

## 8. 修改本文件

方法论变更属于治理层变更：修改本文件必须同步检查 `system_prompt.md` 第 7/15 节与 `cmis_index.py` 实现，三者不一致时以"实现可验证的口径"为准修订文档；涉及指数值口径变化时升级 Report Version 的 minor 并在审计文件中记录变更说明。
