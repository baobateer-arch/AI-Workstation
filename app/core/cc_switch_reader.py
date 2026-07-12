"""CC Switch 数据库读取器。"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


# CC Switch 数据库路径
CC_SWITCH_DB = Path.home() / ".cc-switch" / "cc-switch.db"


def read_cc_model_info() -> dict[str, str]:
    """从 CC Switch 数据库读取当前 Claude Code 模型信息。

    Returns:
        {"provider": "Xiaomi MiMo", "model": "mimo-v2.5-pro"}
    """
    result = {"provider": "", "model": ""}

    if not CC_SWITCH_DB.exists():
        return result

    try:
        conn = sqlite3.connect(str(CC_SWITCH_DB))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, settings_config FROM providers "
            "WHERE app_type='claude' AND is_current=1"
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            result["provider"] = row[0] or ""
            try:
                config = json.loads(row[1] or "{}")
                env = config.get("env", {})
                result["model"] = env.get("ANTHROPIC_MODEL", "")
            except (json.JSONDecodeError, TypeError):
                pass
    except Exception:
        pass

    return result
