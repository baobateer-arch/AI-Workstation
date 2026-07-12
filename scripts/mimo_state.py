"""Investigate MiMo real-time state - Part table analysis."""
import sqlite3
from pathlib import Path
import json
from datetime import datetime

db_path = Path.home() / ".local" / "share" / "mimocode" / "mimocode.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print("=== 1. part 表 status 分布 ===")
rows = conn.execute("""
    SELECT
        json_extract(data, '$.state.status') as tool_status,
        COUNT(*) as cnt
    FROM part
    WHERE json_extract(data, '$.type') = 'tool'
    GROUP BY tool_status
""").fetchall()
for r in rows:
    print(f"  {r['tool_status']}: {r['cnt']}")

print("\n=== 2. 最近 10 分钟内的 part (tool 执行) ===")
ten_min_ago = int((datetime.now().timestamp() - 600) * 1000)
rows = conn.execute("""
    SELECT time_created, data
    FROM part
    WHERE time_created > ?
    ORDER BY time_created DESC
    LIMIT 20
""", (ten_min_ago,)).fetchall()
for r in rows:
    data = json.loads(r['data']) if r['data'] else {}
    ptype = data.get('type', '?')
    state = data.get('state', {})
    status = state.get('status', '?') if isinstance(state, dict) else '?'
    tool = data.get('tool', '?')
    ts = datetime.fromtimestamp(r['time_created']/1000).strftime('%H:%M:%S')
    print(f"  ts={ts} type={ptype} tool={tool} status={status}")

print("\n=== 3. 当前正在运行的 tool (status=running) ===")
rows = conn.execute("""
    SELECT time_created, data
    FROM part
    WHERE json_extract(data, '$.state.status') = 'running'
    ORDER BY time_created DESC
    LIMIT 5
""").fetchall()
if rows:
    for r in rows:
        data = json.loads(r['data']) if r['data'] else {}
        tool = data.get('tool', '?')
        ts = datetime.fromtimestamp(r['time_created']/1000).strftime('%H:%M:%S')
        elapsed = datetime.now().timestamp() - r['time_created']/1000
        print(f"  ts={ts} tool={tool} elapsed={int(elapsed)}s ago")
else:
    print("  No running tools found")

print("\n=== 4. message 表时间戳分析 ===")
# Check the most recent message's time_updated vs now
row = conn.execute("""
    SELECT time_created, time_updated
    FROM message
    ORDER BY time_created DESC
    LIMIT 1
""").fetchone()
if row:
    created = datetime.fromtimestamp(row['time_created']/1000)
    updated = datetime.fromtimestamp(row['time_updated']/1000)
    now = datetime.now()
    elapsed = (now - created).total_seconds()
    print(f"  Latest message created: {created.strftime('%H:%M:%S')} ({int(elapsed)}s ago)")
    print(f"  Latest message updated: {updated.strftime('%H:%M:%S')}")

print("\n=== 5. session.time_updated 分析 ===")
row = conn.execute("""
    SELECT id, time_updated
    FROM session
    WHERE id = 'ses_0ab1e4523ffeMSnrM3m8zJeuSS'
""").fetchone()
if row:
    updated = datetime.fromtimestamp(row['time_updated']/1000)
    now = datetime.now()
    elapsed = (now - updated).total_seconds()
    print(f"  Current session time_updated: {updated.strftime('%H:%M:%S')} ({int(elapsed)}s ago)")
    print(f"  Is recent (< 30s): {elapsed < 30}")

print("\n=== 6. 推荐检测方案总结 ===")
print("""
检测 MiMo RUNNING 的可靠方案:

方案 A (推荐): 查询 part 表
  SELECT COUNT(*) FROM part
  WHERE json_extract(data, '$.state.status') = 'running'
    AND time_created > (当前时间 - 30秒毫秒值)

  结果 > 0 → RUNNING
  结果 = 0 → IDLE

方案 B: 查询 session.time_updated
  SELECT time_updated FROM session WHERE id = '<current_session_id>'
  如果 time_updated 在 30 秒内 → 可能 RUNNING

方案 C: 查询 message 表最新时间
  SELECT time_created FROM message ORDER BY time_created DESC LIMIT 1
  如果 time_created 在 30 秒内 → 可能 RUNNING

最可靠: 方案 A (part 表的 status=running 是实时状态)
""")

conn.close()
