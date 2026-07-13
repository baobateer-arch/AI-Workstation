[中文](README_CN.md) | [English](README.md)

# AI Workstation

Turn your Kindle into an AI Agent Command Center.

![AI Workstation Kindle Dashboard](docs/images/dashboard.jpg)

AI Workstation is a local dashboard for people who run multiple AI coding agents. It turns an idle Kindle e-ink display into a quiet, low-power status screen for Claude Code, OpenAI Codex, and MiMo Code.

## Product overview

When several agents work at the same time, it is easy to miss a completed task, an approval request, or a resource limit. AI Workstation brings the important signals into one always-visible view, so you can spend less time switching windows and more time working.

### AI Agent Monitoring

Supports Claude Code, OpenAI Codex, and MiMo Code with these user-facing states:

- `RUNNING`
- `IDLE`
- `WAITING_APPROVAL`
- `STOPPED`

### Resource Tracking

The dashboard can present:

- Codex 5H quota
- Codex 7D quota
- DeepSeek balance
- MiMo balance

### E-Ink Dashboard

- Kindle e-ink display
- Low power
- Always visible

## Demo

See the [live product page](https://baobateer-arch.github.io/AI-Workstation/) for the product story, real-device image, core modules, service packages, and contact details. The dashboard image above is a representative visual demo; local runtime data is not included in the repository.

The screenshot shows the Kindle-oriented, high-contrast dashboard layout. Public demo images are sanitized and do not include usernames, tokens, private paths, account identifiers, or live subscription details.

## Service entry

For customers who want help getting started:

- **Personal Setup — ¥299**: AI Workstation installation, Kindle dashboard setup, Agent environment configuration.
- **Pro AI Workflow — ¥999+**: AI Agent workflow design, Automation setup, Custom dashboard.
- **Enterprise — Contact**: team, multi-device, and tailored delivery support.

See [service pricing](docs/business/service_pricing.md) or [the customer one-pager](docs/business/sales_one_page.md).

Setup service contact:

- WeChat: `Bao_Bateer_Benjamin`
- Email: `bao.bateer@foxmail.com`

## Architecture

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

The scheduler periodically runs a workstation update, writes local dashboard state, renders PNG output, and can serve the image over HTTP for a Kindle refresh script.

## Project layout

```text
app/              core application and monitors
config/           example configuration files
docs/             product, setup, business, and development docs
extensions/       Kindle refresh extension scripts
scripts/          Windows helper scripts
data/             local generated state; ignored by Git
logs/             local runtime logs; ignored by Git
output/           generated images; ignored by Git
```

## Installation

The supported development environment is Windows with Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Optional integrations use environment variables. Copy `.env.example` to `.env` and fill in only the services you use. Never commit `.env`, credentials, cookies, or tokens.

## Running

Run one dashboard update:

```powershell
python -m app.workstation
```

Render dashboard images:

```powershell
python -m app.main
```

Start the periodic scheduler:

```powershell
python -m app.scheduler
```

Start the Kindle image server or Windows tray launcher when needed:

```powershell
python -m app.kindle_server
python -m app.tray
```

`run.bat`, `start.bat`, and `scripts/start_workstation.bat` provide Windows shortcuts for common flows.

## Privacy and security

The project is designed for local operation. Before publishing or sharing a screenshot, remove `.env`, API keys, cookies, bearer tokens, private paths, account identifiers, and generated runtime data from the material being shared.

## More customer materials

- [Sales one-pager](docs/business/sales_one_page.md)
- [Service pricing](docs/business/service_pricing.md)
- [Customer pitch](docs/business/customer_pitch.md)
- [FAQ](docs/business/faq.md)
- [Commercial roadmap](docs/ROADMAP_COMMERCIAL.md)

## Roadmap

- **v0.1** — current local open-source dashboard and setup service.
- **v0.2** — easier onboarding, clearer recovery guidance, and richer demos.
- **v1.0** — one-click deployment, web console, multi-device support, and enterprise management.

See the complete [commercial roadmap](docs/ROADMAP_COMMERCIAL.md).

## License

This project is released under the [MIT License](LICENSE).
