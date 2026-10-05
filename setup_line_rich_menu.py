"""
自動上傳並綁定 LINE 六宮格圖文選單腳本 (One-click Setup)
使用方式：
直接執行：python setup_line_rich_menu.py <LINE_CHANNEL_ACCESS_TOKEN>
會自動：
1. 建立符合六宮格點擊區域的 Rich Menu 定義
2. 上傳 rich_menu_kisqali.png 圖檔
3. 將該圖文選單設為官方帳號的「預設圖文選單 (Default Rich Menu)」
"""

import sys
import os
import requests
import json

ACCESS_TOKEN = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")

if not ACCESS_TOKEN:
    print("Error: Please provide LINE_CHANNEL_ACCESS_TOKEN as argument or environment variable.")
    print("Usage: python setup_line_rich_menu.py <YOUR_CHANNEL_ACCESS_TOKEN>")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# 2500 x 1686 六宮格尺寸
W = 2500
H = 1686
CELL_W = W // 3
CELL_H = H // 2

# 定義 6 個按鈕點擊觸發文字
RICH_MENU_PAYLOAD = {
    "size": {"width": W, "height": H},
    "selected": True,
    "name": "Kisqali_Care_Menu",
    "chatBarText": "擊癌利小管家存摺",
    "areas": [
        # 第 1 格：我的存摺
        {
            "bounds": {"x": 0, "y": 0, "width": CELL_W, "height": CELL_H},
            "action": {"type": "message", "text": "我的存摺"}
        },
        # 第 2 格：登記收據
        {
            "bounds": {"x": CELL_W, "y": 0, "width": CELL_W, "height": CELL_H},
            "action": {"type": "message", "text": "登記收據"}
        },
        # 第 3 格：門診速報
        {
            "bounds": {"x": CELL_W * 2, "y": 0, "width": CELL_W, "height": CELL_H},
            "action": {"type": "message", "text": "門診速報"}
        },
        # 第 4 格：調整劑量
        {
            "bounds": {"x": 0, "y": CELL_H, "width": CELL_W, "height": CELL_H},
            "action": {"type": "message", "text": "調整劑量"}
        },
        # 第 5 格：永欣領藥
        {
            "bounds": {"x": CELL_W, "y": CELL_H, "width": CELL_W, "height": CELL_H},
            "action": {"type": "message", "text": "永欣領藥"}
        },
        # 第 6 格：病友建檔
        {
            "bounds": {"x": CELL_W * 2, "y": CELL_H, "width": CELL_W, "height": CELL_H},
            "action": {"type": "message", "text": "病友建檔"}
        }
    ]
}

def create_and_bind():
    # 步驟 1: 建立 Rich Menu
    print("[1/3] Creating rich menu definition...")
    res = requests.post(
        "https://api.line.me/v2/bot/richmenu",
        headers=HEADERS,
        data=json.dumps(RICH_MENU_PAYLOAD)
    )
    if res.status_code != 200:
        print(f"Failed to create rich menu: {res.text}")
        return
    rich_menu_id = res.json()["richMenuId"]
    print(f"Created Rich Menu ID: {rich_menu_id}")

    # 步驟 2: 上傳圖片
    img_path = os.path.join(os.path.dirname(__file__), "rich_menu_kisqali.png")
    print(f"[2/3] Uploading rich menu image from {img_path}...")
    upload_headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "image/png"
    }
    with open(img_path, "rb") as f:
        img_res = requests.post(
            f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content",
            headers=upload_headers,
            data=f
        )
    if img_res.status_code != 200:
        print(f"Failed to upload image: {img_res.text}")
        return
    print("Image uploaded successfully!")

    # 步驟 3: 設定為全體預設圖文選單
    print(f"[3/3] Setting {rich_menu_id} as default menu for all users...")
    def_res = requests.post(
        f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}",
        headers=HEADERS
    )
    if def_res.status_code != 200:
        print(f"Failed to set default menu: {def_res.text}")
        return

    print("Success! The 6-grid Kisqali Rich Menu is now LIVE on your LINE Official Account!")

if __name__ == "__main__":
    create_and_bind()
