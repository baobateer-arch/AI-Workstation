"""Render dashboard.json as a high-contrast Kindle AI workstation page."""

from datetime import datetime
import json
import os
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont

from app.monitors.vpn_monitor import read_vpn_status


WIDTH, HEIGHT = 1072, 1448
MARGIN = 60
BLACK = 0
WHITE = 255
MID = 120
LIGHT = 200


def get_font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_text(draw, xy, text, size=32, bold=False, fill=BLACK, anchor=None):
    draw.text(xy, str(text), font=get_font(size, bold), fill=fill, anchor=anchor)


def draw_right(draw, right, y, text, size=32, bold=False, fill=BLACK):
    draw_text(draw, (right, y), text, size, bold, fill, anchor="ra")


def clean_text(value):
    """Repair known mojibake fragments in older dashboard snapshots."""
    text = str(value or "")
    replacements = {
        "灏忔椂": "小时",
        "鍒嗛挓": "分钟",
        "浣欓": "余额",
        "鍓╀綑棰濆害": "剩余额度",
        "娲昏穬": "活跃",
        "娲诲姩": "活动",
        "浼氳瘽": "会话",
        "璋冪敤": "调用",
        "楼": "¥",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.strip()


def percent_from(*values):
    for value in values:
        match = re.search(r"(\d+(?:\.\d+)?)\s*%", clean_text(value))
        if match:
            return float(match.group(1))
    return None


def resource_for(resources, name):
    name = name.lower()
    for resource in resources:
        title = clean_text(resource.get("title", "")).lower()
        if name in title:
            return resource
    return {}


def money_text(value):
    text = clean_text(value)
    if not text:
        return "—"
    if text.startswith("¥"):
        return text
    return f"¥{text}"


def first_time(value):
    match = re.search(r"([01]?\d|2[0-3]):[0-5]\d", clean_text(value))
    return match.group(0) if match else None


def secondary_detail(resource):
    """Return useful provider detail without repeating a balance."""
    detail = clean_text(resource.get("detail", ""))
    value = clean_text(resource.get("value", ""))
    if not detail or detail == value:
        return ""
    if "余额" in detail and re.search(r"\d", detail):
        return ""
    return detail


def today_spend(resource):
    detail = clean_text(resource.get("detail", ""))
    match = re.search(r"今日消耗\s*[:：]?\s*(¥?\s*[\d.]+)", detail)
    return money_text(match.group(1).replace(" ", "")) if match else "—"


def number_after(text, label):
    cleaned = clean_text(text)
    match = re.search(r"(\d+(?:\.\d+)?)\s*" + re.escape(label), cleaned)
    if match:
        return match.group(1)
    match = re.search(re.escape(label) + r"\s*(\d+(?:\.\d+)?)", cleaned)
    if match:
        return match.group(1)
    return "—"


def draw_rule(draw, y):
    draw.line((MARGIN, y, WIDTH - MARGIN, y), fill=BLACK, width=3)


def draw_inline_metric(draw, x, y, label, value, value_size=31):
    draw_text(draw, (x, y), label, size=21, bold=True, fill=MID)
    draw_text(draw, (x, y + 33), value, size=value_size, bold=True)


def draw_agent_cards(draw, dashboard):
    draw_text(draw, (MARGIN, 154), "AGENTS", size=27, bold=True)
    card_y, card_h, gap = 202, 180, 18
    card_w = (WIDTH - MARGIN * 2 - gap * 2) // 3
    agents = {str(a.get("name", "")): a for a in dashboard.get("agents", [])}

    for index, name in enumerate(("Claude", "Codex", "MiMo")):
        agent = agents.get(name, {})
        x = MARGIN + index * (card_w + gap)
        attention = bool(agent.get("attention", False))
        raw = clean_text(agent.get("status", "IDLE")).upper()
        last_activity = clean_text(agent.get("last_activity", ""))

        # STOPPED 状态：灰色文字，无背景填充
        if raw == "STOPPED":
            fg = MID
            draw.rectangle(
                (x, card_y, x + card_w, card_y + card_h),
                fill=WHITE,
                outline=MID,
                width=2,
            )
            draw_text(draw, (x + 22, card_y + 22), name, size=35, bold=True, fill=fg)
            draw_text(draw, (x + 22, card_y + 88), "● OFF", size=30, bold=True, fill=fg)
            draw_right(draw, x + card_w - 22, card_y + 95, "未运行", size=24, bold=True, fill=fg)
        elif attention:
            fg = WHITE
            draw.rectangle(
                (x, card_y, x + card_w, card_y + card_h),
                fill=BLACK,
                outline=BLACK,
                width=3,
            )
            draw_text(draw, (x + 22, card_y + 22), name, size=35, bold=True, fill=fg)
            draw_text(draw, (x + 22, card_y + 88), "● ERROR", size=30, bold=True, fill=fg)
            draw_right(draw, x + card_w - 22, card_y + 95, "需要操作", size=24, bold=True, fill=fg)
        else:
            fg = BLACK
            draw.rectangle(
                (x, card_y, x + card_w, card_y + card_h),
                fill=WHITE,
                outline=BLACK,
                width=3,
            )
            draw_text(draw, (x + 22, card_y + 22), name, size=35, bold=True, fill=fg)
            state, note = ("● RUN", "OK") if raw in {"RUN", "RUNNING", "ACTIVE"} else ("● IDLE", "OK")
            draw_text(draw, (x + 22, card_y + 88), state, size=30, bold=True, fill=fg)
            draw_right(draw, x + card_w - 22, card_y + 95, note, size=24, bold=True, fill=fg)

        # 显示 last_activity（底部小字）
        if last_activity:
            draw_text(draw, (x + 22, card_y + card_h - 35), last_activity, size=20, fill=MID)


def draw_codex_resource(draw, y, resource):
    x, right = MARGIN, WIDTH - MARGIN
    draw_text(draw, (x, y), "Codex", size=30, bold=True)
    progress = percent_from(resource.get("value"), resource.get("detail"))
    progress = 0 if progress is None else max(0, min(100, progress))

    bar_y = y + 58
    bar_left, bar_right = x, 650
    draw.rectangle((bar_left, bar_y, bar_right, bar_y + 26), outline=BLACK, width=3)
    fill_right = bar_left + int((bar_right - bar_left) * progress / 100)
    if fill_right > bar_left:
        draw.rectangle((bar_left, bar_y, fill_right, bar_y + 26), fill=BLACK)

    draw_text(draw, (690, bar_y - 7), f"{progress:g}%", size=34, bold=True)
    refresh = first_time(resource.get("detail")) or datetime.now().strftime("%H:%M")
    draw_right(draw, right, bar_y - 2, refresh, size=25, bold=True)
    return y + 132


def draw_balance_resource(draw, x, y, title, resource):
    draw_text(draw, (x, y), title, size=30, bold=True)
    draw_text(draw, (x, y + 55), f"余额  {money_text(resource.get('value'))}", size=27, bold=True)
    draw_text(draw, (x, y + 103), f"今日消耗  {today_spend(resource)}", size=25, fill=MID if today_spend(resource) == "—" else BLACK)


def draw_ai_resources(draw, dashboard):
    draw_text(draw, (MARGIN, 444), "AI资源", size=32, bold=True)
    resources = dashboard.get("resources", [])
    codex = resource_for(resources, "codex")
    deepseek = resource_for(resources, "deepseek")
    mimo = resource_for(resources, "mimo")

    y = draw_codex_resource(draw, 500, codex)
    draw_balance_resource(draw, MARGIN, y, "DeepSeek", deepseek)
    draw_balance_resource(draw, 576, y, "MiMo", mimo)
    draw.line((MARGIN, y + 150, WIDTH - MARGIN, y + 150), fill=LIGHT, width=2)
    return y + 150


def draw_project_and_system(draw, dashboard, y):
    draw_rule(draw, y + 28)
    section_y = y + 56
    project_x, system_x = MARGIN, 610
    draw_text(draw, (project_x, section_y), "CCSwitch", size=30, bold=True)
    draw_text(draw, (system_x, section_y), "系统状态", size=30, bold=True)
    draw.line((560, section_y, 560, section_y + 174), fill=LIGHT, width=2)

    # CC 模型信息
    cc_model = dashboard.get("cc_model") or {}
    provider = clean_text(cc_model.get("provider", ""))
    model = clean_text(cc_model.get("model", ""))

    draw_text(draw, (project_x, section_y + 62), "Claude Code", size=34, bold=True)

    if model:
        draw_text(draw, (project_x, section_y + 108), model, size=28, bold=True)
    if provider:
        draw_text(draw, (project_x, section_y + 145), provider, size=22, fill=MID)

    system = dashboard.get("system") or {}
    cpu = "—" if system.get("cpu_percent") in (None, "") else f"{float(system['cpu_percent']):.0f}%"
    memory = "—" if system.get("memory_percent") in (None, "") else f"{float(system['memory_percent']):.0f}%"
    uptime = clean_text(system.get("uptime", "—")) or "—"
    draw_inline_metric(draw, system_x, section_y + 74, "CPU", cpu, value_size=30)
    draw_inline_metric(draw, system_x + 130, section_y + 74, "内存", memory, value_size=30)
    draw_inline_metric(draw, system_x + 265, section_y + 74, "Uptime", uptime, value_size=28)

    return section_y + 188


def draw_ai_activity(draw, dashboard, y):
    vpn = read_vpn_status()

    draw_rule(draw, y)

    # VPN 标题和状态
    status = vpn.get("status", "DISCONNECTED")
    status_text = "● ON" if status == "CONNECTED" else "● OFF"
    status_fill = BLACK if status == "CONNECTED" else MID

    draw_text(draw, (MARGIN, y + 28), "VPN", size=30, bold=True)
    draw_text(draw, (MARGIN + 80, y + 32), status_text, size=24, bold=True, fill=status_fill)

    # 节点名称
    node = vpn.get("node", "")
    if node:
        draw_text(draw, (MARGIN, y + 68), node, size=22, fill=MID)

    # 路由模式和流量
    metric_y = y + 105
    routing = vpn.get("routing", "") or "—"
    remaining = vpn.get("remaining", "—") or "—"
    expiry = vpn.get("expiry", "—") or "—"

    draw_inline_metric(draw, MARGIN, metric_y, "路由", routing, value_size=26)
    draw_inline_metric(draw, 450, metric_y, "流量", remaining, value_size=26)
    draw_inline_metric(draw, 750, metric_y, "到期", expiry, value_size=26)


def render_kindle_dashboard(output_path="output/dashboard_kindle.png"):
    dashboard_file = Path(__file__).resolve().parent.parent / "data" / "dashboard.json"
    dashboard = json.loads(dashboard_file.read_text(encoding="utf-8"))

    image = Image.new("L", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)
    now = datetime.now().strftime("%H:%M")

    # Header sizing intentionally matches the existing v1.8.1 treatment.
    draw_text(draw, (MARGIN, 42), "AI工作站", size=56, bold=True)
    draw_right(draw, WIDTH - MARGIN, 48, now, size=52, bold=True)
    draw_rule(draw, 126)

    draw_agent_cards(draw, dashboard)
    draw_rule(draw, 416)

    resources_bottom = draw_ai_resources(draw, dashboard)
    status_bottom = draw_project_and_system(draw, dashboard, resources_bottom)
    draw_ai_activity(draw, dashboard, status_bottom + 36)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return str(output)


if __name__ == "__main__":
    print(render_kindle_dashboard())
