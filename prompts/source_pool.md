# CMIS 扩源源池

本文件用于指导 CMIS Daily 每日扩源采集。`system_prompt.md` 定义数据治理底座，`report_config.md` 定义报告配置，本文件专门维护“到哪里找数据、按什么口径使用、失败后怎么补采”。

核心原则：

- 聚合源可用于发现、补齐、比对和中位价观察，但不得替代官方价或国内主口径。
- 机器可读 API 优先用于结构化采集，网页源用于补充和人工校验。
- 同一价格不得跨类别混用：Token、GPU Cloud、国内 8卡整机租赁、采购价、招投标价、整柜/集群价必须分开。
- 每次运行必须保存 `searched_sources`、`successful_sources`、`failed_sources` 和失败原因。

## 1. Token 价格源池

### 1.1 官方价格源

这些源可进入 `TOKEN_PRICE / Official Price`，但仍需记录模型名、输入价、输出价、缓存价、批处理价、上下文窗口、币种和计费单位。

| 层级 | 来源 | URL | 用途 | 注意事项 |
|---|---|---|---|---|
| P0 官方 | OpenAI API Pricing | https://openai.com/api/pricing/ | OpenAI 官方 Token 价格 | 缓存输入、批处理价必须分列 |
| P0 官方 | Anthropic Pricing | https://www.anthropic.com/pricing | Claude 官方 Token 价格 | 区分模型版本与缓存价 |
| P0 官方 | Google Gemini API Pricing | https://ai.google.dev/gemini-api/docs/pricing | Gemini 官方 Token 价格 | 免费层与付费层分列 |
| P0 官方 | Mistral Pricing | https://mistral.ai/products/la-plateforme | Mistral 官方 Token 价格 | 如价格在控制台，标记访问限制 |
| P0 官方 | Cohere Pricing | https://cohere.com/pricing | Cohere 官方 Token 价格 | 区分 command/embed/rerank |
| P0 官方 | xAI API Pricing | https://docs.x.ai/docs/models | Grok 官方 Token 价格 | 文档价和控制台价需交叉 |
| P0 官方 | DeepSeek API Pricing | https://api-docs.deepseek.com/zh-cn/quick_start/pricing | DeepSeek 官方 Token 价格 | Cache Hit/Miss 必须分列 |
| P0 官方 | 阿里云百炼 Model Studio | https://help.aliyun.com/zh/model-studio/model-pricing | Qwen / 通义千问官方价 | 限时折扣不得覆盖标准价 |
| P0 官方 | 火山方舟模型计费 | https://www.volcengine.com/docs/82379/1099320 | 豆包 / 火山模型官方价 | 区分上下文和推理模式 |
| P0 官方 | 百度千帆计费 | https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Blfmc9dlf | 文心 / 千帆官方价 | 区分输入输出与按次计费 |
| P0 官方 | 腾讯云混元计费 | https://cloud.tencent.com/document/product/1729/97731 | 混元官方价 | 区分模型版本 |
| P0 官方 | 智谱开放平台计费 | https://open.bigmodel.cn/pricing | GLM 官方价 | 免费额度不得计入标准价 |
| P0 官方 | Moonshot/Kimi Pricing | https://platform.kimi.com/docs/pricing/chat | Kimi 官方价 | 区分长上下文模型、缓存命中/未命中 |
| P0 官方 | MiniMax 开放平台计费 | https://platform.minimaxi.com/document/Price | MiniMax 官方价 | 不同能力分列 |
| P0 官方 | 讯飞星火计费 | https://www.xfyun.cn/doc/spark/Price.html | 星火官方价 | 包量/后付费分列 |

### 1.2 Token 机器可读与市场辅助源

这些源进入 `Market / Reference / Structured Auxiliary`。可用于发现新模型、补上下文窗口、比对市场渠道价和抓取模型矩阵，但不得冒充官方价格。

Token 扩源执行规则：

- 不只按厂商覆盖，必须按“厂商 + 主流模型”覆盖，每个厂商至少列出当前主推的 2-5 个模型。
- 国产模型官方价必须优先从官网、官方文档、控制台公开价、购买页或计费页抓取；遇到图片价格表、登录限制或动态渲染，要记录 `Official access limited` 并继续查移动页、文档页、价格计算器或镜像页。
- 三方市场价不得为空。若 OpenRouter 没有同名模型，必须继续查 LiteLLM、models.dev、BenchLM、llmpricing、morph-llm、Together、Fireworks、Replicate、Hugging Face Inference Providers，并记录最终缺口。
- 官方价和市场价冲突时，官方价优先；市场价只作为替代渠道成本观察。

| 层级 | 来源 | URL | 用途 | 使用方式 |
|---|---|---|---|---|
| P2 开源结构化 | LiteLLM model prices JSON | https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json | 模型价格、上下文窗口、provider 映射 | 每日抓取 JSON，作为 Token 市场辅助和缺口发现 |
| P2 市场 API | OpenRouter Models API | https://openrouter.ai/api/v1/models | 市场价、上下文、provider 路由 | 作为 Market Price，和官方价分列 |
| P2 开源结构化 | models.dev API | https://models.dev/api.json | 多 provider 模型目录和价格 | 用于发现缺失厂商和模型 |
| P2 开源结构化 | BenchLM Pricing JSON | https://www.benchlm.ai/data/pricing.json | 价格矩阵和模型字段 | 用于交叉验证市场价格 |
| P2 分析平台 | Artificial Analysis | https://artificialanalysis.ai/ | 模型价格、质量、速度、上下文 | 不作为官方价，只做市场/性能辅助 |
| P2 开源图表 | llmpricing | https://sanand0.github.io/llmpricing/ | Token 价格 × LMArena/LMSYS Elo 性价比 | 做性价比观察，不替代官方价 |
| P2 市场矩阵 | morph-llm LLM Cost Calculator | https://www.morphllm.com/llm-cost-calculator | 模型价格、上下文、限流矩阵 | 做辅助矩阵和缺口提示 |
| P2 市场渠道 | Together.ai Pricing | https://www.together.ai/pricing | 开源模型托管市场价 | 与官方/云市场价分列 |
| P2 市场渠道 | Fireworks.ai Pricing | https://fireworks.ai/pricing | 开源模型托管市场价 | 与官方/云市场价分列 |
| P2 市场渠道 | Replicate Pricing | https://replicate.com/pricing | 模型托管市场价 | 多为按秒/按硬件计费，需单独分类 |
| P2 市场渠道 | Hugging Face Inference Providers | https://huggingface.co/docs/inference-providers/pricing | 托管市场价 | 不可混入官方 Token 价 |

## 2. 海外 GPU Cloud 源池

### 2.1 聚合与价格分析源

| 层级 | 来源 | URL | 用途 | 注意事项 |
|---|---|---|---|---|
| P2 聚合源 | Cloud-GPUs | https://cloud-gpus.com/ | 多 provider、多 GPU 型号、实例配置和 Price Analytics | 用于补齐覆盖率、中位价和最低价，不进入国内租赁主指数 |
| P2 聚合源 | GPUCloudPricing | https://www.gpucloudpricing.com/ | RunPod、Vast、Novita、Salad 等平台横向对比 | 适合做海外云价和平台特性辅助 |

### 2.2 官方/Marketplace 价格源

这些源进入 `GPU_CLOUD`，原始单位通常为 `USD/GPU/hour` 或 `CNY/GPU/hour`。如来源给出实例价，必须先解析 GPU 数量；报告图表和主表标准展示统一折算为 `万元/8卡整机/月`，单卡小时价只作为辅助字段保留。

| 层级 | 来源 | URL | 覆盖重点 | 采集字段 |
|---|---|---|---|---|
| P0/P2 | RunPod Pricing | https://www.runpod.io/pricing | B300、B200、H200、H100、A100、L40S、RTX 5090、RTX 4090、L4 | GPU、显存、Secure/Community、小时价 |
| P0/P2 | Lambda Cloud Pricing | https://lambda.ai/pricing | B200、H100、A100、1-Click Cluster | 实例 GPU 数、小时价、集群价 |
| P2 Marketplace | Vast.ai Pricing | https://vast.ai/pricing | RTX 5090/4090、H200、H100、B200/B300 | p25、median、p90、库存信号 |
| P0 官方 | TensorDock Hostnodes API | https://dashboard.tensordock.com/api/docs/fetch-hostnodes | 实时节点、GPU 小时价、库存 | `price_per_hr`、availableCount、vCPU/RAM/storage |
| P0 官方 | CUDO Compute | https://www.cudocompute.com/pricing | GPU Marketplace 价格 | GPU、区域、小时价、库存 |
| P0 官方 | DataCrunch Pricing | https://datacrunch.io/pricing | H100/H200/A100/L40S 等 | 实例价、GPU 数、区域 |
| P0 官方 | CoreWeave GPU Cloud | https://www.coreweave.com/products/gpu-cloud | 企业 GPU 云 | 若无公开价，标记 Price Missing |
| P0 官方 | Nebius AI Cloud | https://nebius.com/prices | H100/H200/B200 等云价 | 区域、实例价、GPU 数 |
| P0 官方 | Crusoe Cloud | https://crusoe.ai/cloud/ | H100/H200 云价 | 若需登录，记录访问限制 |
| P0 官方 | Oracle OCI GPU | https://www.oracle.com/cloud/price-list/ | A100/H100/BM GPU 实例 | 实例价、GPU 数、区域 |
| P0 官方 | Paperspace | https://www.paperspace.com/pricing | A100、RTX 系列 | 实例价与 GPU 数 |
| P0 官方 | Modal Pricing | https://modal.com/pricing | Serverless GPU | 按 GPU 秒计费，单独归类 |
| P0 官方 | Together GPU Clusters | https://www.together.ai/pricing | GPU 集群 / 推理托管 | 区分 Token 服务和 GPU 服务 |
| P0 官方 | Fireworks Pricing | https://fireworks.ai/pricing | Serverless 推理与 GPU 服务 | Token 与硬件服务分列 |
| P0 官方 | DeepInfra Pricing | https://deepinfra.com/pricing | 模型推理市场价 | 通常进入 Token/推理市场，不进 GPU 租赁主指数 |

## 3. 国内租赁与云厂商辅助源池

国内主指数只接受“中国大陆、8卡整机、万元/台/月、长租、含机柜/电力/网络/运维”的数据。其它国内云厂商、按量、包月、抢占式、单卡小时价一律进入 `Auxiliary Quotes` 或 `Candidate Samples`。

### 3.1 SMM 深扒规则

SMM 是国内服务器租赁价格的高优先级来源，不得只抓单篇历史文章。每次运行必须做多入口深扒：

| 入口 | URL / 检索方式 | 抓取重点 | 入库层级 |
|---|---|---|---|
| SMM 算力金属直播 | https://news.smm.cn/live/metal/143 | 当日与近 7 日快讯、H100/H200/H20/A100/4090/5090/昇腾等价格、成交区间、供需、交付周期 | 可进入 Main Index / Candidate |
| SMM 移动详情页 | `https://m.smm.cn/news/detail/{id}` | 原文标题、发布时间、来源、价格原句 | 与桌面页交叉验证 |
| SMM 英文/多语言镜像 | `https://news.metal.com/.../newscontent/{id}` | 同一条快讯的英文/多语言摘要 | 用于补全文本和校验 |
| SMM 站内搜索 | `site:news.smm.cn/live/detail SMM算力快讯 H100 月租`、`site:m.smm.cn/news/detail SMM算力快讯 A100 80G` | 历史快讯、同型号多日行情 | Candidate / 历史趋势 |
| SMM 关键词滚动 | `H100 裸金属`、`A100 80G IB组网`、`H20 141G`、`5090 月租`、`4090 市场报价`、`昇腾910C 月租` | 型号级补采 | Missing with searched sources |

SMM 深扒必须抽取以下字段：

- `smm_item_id`、标题、发布时间、原文链接、移动端链接、镜像链接
- GPU 型号、显存版本、服务器数量、每台 GPU 数、是否 IB 组网、地区、合同期、押付方式、是否闭口长协
- 原始价格、价格区间、成交价/报价/买方出价/卖方报价的区别
- 供需描述、库存/上线时间、交付周期、主体资质要求
- 是否云上服务价、裸金属价、IDC 长租价、采购价或集群价
- `usage_class` 和 `confidence`

SMM 价格分类规则：

- 明确为“8卡服务器/单台/月/一年起签/含服务”的 SMM 样本，可进入国内主指数候选；通过单位、数量、历史波动和合理性校验后进入 Main Index。
- “买方出价”“期货”“大单意向”“居间报价”“高端算力系统价”“单台采购价”不得直接进入主指数，只能进入 Candidate 或 Procurement。
- SMM 同一型号多条价格若存在区间，应保留 `min / median / max` 或 `bid / ask / transaction`，不得只取最高价。
- SMM 低价尾货、散租平台、短租、云上溢价、单卡小时价必须标明口径，进入 Auxiliary。

| 层级 | 来源 | URL | 用途 | 注意事项 |
|---|---|---|---|---|
| P1 行业 | SMM 算力快讯 | https://news.metal.com/featured-category.html | 国内 8卡整机月租主口径 | 优先进入主指数，仍需合理性校验 |
| P1 行业 | SMM 算力金属直播 | https://news.smm.cn/live/metal/143 | 国内服务器租赁深扒主入口 | 必须抓取近 7 日并按型号归类 |
| P0 官方 | 阿里云 GPU 云服务器 | https://www.aliyun.com/price/product?spm=5176.28103460&productCode=ecs | 国内云厂商实例价 | 只能做辅助，不进国内主指数 |
| P0 官方 | 腾讯云 GPU 云服务器 | https://cloud.tencent.com/product/gpu | 国内云厂商实例价 | 包月/按量/竞价分列 |
| P0 官方 | 华为云 GPU 加速型 | https://www.huaweicloud.com/product/gpu.html | 国内云厂商实例价 | 地域与实例规格分列 |
| P0 官方 | 火山引擎 GPU 云服务器 | https://www.volcengine.com/product/gpu | 国内云厂商实例价 | 与豆包 Token 计费分开 |
| P0 官方 | 百度智能云 GPU 云服务器 | https://cloud.baidu.com/product/gpu.html | 国内云厂商实例价 | 作为辅助样本 |
| P2 平台 | AutoDL | https://www.autodl.com/price | 国内 GPU 租赁平台价 | 多为单卡/容器价，进辅助 |
| P2 平台 | 矩池云 | https://matpool.com/host-market | 国内 GPU 租赁平台价 | 单卡小时价，进辅助 |
| P2 平台 | UCloud GPU 云主机 | https://www.ucloud.cn/site/product/gpu.html | 国内云厂商实例价 | 作为辅助样本 |
| P2/P3 门户 | GoGPU、墨天轮、东方财富财富号、CSDN、掘金、51CTO 等 | 逐站点检索 | 服务器价格榜单、行业文章、价格走势线索 | 只作为 Candidate / Lead，必须标注低置信度 |
| P3 自媒体 | 微信公众号、视频号、抖音、B站、小红书、知乎等公开可访问内容 | 平台内搜索或公开网页索引 | 渠道报价、截图、供需线索、联系方式 | 不进入主指数；截图/口述必须保留来源、发布时间和原始上下文 |

### 3.2 自媒体与低置信线索规则

公众号、抖音、视频号、B站、小红书、知乎、CSDN、掘金、墨天轮、东方财富财富号、个人站、IDC 门户等可以用于“有数据先留痕”，但必须严格降级：

- 能公开访问并可保留 URL 的，进入 `Candidate Samples` 或 `Auxiliary Quotes`。
- 只有截图、口述、群聊或转述的，进入 `Lead`，不得进入主图、主指数、ROI 或 AI 总结。
- 若低置信线索与 SMM / IDC / 运营商 / 云厂商公开价一致，可用于提高 Source Consensus，但不能单独决定价格。
- 必须记录 `platform`、`author/account`、`publish_time`、`capture_time`、`raw_text`、`raw_image_path`（如有）、`confidence_reason`。
- 平台内容如果需要登录、无法公开访问或无法稳定引用，记录为 `failed_sources` 或 `access_limited`，不得伪造。

重点检索词：

- `H100 8卡 月租`、`H100 裸金属 月租`、`H100 服务器 租赁 7万 8万`
- `H200 8卡 月租`、`H20 141G 月租`、`A100 80G 8卡 租赁`
- `RTX 4090 八卡服务器 月租`、`RTX 5090 八卡整机 月租`
- `昇腾 910C 服务器 月租`、`昇腾 910B 租赁`
- `算力租赁 报价 单台/月`、`智算中心 H100 出租`、`GPU服务器租赁价格`

## 4. 采购价、招投标与整机规格源池

采购价用于 `GPU_PURCHASE / GPU_SYSTEM / GPU_CLUSTER / GPU_RACK`，不得和租赁价混用。招投标数据必须解析 GPU 型号、数量、服务器台数、是否含税、是否含维保、是否含网络/存储。

| 层级 | 来源 | URL | 用途 | 注意事项 |
|---|---|---|---|---|
| P0 政府 | 中国政府采购网 | http://www.ccgp.gov.cn/ | 中标公告、采购价 | 解析型号、数量、总价、税费 |
| P0/P1 招投标 | 高校采购网/公共资源交易中心 | 逐站点检索 | 服务器/集群中标价 | 只能作为采购价，不直接做租赁价 |
| P0 规格 | NVIDIA Data Center GPUs | https://www.nvidia.com/en-us/data-center/ | GPU 规格、系统形态 | 用于规格校验，不提供成交价 |
| P0 整机 | Supermicro GPU Systems | https://www.supermicro.com/en/products/gpu | 8卡/多卡服务器形态 | 规格校验，价格需另找 |
| P0 整机 | Dell PowerEdge AI Servers | https://www.dell.com/en-us/lp/dt/servers-ai | 整机规格 | 规格校验 |
| P0 整机 | HPE AI Systems | https://www.hpe.com/us/en/compute/hpc.html | 整机/集群规格 | 规格校验 |
| P0 整机 | Lenovo AI Servers | https://www.lenovo.com/us/en/servers-storage/solutions/ai/ | 整机规格 | 规格校验 |
| P2 渠道 | BIZON GPU Workstations/Servers | https://bizon-tech.com/ | 工作站/服务器公开配置价 | 多为 2卡/4卡，不可直接折 8卡 HGX |
| P2 渠道 | Exxact GPU Systems | https://www.exxactcorp.com/ | 整机配置价 | 区分工作站和服务器 |
| P2 渠道 | Thinkmate GPU Servers | https://www.thinkmate.com/ | 整机配置价 | 作为采购辅助 |

## 5. 运行时扩源顺序

当覆盖不足时，按以下顺序自动补采：

1. Token 官方价缺失：先检索厂商官方价格页和开发者文档，再查云平台官方计费页，最后用 LiteLLM / OpenRouter / models.dev / BenchLM / llmpricing / morph-llm 作为辅助。
2. 海外 GPU Cloud 覆盖不足：先抓 RunPod、Lambda、Vast.ai、TensorDock、DataCrunch、CUDO，再用 Cloud-GPUs 和 GPUCloudPricing 补齐 provider 与中位价。
3. 国内主指数 PASS 少于 3：先查 SMM 和 IDC/运营商线索，再查国内云厂商包月/包年、AutoDL/矩池云等辅助价，最后查招投标和媒体线索。
4. 采购价不足：先查政府采购/高校招标，再查整机厂商和渠道配置价，最后查媒体/研报。
5. 任一数据无法确认单位、GPU 数、地区或税费时，不得进入主指数；保留到 `Candidate Samples` 或 `Rejected Samples`。
