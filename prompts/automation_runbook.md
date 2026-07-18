# CMIS Daily 自动化运行说明

本文件用于定时任务执行端。定时任务正文应尽量短，只负责拉取仓库、读取本文件和其它 prompt 文件、运行、校验、推送、通知。

## 1. 执行入口

每次运行先进入仓库根目录，并执行：

1. `git fetch origin main`
2. `git pull --rebase origin main`
3. 读取：
   - `prompts/system_prompt.md`
   - `prompts/report_config.md`
   - `prompts/source_pool.md`
   - `prompts/automation_runbook.md`
4. 按上述规则完成当期数据采集、补采、校验和必要的脚本配置更新。
5. 运行 `python3 scripts/generate_cmis_daily.py` 生成报告。
6. 运行基础校验：
   - `node --check assets/charts.js`
   - 确认 `latest.html`、`latest-mobile.html`、`reports/{YYYY-MM-DD}.html`、`reports/{YYYY-MM-DD}-mobile.html` 已生成。
   - 搜索报告中不得出现 `null`、`Official Missing`、`海外三方未覆盖`、`境内三方待补采`、`无法计算`。
7. 提交并推送 GitHub main。
8. 通过飞书 webhook 发送成功或失败通知。**必须调用 `FEISHU_WEBHOOK=<webhook> python3 scripts/notify_feishu.py`**，由脚本从 `data/cmis_snapshot_{YYYY-MM-DD}.json` 自动提取关键价格并按 `report_config.md` 第 9 节飞书通知固定模板渲染。执行端 AI 不得自行用 curl 或手写方式编写含具体价格数字的飞书摘要，避免引用脚本硬编码配置中的过期值（如 DOMESTIC_RENTAL_INPUT 中的旧值）与实际报告页面不一致。脚本内部已实现：GPU 租赁从 domestic_rental 的 PASS 样本提取标准化价格；GPU 采购从 gpu_procurement 提取采购价中位数；Token 价格从 token_prices 的 PASS 样本提取官方价；AI 一句话基于 PASS 且 Consensus 非 Low 的数据生成。若脚本执行失败，才允许执行端按 `report_config.md` 失败模板手写失败原因和修复建议（不得包含具体价格数字）。

## 2. 运行边界

- 不创建 GitHub Actions 或 `.github/workflows`。
- 不把 GitHub Token、飞书 Webhook 或其它敏感信息写入仓库文件、HTML、数据文件、日志或报告正文。
- Git 上传凭据只能通过临时环境变量、`GIT_ASKPASS`、stdin 或等效方式使用。
- `README.md` 是人工维护文件。本次 README 更新后，除非 Gavin YszY 明确下达人工命令，否则定时任务和常规日报更新不得修改 `README.md`。
- 如果采集阶段触达单次会话上限，优先保证已完成的数据校验和页面生成，不得输出半成品；同时在飞书通知中说明未完成阶段和下一步修复建议。

## 3. 成功标准

当次运行至少应完成：

- 生成桌面版和手机版最新报告。
- 生成当日历史归档。
- 更新 `data/` 下 snapshot、audit、rejected、history。
- Token 六个核心价格字段全部为数值。
- 国内 GPU 主指数、海外 GPU Cloud、Rejected / Review、Token、采购价和利润测算模块均可正常渲染。
- GitHub Pages 链接可通过 cache-busting 参数访问最新版本。

## 4. SPA 数据源每日抓取（国产卡单卡云价）

以下网站为 JS 动态渲染（SPA），`urllib` 无法抓取。每日运行时需通过 MCP 浏览器工具抓取后写入 JSON 缓存文件，供 `discover_latest.py` 读取。

### 4.1 胜算云

- **URL**: `https://www.shengsuanyun.com/hashrate`
- **浏览器抓取步骤**:
  1. 用 MCP 浏览器导航到 URL
  2. 获取页面 snapshot 或 evaluate JS 提取文本
  3. 提取所有 GPU 型号和对应时价（格式：`型号 ¥X.XX / 小时`）
  4. 重点关注：天垓100、摩尔线程 MTT S4000、华为 Ascend 910
- **写入文件**: `data/shengsuanyun_{DATE}.json`
- **格式**: `{"scraped_at": "2026-07-15", "prices": {"壁仞 天垓100": {"hourly_cny": 1.49, "source": "胜算云"}, ...}}`
- **回退**: 若抓取失败，使用 `discover_latest.py` 中的硬编码 fallback（最后验证日期 2026-07-15）

### 4.2 模力方舟（Gitee AI）

- **URL**: `https://ai.gitee.com/compute`
- **浏览器抓取步骤**:
  1. 用 MCP 浏览器导航到 URL
  2. 翻页检查第 1-4 页（每页约 6-8 款 GPU）
  3. 提取所有国产 GPU 型号和对应时价
  4. 重点关注：海光 BW1000、摩尔线程 MTT S5000、壁仞 天垓150、壁仞 壁砺106M、天数智芯 智铠100、燧原 S60、昇腾 910B
- **写入文件**: `data/gitee_ai_{DATE}.json`
- **格式**: `{"scraped_at": "2026-07-15", "prices": {"海光 BW1000": {"hourly_cny": 3.00, "source": "模力方舟"}, ...}}`
- **回退**: 若抓取失败，使用 `discover_latest.py` 中的硬编码 fallback（最后验证日期 2026-07-15）

### 4.3 折算公式

单卡时价抓取后，`discover_latest.py` 自动按以下公式折算为 8 卡整机参考月租：

```
参考价(万/月) = 单卡时价(元) × 8卡 × 24时 × 30天 × 0.7(长协折扣系数) ÷ 10000
```

其中 0.7 为长协折扣系数，反映云实例含虚拟化加价，批量裸金属长协价通常比云零售价低 30-40%。
