# Setup

## Requirements

- Windows 10 or newer
- Python 3.11+
- A Kindle e-ink device with a compatible local refresh method, if Kindle delivery is required
- Optional: Claude Code, Codex Desktop, MiMo Code, CCSwitch, DeepSeek, or v2rayN integrations

## Install

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configure Optional Services

Create a local `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Set only the values needed by the integrations you use:

```text
DEEPSEEK_API_KEY=your-key
MIMO_COOKIE=your-cookie
```

Do not put Codex, Claude, CCSwitch, VPN, or other account tokens in project files. The monitors read their supported local application state from the user profile.

## First Run

Generate a single update and inspect the console output:

```powershell
python -m app.workstation
```

Render the standalone images:

```powershell
python -m app.main
```

Generated state is written under `data/`; generated images are written under `output/`. Both are local-only and ignored by Git.

## Scheduler and Kindle Server

For a continuously refreshed dashboard:

```powershell
python -m app.scheduler
```

To serve the Kindle image on the local network:

```powershell
python -m app.kindle_server
```

The Windows tray launcher can start both services:

```powershell
python -m app.tray
```

The `extensions/AIWorkstation/` scripts can be copied to a jailbroken Kindle and configured with the workstation URL and target image path on the device. Review those values for your own network before deployment.

## Troubleshooting

- `NOT_CONFIGURED` means the optional environment variable is missing.
- `DISCONNECTED` means the local VPN application or database is unavailable.
- `STOPPED` means no supported Agent process or active local event was found.
- If images are stale, run `python -m app.workstation` once and inspect `data/` and `output/` locally.
- If Windows blocks a script, run it from an activated Python environment and check the current working directory.

## Security Checklist

Before sharing the project:

1. Remove or keep untracked `.env`.
2. Confirm `data/`, `logs/`, `output/`, SQLite files, and JSONL logs are ignored.
3. Search the staged file list for usernames, absolute paths, keys, cookies, and VPN URLs.
4. Review screenshots manually before placing them in `docs/images/`.