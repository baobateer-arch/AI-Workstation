"""Agent status board renderer for Kindle Paperwhite 3 (1072x1448)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from PIL import Image, ImageDraw, ImageFont

from app.agent_models import (
    AgentDashboardData,
    AgentInfo,
    STATUS_IDLE,
    STATUS_RUNNING,
    STATUS_PERMISSION,
    STATUS_INPUT,
    STATUS_COMPLETED,
    STATUS_ERROR,
    status_cn,
    minutes_between,
)
from app.attention import (
    get_attention_agents,
    get_attention_count,
    get_highest_priority_agent,
    should_show_attention_page,
)

# ---------------------------------------------------------------------------
# 画布与颜色
# ---------------------------------------------------------------------------
CANVAS_W = 1072
CANVAS_H = 1448

BG = 255
FG = 0
MID = 110
LIGHT = 220

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
DEFAULT_OUTPUT = OUTPUT_DIR / "agent_status.png"

# ---------------------------------------------------------------------------
# 字体（复用 renderer.py 的查找逻辑）
# ---------------------------------------------------------------------------

def _find_font() -> Path:
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\msyhbd.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
        Path(r"C:\Windows\Fonts\Deng.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("未找到可显示中文的字体。")


FONT_PATH = _find_font()


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size)


F_TITLE = _font(52)
F_DATE = _font(26)
F_SECTION = _font(36)
F_LABEL = _font(22)
F_VALUE_L = _font(42)
F_VALUE_M = _font(30)
F_VALUE_S = _font(24)
F_TINY = _font(20)
F_ALERT_TITLE = _font(56)
F_ALERT_BIG = _font(68)

# ---------------------------------------------------------------------------
# 绘图工具
# ---------------------------------------------------------------------------

def _text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: Any,
          font: ImageFont.FreeTypeFont, fill: int = FG,
          anchor: str | None = None) -> None:
    draw.text(xy, str(text), font=font, fill=fill, anchor=anchor)


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def _rounded_box(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int],
                 radius: int = 18, outline: int = FG, width: int = 3,
                 fill: int | None = None) -> None:
    kw: dict[str, Any] = {"radius": radius, "outline": outline, "width": width}
    if fill is not None:
        kw["fill"] = fill
    draw.rounded_rectangle(xy, **kw)


def _line(draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int,
          fill: int = FG, width: int = 2) -> None:
    draw.line((x1, y1, x2, y2), fill=fill, width=width)


# ---------------------------------------------------------------------------
# 卡片绘制
# ---------------------------------------------------------------------------

def _draw_normal_card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
                      agent: AgentInfo, now: datetime) -> None:
    """普通白底卡片（running / idle / completed）。"""
    _rounded_box(draw, (x, y, x + w, y + h), radius=16, outline=FG, width=3)

    # 状态标签（右上角）
    status_text = status_cn(agent.status)
    _text(draw, (x + w - 24, y + 18), status_text, F_VALUE_S, MID, "ra")

    # Agent 名称
    _text(draw, (x + 24, y + 16), agent.name, F_SECTION)

    # 项目
    _text(draw, (x + 24, y + 68), f"项目：{agent.project}", F_VALUE_S)

    # 任务
    _text(draw, (x + 24, y + 102), f"任务：{agent.task}", F_VALUE_S)

    # 说明
    _text(draw, (x + 24, y + 136), f"说明：{agent.message}", F_TINY, MID)

    # 已运行/已等待时间
    elapsed = minutes_between(agent.started_at, now)
    if elapsed is not None:
        label = "已等待" if agent.status in (STATUS_COMPLETED, STATUS_INPUT, STATUS_PERMISSION) else "已运行"
        _text(draw, (x + 24, y + 170), f"{label} {elapsed} 分钟", F_TINY, MID)


def _draw_permission_card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
                          agent: AgentInfo, now: datetime) -> None:
    """黑底白字卡片（permission_required）。"""
    _rounded_box(draw, (x, y, x + w, y + h), radius=16, outline=FG, width=5, fill=FG)

    # 大号状态
    _text(draw, (x + 28, y + 20), "需要授权", F_ALERT_TITLE, BG)

    # Agent 名称
    _text(draw, (x + 28, y + 90), agent.name, F_SECTION, BG)

    # 请求内容
    _text(draw, (x + 28, y + 140), agent.message, F_VALUE_M, BG)

    # 已等待
    waited = minutes_between(agent.waiting_since, now)
    if waited is not None:
        _text(draw, (x + 28, y + 190), f"已等待 {waited} 分钟", F_VALUE_S, BG)


def _draw_input_card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
                     agent: AgentInfo, now: datetime) -> None:
    """双层粗边框卡片（input_required）。"""
    # 外层边框
    _rounded_box(draw, (x - 4, y - 4, x + w + 4, y + h + 4), radius=20, outline=FG, width=6)
    # 内层边框
    _rounded_box(draw, (x + 4, y + 4, x + w - 4, y + h - 4), radius=14, outline=FG, width=3)

    _text(draw, (x + 28, y + 18), "等待回复", F_ALERT_TITLE)
    _text(draw, (x + 28, y + 88), agent.name, F_SECTION)
    _text(draw, (x + 28, y + 138), f"项目：{agent.project}", F_VALUE_S)
    _text(draw, (x + 28, y + 172), f"说明：{agent.message}", F_TINY, MID)

    waited = minutes_between(agent.waiting_since, now)
    if waited is not None:
        _text(draw, (x + 28, y + 210), f"已等待 {waited} 分钟", F_VALUE_S)


def _draw_error_card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
                     agent: AgentInfo, now: datetime) -> None:
    """粗黑边框卡片（error）。"""
    _rounded_box(draw, (x, y, x + w, y + h), radius=16, outline=FG, width=6)

    _text(draw, (x + 28, y + 18), "运行异常", F_ALERT_TITLE)
    _text(draw, (x + 28, y + 88), agent.name, F_SECTION)
    _text(draw, (x + 28, y + 138), f"项目：{agent.project}", F_VALUE_S)
    _text(draw, (x + 28, y + 172), f"错误：{agent.message}", F_TINY, MID)


def _draw_completed_card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
                         agent: AgentInfo, now: datetime) -> None:
    """普通白底卡片，显示任务完成。"""
    _rounded_box(draw, (x, y, x + w, y + h), radius=16, outline=FG, width=3)

    _text(draw, (x + 28, y + 18), "任务完成", F_ALERT_TITLE)
    _text(draw, (x + 28, y + 88), agent.name, F_SECTION)
    _text(draw, (x + 28, y + 138), f"项目：{agent.project}", F_VALUE_S)
    _text(draw, (x + 28, y + 172), f"说明：{agent.message}", F_TINY, MID)

    waited = minutes_between(agent.waiting_since, now)
    if waited is not None:
        _text(draw, (x + 28, y + 210), f"已等待 {waited} 分钟", F_VALUE_S)


# ---------------------------------------------------------------------------
# 紧急提醒区
# ---------------------------------------------------------------------------

def _draw_attention_banner(draw: ImageDraw.ImageDraw, agent: AgentInfo,
                           now: datetime, y_start: int, margin: int) -> int:
    """绘制顶部紧急提醒区，返回占用的高度。"""
    banner_h = 320
    x = margin
    w = CANVAS_W - margin * 2
    y = y_start

    # 黑底白字大区域
    _rounded_box(draw, (x, y, x + w, y + banner_h), radius=20, outline=FG, width=5, fill=FG)

    # 标题
    _text(draw, (x + 32, y + 20), "需要授权", F_ALERT_BIG, BG)

    # Agent 名称
    _text(draw, (x + 32, y + 100), agent.name, F_SECTION, BG)

    # 请求内容（message 已包含完整信息）
    _text(draw, (x + 32, y + 155), agent.message, F_VALUE_L, BG)

    # 已等待
    waited = minutes_between(agent.waiting_since, now)
    if waited is not None:
        _text(draw, (x + 32, y + 220), f"已等待 {waited} 分钟", F_VALUE_M, BG)

    return banner_h


# ---------------------------------------------------------------------------
# 主渲染函数
# ---------------------------------------------------------------------------

def render_agent_status(data: AgentDashboardData,
                        output_path: str | Path = DEFAULT_OUTPUT) -> Path:
    """生成 Agent 值守台 PNG。"""
    now = datetime.now()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("L", (CANVAS_W, CANVAS_H), BG)
    draw = ImageDraw.Draw(image)

    margin = 48
    content_w = CANVAS_W - margin * 2

    # --- 顶部 ---
    _text(draw, (margin, 24), "Agent 值守台", F_TITLE)
    _text(draw, (CANVAS_W - margin, 34), now.strftime("%Y-%m-%d  %H:%M"), F_DATE, MID, "ra")

    attention_count = get_attention_count(data)
    if attention_count > 0:
        attention_text = f"需要处理：{attention_count} 项"
    else:
        attention_text = "无需处理"
    _text(draw, (margin, 88), attention_text, F_VALUE_S, MID)

    _line(draw, margin, 125, CANVAS_W - margin, 125, FG, 4)

    y_cursor = 142

    # --- 紧急提醒区（如果有 permission_required）---
    highest = get_highest_priority_agent(data)
    if highest and highest.status == STATUS_PERMISSION:
        banner_h = _draw_attention_banner(draw, highest, now, y_cursor, margin)
        y_cursor += banner_h + 20

    # --- Agent 卡片 ---
    agents = data.agents
    card_w = content_w
    card_h = 240
    card_gap = 20

    for agent in agents:
        # 计算卡片高度（permission 卡片稍高）
        if agent.status == STATUS_PERMISSION:
            ch = 250
        elif agent.status == STATUS_INPUT:
            ch = 260
        elif agent.status == STATUS_ERROR:
            ch = 230
        elif agent.status == STATUS_COMPLETED:
            ch = 260
        else:
            ch = 210

        # 检查是否需要换行（简化：单列布局）
        if y_cursor + ch > CANVAS_H - 120:
            break

        if agent.status == STATUS_PERMISSION:
            _draw_permission_card(draw, margin, y_cursor, card_w, ch, agent, now)
        elif agent.status == STATUS_INPUT:
            _draw_input_card(draw, margin, y_cursor, card_w, ch, agent, now)
        elif agent.status == STATUS_ERROR:
            _draw_error_card(draw, margin, y_cursor, card_w, ch, agent, now)
        elif agent.status == STATUS_COMPLETED:
            _draw_completed_card(draw, margin, y_cursor, card_w, ch, agent, now)
        else:
            _draw_normal_card(draw, margin, y_cursor, card_w, ch, agent, now)

        y_cursor += ch + card_gap

    # --- 底部 ---
    footer_y = CANVAS_H - 100
    _line(draw, margin, footer_y, CANVAS_W - margin, footer_y, LIGHT, 2)

    _text(draw, (margin, footer_y + 12), "提示：请回到电脑处理授权", F_TINY, MID)
    _text(draw, (CANVAS_W // 2, footer_y + 12), f"更新 {now.strftime('%H:%M')}", F_TINY, MID, "ma")
    _text(draw, (CANVAS_W - margin, footer_y + 12), "版本 v0.3", F_TINY, MID, "ra")

    image.save(output_path, format="PNG", optimize=True)
    return output_path
