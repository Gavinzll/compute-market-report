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
8. 通过飞书 webhook 发送成功或失败通知。

## 2. 运行边界

- 不创建 GitHub Actions 或 `.github/workflows`。
- 不把 GitHub Token、飞书 Webhook 或其它敏感信息写入仓库文件、HTML、数据文件、日志或报告正文。
- Git 上传凭据只能通过临时环境变量、`GIT_ASKPASS`、stdin 或等效方式使用。
- 如果采集阶段触达单次会话上限，优先保证已完成的数据校验和页面生成，不得输出半成品；同时在飞书通知中说明未完成阶段和下一步修复建议。

## 3. 成功标准

当次运行至少应完成：

- 生成桌面版和手机版最新报告。
- 生成当日历史归档。
- 更新 `data/` 下 snapshot、audit、rejected、history。
- Token 六个核心价格字段全部为数值。
- 国内 GPU 主指数、海外 GPU Cloud、Rejected / Review、Token、采购价和利润测算模块均可正常渲染。
- GitHub Pages 链接可通过 cache-busting 参数访问最新版本。

