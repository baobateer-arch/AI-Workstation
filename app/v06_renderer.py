
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os

WIDTH = 1072
HEIGHT = 1448

# 状态显示映射
STATUS_DISPLAY = {
    "PERMISSION": "⚠ 需要授权",
    "RUNNING": "▶ 正在运行",
    "WAITING": "◐ 等待输入",
    "DONE": "✓ 已完成",
    "ERROR": "✕ 错误",
    "IDLE": "○ 空闲",
}


def find_font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def draw_text(draw, xy, text, size=40, bold=False, anchor=None, fill=0):
    draw.text(xy, text, font=find_font(size, bold), fill=fill, anchor=anchor)

def text_width(draw, text, size=40, bold=False):
    bb = draw.textbbox((0,0), text, font=find_font(size, bold))
    return bb[2] - bb[0]

def line(draw, y):
    draw.line((60, y, WIDTH-60, y), fill=0, width=2)


def _draw_agent_section(d, y, agents: list) -> int:
    """绘制 Agent 状态区域"""
    draw_text(d, (60, y), "Agent 状态", 32)
    y += 50

    if not agents:
        draw_text(d, (80, y), "无运行中的 Agent", 28, fill=110)
        return y + 45

    for agent in agents[:3]:  # 最多显示3个
        name = agent.get("name", "Unknown")
        channel = agent.get("channel", "")
        status = agent.get("status", "IDLE")
        message = agent.get("message", "")

        # 状态显示
        status_text = STATUS_DISPLAY.get(status, status)

        # 绘制 Agent 卡片
        d.rounded_rectangle((80, y, WIDTH-80, y+75), radius=10, outline=0, width=2)

        # 名称和渠道
        draw_text(d, (95, y+8), f"{name}", 28, True)
        draw_text(d, (95, y+38), f"{channel}", 22, fill=110)

        # 状态
        draw_text(d, (WIDTH-100, y+8), status_text, 26, anchor="ra")

        # 消息（截断）
        if message:
            short_msg = message[:30] + "..." if len(message) > 30 else message
            draw_text(d, (95, y+52), short_msg, 20, fill=110)

        y += 85

    return y


def render_v06(data, output_path="output/dashboard.png"):
    img = Image.new("L", (WIDTH, HEIGHT), 255)
    d = ImageDraw.Draw(img)

    # Header
    draw_text(d, (60, 40), "AI 工作站", 58, True)
    draw_text(d, (WIDTH-60, 60), datetime.now().strftime("%Y-%m-%d %H:%M"),
              28, anchor="ra")
    line(d, 110)

    y = 145

    # 状态区
    draw_text(d, (60, y), "当前状态", 32)
    y += 55

    attention = data.get("agent_attention", 0)
    attention_agents = data.get("attention_agents", [])

    if attention:
        # 黑底白字区域
        d.rounded_rectangle((60, y, WIDTH-60, y+180), radius=20, fill=0)
        draw_text(d, (100, y+25), "⚠ 需要处理", 52, True, fill=255)

        # 显示具体 Agent 名称
        if attention_agents and attention_agents != ["无"]:
            agents_text = "  ".join(attention_agents[:3])
            draw_text(d, (100, y+90), agents_text, 36, fill=255)
            draw_text(d, (100, y+135), "等待授权", 30, fill=255)
        else:
            draw_text(d, (100, y+90), "Agent 等待你的操作", 34, fill=255)
    else:
        d.rounded_rectangle((60, y, WIDTH-60, y+100), radius=20, outline=0, width=3)
        draw_text(d, (100, y+15), "✓ 可以继续工作", 48, True)
        running = data.get("agent_running", 0)
        if running > 0:
            draw_text(d, (100, y+60), f"Agent 运行中  运行中 {running} 个", 26, fill=110)

    y += 210

    # 今日收入
    line(d, y)
    y += 40
    draw_text(d, (60, y), "今日收入", 32)
    y += 60

    income = data.get("income", 1250)
    income_text = f'¥{income:,.0f}'
    # 居中显示
    iw = text_width(d, income_text, 88, True)
    draw_text(d, ((WIDTH - iw) // 2, y), income_text, 88, True)
    y += 100

    # 今日战绩
    line(d, y)
    y += 40
    draw_text(d, (60, y), "今日战绩", 32)
    y += 55

    completed = data.get("completed", 2)
    target = data.get("target", 5)
    avg_time = data.get("avg_time", 45)
    draw_text(d, (60, y), f'{completed}/{target} 项目', 38)
    draw_text(d, (500, y), f'平均 {avg_time}分钟', 38)
    y += 60

    # 当前项目 (Claude Code 模型显示)
    line(d, y)
    y += 40
    draw_text(d, (60, y), "当前项目", 32)
    y += 55

    # 显示 Claude Code 标题
    draw_text(d, (60, y), "Claude Code", 52, True)
    y += 75

    # 显示模型名称
    cc_model = data.get("cc_model", "")
    cc_provider = data.get("cc_provider", "")

    if cc_model:
        # 显示模型名
        draw_text(d, (60, y), cc_model, 42, True)
        y += 55

        # 显示 Provider
        if cc_provider:
            draw_text(d, (60, y), cc_provider, 28, fill=110)
            y += 40
    else:
        draw_text(d, (60, y), "未检测到模型", 36, fill=110)
        y += 50

    y += 10

    # Agent 状态
    agents = data.get("agents", [])
    line(d, y)
    y += 40
    y = _draw_agent_section(d, y, agents)
    y += 10

    # AI资源（紧凑一行）
    line(d, y)
    y += 40
    draw_text(d, (60, y), "AI资源", 32)
    y += 55

    codex = data.get("codex", "68%")
    deepseek = data.get("deepseek", "¥83")
    mimo = data.get("mimo", "¥46")

    draw_text(d, (60, y), f"Codex {codex}", 34, True)
    draw_text(d, (370, y), f"DeepSeek {deepseek}", 34, True)
    draw_text(d, (720, y), f"MiMo {mimo}", 34, True)
    y += 60

    # AI建议
    line(d, y)
    y += 40
    draw_text(d, (60, y), "AI建议", 32)
    y += 55

    suggestions = data.get("suggestions", [
        "先处理 Agent 请求",
        "当前资源充足，可以继续接项目",
        "保持 60 分钟交付目标"
    ])

    for s in suggestions[:4]:
        draw_text(d, (70, y), "• " + s, 30)
        y += 45

    img.save(output_path)
    return output_path
