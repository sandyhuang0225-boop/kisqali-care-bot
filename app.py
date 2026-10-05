"""
擊癌利病患照護小管家 (Kisqali Care Bot) - 伺服器主程式
專屬服務責任醫院：基隆長庚醫院、三軍總醫院、汐止國泰醫院
提供功能：
1. 醫療個管師專屬獨立運作系統
2. LINE Webhook 支援圖文選單六大功能自動回應
3. 存摺 Web App (LIFF) 靜態與 API 路由
4. 200 OK 健康檢查路由 (供 UptimeRobot 永不休眠)
"""

import os
import json
from flask import Flask, request, abort, jsonify, send_from_directory

app = Flask(__name__, static_folder=".")

# LINE 憑證 (可由環境變數注入，個管師交接只需更換環境變數)
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")

# 醫院與藥局對應規則
HOSPITALS = {
    "tsgh": {
        "name": "三軍總醫院",
        "campus": "（內湖、汀州、松山院區）",
        "pharmacy": "躍獅寶湖藥局",
        "address": "114台北市內湖區寶湖里民權東路6段123巷28號",
        "phone": "02-87928335",
        "tel": "tel:0287928335",
        "note": ""
    },
    "cgmh": {
        "name": "基隆長庚醫院",
        "campus": "（基隆院區、情人湖院區）",
        "pharmacy": "宏仁藥局",
        "address": "基隆市安樂區安樂路2段130號",
        "phone": "02-24321739",
        "tel": "tel:0224321739",
        "note": ""
    },
    "xg": {
        "name": "汐止國泰醫院",
        "campus": "（汐止院區）",
        "pharmacy": "躍獅寶湖藥局（內湖支援）",
        "address": "114台北市內湖區寶湖里民權東路6段123巷28號",
        "phone": "02-87928335",
        "tel": "tel:0287928335",
        "note": "汐止國泰醫院目前由內湖躍獅寶湖藥局支援服務。"
    }
}

# 永欣生技顧問公司資訊
AUDIT_COMPANY = {
    "name": "永欣生技顧問股份有限公司",
    "address": "110台北市信義區忠孝東路五段410號6樓之一",
    "phone": "02-8780-3236",
    "days": "7~10 個工作天"
}

@app.route("/", methods=["GET"])
def index():
    """首頁 / 健康檢查路由，供 UptimeRobot Ping 與存摺網頁檢視"""
    if os.path.exists("index.html"):
        return send_from_directory(".", "index.html")
    return jsonify({
        "status": "online",
        "system": "擊癌利病患照護小管家 (Kisqali Care Bot)",
        "version": "1.0.0",
        "hospitals": ["三軍總醫院", "基隆長庚醫院", "汐止國泰醫院"]
    }), 200

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

@app.route("/callback", methods=["POST"])
def callback():
    """LINE Messaging API Webhook 入口"""
    # 接收 LINE 伺服器通知
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 簡易測試回應或正式 LineBotApi 處理
    return "OK", 200

@app.route("/api/hospitals", methods=["GET"])
def get_hospitals():
    """取得三家醫院與藥局對應清單"""
    return jsonify({
        "hospitals": HOSPITALS,
        "auditCompany": AUDIT_COMPANY
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
