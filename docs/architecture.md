# Architecture

## Overview

AI Workstation is a local, file-oriented monitoring and rendering pipeline. It does not require a central server for its core dashboard flow.

```text
Local agent state
      │
      ▼
Collectors and monitors
      │
      ▼
State manager / dashboard builder
      │
      ▼
data/dashboard.json
      │
      ▼
PNG renderers and Kindle server
      │
      ▼
Kindle e-ink display
```

## Main Components

### Agent and service monitors

- `agent_health_checker.py` combines process and local event evidence for Claude, Codex, and MiMo status.
- `codex_usage_monitor.py` reads Codex quota information from local session data.
- `deepseek_balance_monitor.py` optionally calls the DeepSeek balance API using `DEEPSEEK_API_KEY`.
- `mimo_balance_monitor.py` optionally calls the MiMo balance API using `MIMO_COOKIE`.
- `vpn_monitor.py` reads local v2rayN state and reports connection, node, routing, traffic, and expiry details.
- `cc_switch_reader.py` reads the current Claude provider/model from the local CCSwitch database.

### State and orchestration

- `app/workstation.py` performs one complete update cycle.
- `app/scheduler.py` repeats the update cycle at a fixed interval.
- `app/core/state_manager.py` owns the local workstation state model.
- `app/core/dashboard_builder.py` converts state into dashboard data.
- `app/tray.py` starts the scheduler and Kindle server from the Windows notification area.

### Rendering and delivery

- `app/main.py` renders the primary dashboard and Agent status PNGs.
- `app/kindle_renderer.py` renders the Kindle-oriented image.
- `app/kindle_server.py` serves the generated image to a local network client.
- `extensions/AIWorkstation/` contains Kindle-side refresh scripts.

## Runtime Data

Runtime state is intentionally local and ignored by Git:

- `data/*.json` and `data/*.jsonl`: generated state and event history.
- `logs/`: local monitor and hook logs.
- `output/`: generated PNG images.
- SQLite files: local integration databases or caches.

The public repository should contain source code and examples, not these runtime artifacts.

## Status Model

Each Agent is represented by a status and a short message. The public status vocabulary is `RUNNING`, `IDLE`, `WAITING_APPROVAL`, and `STOPPED`. Status detection uses local process records, event files, hooks, and the MiMo database depending on the Agent.

The Agent status and VPN logic are deliberately isolated from the rendering layer. Renderers consume normalized state and should not reach into external agent databases directly.

## Optional Integrations

External services are optional. The dashboard remains useful when a provider is not configured. Credentials are loaded from environment variables and must never be written into generated JSON, logs, screenshots, or source files.