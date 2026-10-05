"""
將使用者專屬設計的精美插畫六宮格圖文選單，上傳並綁定至 LINE 官方帳號
圖片檔案：rich_menu_2500x1686.png
六格精確文字對齊：
1. 擊癌利存摺 (查看目前計畫進度)
2. 購藥登記 (登記收據與購買顆數)
3. 門診速報 (提供醫師查看進度)
4. 劑量調整 (回報不適・依醫囑調整)
5. 領藥流程 (查看領藥步驟與提醒)
6. 病友建檔 (建立基本資料)
"""

import os
import requests
import json

ACCESS_TOKEN = "Upmod4oov1d4uGawXN7T8ueE+vH09eU80aQQzdGbF93yy8qOn9d3yEnfvSBvq0iU2PLVT+M8YQnzKA46c5yR3ocKBlcxtOn6veim2KJnzDzWcNRYF7qB50URl9+pD8B0JdkaFAPWwMBcCgDG2/BQXQdB04t89/1O/w1cDnyilFU="

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

W = 2500
H = 1686
CELL_W = W // 3
CELL_H = H // 2

RICH_MENU_PAYLOAD = {
    "size": {"width": W, "height": H},
    "selected": True,
    "name": "Kisqali_Care_Menu_Custom",
    "chatBarText": "擊癌利小管家",
    "areas": [
        # 第 1 格：擊癌利存摺
        {
            "bounds": {"x": 0, "y": 0, "width": CELL_W, "height": CELL_H},
            "action": {"type": "message", "text": "擊癌利存摺"}
        },
        # 第 2 格：購藥登記
        {
            "bounds": {"x": CELL_W, "y": 0, "width": CELL_W, "height": CELL_H},
            "action": {"type": "message", "text": "購藥登記"}
        },
        # 第 3 格：門診速報
        {
            "bounds": {"x": CELL_W * 2, "y": 0, "width": CELL_W, "height": CELL_H},
            "action": {"type": "message", "text": "門診速報"}
        },
        # 第 4 格：劑量調整
        {
            "bounds": {"x": 0, "y": CELL_H, "width": CELL_W, "height": CELL_H},
            "action": {"type": "message", "text": "劑量調整"}
        },
        # 第 5 格：領藥流程
        {
            "bounds": {"x": CELL_W, "y": CELL_H, "width": CELL_W, "height": CELL_H},
            "action": {"type": "message", "text": "領藥流程"}
        },
        # 第 6 格：病友建檔
        {
            "bounds": {"x": CELL_W * 2, "y": CELL_H, "width": CELL_W, "height": CELL_H},
            "action": {"type": "message", "text": "病友建檔"}
        }
    ]
}

def update_rich_menu():
    print("[1/3] Creating new custom rich menu...")
    res = requests.post(
        "https://api.line.me/v2/bot/richmenu",
        headers=HEADERS,
        data=json.dumps(RICH_MENU_PAYLOAD)
    )
    if res.status_code != 200:
        print(f"Error creating menu: {res.text}")
        return
    menu_id = res.json()["richMenuId"]
    print(f"New Rich Menu ID: {menu_id}")

    print("[2/3] Uploading custom illustration image...")
    upload_headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "image/jpeg"
    }
    with open("rich_menu_2500x1686.jpg", "rb") as f:
        img_res = requests.post(
            f"https://api-data.line.me/v2/bot/richmenu/{menu_id}/content",
            headers=upload_headers,
            data=f
        )
    if img_res.status_code != 200:
        print(f"Error uploading image: {img_res.text}")
        return
    print("Image uploaded successfully!")

    print("[3/3] Setting as default rich menu for all users...")
    def_res = requests.post(
        f"https://api.line.me/v2/bot/user/all/richmenu/{menu_id}",
        headers=HEADERS
    )
    if def_res.status_code != 200:
        print(f"Error setting default: {def_res.text}")
        return

    print("Success! Custom illustration Rich Menu is now LIVE on LINE!")

if __name__ == "__main__":
    update_rich_menu()
