# What does personal observability look like for multiple coding agents?

## Body

Production systems have dashboards, but personal AI workflows often rely on manually checking terminals. Once I started running Claude Code, Codex, and MiMo Code in parallel, I wanted a tiny observability layer for my own desk.

My current model is intentionally simple:

- RUNNING
- IDLE
- WAITING_APPROVAL
- STOPPED

I also surface Codex 5H / 7D quota and selected balances. The output is rendered for a Kindle e-ink display, so the dashboard favors durable state over high-frequency telemetry.

This is not meant to replace logs or debugging. It answers one operational question: “Do I need to look at an agent right now?”

What state model would you use for a personal multi-agent dashboard?

## Tags

observability, AI agents, coding agents, local dashboard, e-ink

## Image suggestion

A diagram from three agents into one compact dashboard, followed by a photo of the physical display.
