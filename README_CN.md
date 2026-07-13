[English](README.md) | [中文](README_CN.md)

# AI Workstation

把 Kindle 变成 AI Agent 控制中心。

![AI Workstation Kindle Dashboard](docs/images/dashboard.jpg)

AI Workstation 是一套面向多 Agent 工作流的本地仪表盘。它把闲置 Kindle 电子墨水屏变成安静、低功耗、始终可见的状态屏，用于查看 Claude Code、OpenAI Codex 和 MiMo Code 的工作情况。

## 产品介绍

当多个 AI Agent 同时工作时，用户很容易错过任务完成、授权请求或资源不足提醒。AI Workstation 将关键状态集中到一块屏幕上，减少窗口切换，让你更快判断下一步该关注什么。

### AI Agent Monitoring

支持 Claude Code、OpenAI Codex、MiMo Code，并展示：

- `RUNNING`
- `IDLE`
- `WAITING_APPROVAL`
- `STOPPED`

### Resource Tracking

支持展示：

- Codex 5H quota
- Codex 7D quota
- DeepSeek balance
- MiMo balance

### E-Ink Dashboard

- Kindle e-ink display
- Low power
- Always visible

## Demo 说明

欢迎查看[产品官网](https://baobateer-arch.github.io/AI-Workstation/)，了解产品定位、真实设备展示、核心模块、服务价格和联系方式。上方仪表盘截图用于展示产品形态，仓库不包含个人运行时数据。

截图展示的是面向 Kindle 优化的高对比仪表盘布局。公开 Demo 图片已做隐私检查，不包含用户名、Token、私有路径、账户标识或实时订阅信息。

## 服务入口

如果你希望获得安装或工作流配置支持：

- **Personal Setup — ¥299**：AI Workstation installation、Kindle dashboard setup、Agent environment configuration。
- **Pro AI Workflow — ¥999+**：AI Agent workflow design、Automation setup、Custom dashboard。
- **Enterprise — Contact**：团队、多设备和定制化交付支持。

查看[服务价格](docs/business/service_pricing.md)或[客户一页介绍](docs/business/sales_one_page.md)。

服务联系方式：

- 微信：`Bao_Bateer_Benjamin`
- 邮箱：`bao.bateer@foxmail.com`

## 系统架构

```text
Agent
  |
  v
Monitor
  |
  v
Dashboard JSON
  |
  v
Renderer
  |
  v
Kindle
```

调度器会周期性执行工作站更新，写入本地仪表盘状态，生成 PNG 图片，并可通过 HTTP 为 Kindle 刷新脚本提供图片。

## 安装运行

### 环境要求

- Windows 10 或更高版本
- Python 3.11 或更高版本
- 可选：支持图片刷新的 Kindle 设备

### 安装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 配置可选服务

```powershell
Copy-Item .env.example .env
```

根据需要填写可选服务配置。不要提交 `.env`，也不要在 README、截图、日志或 JSON 文件中保存真实密钥、Cookie 或 Token。

### 运行一次更新

```powershell
python -m app.workstation
```

### 生成仪表盘图片

```powershell
python -m app.main
```

### 启动调度器和 Kindle 服务

```powershell
python -m app.scheduler
python -m app.kindle_server
```

Windows 托盘启动：

```powershell
python -m app.tray
```

## 项目结构

```text
app/              核心应用和监控逻辑
config/           示例配置
docs/             产品、安装、商业和开发文档
extensions/       Kindle 刷新扩展
scripts/          Windows 辅助脚本
data/             本地生成状态，已加入 Git 忽略
logs/             本地运行日志，已加入 Git 忽略
output/           生成图片，已加入 Git 忽略
```

## 隐私与安全

项目以本地运行作为设计方向。发布或分享截图前，请确认材料中没有 `.env`、API Key、Cookie、Bearer Token、私有路径、账户标识和本地运行时数据。

## 客户资料

- [销售一页介绍](docs/business/sales_one_page.md)
- [服务价格说明](docs/business/service_pricing.md)
- [客户介绍稿](docs/business/customer_pitch.md)
- [客户 FAQ](docs/business/faq.md)
- [商业路线](docs/ROADMAP_COMMERCIAL.md)

## Roadmap

- **v0.1**：当前本地开源仪表盘与安装服务。
- **v0.2**：优化首次使用、恢复引导和产品 Demo。
- **v1.0**：一键部署、Web 控制台、多设备支持和企业管理。

完整规划见[商业路线](docs/ROADMAP_COMMERCIAL.md)。

## 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。
