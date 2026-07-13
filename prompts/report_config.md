# CMIS Daily 报告配置

本文件是《全球算力市场情报日报（CMIS Daily）》的可变配置，允许经常调整。新增 GPU、模型、模块、图表或输出路径时，优先修改本文件；不要频繁修改 `system_prompt.md` 的数据治理底座。

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

GitHub 只作为静态页面托管和历史归档，不作为日报执行端。不得创建 `.github/workflows` 或 GitHub Actions 工作流。

## 2. 发布地址

- GitHub 仓库：`https://github.com/Gavinzll/compute-market-report.git`
- 首页：`https://gavinzll.github.io/compute-market-report/`
- 最新报告：`https://gavinzll.github.io/compute-market-report/latest.html`
- 历史报告：`https://gavinzll.github.io/compute-market-report/reports/{YYYY-MM-DD}.html`
- 飞书通知链接：`https://gavinzll.github.io/compute-market-report/latest.html?v={YYYYMMDDHHmm}`

敏感信息如 GitHub Token 和飞书 Webhook 不得写入本文件或任何仓库文件，只能由定时任务运行上下文提供。

## 3. 核心 GPU 覆盖

主流 GPU 至少覆盖：

- GB200
- B300
- B200
- H200
- H100 80G
- H800
- H20
- A100 80G
- A800
- L40S
- RTX 5090
- RTX 4090
- L20
- L4
- 昇腾 910C
- 昇腾 910B
- 寒武纪思元 MLU
- 海光 DCU
- 壁仞
- 摩尔线程

如果公开价格不可得，不得简单留空；应扩展搜索官方价、渠道价、整机拆算价、招投标价、公开市场价、行业报道和合理估算，并标注来源类型、置信度和是否参与指数。

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

所有列出的厂商和模型必须检索官方价格。官方价缺失时，保留模型行并标注 `Official Missing`，不得用市场价冒充官方价。

## 5. 报告模块

HTML 报告至少包含：

- 今日摘要
- Token 价格：Official vs Market
- 主要模型输入 Token 官方价对比图
- 主要模型输出 Token 官方价对比图
- 国内算力租赁
- 海外 GPU Cloud / 租赁
- 国内/海外价差参考
- GPU 采购价格
- GPU 利润测算
- GPU 供需监测
- AI 基础设施市场信号
- 主流算力卡 Top 10+ 覆盖表
- GPU 生命周期
- 历史趋势与走势图
- Rejected Samples / 数据审计摘要
- 价格、供需、利润异动提醒
- 数据源与口径说明
- AI 总结

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
- OpenRouter/替代市场输入价
- OpenRouter/替代市场输出价
- 官方-市场价差
- 较昨日变化
- 官方来源
- 市场来源
- 采集时间
- 置信度
- 校验状态
- 备注

租赁表格固定列：

- GPU 型号
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
- 最高价
- 最低价
- 中位价
- 库存/可用性
- 较昨日变化
- 近 7 日变化
- 国内/海外价格比例
- 口径说明
- 置信度
- 校验状态
- 备注

生命周期表格固定列：

- GPU 型号
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

ComputeStacker > RunPod > Lambda > Vast.ai > CoreWeave > Nebius/Crusoe/Oracle OCI > 其它 Marketplace

Token：

厂商官方价格页 / API 文档 > 云平台官方计费页 > 官方开发者文档 > OpenRouter / Artificial Analysis / 第三方市场价门户

采购价：

SMM 现货指数、英伟达代理渠道、整机厂商报价、招投标结果和公开渠道价格共同构成参考。非官方数据必须单独标注置信度。

## 8. 飞书摘要

飞书通知应短，不要粘贴完整报告。内容包括：

- 标题
- 日期
- 3-5 条核心摘要
- 关键异动
- AI 总结一句话
- 完整 HTML 报告链接

如果 GitHub 上传失败，也必须发送飞书失败提示，说明失败原因和建议，不得静默失败。

## 9. 运行约束

每次发布前先拉取远端 `main`，避免 push 冲突。推荐流程：

`git fetch origin main` → `git pull --rebase origin main` → 生成日报 → `git add` → `git commit` → `git push origin main`

不得把 GitHub Token、飞书 Webhook 或其它敏感信息写入仓库、HTML、数据文件、报告正文、飞书摘要或日志。
