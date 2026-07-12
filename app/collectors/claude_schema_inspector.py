"""Claude Session Schema Inspector - 分析 session 文件字段结构。"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Claude 数据目录
CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
SESSIONS_DIR = CLAUDE_DIR / "sessions"

# 最大扫描文件数
MAX_FILES = 100

# 敏感字段（禁止输出）
SENSITIVE_FIELDS = {
    "message", "content", "prompt", "input", "output",
    "text", "body", "data", "key", "token", "secret",
    "api_key", "apikey", "authorization",
}


def _scan_files(directory: Path, max_files: int = MAX_FILES) -> list[Path]:
    """扫描目录下的 json/jsonl 文件"""
    files = []
    if not directory.exists():
        return files

    try:
        for item in directory.rglob("*"):
            if item.is_file() and item.suffix in (".json", ".jsonl"):
                files.append(item)
                if len(files) >= max_files:
                    break
    except Exception:
        pass

    return files


def _extract_keys(obj: Any, prefix: str = "", depth: int = 0) -> set[str]:
    """递归提取所有键名"""
    keys = set()
    if depth > 5:
        return keys

    if isinstance(obj, dict):
        for k, v in obj.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.add(full_key)
            keys.update(_extract_keys(v, full_key, depth + 1))
    elif isinstance(obj, list) and obj:
        keys.update(_extract_keys(obj[0], f"{prefix}[]", depth + 1))

    return keys


def _is_token_field(key: str) -> bool:
    """判断是否是 token 相关字段"""
    key_lower = key.lower()
    token_indicators = ["token", "usage", "input", "output", "prompt", "completion"]
    return any(indicator in key_lower for indicator in token_indicators)


def _is_cost_field(key: str) -> bool:
    """判断是否是 cost 相关字段"""
    key_lower = key.lower()
    cost_indicators = ["cost", "price", "charge", "billing", "fee"]
    return any(indicator in key_lower for indicator in cost_indicators)


def _is_sensitive(key: str) -> bool:
    """判断是否是敏感字段"""
    key_lower = key.lower()
    return any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS)


class ClaudeSchemaInspector:
    """Claude Session Schema Inspector"""

    def __init__(self):
        self._files_scanned = 0
        self._token_fields: set[str] = set()
        self._cost_fields: set[str] = set()
        self._all_keys: set[str] = set()
        self._example_keys: list[str] = []

    def inspect(self) -> dict[str, Any]:
        """
        扫描并分析 session 文件结构。

        Returns:
            分析结果
        """
        # 扫描文件
        files = []
        files.extend(_scan_files(PROJECTS_DIR, MAX_FILES))
        files.extend(_scan_files(SESSIONS_DIR, MAX_FILES))

        self._files_scanned = len(files)

        # 分析每个文件
        for file_path in files:
            try:
                self._analyze_file(file_path)
            except Exception:
                continue

        # 过滤敏感字段
        self._token_fields = {k for k in self._token_fields if not _is_sensitive(k)}
        self._cost_fields = {k for k in self._cost_fields if not _is_sensitive(k)}
        self._all_keys = {k for k in self._all_keys if not _is_sensitive(k)}

        # 提取示例键
        self._example_keys = sorted(list(self._all_keys))[:20]

        return {
            "files_scanned": self._files_scanned,
            "token_fields": sorted(list(self._token_fields)),
            "cost_fields": sorted(list(self._cost_fields)),
            "example_keys": self._example_keys,
        }

    def _analyze_file(self, file_path: Path) -> None:
        """分析单个文件"""
        if file_path.suffix == ".jsonl":
            self._analyze_jsonl(file_path)
        elif file_path.suffix == ".json":
            self._analyze_json(file_path)

    def _analyze_jsonl(self, file_path: Path) -> None:
        """分析 JSONL 文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= 10:  # 每个文件最多分析10行
                        break
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            self._analyze_entry(entry)
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass

    def _analyze_json(self, file_path: Path) -> None:
        """分析 JSON 文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                for entry in data[:10]:
                    self._analyze_entry(entry)
            elif isinstance(data, dict):
                self._analyze_entry(data)
        except Exception:
            pass

    def _analyze_entry(self, entry: Any) -> None:
        """分析单条记录"""
        keys = _extract_keys(entry)
        self._all_keys.update(keys)

        # 分类字段
        for key in keys:
            if _is_token_field(key):
                self._token_fields.add(key)
            if _is_cost_field(key):
                self._cost_fields.add(key)


# 全局检查器实例
claude_schema_inspector = ClaudeSchemaInspector()


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== Claude Schema Inspector ===")
    print()

    inspector = ClaudeSchemaInspector()
    result = inspector.inspect()

    print(f"Files scanned: {result['files_scanned']}")
    print()
    print("Found token fields:")
    for field in result['token_fields']:
        print(f"  - {field}")
    print()
    print("Found cost fields:")
    for field in result['cost_fields']:
        print(f"  - {field}")
    print()
    print("Example keys:")
    print("[")
    for key in result['example_keys']:
        print(f"  {key},")
    print("]")


if __name__ == "__main__":
    main()
