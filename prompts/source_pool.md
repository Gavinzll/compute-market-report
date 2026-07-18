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
| P0 官方 | 百度千帆计费 | https://cloud.baidu.com/doc/qianfan/s/wmh4sv6ya | 文心 / 千帆官方价 | 已确认 ERNIE-4.5-Turbo-VL-32K 为 3/9 元/百万 tokens；ERNIE 5.0 需按上下文区间记录 |
| P0 官方 | 腾讯云混元计费 | https://cloud.tencent.com/document/product/1729/97731 | 混元官方价 | 区分模型版本 |
| P0 官方 | 智谱开放平台计费 | https://open.bigmodel.cn/pricing | GLM 官方价 | 免费额度不得计入标准价 |
| P0 官方 | Moonshot/Kimi Pricing | https://platform.kimi.com/docs/pricing/chat | Kimi 官方价 | 区分长上下文模型、缓存命中/未命中 |
| P0 官方 | MiniMax 开放平台计费 | https://platform.minimaxi.com/docs/guides/pricing-paygo | MiniMax 官方价 | 已确认 MiniMax-M3 标准层与优先服务倍率，不同上下文区间分列 |
| P0 官方 | 讯飞星火计费 | https://www.xfyun.cn/doc/spark/Price.html | 星火官方价 | 包量/后付费分列 |

### 1.2 Token 机器可读与市场辅助源

这些源进入 `Market / Reference / Structured Auxiliary`。可用于发现新模型、补上下文窗口、比对市场渠道价和抓取模型矩阵，但不得冒充官方价格。三方价必须拆分为海外三方价与境内三方价。

Token 扩源执行规则：

- 不只按厂商覆盖，必须按“厂商 + 主流模型”覆盖，每个厂商至少列出当前主推的 2-5 个模型。
- 国产模型官方价必须优先从官网、官方文档、控制台公开价、购买页或计费页抓取；遇到图片价格表、登录限制或动态渲染，要记录 `Official access limited` 并继续查移动页、文档页、价格计算器或镜像页。
- 三方市场价不得为空，且必须拆成海外三方价和境内三方价。海外三方若 OpenRouter 没有同名模型，必须继续查 LiteLLM、models.dev、BenchLM、llmpricing、morph-llm、Together、Fireworks、Replicate、Hugging Face Inference Providers；境内三方以硅基流动为基准，若无同名模型可记录近似模型但不得硬套为精确价。
- 官方价和市场价冲突时，官方价优先；市场价只作为替代渠道成本观察。
- 每条海外/境内三方价必须保存匹配级别：`精确同名`、`官方同步/路由价`、`同厂参考`、`同系列参考`、`同类型参考` 或 `近似参考`。同厂、同系列、同类型、近似、待补、非文本模型参考都只能作为参考价展示，不能写成精确同名价；如果官方价与三方价完全相同，必须在 `同价原因` 解释同步官方价、同名价一致或参考价巧合相等。

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
| P2 境内三方 | 硅基流动价格页 | https://siliconflow.cn/pricing | 境内三方模型 API 价格基准 | 精确匹配模型才填写精确价；近似模型必须标注近似，不得硬套 |

## 2. 海外 GPU Cloud 源池

### 2.1 聚合与价格分析源

| 层级 | 来源 | URL | 用途 | 注意事项 |
|---|---|---|---|---|
| P2 聚合源 | Cloud-GPUs | https://cloud-gpus.com/ | 多 provider、多 GPU 型号、实例配置和 Price Analytics | 用于补齐覆盖率、中位价和最低价，不进入国内租赁主指数 |
| P2 聚合源 | GPUCloudPricing | https://www.gpucloudpricing.com/ | RunPod、Vast、Novita、Salad 等平台横向对比 | 适合做海外云价和平台特性辅助 |
| P2 聚合源 | IntuitionLabs GPU 对比 | https://intuitionlabs.ai/articles/h100-rental-prices-cloud-comparison | H100 8 卡 $/h 跨平台横向对比（AWS/Azure/GCP/Lambda/RunPod/CoreWeave） | 跨云中位价校验，B200/H200 部分覆盖；独立于 Cloud-GPUs 的第三视角 |
| P2 聚合源 | Computestacker | https://computestacker.com/region/global/ | 全球区全云 GPU 价格地图，含区域价差 | 比 Cloud-GPUs 颗粒度更细，适合做海外 GPU Cloud 区域价校验和趋势辅助 |
| P2 聚合源 | Computestacker 2026 指南 | https://computestacker.com/insights/gpu-cloud-pricing-guide-2026/ | 2026 GPU Cloud 趋势报告 | 年度行业报告，适合做趋势参考 |
| P2 聚合源 | GPU Compare 日报 | https://gpucompare.com/blog/ | 日级 GPU Cloud 价格更新 | 提供历史价格变化趋势，适合做日环比辅助 |
| P2 聚合源 | Cloudprice Azure | https://cloudprice.net/vm/Standard_NC40ads_H100_v5 | Azure ND H100 v5 区域级详价 | Azure 实例价颗粒度比官方价目更细，适合做 Azure 特定区域价校验 |
| P2 聚合源 | Thunder Compute H100 | https://www.thundercompute.com/blog/nvidia-h100-pricing | H100 8 卡 $/h 对比 | 覆盖 AWS/Azure/GCP/Lambda 等 |
| P2 聚合源 | Thunder Compute B200 | https://www.thundercompute.com/blog/nvidia-b200-pricing | B200 8 卡 $/h（约 $82/h） | 补齐 B200 数据，我们 B200 海外源偏少 |

**Hyperscaler 区域价差异注脚**：以上主要 hyperscaler（AWS/Azure/GCP/阿里云）的关键 GPU 型号在不同区域定价差异显著（可达 30-50%），采集时至少记录两个锚点区域：`us-east-1`（北美基准）和 `cn-north-1`（中国区基准），其他区域价格作为辅助。Azure 中国区（azure.cn）与全球区（azure.microsoft.com）价目独立，必须分开记录。阿里云国内（aliyun.com）与海外（alibabacloud.com）同理。汇率折算时必须标注原始区域和币种。

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

国产战略关注例外：`昇腾 910B`、`寒武纪 MLU`、`海光 DCU`、`壁仞`、`摩尔线程` 必须进入国内指数表和国内柱状图。若无法取得标准 8卡整机月租或 Confidence < 70，仍保留在指数和柱状图中并标注 `Strategic Watch / REVIEW`。每日刷新优先级为：明确公开市场价 > 可折算云价/包年包月价 > 云价折算 fallback > 价格待补。每次运行都要先扩源到国产智算中心报价、8卡训推一体机租赁、集成商报价、媒体/社区线索和招投标线索；若找到新的明确 8卡整机/裸机/月租，应更新 `价格口径`、`价格区间`、`标准化价格`、`Confidence Score` 和备注。严禁把云主机单卡价、单卡月租或未确认卡数的套餐价直接乘以 8 当成 8卡整机月租；只有同时确认硬件配置/卡数和公开价格时，才允许折算为 `云价折算` 或公开价。连配置/卡数/形态都无法确认时才显示 `价格待补`，不得用 910B 区间或任何无来源系数生成占位价。

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
| P2 平台 | 极智算 jygpu.com | https://www.jygpu.com/ | GPU云服务器/裸金属租赁平台 | 已验证有910B（15,600-17,040元/月）和NVIDIA系列；**尚未验证**摩尔线程/壁仞/寒武纪/海光覆盖 |
| P2 平台 | 云擎天下 omniyq.com | https://www.omniyq.com/ | GPU算力批量租赁平台 | 已验证有910B（15,000元/月）和NVIDIA系列；**尚未验证**摩尔线程/壁仞/寒武纪/海光覆盖 |
| P2 平台 | 曙光智算·超算互联网 scnet.cn | https://www.scnet.cn/ | 超算互联网平台/曙光智算旗舰店 | 平台真实存在，需登录查看具体GPU价格；有Bare Metal Server和曙光智算旗舰店入口 |
| P2 平台 | 胜算云 shengsuanyun.com | https://www.shengsuanyun.com/hashrate | GPU算力租赁平台 | 已验证有壁仞天垓100（1.49元/时）、摩尔线程S4000（1.69元/时）、昇腾910（2.36元/时）单卡云实例价；**无8卡整机月租价** |
| P2 平台 | 模力方舟 ai.gitee.com/compute | https://ai.gitee.com/compute | Gitee AI算力市场 | 已验证有海光BW1000（3.00元/时）、摩尔线程S5000（8.00元/时）、壁仞天垓150（3.00元/时）、壁砺106M（2.00元/时）、天数智芯智铠100（2.00元/时）、燧原S60（2.00元/时）、昇腾910B（3.00-4.00元/时）单卡云实例价；**无8卡整机月租价** |
| P2 平台 | 智星云 ai-galaxy.cn | https://www.ai-galaxy.cn/ | GPU算力服务平台 | 有昇腾910B、海光DCU、壁仞天垓100现货，但**公开页面无价格**；裸金属/云主机需登录查看 |
| P2 平台 | UCACHE ucache.cn | https://ucache.cn/enterprise/new/302.html | 北京IDC/服务器托管/算力租赁 | 有摩尔线程S4000 8卡训推一体机租赁，**无标准月租价**（案例：某电商2万元/项目） |
| P2 平台 | 网宿商城 online.wangsu.com | https://online.wangsu.com/product/gpu- | GPU算力服务器租赁（8卡整机） | 已验证覆盖H100/H200/A100/H20/4090/A800/H800，**有8卡¥/月详表**；国内少数公开列出8卡整机月租的平台，可进入国内主指数候选 |
| P2 平台 | 晨涧云 mornai.cn | https://www.mornai.cn/news/gpu/a100-gpu-rent-trend/ | A100 GPU租用价格趋势 | A100 价目较全（2.8-6.5元/h），可做A100辅助校验；**尚未验证**其他GPU型号覆盖 |
| P2 平台 | 啸月网络 xiaoyueidc.com | https://www.xiaoyueidc.com/news/detail/article/8278 | GPU服务器租赁（8卡整机） | 已验证有H100/A100/H20/4090的8卡¥/月；**尚未验证**国产GPU覆盖 |
| P2/P3 门户 | 什么值得买（区域GPU租用调研） | https://post.m.smzdm.com/ | 区域市场GPU服务器租用价格 | 厦门地区：寒武纪思元590单卡7,000-8,000元/月；昇腾910B单卡8,500-9,500元/月；**非8卡整机价** |
| P2/P3 门户 | GoGPU、墨天轮、东方财富财富号、CSDN、掘金、51CTO 等 | 逐站点检索 | 服务器价格榜单、行业文章、价格走势线索 | 只作为 Candidate / Lead，必须标注低置信度 |
| P3 自媒体 | 微信公众号、视频号、抖音、B站、小红书、知乎等公开可访问内容 | 平台内搜索或公开网页索引 | 渠道报价、截图、供需线索、联系方式 | 不进入主指数；截图/口述必须保留来源、发布时间和原始上下文 |

**国产卡专项扩源补充（2026-07-15 验证状态）：**

以下来源和型号覆盖状态基于 2026-07-15 实际验证：

| 来源 | 910B | 摩尔线程 | 壁仞 | 寒武纪 | 海光 | 验证方式 |
|------|------|----------|------|--------|------|----------|
| 极智算 jygpu.com | ✅ 15,600-17,040元/月 | ❌ 未覆盖 | ❌ 未覆盖 | ❌ 未覆盖 | ❌ 未覆盖 | 浏览器直接访问首页 |
| 云擎天下 omniyq.com | ✅ 15,000元/月 | ❌ 未覆盖 | ❌ 未覆盖 | ❌ 未覆盖 | ❌ 未覆盖 | 浏览器直接访问首页 |
| 胜算云 shengsuanyun.com | ✅ 2.36元/时（单卡） | ✅ S4000 1.69元/时 | ✅ 天垓100 1.49元/时 | ❌ 未覆盖 | ❌ 未覆盖 | 浏览器直接访问首页 |
| 模力方舟 ai.gitee.com | ✅ 3.00-4.00元/时 | ✅ S5000 8.00元/时 | ✅ 天垓150 3.00元/时 | ❌ 未覆盖 | ✅ BW1000 3.00元/时 | 浏览器翻页1-4 |
| 网宿商城 online.wangsu.com | ✅ 有H100/H200/A100/H20/4090/A800/H800 8卡月租 | ❓ 待验证 | ❓ 待验证 | ❓ 待验证 | ❓ 待验证 | 浏览器访问GPU产品页 |
| 晨涧云 mornai.cn | ❌ 未验证 | ❌ 未验证 | ❌ 未验证 | ❌ 未覆盖 | ❌ 未覆盖 | 浏览器访问价格页（已验证A100） |
| 啸月网络 xiaoyueidc.com | ✅ 有H100/A100/H20/4090 8卡月租 | ❓ 待验证 | ❓ 待验证 | ❓ 待验证 | ❓ 待验证 | 浏览器访问新闻页（已验证NVIDIA系列） |
| 智星云 ai-galaxy.cn | ✅ 有现货 | ❓ 未确认 | ✅ 天垓100现货 | ❓ 未确认 | ✅ 有现货 | 首页无价格 |
| 曙光智算 scnet.cn | ❓ 需登录确认 | ❓ 需登录确认 | ❓ 需登录确认 | ❓ 需登录确认 | ❓ 需登录确认 | 浏览器访问平台首页 |
| SMM 算力快讯 | ✅ 有数据 | ⚠️ 偶有线索 | ⚠️ 偶有线索 | ✅ MLU370-X8有数据 | ⚠️ 偶有线索 | 历史采集记录 |
| 天翼云 PCH1 | ✅ 18,454元/月 | ❌ 无 | ❌ 无 | ✅ MLU370-S4有云价 | ❌ 无（仅K100） | 浏览器访问价格总览 |
| UCACHE | ❌ 无 | ✅ S4000 8卡一体机 | ❌ 无 | ❌ 无 | ❌ 无 | 浏览器访问新闻页 |
| 什么值得买 | ✅ 单卡8,500-9,500元 | ❌ 无 | ❌ 无 | ✅ 单卡7,000-8,000元 | ❌ 无 | 区域市场调查 |

**关键结论：** 截至 2026-07-15：
1. **昇腾910B** — 多源交叉验证，有裸金属和云主机价格，数据较充分
2. **摩尔线程S4000/S5000** — 有单卡云实例价（胜算云、模力方舟），**无8卡整机月租**
3. **壁仞天垓100/150/壁砺106M** — 有单卡云实例价（胜算云、模力方舟），**无BR100 OAM服务器8卡整机月租**
4. **海光BW1000** — 有单卡云实例价（模力方舟），**无DCU Z100租赁价**；天翼云只有DCU-K100
5. **寒武纪MLU590** — **无任何公开租赁价格**；只有MLU370-S4的云价和思元590的单卡区域数据

**SMM算力快讯覆盖范围确认**：SMM主要跟踪H100、A100、4090、5090、910B2/910C等交易量大的卡种。**MLU590、DCU Z100、BR100尚未进入SMM监测体系**，说明这些卡的租赁市场交易量还不足以形成公开报价。

**扩源优先级（更新）：**
1. **SMM算力快讯** — 每日检索关键词：`寒武纪 MLU590 月租`、`海光 DCU Z100 租赁`、`壁仞 BR100 月租`、`摩尔线程 MTT S4000 租赁`、`国产算力 8卡 整机 月租`
2. **什么值得买区域调研** — 关注各城市GPU租用价格调研文章，可能陆续出现MLU590/DCU Z100单卡数据
3. **算力社群/微信群** — 低置信，但可能是国产卡价格最先流出的渠道
4. **招投标网站** — 搜索政府采购网、运营商集采公告，可能有批量采购/租赁价格
5. **曙光智算登录** — 登录后查看资源市场→裸金属→国产DCU/MLU
6. **智星云客服询价** — 400-021-0001，直接询问国产卡8卡整机月租
7. **淘宝/闲鱼** — 关键词：`寒武纪MLU590 裸金属`、`海光DCU Z100 服务器租赁`、`壁仞BR100 8卡`

### 3.2 AI 生成内容幻觉识别规则（2026-07-15 新增）

**背景：** 2026-07-15 核验豆包（字节跳动 AI）提供的国产卡批量价格信息，发现其大量声称的"可追溯、可爬虫"来源为**虚构**。此类幻觉模式在其他 AI 助手（ChatGPT、文心一言、通义千问等）中同样可能出现，必须建立系统化防御规则。

**已证伪的幻觉案例（2026-07-15 豆包）：**

| 豆包声称 | 声称来源 | 实际验证结果 |
|---------|---------|------------|
| 海光Z100 8卡批量长协 1.1-1.3万/月 | SMM + 云擎天下 + 移动集采 | ❌ SMM 站内搜索无 Z100 月租价；云擎天下首页无海光卡；未找到移动集采 Z100 中标公告 |
| 寒武纪MLU590 8卡批量 3.8-4.5万/月 | SMM + 曙光智算 | ❌ SMM 无 MLU590 月租价；曙光智算需登录无法验证 |
| 壁仞BR100 8卡批量 4.5-5.5万/月 | SMM + 头部IDC | ❌ SMM 无 BR100 月租价；云擎天下、极智算首页无壁仞卡 |
| 摩尔线程S4000 8卡批量 0.9-1.1万/月 | SMM + IDC平台 | ❌ SMM 无 S4000 月租价；云擎天下、极智算无摩尔线程卡 |
| SMM 有海光Z100/MLU590/BR100/S4000 的 8卡批量裸金属月租 | SMM 算力直播 | ❌ 浏览器访问 news.smm.cn/live/metal/143，JS 全文搜索关键词均未命中 |
| 云擎天下有 Z100/MLU590/BR100/S4000 的 8卡批量价 | omniyq.com | ❌ 浏览器访问首页，裸金属列表仅含 910B 和 NVIDIA 卡，无其他国产卡 |

**幻觉识别规则（适用于所有 AI 生成内容来源，不限于豆包）：**

1. **"声称多源交叉验证"必须逐源核查**：AI 经常声称"SMM + 云擎天下 + 移动集采"等多源验证，但实际来源可能全部虚构。每一条引用都必须通过浏览器直接访问 URL、站内搜索关键词、WebSearch 搜索精确引用片段中至少一种方式独立验证。
2. **真实平台名 + 虚假数据是常见幻觉模式**：AI 会使用真实的平台名称（SMM、云擎天下、极智算、招投标网）但编造该平台并不存在的具体价格数据。平台名真实 ≠ 数据真实。
3. **精确数字无 URL = 高概率幻觉**：任何给出精确价格数字（如"1.15万/月""3.9万/月"）但未附带可点击公开 URL 的 AI 输出，必须视为疑似幻觉，直到通过独立搜索验证。
4. **"可爬虫""可正则匹配" ≠ 已实际验证**：AI 经常声称数据"可爬虫"，但这只是它在描述一个它认为"应该存在"的数据源，不代表该数据确实存在。
5. **国产卡批量长协价是幻觉重灾区**：由于 MLU590、DCU Z100、BR100、S4000 的 8卡整机月租价在公开互联网上极度稀缺（截至 2026-07-15 几乎不存在），AI 极易产生"合理数字 + 合理来源"的幻觉组合。任何声称这些卡有明确 8卡整机月租价的 AI 输出，默认视为幻觉，除非能提供可点击的公开 URL 并通过独立验证。
6. **验证流程必须可追溯**：每次核验必须记录：验证日期、验证工具（浏览器/WebSearch/其他）、验证关键词、验证结果（命中/未命中/需登录）、截图或原始搜索结果片段。验证结果写入本文件。

### 3.3 自媒体与低置信线索规则

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
- `寒武纪 MLU 租赁`、`海光 DCU 租赁`、`壁仞 GPU 租赁`、`摩尔线程 GPU 租赁`
- `国产算力卡 租赁 报价`、`国产智算中心 出租`、`国产 GPU 服务器 月租`、`国产 AI 服务器 招投标`
- `算力租赁 报价 单台/月`、`智算中心 H100 出租`、`GPU服务器租赁价格`

## 4. 采购价、招投标与整机规格源池

采购价用于 `GPU_PURCHASE / GPU_SYSTEM / GPU_CLUSTER / GPU_RACK`，不得和租赁价混用。招投标数据必须解析 GPU 型号、数量、服务器台数、是否含税、是否含维保、是否含网络/存储。

利润测算覆盖的采购价型号必须与国内租赁指数覆盖范围一致。若某型号有租赁价但缺采购价，必须继续扩源；精确采购价不可得时，可以采用采购价估算，但必须写明区间、中位数、依据来源、置信度和不可审计边界。

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
| P2 渠道 | Petronella SXM TCO | https://petronellatech.com/hardware/nvidia-sxm-total-cost-ownership/ | OEM 8 卡 SXM TCO 成本拆解 | 独立于 Amnic/Mercatus 的第三视角，适合做采购价交叉验证 |
| P2 聚合 | Gpu Lease Index | https://gpuleaseindex.com/calculators/gpu-cost | 多平台 GPU 成本计算器 + H100 单价 | 多平台 TCO 对比，适合做采购价辅助和回本分析 |
| P2/P3 渠道 | ZOL、1688、淘宝、苏宁、e算商城 | 逐站点检索 | 消费级 8卡整机、国产卡单卡和服务器公开报价 | 只能作为三方渠道或 Candidate，需标注税费/保修/渠道不确定性 |
| P2/P3 财经/社区 | 雪球、东方财富、CSDN、腾讯云开发者、商业新知 | 逐站点检索 | 国产 GPU 框架协议、集采、采购价估算线索 | 必须追溯原始公告；未追溯前只作线索或采购价估算依据 |

## 5. 运行时扩源顺序

当覆盖不足时，按以下顺序自动补采：

0. **Token 模型目录更新（最高优先级）**：每次运行必须先检索各家厂商最新模型矩阵，按"主流/核心/先进"标准筛选模型目录，淘汰 deprecated 模型和无数据旧模型，更新脚本中的模型清单后再进入价格采集。此步骤不依赖价格数据，只依赖厂商官网/文档/发布页的模型列表。
1. Token 官方价缺失：在已更新的模型目录基础上，检索各模型的官方价格页和开发者文档，再查云平台官方计费页，最后用 LiteLLM / OpenRouter / models.dev / BenchLM / llmpricing / morph-llm 作为辅助。
2. 海外 GPU Cloud 覆盖不足：先抓 RunPod、Lambda、Vast.ai、TensorDock、DataCrunch、CUDO，再用 Cloud-GPUs、GPUCloudPricing、IntuitionLabs、Computestacker、Thunder Compute、GPU Compare、Cloudprice 补齐 provider、中位价、区域价差和历史趋势。
3. 国内主指数 PASS 少于 3，或国产战略关注卡缺价格：先查 SMM 和 IDC/运营商线索，再查网宿商城、晨涧云、啸月网络、AutoDL/矩池云等平台辅助价，最后查招投标、集成商、国产智算中心和媒体线索。
4. 采购价不足：先查政府采购/高校招标、运营商/银行/央国企框架协议和中标公告，再查整机厂商和渠道配置价（Petronella SXM TCO / Gpu Lease Index 可做交叉验证），最后查媒体/研报/社区线索；若精确采购价不可得但配置或单卡价可确认，形成采购价估算并标注估算依据。
5. 任一数据无法确认单位、GPU 数、地区或税费时，不得进入主指数；保留到 `Candidate Samples` 或 `Rejected Samples`。
6. 新算力卡发现：每次采集时除覆盖基线名单外，必须主动扫描 NVIDIA 官方产品页、国产 GPU 厂商发布页、Cloud-GPUs / GPUCloudPricing / Computestacker 新增型号、SMM 快讯和行业媒体，发现基线名单外的新卡（如 NVIDIA 新架构、国产新厂商/新系列）。新卡首次出现时进入 `Candidate Samples`；连续 3 期均有可追溯数据后，升级加入 `GPU_ORDER` 基线名单并同步更新脚本配置。纳入标准：① 有明确型号和显存规格；② 至少有一个可追溯价格来源；③ 已发布非 rumor/概念产品。

## 6. 数据层级分级（data_tier）

每条数据在快照中必须标注 `data_tier` 字段，用于区分数据可信度和用途边界：

| data_tier | 定义 | 进入主指数 | 进入图表/AI 摘要 | 典型来源 |
|---|---|---|---|---|
| `official` | 厂商官方价目表、政府采购中标公告 | 经校验后可进入 | 可引用 | AWS/Azure/GCP/阿里云/腾讯云/华为云官方价、政府采购网 |
| `market` | 行业媒体、交易平台公开报价、IDC/运营商公开价 | 经校验后可进入 | 可引用 | SMM、RunPod/Lambda 官方价、网宿商城、极智算 |
| `grey_market` | 灰色渠道、非正规市场、黑市溢价、二手转售 | **不得进入**主指数 | 只作趋势观察，AI 摘要中标注"趋势参考" | 微博黑市价、头条灰色渠道、雪球非官方报价、闲鱼/淘宝二手转售 |

grey_market 数据必须满足以下规则：
- 在快照 JSON 中 `data_tier: "grey_market"` 字段必填
- 在报告中展示时必须标注"（趋势参考，非正规渠道）"
- 不得参与标准化价格计算、中位价计算或 Source Consensus 投票
- 可用于补充说明市场供需紧张程度（如溢价幅度反映紧缺度）

## 7. 数据时效性矩阵

每次运行必须更新以下时效性矩阵，记录每个关键数据源的最近采集时间和可信窗口。超期源自动标记为 `stale`，在 `searched_sources` 中标注需要重新验证。

| 数据源类别 | 关键源 | 默认可信窗口 | 更新频率 |
|---|---|---|---|
| Token 官方价 | 各厂商定价页 | 7 天 | 每次运行 |
| Token 市场价 | OpenRouter / LiteLLM / 硅基流动 | 3 天 | 每次运行 |
| 海外 GPU Cloud | RunPod / Lambda / Vast.ai | 7 天 | 每次运行 |
| 海外聚合对比 | IntuitionLabs / Computestacker / Thunder Compute | 30 天 | 每周验证 |
| 国内行业媒体 | SMM 算力快讯 | 7 天 | 每次运行 |
| 国内云厂商 | 阿里云 / 腾讯云 / 华为云 / 火山引擎 | 30 天 | 每周验证 |
| 国内租赁平台 | 网宿商城 / 极智算 / 云擎天下 / 胜算云 / 模力方舟 | 14 天 | 每周验证 |
| 采购价 | Amnic / Mercatus / Petronella / Gpu Lease Index | 90 天 | 每月验证 |
| 招投标 | 政府采购网 / 高校采购 | 按公告时效 | 每次运行扫描 |

**标记规则**：超过可信窗口的源在快照中标注 `stale: true`，在审计文件中记录 `reason: "超过可信窗口 N 天，需重新验证"`。连续 2 次运行 stale 的源降级一个优先级（P0→P1，P1→P2）。

## 8. 全局覆盖度矩阵

每次运行结束后，生成以下按型号 × 数据类别的覆盖度矩阵，作为下一次运行的扩源优先级输入。

**动态生成规则**：覆盖度矩阵不得在规则文件中写死固定型号列表。必须从当天 `cmis_snapshot_{date}.json` 的 `domestic_rental`、`overseas_rental`、`gpu_procurement` 三个数组的去重 GPU 型号集合中自动生成行，三个数据类别作为列。同时将 `GPU_ORDER` 基线名单中的型号也纳入（即使当天无数据，也占一行标注 ❌）。

### 8.1 GPU 型号覆盖度（运行时动态生成）

由 `generate_cmis_daily.py` 在生成报告后自动输出 `data/coverage_matrix_{date}.json`，格式如下：

```json
{
  "generated_at": "2026-07-18",
  "columns": ["国内租赁（8卡整机月租）", "海外 Cloud（$/h）", "采购价（万元/8卡）"],
  "rows": [
    {
      "GPU 型号": "H100 80G",
      "国内租赁（8卡整机月租）": {"status": "✅", "sources": ["SMM", "网宿商城", "极智算", "云擎天下"]},
      "海外 Cloud（$/h）": {"status": "✅", "sources": ["AWS", "RunPod", "Lambda", "CoreWeave"]},
      "采购价（万元/8卡）": {"status": "✅", "sources": ["Amnic", "Mercatus", "Petronella"]}
    },
    {
      "GPU 型号": "寒武纪 MLU590",
      "国内租赁（8卡整机月租）": {"status": "❌", "sources": []},
      "海外 Cloud（$/h）": {"status": "❌", "sources": []},
      "采购价（万元/8卡）": {"status": "❌", "sources": []}
    }
  ]
}
```

### 8.2 覆盖度评分规则

- ✅ = 有 2+ 个独立来源交叉验证
- ⚠️ = 仅 1 个来源或有待验证数据
- ❌ = 无公开数据，需持续扩源

### 8.3 厂商报价缺口（运行时动态生成）

由生成脚本自动扫描 `source_pool.md` 中标记为"待验证""待补""❓""需登录"的源+型号组合，输出 `data/coverage_gaps_{date}.json`。人工维护部分仅限以下需要浏览器实际验证的明确条目（这些条目在验证后应从待补清单中移除）：

| 缺口来源 | 型号 | 验证动作 | 优先级 |
|---|---|---|---|
| OVH 8 卡 H100 | H100 | 通过 Computestacker 查区域价或访问 OVH 官方 | P2 |
| Equinix 8 卡 H100 | H100 | 通过 Computestacker 查区域价或访问 Equinix 官方 | P2 |
| Oracle Cloud | A100/4090 | 运行时首次采集验证 | P2 |

其余缺口（如"网宿商城国产卡待验证""晨涧云非 A100 待验证"等）均由脚本在运行时自动检测：如果当天采集发现该源有对应型号数据，则自动从缺口清单移除并更新验证状态。
