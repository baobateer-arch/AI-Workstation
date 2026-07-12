# Development

## Development Principles

- Keep monitor logic separate from renderers.
- Keep runtime state local and out of source control.
- Use environment variables for credentials.
- Prefer small, focused changes that preserve the existing Windows and Kindle workflows.
- Do not add provider-specific secrets, account identifiers, or private paths to examples.

## Update Flow

A normal update follows this sequence:

1. `app/workstation.py` calls the Agent health checker.
2. Resource monitors refresh optional quota, balance, model, and VPN data.
3. The state manager persists local runtime state.
4. The dashboard builder creates normalized dashboard JSON.
5. Renderers produce PNG files for the desktop and Kindle.
6. The Kindle server or Kindle extension retrieves the generated image.

## Useful Commands

```powershell
# Syntax check
python -m compileall app

# One-shot update
python -m app.workstation

# Standalone render
python -m app.main

# Scheduler
python -m app.scheduler
```

There is no committed automated test suite yet. When changing a monitor, validate both the positive and negative states and confirm that optional integrations still return a safe `NOT_CONFIGURED` or `DISCONNECTED` result when their local source is absent.

## Boundaries

The following modules are operational boundaries and should be changed only with explicit behavioral tests:

- `app/monitors/agent_health_checker.py`
- `app/monitors/codex_usage_monitor.py`
- `app/scheduler.py`
- `app/kindle_renderer.py`
- `app/monitors/vpn_monitor.py`

Changes to status detection, quota parsing, scheduling, VPN data access, or Kindle layout can affect both the local dashboard and the e-ink device.

## Pull Requests

A useful change description should include:

- What changed and why
- Which local data sources were used
- How the change was tested
- Whether generated files were intentionally refreshed
- Confirmation that no credentials or personal paths were added

Do not push directly from an automated cleanup task. Review the staged file list locally before creating a commit or opening a pull request.