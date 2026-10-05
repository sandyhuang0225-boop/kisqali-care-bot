"""
自動生成 LINE 官方圖文選單六宮格 (Rich Menu) 圖片
尺寸：2500 x 1686 (符合 LINE 官方規範)
六格主題：
1. 📕 我的存摺
2. 🧾 登記收據
3. 🏥 門診速報
4. ⚙️ 調整劑量
5. 📬 永欣領藥
6. 👤 病友建檔
"""

from PIL import Image, ImageDraw, ImageFont
import os

WIDTH = 2500
HEIGHT = 1686
COLS = 3
ROWS = 2
CELL_W = WIDTH // COLS
CELL_H = HEIGHT // ROWS

# 建立畫布
img = Image.new("RGB", (WIDTH, HEIGHT), color="#F8FAFC")
draw = ImageDraw.Draw(img)

# 六格定義 (標題, 副標, 主題色, 圖示文字)
GRID_ITEMS = [
    # 第一排
    {"title": "我的存摺", "sub": "方案階段・存藥天數・回診警報", "bg": "#991B1B", "badge": "📕 核心存摺"},
    {"title": "登記收據", "sub": "零存整付・滿63顆贈藥・餘額滾動", "bg": "#065F46", "badge": "🧾 零存整付"},
    {"title": "門診速報", "sub": "大字模式・亮給主治醫師快速開藥", "bg": "#1E293B", "badge": "🏥 醫師專用"},
    # 第二排
    {"title": "調整劑量", "sub": "副作用耐受評估・3/2/1顆/暫停", "bg": "#C2410C", "badge": "⚙️ 醫囑變更"},
    {"title": "永欣領藥", "sub": "同意書免郵寄送・簡訊・三院藥局", "bg": "#854D0E", "badge": "📬 審核流程"},
    {"title": "病友建檔", "sub": "三總/基長/汐止・EBC/MBC・代號", "bg": "#4338CA", "badge": "👤 醫院設定"},
]

try:
    # 嘗試載入微軟正黑體或預設字型
    font_large = ImageFont.truetype("msjhbd.ttc", 82)
    font_sub = ImageFont.truetype("msjh.ttc", 40)
    font_badge = ImageFont.truetype("msjhbd.ttc", 44)
except Exception:
    font_large = ImageFont.load_default()
    font_sub = ImageFont.load_default()
    font_badge = ImageFont.load_default()

for idx, item in enumerate(GRID_ITEMS):
    r = idx // COLS
    c = idx % COLS
    x0 = c * CELL_W
    y0 = r * CELL_H
    x1 = x0 + CELL_W
    y1 = y0 + CELL_H

    # 卡片外框與內縮留白
    pad = 16
    draw.rounded_rectangle([x0 + pad, y0 + pad, x1 - pad, y1 - pad], radius=32, fill="#FFFFFF", outline="#E2E8F0", width=6)

    # 頂部主題彩色條
    draw.rounded_rectangle([x0 + pad, y0 + pad, x1 - pad, y0 + pad + 180], radius=28, fill=item["bg"])
    # 徽章標題
    draw.text((x0 + pad + 50, y0 + pad + 60), item["badge"], fill="#FFFFFF", font=font_badge)

    # 主標題
    draw.text((x0 + pad + 50, y0 + 360), item["title"], fill="#0F172A", font=font_large)

    # 副標題說明
    draw.text((x0 + pad + 50, y0 + 520), item["sub"], fill="#64748B", font=font_sub)

# 存檔
out_path = os.path.join(os.path.dirname(__file__), "rich_menu_kisqali.png")
img.save(out_path, "PNG")
print("Rich menu image generated: " + out_path)
