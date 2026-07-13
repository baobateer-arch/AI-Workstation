# 我把 Kindle 变成了 AI Agent 控制中心：从多窗口巡检到一眼可见

## 前言

当 AI 编程从一个聊天窗口变成多个 Agent 并行工作，开发者遇到的新问题不再只是“怎么写提示词”，而是“怎么知道它们现在在做什么”。

Claude Code 在执行修改，Codex 跑另一个任务，MiMo 处理工具调用。表面上算力在并行，人的注意力却在多个窗口之间串行切换。

我做了 AI Workstation，把一台旧 Kindle 变成 AI Agent 控制中心。

## 我真正想解决的问题

完整日志一直都在终端里。缺少的不是更多信息，而是一个持续可见的状态层：

- `RUNNING`：Agent 正在工作，可以继续做自己的事。
- `IDLE`：进程存在，但近期没有任务活动。
- `WAITING_APPROVAL`：需要人工确认，应该立即介入。
- `STOPPED`：任务或进程已停止，需要检查结果。

其中最关键的是 `WAITING_APPROVAL`。Agent 可能几分钟前就停在授权提示，用户却以为它还在工作。模型很快，但人机反馈环很慢。

## 为什么选择 Kindle

Kindle 的刷新速度不适合实时日志，却非常适合稳定状态。电子墨水屏低功耗、始终可见、不会播放动画，也不会变成新的消息中心。

这种限制反而帮助我控制信息密度：只显示会改变下一步行为的信息。

## 当前能力

AI Workstation 当前包括：

1. Claude Code Monitor
2. Codex Monitor
3. MiMo Monitor
4. Codex 5H / 7D quota
5. DeepSeek 与 MiMo balance
6. Kindle E-Ink Dashboard

项目在 Windows 本地运行，生成状态数据与仪表盘图片，再由 Kindle 显示。

## 从开源项目到可交付产品

代码能运行之后，我没有继续堆功能，而是补齐了官网、真实设备 Demo、服务价格、FAQ 和交付范围。

开源用户可以自行安装；不想处理环境和设备配置的用户可以选择 Personal Setup（¥299）；需要 Agent 分工、自动化和定制仪表盘的用户可以选择 Pro AI Workflow（¥999+）；团队与多设备场景通过 Enterprise 沟通。

## 适合谁

如果你只偶尔使用一个 Agent，可能不需要这块屏。如果你经常同时运行两个以上 Agent、执行长任务、容易错过授权请求，或者正好有一台闲置 Kindle，它会更有价值。

## 项目地址

产品 Demo：<https://baobateer-arch.github.io/AI-Workstation/>

GitHub：<https://github.com/baobateer-arch/AI-Workstation>

微信：Bao_Bateer_Benjamin
Email：bao.bateer@foxmail.com

欢迎讨论一个具体问题：如果只能在桌边常驻显示三项 AI Agent 信息，你会选择哪三项？

## 标签

#AI编程 #ClaudeCode #OpenAICodex #Kindle #电子墨水屏 #开源项目 #开发者效率

## 图片建议

首图使用真实 Kindle 与开发环境同框；正文加入状态模型示意图、数据流图和服务价格卡。
