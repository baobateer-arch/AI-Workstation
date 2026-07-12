
import json
from pathlib import Path
from datetime import datetime

def load_runtime():
    path = Path("data/agent_runtime.json")
    if not path.exists():
        return {}

    return json.loads(path.read_text(encoding="utf-8"))

def get_agents():
    data = load_runtime()

    defaults = {
        "claude": {"name":"Claude", "status":"IDLE", "message":""},
        "codex": {"name":"Codex", "status":"IDLE", "message":""},
        "mimo": {"name":"MiMo", "status":"IDLE", "message":""}
    }

    for k,v in data.items():
        key = k.lower()
        if "claude" in key:
            defaults["claude"].update(v)
        elif "codex" in key:
            defaults["codex"].update(v)
        elif "mimo" in key:
            defaults["mimo"].update(v)

    return list(defaults.values())

def runtime_text(start_time):
    try:
        start = datetime.fromisoformat(start_time)
        delta = datetime.now() - start
        return str(delta).split(".")[0]
    except:
        return "--:--:--"
