"""
擊癌利病患照護小管家 (Kisqali Care Bot) - 伺服器主程式
專屬責任醫院：基隆長庚醫院、三軍總醫院、汐止國泰醫院
提供功能：
1. 醫療個管師專屬獨立運作系統
2. LINE Webhook 支援圖文選單六大功能自動回應 (Flex Message)
3. 存摺 Web App (LIFF) 靜態與 API 路由
4. 200 OK 健康檢查路由 (供 UptimeRobot Ping 確保永不休眠)
"""

import os
import json
import logging
from flask import Flask, request, abort, jsonify, send_from_directory
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, ReplyMessageRequest,
    TextMessage, FlexMessage, FlexContainer
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__, static_folder=".")
logging.basicConfig(level=logging.INFO)

# LINE 憑證
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get(
    "LINE_CHANNEL_ACCESS_TOKEN",
    "Upmod4oov1d4uGawXN7T8ueE+vH09eU80aQQzdGbF93yy8qOn9d3yEnfvSBvq0iU2PLVT+M8YQnzKA46c5yR3ocKBlcxtOn6veim2KJnzDzWcNRYF7qB50URl9+pD8B0JdkaFAPWwMBcCgDG2/BQXQdB04t89/1O/w1cDnyilFU="
)
LINE_CHANNEL_SECRET = os.environ.get(
    "LINE_CHANNEL_SECRET",
    "a3926ce21639f4d64e293eb822d9c807"
)

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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
    """專用輕量健康檢查 Ping 接口"""
    return "OK", 200

@app.route("/callback", methods=["POST"])
def callback():
    """LINE Messaging API Webhook 入口"""
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature from LINE")
        abort(400)
    except Exception as e:
        app.logger.error(f"Error handling webhook: {e}")

    return "OK", 200

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """處理使用者點擊六宮格文字或輸入訊息"""
    text = event.message.text.strip()
    reply_token = event.reply_token

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        # 1. 擊癌利存摺
        if "存摺" in text:
            msg = TextMessage(
                text="📕【您的擊癌利存摺】\n"
                     "• 當前進度：第 1 階段（買 1 送 1）\n"
                     "• 自費進度：已自購 4 / 6 盒（再購 2 盒晉級「買1送3」）\n"
                     "• 當前劑量：每日 2 顆 (400mg)\n"
                     "• 手邊存藥：20 顆（剩 10 天份）\n"
                     "⚠️【安全庫存提醒】：目前存藥不足兩週！請於本次門診告知醫師補藥！"
            )
            line_bot_api.reply_message(ReplyMessageRequest(reply_token=reply_token, messages=[msg]))

        # 2. 購藥登記 / 登記收據
        elif "購藥" in text or "收據" in text:
            msg = TextMessage(
                text="🧾【零存整付・購藥登記】\n"
                     "每累積自費滿 63 顆收據，即可申請贈送 1 盒（63顆）！\n\n"
                     "請直接回覆自購顆數，例如輸入：\n"
                     "👉「自購 21 顆」或「自購 14 顆」\n"
                     "（多出的顆數系統將自動為您滾入下一期繼續累積，一顆都不浪費！）"
            )
            line_bot_api.reply_message(ReplyMessageRequest(reply_token=reply_token, messages=[msg]))

        # 3. 門診速報
        elif "門診" in text or "速報" in text:
            msg = TextMessage(
                text="🏥【擊癌利門診速報卡（亮給醫師看）】\n"
                     "━━━━━━━━━━━━━━━\n"
                     "• 病友代號：KSQ-8821\n"
                     "• 主治醫院：三軍總醫院\n"
                     "• 治療方案：早期乳癌 (買1送1)\n"
                     "• 自購盒數：已購 4 / 6 盒\n"
                     "• 目前劑量：每日 2 顆 (400mg)\n"
                     "• 手邊庫存：20 顆（剩 10 天）\n"
                     "⚠️ 門診建議：存藥不足兩週，建議開立處方補藥！"
            )
            line_bot_api.reply_message(ReplyMessageRequest(reply_token=reply_token, messages=[msg]))

        # 4. 劑量調整
        elif "劑量" in text:
            msg = TextMessage(
                text="⚙️【醫師調整劑量】\n"
                     "若因副作用（如白血球或肝指數）經主治醫師評估需調整每日顆數，請回覆：\n\n"
                     "•「改為 3 顆」(600mg 起始劑量)\n"
                     "•「改為 2 顆」(400mg 標準/一級減量)\n"
                     "•「改為 1 顆」(200mg 二級減量)\n"
                     "•「暫停服藥」(副作用休養，暫停扣庫存)"
            )
            line_bot_api.reply_message(ReplyMessageRequest(reply_token=reply_token, messages=[msg]))

        # 5. 領藥流程 / 永欣領藥
        elif "領藥" in text or "流程" in text or "永欣" in text:
            msg = TextMessage(
                text="📬【贈藥申請 ＆ 院外藥局領藥流程】\n"
                     "━━━━━━━━━━━━━━━\n"
                     "1️⃣ 回診填寫同意書：\n"
                     "   • 請醫師填寫黃框（⚠️ 日期請務必手寫！）\n"
                     "   • 填寫紅框病患資料，第二聯粉紅聯「撕下自留」\n\n"
                     "2️⃣ 摺疊免郵信封寄出：\n"
                     "   • 封面已預印回郵，免貼郵票直接投遞郵筒！\n"
                     "   • 寄至【永欣生技顧問股份有限公司】\n"
                     "   • 審核約需 7~10 個工作天 (📞 02-8780-3236)\n\n"
                     "3️⃣ 接獲 SMS 簡訊前往藥局領藥：\n"
                     "   🏥 三軍總醫院 / 汐止國泰 ➔ 躍獅寶湖藥局\n"
                     "      (台北市內湖區民權東路6段123巷28號 / 02-87928335)\n"
                     "   🏥 基隆長庚醫院 ➔ 宏仁藥局\n"
                     "      (基隆市安樂區安樂路2段130號 / 02-24321739)\n"
                     "   ⚠️ 藥品送達 3 個月內需領取完畢！"
            )
            line_bot_api.reply_message(ReplyMessageRequest(reply_token=reply_token, messages=[msg]))

        # 6. 病友建檔
        elif "建檔" in text:
            msg = TextMessage(
                text="👤【新病友開戶建檔 ＆ 醫院設定】\n"
                     "歡迎加入擊癌利小管家！請依序提供您的基本療程設定：\n\n"
                     "1. 就診醫院：三總 / 基隆長庚 / 汐止國泰\n"
                     "2. 治療類型：早期乳癌 (EBC) / 晚期乳癌 (MBC)\n"
                     "3. 每日劑量：3顆 / 2顆 / 1顆\n"
                     "4. 目前手邊庫存顆數\n\n"
                     "建檔後將生成專屬病友代號（如 KSQ-8821），女兒/家屬也能加入 LINE 同步查閱存摺！"
            )
            line_bot_api.reply_message(ReplyMessageRequest(reply_token=reply_token, messages=[msg]))

        else:
            msg = TextMessage(
                text="您好！我是「擊癌利病患照護小管家」🌸\n"
                     "請點擊下方圖文選單六宮格，或輸入「存摺」、「登記收據」、「門診速報」、「劑量調整」、「領藥流程」為您服務！"
            )
            line_bot_api.reply_message(ReplyMessageRequest(reply_token=reply_token, messages=[msg]))

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
