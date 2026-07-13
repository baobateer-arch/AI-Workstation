# Claude Code Waiting for Approval：如何减少人机协作中的空等

> SEO description：了解 Claude Code 等待授权为什么容易被忽略，以及如何设计清晰的 human-in-the-loop 提醒。

工具授权是 AI 编程工作流中的必要安全边界。但授权提示如果只存在于某个被遮挡的终端窗口，就会成为隐形等待队列。

## 空等是怎样发生的

开发者启动一个较长任务后转去处理其他工作。Agent 运行几分钟后请求工具权限，任务暂停。开发者没有收到合适的信号，直到下一次主动检查才发现。

这不是模型速度问题，而是 human-in-the-loop 设计问题。系统已经知道它需要人，但这个状态没有在人的注意力边缘持续存在。

## 一个更简单的提醒方式

把 `WAITING_APPROVAL` 作为独立状态，并在低干扰屏幕上持续显示。与一次性弹窗相比，持续状态不容易因为短暂离开而错过；与声音通知相比，它也不会打断不相关的工作。

AI Workstation 用 Kindle 呈现这一状态，并同时显示 RUNNING、IDLE 和 STOPPED。用户看到授权等待后再回到终端处理，完成后屏幕恢复正常状态。

## 不要过度自动化授权

减少等待不等于取消安全确认。更合理的目标是让审批在需要的时候及时到达人，而不是默认批准高风险操作。

关键词：Claude Code waiting for approval、Claude Code permission、human in the loop、AI Agent approval、开发者效率
