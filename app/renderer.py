from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from PIL import Image, ImageDraw, ImageFont

CANVAS_W = 1072
CANVAS_H = 1448

BG = 255
FG = 0
MID = 110
LIGHT = 220

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
DEFAULT_OUTPUT = OUTPUT_DIR / "dashboard.png"


def _find_font() -> Path:
    """优先寻找可显示中文的 Windows 字体，不复制字体文件。"""
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),      # 微软雅黑
        Path(r"C:\Windows\Fonts\msyhbd.ttc"),    # 微软雅黑粗体
        Path(r"C:\Windows\Fonts\simhei.ttf"),     # 黑体
        Path(r"C:\Windows\Fonts\simsun.ttc"),     # 宋体
        Path(r"C:\Windows\Fonts\Deng.ttf"),       # 等线
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "未找到可显示中文的字体。请确认 Windows 字体目录中存在微软雅黑、黑体、宋体或等线。"
    )


FONT_PATH = _find_font()


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size)


F_TITLE = _font(56)
F_DATE = _font(27)
F_SECTION = _font(38)
F_LABEL = _font(25)
F_VALUE_XL = _font(72)
F_VALUE_L = _font(52)
F_VALUE_M = _font(34)
F_VALUE_S = _font(26)
F_TINY = _font(22)


def _get(data: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, Mapping) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _fmt_tokens(value: Any) -> str:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return str(value or "--")
    if n >= 100_000_000:
        return f"{n / 100_000_000:.2f}亿"
    if n >= 10_000:
        return f"{n / 10_000:.1f}万"
    return f"{int(n):,}"


def _fmt_money(value: Any) -> str:
    try:
        return f"¥{float(value):.2f}"
    except (TypeError, ValueError):
        text = str(value or "--")
        return text if text.startswith("¥") else f"¥{text}"


def _rounded_box(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], radius: int = 18,
                 outline: int = FG, width: int = 3, fill: int = BG) -> None:
    draw.rounded_rectangle(xy, radius=radius, outline=outline, width=width, fill=fill)


def _progress(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, percent: float) -> None:
    percent = max(0.0, min(100.0, float(percent)))
    draw.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, outline=FG, width=3, fill=BG)
    inner = int((w - 6) * percent / 100)
    if inner > 0:
        draw.rounded_rectangle(
            (x + 3, y + 3, x + 3 + inner, y + h - 3),
            radius=max(1, (h - 6) // 2),
            fill=FG,
        )


def _text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: Any, font: ImageFont.FreeTypeFont,
          fill: int = FG, anchor: str | None = None) -> None:
    draw.text(xy, str(text), font=font, fill=fill, anchor=anchor)


def _metric(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, value: str,
            value_font: ImageFont.FreeTypeFont = F_VALUE_M, right: int | None = None) -> None:
    _text(draw, (x, y), label, F_LABEL, MID)
    if right is None:
        _text(draw, (x, y + 33), value, value_font)
    else:
        _text(draw, (right, y + 2), value, value_font, anchor="ra")


def render_dashboard(data: Mapping[str, Any], output_path: str | Path = DEFAULT_OUTPUT) -> Path:
    """
    生成全中文、适合 Kindle Paperwhite 3 的黑白仪表盘。

    data 支持嵌套结构，也兼容缺失字段；缺失值显示为 --。
    """
    now = datetime.now()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("L", (CANVAS_W, CANVAS_H), BG)
    draw = ImageDraw.Draw(image)

    margin = 48
    content_w = CANVAS_W - margin * 2

    # 顶部
    _text(draw, (margin, 38), "AI 工作站", F_TITLE)
    _text(draw, (CANVAS_W - margin, 47), now.strftime("%Y-%m-%d  %H:%M"), F_DATE, MID, "ra")
    draw.line((margin, 118, CANVAS_W - margin, 118), fill=FG, width=4)

    # ===== Codex 卡片 =====
    y = 145
    card_h = 285
    _rounded_box(draw, (margin, y, CANVAS_W - margin, y + card_h), radius=20, width=4)
    _text(draw, (margin + 24, y + 20), "Codex 额度", F_SECTION)

    five = float(_get(data, "codex", "five_hour_percent", default=_get(data, "codex_5h", default=68)) or 0)
    week = float(_get(data, "codex", "weekly_percent", default=_get(data, "codex_week", default=41)) or 0)
    reset = _get(data, "codex", "reset_text", default=_get(data, "codex_reset", default="02:35"))

    _text(draw, (margin + 28, y + 78), "5 小时剩余", F_LABEL, MID)
    _text(draw, (CANVAS_W - margin - 28, y + 67), f"{five:.0f}%", F_VALUE_L, anchor="ra")
    _progress(draw, margin + 28, y + 132, content_w - 56, 30, five)

    _text(draw, (margin + 28, y + 177), "本周剩余", F_LABEL, MID)
    _text(draw, (CANVAS_W - margin - 28, y + 166), f"{week:.0f}%", F_VALUE_L, anchor="ra")
    _progress(draw, margin + 28, y + 230, content_w - 240, 28, week)

    _text(draw, (CANVAS_W - margin - 24, y + 204), "预计恢复", F_TINY, MID, "ra")
    _text(draw, (CANVAS_W - margin - 24, y + 238), reset, F_VALUE_S, anchor="ra")

    # ===== DeepSeek / MiMo 两列 =====
    y = 452
    gap = 22
    col_w = (content_w - gap) // 2
    card_h = 350

    def provider_card(x: int, title: str, node: str, fallback: dict[str, Any]) -> None:
        _rounded_box(draw, (x, y, x + col_w, y + card_h), radius=20, width=4)
        _text(draw, (x + 24, y + 20), title, F_SECTION)

        balance = _get(data, node, "balance", "total",
                       default=_get(data, node, "balance", default=fallback["balance"]))
        tokens = _get(data, node, "usage", "today", "total_tokens",
                      default=_get(data, node, "today_tokens", default=fallback["tokens"]))
        in_tokens = _get(data, node, "usage", "today", "prompt_tokens",
                         default=_get(data, node, "input_tokens", default=fallback["input"]))
        out_tokens = _get(data, node, "usage", "today", "completion_tokens",
                          default=_get(data, node, "output_tokens", default=fallback["output"]))
        cost = _get(data, node, "usage", "today", "cost",
                    default=_get(data, node, "today_cost", default=fallback["cost"]))

        _text(draw, (x + 24, y + 82), "剩余金额", F_LABEL, MID)
        _text(draw, (x + 24, y + 116), _fmt_money(balance), F_VALUE_L)

        draw.line((x + 24, y + 184, x + col_w - 24, y + 184), fill=LIGHT, width=2)

        _metric(draw, x + 24, y + 202, "今日 Token", _fmt_tokens(tokens), F_VALUE_M)
        _text(draw, (x + 24, y + 278), f"输入 {_fmt_tokens(in_tokens)}", F_VALUE_S)
        _text(draw, (x + col_w - 24, y + 278), f"输出 {_fmt_tokens(out_tokens)}", F_VALUE_S, anchor="ra")
        _text(draw, (x + 24, y + 321), "今日花费", F_TINY, MID)
        _text(draw, (x + col_w - 24, y + 323), _fmt_money(cost), F_VALUE_S, anchor="ra")

    provider_card(
        margin, "DeepSeek", "deepseek",
        {"balance": 83.26, "tokens": 1_820_000, "input": 1_310_000, "output": 510_000, "cost": 2.43},
    )
    provider_card(
        margin + col_w + gap, "MiMo", "mimo",
        {"balance": 46.20, "tokens": 3_460_000, "input": 2_810_000, "output": 650_000, "cost": 3.17},
    )

    # ===== 当前项目 =====
    y = 825
    card_h = 315
    _rounded_box(draw, (margin, y, CANVAS_W - margin, y + card_h), radius=20, width=4)
    _text(draw, (margin + 24, y + 20), "当前项目", F_SECTION)

    project_name = _get(data, "current_project", "name",
                        default=_get(data, "project", "name", default="客户管理系统"))
    elapsed = _get(data, "current_project", "elapsed_minutes",
                   default=_get(data, "project", "elapsed_minutes", default=47))
    target = _get(data, "current_project", "target_minutes",
                  default=_get(data, "project", "target_minutes", default=60))
    ai_cost = _get(data, "current_project", "total_cost",
                   default=_get(data, "project", "ai_cost", default=1.62))
    today_income = _get(data, "work", "income_today",
                        default=_get(data, "today_income", default=0))

    _text(draw, (margin + 28, y + 78), project_name, F_VALUE_L)
    draw.line((margin + 28, y + 152, CANVAS_W - margin - 28, y + 152), fill=LIGHT, width=2)

    _metric(draw, margin + 28, y + 172, "已用时间", f"{elapsed} 分钟", F_VALUE_M)
    _metric(draw, margin + 360, y + 172, "目标时间", f"{target} 分钟", F_VALUE_M)
    _metric(draw, margin + 690, y + 172, "AI 成本", _fmt_money(ai_cost), F_VALUE_M)

    _text(draw, (margin + 28, y + 258), "今日收入", F_LABEL, MID)
    _text(draw, (CANVAS_W - margin - 28, y + 245), _fmt_money(today_income), F_VALUE_L, anchor="ra")

    # ===== 底部状态条 =====
    y = 1170
    _rounded_box(draw, (margin, y, CANVAS_W - margin, y + 190), radius=20, width=4)

    updated = _get(data, "generated_at", default=now.strftime("%H:%M"))
    if isinstance(updated, str) and "T" in updated:
        try:
            updated = datetime.fromisoformat(updated).strftime("%H:%M")
        except ValueError:
            pass

    status = _get(data, "status", default="全部正常")
    version = _get(data, "version", default="v0.2")

    _text(draw, (margin + 26, y + 24), "运行状态", F_LABEL, MID)
    _text(draw, (margin + 26, y + 63), str(status), F_VALUE_M)
    _text(draw, (CANVAS_W // 2, y + 24), "更新时间", F_LABEL, MID, "ma")
    _text(draw, (CANVAS_W // 2, y + 63), str(updated), F_VALUE_M, anchor="ma")
    _text(draw, (CANVAS_W - margin - 26, y + 24), "版本", F_LABEL, MID, "ra")
    _text(draw, (CANVAS_W - margin - 26, y + 63), version, F_VALUE_M, anchor="ra")

    draw.line((margin + 26, y + 125, CANVAS_W - margin - 26, y + 125), fill=LIGHT, width=2)
    _text(draw, (CANVAS_W // 2, y + 144), "余额、Token 与项目成本一目了然", F_TINY, MID, "ma")

    image.save(output_path, format="PNG", optimize=True)
    return output_path


# 兼容可能存在的旧调用名
def render(data: Mapping[str, Any], output_path: str | Path = DEFAULT_OUTPUT) -> Path:
    return render_dashboard(data, output_path)
