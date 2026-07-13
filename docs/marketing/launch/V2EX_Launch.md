# V2EX 发布文案

## 标题

[分享创造] 把旧 Kindle 做成 Claude Code / Codex / MiMo 状态屏，开源了

## 正文

最近同时使用 Claude Code、Codex 和 MiMo Code 时，我遇到一个很小但很烦的问题：需要不停切终端确认 Agent 是还在跑、已经完成，还是停在等待授权。

于是做了 AI Workstation，把旧 Kindle 变成一块低功耗、始终可见的 AI Agent 控制中心。

目前展示：

- Claude Code Monitor
- Codex Monitor
- MiMo Monitor
- `RUNNING` / `IDLE` / `WAITING_APPROVAL` / `STOPPED`
- Codex 5H / 7D quota
- DeepSeek / MiMo balance
- Kindle 电子墨水仪表盘

项目以 Windows 本地工作流为主，状态和渲染结果留在本机。Kindle 不用来显示完整日志，只负责提示“现在是否需要人工介入”。

Demo：<https://baobateer-arch.github.io/AI-Workstation/>

GitHub：<https://github.com/baobateer-arch/AI-Workstation>

代码开源；同时提供可选的 Personal Setup（¥299）和多 Agent 工作流定制服务。商业部分直接说明，避免造成软广误解。

想请教大家：如果你同时跑多个编码 Agent，最希望常驻显示的是任务状态、待授权提醒、完成提醒，还是额度？

## 标签

Kindle、AI、Claude Code、Codex、开源项目、分享创造

## 图片建议

正文只放一张真实 Kindle 实拍和一张屏幕近景，确保遮挡用户名、额度账号和私有路径。
