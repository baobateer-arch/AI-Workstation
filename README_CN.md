[English](README.md) | [中文](README_CN.md)

# AI Workstation

## 项目介绍

AI Workstation 是一个面向 AI 开发者的本地工作站，将 Kindle 电子墨水屏变成 AI Agent 工作站控制中心。

当同时运行 Claude Code、Codex、MiMo 等多个编码 Agent 时，开发者需要快速了解 Agent 当前是否正在运行、是否需要授权、任务是否完成，以及剩余额度是否充足。AI Workstation 通过本地监控器采集状态，生成轻量级仪表盘，并将结果渲染为适合 Kindle 电子墨水屏阅读的图片。

项目核心在本地运行，Agent 状态、运行日志和仪表盘数据默认不会上传到本项目服务器。可选的余额监控功能在配置后会访问对应服务的官方 API。

## 功能特点

- Kindle 电子墨水屏 AI Agent 工作站
- Claude Code、Codex、MiMo 多 Agent 状态监控
- `RUNNING`、`IDLE`、`WAITING_APPROVAL`、`STOPPED` 状态识别
- `WAITING_APPROVAL` 权限等待检测
- Codex 5 小时 / 7 天额度监控
- DeepSeek 余额监控
- MiMo 余额监控
- CCSwitch 当前模型和 Provider 展示
- VPN 连接、节点和流量状态监控
- Kindle 黑白仪表盘图片渲染
- Windows 调度器和系统托盘启动
- 本地 JSON 状态文件和 PNG 图片输出

## 支持 Agent

### Claude Code

支持以下状态：

- `RUNNING`：近期存在 Agent 活动
- `IDLE`：进程存在但暂时没有近期活动
- `WAITING_APPROVAL`：等待工具或权限确认
- `STOPPED`：未检测到进程

### Codex

支持以下状态：

- `RUNNING`：存在存活进程、近期 rollout 事件或未完成任务
- `IDLE`：Codex 进程存在但没有近期任务活动
- `WAITING_APPROVAL`：存在未完成的工具授权请求
- `STOPPED`：未检测到运行进程或活动任务

同时支持 Codex 5 小时和 7 天额度信息展示。

### MiMo

支持以下状态：

- `RUNNING`
- `IDLE`
- `WAITING_APPROVAL`
- `STOPPED`

MiMo 状态主要读取本地 MiMo 数据库和工具执行记录。

## Kindle 展示效果

系统会生成适合电子墨水屏阅读的黑白仪表盘图片，展示 Agent 状态、额度、余额、运行提醒和当前工作信息。

![AI Workstation Kindle Dashboard](docs/images/dashboard.jpg)

截图资源位于 [`docs/images/`](docs/images/)。发布前请确认截图中不包含用户名、Token、私有路径或账户信息。

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

主要流程：

1. 监控器读取本地 Agent、服务和系统状态。
2. 状态管理器统一整理运行状态和资源信息。
3. Dashboard Builder 生成标准化数据。
4. Renderer 将数据渲染为 PNG 图片。
5. Kindle Server 或 Kindle 刷新脚本获取图片并显示。

## 安装运行

### 环境要求

- Windows 10 或更高版本
- Python 3.11 或更高版本
- 可选：已越狱并支持图片刷新脚本的 Kindle 设备

### 安装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 配置可选服务

复制环境变量示例：

```powershell
Copy-Item .env.example .env
```

根据需要配置：

```text
DEEPSEEK_API_KEY=your-api-key
MIMO_COOKIE=your-cookie
```

不要提交 `.env`，也不要在 README、截图、日志或 JSON 文件中保存真实密钥。

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
app/
  monitors/       Agent、额度、余额和 VPN 监控
  collectors/     本地事件和会话采集器
  core/           状态模型、聚合和 Dashboard 构建
  hooks/          Claude Hook 安装和事件处理
  renderer*.py    桌面与 Kindle 图片渲染器
  workstation.py  单次更新入口
  scheduler.py    周期调度器
  tray.py         Windows 托盘入口
config/           示例配置
scripts/          Windows 辅助脚本
docs/             架构、安装和开发文档
extensions/       Kindle 刷新扩展
data/             本地生成状态，已加入 Git 忽略
logs/             本地运行日志，已加入 Git 忽略
output/           生成图片，已加入 Git 忽略
```

## Roadmap

- [ ] 增加更多 Agent 客户端适配器
- [ ] 完善跨平台路径和进程检测
- [ ] 增加可配置的 Kindle 刷新间隔
- [ ] 增加更多额度和余额服务适配
- [ ] 增加本地历史趋势图
- [ ] 增加自动化测试和发布检查
- [ ] 优化不同 Kindle 分辨率的布局模板

## 开源协议

当前项目尚未添加正式开源协议。若要在 GitHub 上公开复用，请根据发布意图补充 MIT、Apache-2.0 或其他合适的 LICENSE 文件。在添加协议前，项目默认不授予明确的再发布或商业使用许可。