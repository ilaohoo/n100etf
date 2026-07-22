# NASDAQ-100 每日复盘推送

自动抓取纳斯达克100前50权重股新闻，使用 DeepSeek AI 生成详细复盘报告，并通过 PushPlus 推送到微信。

## 功能特点
- 每日北京时间 08:00 自动执行（GitHub Actions）
- 抓取前50大权重股的最新新闻（RSS 源）
- 结合指数涨跌幅生成专业分析报告
- 支持手动触发工作流

## 配置步骤

### 1. Fork 本仓库

### 2. 添加 GitHub Secrets
进入仓库 Settings → Secrets and variables → Actions，添加以下 secrets：
- `DEEPSEEK_API_KEY`：你的 DeepSeek API Key
- `PUSHPULUS_TOKEN`：你的 PushPlus Token

### 3. 可选修改
- 编辑 `config.yaml` 更新股票列表或 RSS 源地址
- 调整 `max_news_per_ticker` 控制新闻数量

### 4. 手动运行
在 Actions 页面选择 `Daily NASDAQ-100 Report`，点击 "Run workflow"。

## 依赖
见 `requirements.txt`，在 GitHub Actions 中自动安装。

## 推送示例
报告以 Markdown 格式推送，包含指数分析、重点事件和前瞻。

## 注意事项
- RSS 源使用 Google News，国内网络可能需代理，可更换为 RSSHub 镜像。
- 若某只股票无新闻，会自动跳过。
- 日志保存在 `logs/` 目录，可作为 artifact 下载。
