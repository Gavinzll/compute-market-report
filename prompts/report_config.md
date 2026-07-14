# CMIS Daily 报告配置

本文件是《全球算力市场情报日报（CMIS Daily）》的可变配置，允许经常调整。新增 GPU、模型、模块、图表或输出路径时，优先修改本文件；不要频繁修改 `system_prompt.md` 的数据治理底座。

扩源明细维护在 `prompts/source_pool.md`。每次日报执行时必须同时读取 `system_prompt.md`、`report_config.md` 和 `source_pool.md`：前者负责治理规则，本文件负责报告形态，`source_pool.md` 负责可抓取来源、补采顺序和数据分层。

## 1. 报告目标

每日生成一份面向个人决策的全球算力市场情报日报，覆盖 Token 价格、国内算力租赁、海外 GPU Cloud、GPU 采购价格、利润测算、供需状态、生命周期、趋势图、异常样本和审计摘要。

最终输出：

- `latest.html`
- `reports/{YYYY-MM-DD}.html`
- `index.html`
- `data/cmis_snapshot_{YYYY-MM-DD}.json`
- `data/history.jsonl`
- `data/audit_{YYYY-MM-DD}.json`
- `data/rejected_{YYYY-MM-DD}.json`
- `assets/` 图表资源
- `prompts/source_pool.md` 源池清单与扩源补采规则

GitHub 只作为静态页面托管和历史归档，不作为日报执行端。不得创建 `.github/workflows` 或 GitHub Actions 工作流。

## 2. 发布地址

- GitHub 仓库：`https://github.com/Gavinzll/compute-market-report.git`
- 首页：`https://gavinzll.github.io/compute-market-report/`
- 最新报告：`https://gavinzll.github.io/compute-market-report/latest.html`
- 历史报告：`https://gavinzll.github.io/compute-market-report/reports/{YYYY-MM-DD}.html`
- 飞书通知链接：`https://gavinzll.github.io/compute-market-report/latest.html?v={YYYYMMDDHHmm}`

敏感信息如 GitHub Token 和飞书 Webhook 不得写入本文件或任何仓库文件，只能由定时任务运行上下文提供。

## 3. GPU 固定分类

GPU 必须按以下分类固定展示，图表和表格中不得随意调整顺序或遗漏分类。每个分类下的型号相对固定，新增型号时需在本配置中显式声明。

### Training（训练卡）

| 型号 | 备注 |
|------|------|
| GB300 | Blackwell Ultra，系统交付为主 |
| GB200 | NVLink 全互联，系统交付为主 |
| B300 | Blackwell 单卡/整机 |
| B200 | Blackwell 主流 |
| H200 | Hopper 高带宽 |
| H100 80G | Hopper 主流 |
| H800 | 中国特供版 |
| H20 | 中国特供版，算力裁剪 |
| A100 80G | Ampere 主流 |
| A800 | 中国特供版 |

### Inference（推理卡）

| 型号 | 备注 |
|------|------|
| L40S | Ada Lovelace 推理主力 |
| L20 | 推理/轻训练 |
| L4 | 入门推理 |

### Consumer（消费级）

| 型号 | 备注 |
|------|------|
| RTX 5090 | Blackwell 消费级 |
| RTX 4090 | Ada 消费级 |

### 国产（Domestic）

| 型号 | 备注 |
|------|------|
| 昇腾 910C | 华为 |
| 昇腾 910B | 华为 |
| 寒武纪思元 MLU | 寒武纪 |
| 海光 DCU | 海光 |
| 壁仞 | 壁仞科技 |
| 摩尔线程 | 摩尔线程 |

图表必须按 Training → Inference → Consumer → 国产 分组展示，每个分组内按上述固定顺序排列。不同日期之间的 GPU 覆盖范围必须一致，不得今天有明天没有。

## 4. Token 覆盖

国产模型重点覆盖：

- DeepSeek
- 阿里通义千问
- 智谱 GLM / GLM-Z
- 百度文心 / 千帆
- 火山引擎豆包
- 腾讯混元
- 讯飞星火
- Kimi / Moonshot
- MiniMax / 海螺
- 百川
- 零一万物
- 阶跃星辰
- 商汤日日新
- 昆仑万维天工

海外模型重点覆盖：

- OpenAI GPT / o 系列
- Anthropic Claude
- Google Gemini
- Mistral
- Cohere
- xAI Grok
- Meta Llama 主要商业托管或 API 渠道

所有列出的厂商和模型必须检索官方价格。官方价必须来自官网、官方文档、控制台公开价、购买页、计费页、价格计算器或云平台官方计费页；不能用市场价冒充官方价。

每个厂商必须列出主流模型清单，而不是只按厂商覆盖。最低模型覆盖要求：

- OpenAI：GPT 主线、mini/nano、o 系列或当前主力推理模型。
- Anthropic：Claude Opus / Sonnet / Haiku 当前主力版本。
- Google：Gemini Pro / Flash / Flash-Lite 当前主力版本。
- DeepSeek：V 系列、R 系列、Flash/Pro 或当前官网主推模型。
- 阿里通义千问：Qwen Max、Qwen Plus、Qwen Turbo / Long Context 当前主力版本。
- 火山豆包：Seed / Pro / Lite / Thinking / Vision 当前主力版本。
- 腾讯混元：Hunyuan-a13b、role、translation、vision 等官方在售模型。
- Kimi / Moonshot：Kimi K、Moonshot V1 长上下文主力模型。
- 智谱 GLM：GLM / GLM-Z / Coding 主力模型。
- MiniMax、讯飞星火、百度文心、百川、零一万物、阶跃星辰等：至少列出官网当前主推模型和价格状态。

国产模型官方价必须优先从官网、官方文档、控制台公开价、购买页或计费页抓取。遇到网页端价格表是图片、需要登录控制台或动态渲染时，不能简单留空；必须继续尝试移动页、文档页、价格计算器、API 文档、购买页或云平台镜像页。三方市场价必须拆成海外三方价和境内三方价：海外三方价以 OpenRouter、LiteLLM、models.dev、BenchLM、llmpricing、morph-llm、Together、Fireworks、Replicate、Hugging Face Inference Providers 等为主；境内三方价以硅基流动为基准，并继续查 AIHubMix、海鲸AI、Gitee AI、GeekAI、PPIO 派欧云等国内第三方或聚合平台。

Token 表必须展示 `三方价格匹配级别` 和 `同价原因`。匹配级别至少区分 `精确同名`、`官方同步/路由价`、`同厂参考`、`同系列参考`、`同类型参考`、`近似参考`；只要来源或备注含 `参考`、`待补`、`近似`、`同厂`、`同系列`、`同类型`、`非文本精确价` 等词，就不得标成精确同名。官方价与三方价相同时，必须说明是第三方同步官方价、同名模型当前价一致，还是参考价巧合相等。

## 5. 报告模块

HTML 报告至少包含：

- 今日摘要
- Token 价格：Official vs Overseas Third-party vs Domestic Third-party
- Token 输入价：官方 vs 海外三方 vs 境内三方
- Token 输出价：官方 vs 海外三方 vs 境内三方
- Token 三方输入价差：境内三方 - 海外三方
- Token 官方与境内三方输入价差
- 国内算力租赁（按 Training / Inference / Consumer / 国产 分组）
- 海外 GPU Cloud / 租赁
- 国内/海外价差参考
- GPU 采购价格
- GPU 利润测算
- GPU 供需监测
- AI 基础设施市场信号
- 主流算力卡覆盖表（按固定分类展示）
- GPU 生命周期
- 历史趋势与走势图（至少覆盖核心 Training 卡和核心 Token）
- Rejected Samples / 数据审计摘要
- 价格、供需、利润异动提醒
- 数据源与口径说明
- AI 总结
- 页脚版本信息（Report Version / Prompt Version / Data Freeze）

## 6. 表格字段

Token 表格固定列：

- 厂商
- 模型
- 国家/地区
- 上下文上限
- 输入官方价（原币/百万 Token）
- 输出官方价（原币/百万 Token）
- 输入官方价（人民币/百万 Token）
- 输出官方价（人民币/百万 Token）
- 海外三方输入价
- 海外三方输出价
- 境内三方输入价
- 境内三方输出价
- 官方-海外三方价差
- 官方-境内三方价差
- 三方价格匹配级别
- 同价原因
- 较昨日变化
- 官方来源
- 海外三方来源
- 境内三方来源
- 采集时间
- 置信度
- 校验状态
- 备注

租赁表格固定列：

- GPU 型号
- GPU 分类（Training / Inference / Consumer / 国产）
- 热度排序
- 地区/市场
- 主数据源
- 辅助校验源
- category
- 原始价格
- 原始单位
- 标准化价格
- 标准化单位
- 8卡整机月租（如适用）
- 单卡小时价（如适用）
- 海外同型号等效8卡月租（万元）
- 最高价
- 最低价
- 中位价
- Confidence Score
- Source Consensus
- Historical Validation
- 库存/可用性
- 较昨日变化
- 近 7 日变化
- 国内/海外价格比例
- 口径说明
- 校验状态
- 备注

生命周期表格固定列：

- GPU 型号
- GPU 分类
- 生命周期阶段
- 热度排序
- 租赁价格水平
- 采购价格水平
- 库存/交期
- 近 7 日价格趋势
- 供需状态
- 利润测算状态
- 采购建议
- 主要风险
- 判断依据
- 置信度

## 7. 数据源优先级

国内租赁：

SMM > IDC 一手 > 运营商 > 招投标 > 媒体 > 云厂商 > 论坛 > 社区

海外租赁：

ComputeStacker > Cloud-GPUs Price Analytics > RunPod > Lambda > Vast.ai > GPUCloudPricing > CoreWeave > Nebius/Crusoe/Oracle OCI > 其它 Marketplace

Token：

厂商官方价格页 / API 文档 > 云平台官方计费页 > 官方开发者文档 > LiteLLM JSON / OpenRouter API / models.dev / BenchLM > LLMPriceCheck / llmpricing / morph-llm / Artificial Analysis / 第三方市场价门户

采购价：

SMM 现货指数、英伟达代理渠道、整机厂商报价、招投标结果和公开渠道价格共同构成参考。非官方数据必须单独标注置信度。

## 8. 源池与扩源策略

报告覆盖不能只依赖主指数 PASS 数据。每次运行必须按以下源池扩展采集，并将数据分层展示为 `Main Index`、`Auxiliary Quotes`、`Candidate Samples`、`Rejected Samples` 和 `Missing with searched sources`。

扩源源池不得只写在报告正文中。每次执行必须先读取 `prompts/source_pool.md`，并在审计文件中记录：

- `searched_sources`：实际检索过的源
- `successful_sources`：成功解析出数据的源
- `failed_sources`：失败或访问受限的源
- `source_layer`：Official / Structured API / Aggregator / Marketplace / Auxiliary / Lead
- `usage_class`：Main Index / Auxiliary Quotes / Candidate Samples / Rejected Samples / Missing with searched sources

### 8.1 国内 8卡整机租赁主口径

优先寻找“万元/8卡整机/月，中国大陆，含 IDC/电力/网络/托管/运维”的长租报价。

首选源：

- SMM 算力快讯、SMM 算力价格/现货相关栏目
- SMM 算力金属直播 `https://news.smm.cn/live/metal/143`，必须深扒近 7 日快讯，不得只抓单篇历史文章
- SMM 移动详情页和 news.metal.com 多语言镜像，用于补全文本和交叉校验
- 国内 IDC 一手报价或渠道报价
- 运营商智算中心、IDC 合作方公开报价

补充源：

- 国内云厂商 GPU 包月/包年实例价格：阿里云、腾讯云、华为云、火山引擎、百度智能云、UCloud、AutoDL、矩池云等
- 招投标与中标公告：中国政府采购网、各高校/科研院所招标网、公共资源交易中心
- 行业媒体、研报、券商报告
- 个人站、指数站、IDC 门户、CSDN、掘金、墨天轮、东方财富财富号等公开网页
- 微信公众号、视频号、抖音、B站、小红书、知乎、微信群截图等低可信来源

规则：

- 云厂商实例价、单卡小时价、抢占式价格、按量价格不得进入国内主指数，但必须进入 `Auxiliary Quotes`。
- 招投标价格一般进入采购价或整机价模块，不得直接进入租赁主指数。
- 如果国内主指数 PASS 样本少于 3 个，必须扩展到云厂商包月/包年实例价和招投标数据，并在报告中明确“主指数样本不足，但辅助市场样本如下”。
- 对 SMM 必须抽取 `title`、`publish_time`、`smm_item_id`、`original_price`、`gpu_count`、`server_count`、`region`、`contract_period`、`bid/ask/transaction`、`supply_signal` 和原文链接。
- 对公众号、抖音、视频号、B站、小红书、知乎、论坛、个人站等低可信来源，必须作为 `Lead` 或 `Candidate` 保存原文、作者、发布时间、截图/链接和置信度原因；不得进入主指数、ROI 或 AI 总结。
- 如果 SMM、IDC、运营商和低可信线索在同一 GPU 上形成一致区间，可提高 Source Consensus；但低可信线索不能单独决定价格。
- 国内算力租赁主指数柱状图以“万元/8卡整机/月”绘制。每个国内柱子的标签除显示国内月租外，还必须标注“相当于海外同型号等效 8卡月租的百分之多少”；无法找到海外同型号时标注“海外缺口”。

### 8.2 海外 GPU Cloud / 租赁源池

优先抓取公开可验证的美元/卡/小时价格。

聚合源：

- Cloud-GPUs / cloud-gpus.com：覆盖 30+ providers、75+ GPU models、5000+ instance configurations，含 Price Analytics 和日度更新，可作为海外 GPU Cloud 覆盖率补齐与中位价参考。
- GPUCloudPricing / gpucloudpricing.com：覆盖去中心化和中小 GPU 云厂商，适合补充 Vast.ai、Salad、Novita、RunPod 等平台的横向比较。
- 聚合源只能用于海外 GPU Cloud 覆盖率、最低价/中位价/最高价观察和 provider 发现；不得进入国内 8卡整机租赁主指数。

核心源：

- RunPod Pricing
- Lambda Pricing
- Vast.ai Pricing
- TensorDock Hostnodes API
- DataCrunch Pricing
- CUDO Compute
- CoreWeave Pricing / 产品页
- Nebius GPU Cloud
- Crusoe Cloud
- Oracle OCI GPU
- Paperspace
- Fluidstack
- Modal Pricing
- Together.ai GPU / Inference Pricing
- Fireworks.ai Pricing
- DeepInfra Pricing

规则：

- 海外价格只进入海外 GPU Cloud 模块，不进入国内租赁指数。
- 海外 GPU Cloud 原始价格即使是美元/卡/小时，也必须统一折算为“万元/8卡整机/月”用于图表和表格主展示；单卡小时价只作为辅助字段保留。
- 对同一 GPU，同日至少保留 p25 / median / p90 或 min / median / max（如来源提供）。
- 如 RunPod、Lambda、Vast.ai 同时有数据，必须计算 Source Consensus。

### 8.3 GPU 采购价 / 整机价源池

采购价必须单独成表，不与租赁价混用。

核心源：

- 英伟达 OEM / 认证系统说明页，用于确认规格而非价格
- 整机厂商与渠道报价：BIZON、Supermicro、Dell、HPE、Lenovo、ASUS、GIGABYTE、Exxact、Lambda Labs、Thinkmate 等
- 国内招投标/中标公告：中国政府采购网、高校采购网、科研院所公告、公共资源交易中心
- 国内渠道/整机厂商公开报价
- 行业媒体、研报、券商报告

规则：

- 明确区分单卡、2卡工作站、4卡服务器、8卡 HGX 整机、16卡/64卡集群、GB 系统、整柜。
- 采购价可以进入“采购价与成本参考”，但只有完成来源交叉验证后才能进入 ROI。
- 若采购价只有单一渠道，最多标为 Candidate 或 Auxiliary，不得作为投资结论。

### 8.4 Token 官方价源池

官方价必须从官方页面或官方文档抓取。

海外：

- OpenAI API Pricing
- Anthropic Claude Pricing
- Google Gemini API Pricing
- Mistral Pricing
- Cohere Pricing
- xAI API Pricing
- Meta Llama 官方托管/云市场价格

国产：

- DeepSeek API Pricing
- 阿里云百炼 / Model Studio Pricing
- 火山方舟 / 豆包计费页
- 百度智能云千帆计费页
- 腾讯云混元计费页
- 智谱开放平台计费页
- Moonshot / Kimi API 计费页
- MiniMax 开放平台计费页
- 讯飞星火计费页

市场价：

- LiteLLM `model_prices_and_context_window.json`：可作为机器可读模型价格、上下文窗口和 provider 映射源。
- OpenRouter `/api/v1/models`：可作为市场价、上下文和路由信息源，不得替代官方价格。
- models.dev `api.json`：可作为多 provider 模型目录和价格结构化源。
- BenchLM `pricing.json`：可作为模型价格矩阵辅助源。
- llmpricing / sanand0.github.io/llmpricing：可作为 Token 价格与 LMSYS/LMArena Elo 性价比参考，不得替代官方价格。
- morph-llm LLM Cost Calculator / LLM API Comparison：可作为模型上下文、限流、价格矩阵的辅助源，需标注 Market / Reference。
- Artificial Analysis
- Together.ai
- Fireworks.ai
- Replicate
- Hugging Face Inference Providers

规则：

- 官方价和市场价必须分列展示。
- 官方价一开始没拿到时，不得留空；必须继续补采官方页、文档页、云平台计费页或价格计算器，直到核心官方价字段可数值化，并记录已检索来源。
- 机器可读源如果与官方价冲突，官方价优先；冲突本身进入审计摘要。

### 8.5 扩源补采矩阵

执行端不得只依赖固定写死的样本。每次运行如果发现覆盖不足，按以下矩阵补采：

| 模块 | 第一层 | 第二层 | 第三层 | 不得做的事 |
|------|--------|--------|--------|------------|
| Token Official | 厂商官方价格页/API 文档 | 云平台官方计费页 | LiteLLM/OpenRouter/models.dev/BenchLM/llmpricing/morph-llm | 用市场价冒充官方价 |
| 海外 GPU Cloud | RunPod/Lambda/Vast/TensorDock/DataCrunch/CUDO | Cloud-GPUs/GPUCloudPricing | CoreWeave/Nebius/Crusoe/OCI/Paperspace/Modal | 把美元卡小时价混入国内月租 |
| 国内租赁主口径 | SMM 算力直播/快讯/移动页/镜像 + IDC/运营商 | 国内云厂商包月/包年/AutoDL/矩池云 | 招投标/个人站/指数站/门户/公众号/抖音/自媒体线索 | 把单卡小时价或云实例价放入主指数 |
| GPU 采购价 | 政府采购/高校招标 | OEM/整机厂商 | 渠道报价/研报 | 把采购价当租赁价 |
| 规格校验 | NVIDIA/OEM 官方规格 | 整机厂商配置页 | 行业资料 | 用规格页推断价格 |

源池完整清单以 `prompts/source_pool.md` 为准。本文件只保留摘要和执行原则。

### 8.6 覆盖率失败处理

如果任一模块覆盖不足，不得直接输出低价值报告。必须：

1. 列出已检索源、成功源、失败源和失败原因。
2. 自动扩展到下一层级源池。
3. 重新执行 Classify → Normalize → Validate。
4. 报告中显示“覆盖率诊断”模块，说明主指数样本数量、辅助样本数量、候选样本数量、缺口数量。
5. 对缺口明确输出下一步补采建议。

## 9. 飞书通知固定模板

飞书通知必须使用以下固定模板，确保每天格式一致：

```
📌 全球算力市场情报日报
📅 日期：{YYYY-MM-DD}

📈 GPU 租赁：
{一句话概括国内主力卡租赁价格变化，如"国内 H100 8卡整机月租约 7.5 万元，较昨日持平"或"数据存在分歧，等待进一步确认"}

💰 GPU 采购：
{一句话概括主流卡采购价格变化}

🪙 Token 价格：
{一句话概括主要模型 Token 价格变化}

⚡ 关键异动：
{1-2 条当日最大价格波动或供需变化}

🧠 AI 一句话：
{基于 PASS 且 Consensus 非 Low 数据的一句话总结}

📊 完整报告：{latest.html?v=YYYYMMDDHHmm 链接}
```

如果 GitHub 上传失败，发送以下失败模板：

```
⚠️ CMIS 日报生成失败
📅 日期：{YYYY-MM-DD}
❌ 原因：{具体失败原因}
💡 建议：{修复建议}
```

不得静默失败。

## 10. 运行约束

每次发布前先拉取远端 `main`，避免 push 冲突。推荐流程：

`git fetch origin main` → `git pull --rebase origin main` → 记录 `freeze_time` → 采集数据 → ETL 校验 → 生成日报 → `git add` → `git commit` → `git push origin main`

不得把 GitHub Token、飞书 Webhook 或其它敏感信息写入仓库、HTML、数据文件、报告正文、飞书摘要或日志。
