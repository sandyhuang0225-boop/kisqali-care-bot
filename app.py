"""
擊癌利病患照護小管家 (Kisqali Care Bot) - 伺服器主程式
專屬責任醫院：基隆長庚醫院、三軍總醫院、汐止國泰醫院
採用與 line_bot 100% 一模一樣且最穩定的 linebot v2 架構
"""

import os
import json
import logging
from flask import Flask, request, abort, jsonify, send_from_directory
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, PostbackEvent,
    FlexSendMessage
)

app = Flask(__name__, static_folder=".")
logging.basicConfig(level=logging.INFO)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get(
    "LINE_CHANNEL_ACCESS_TOKEN",
    "Upmod4oov1d4uGawXN7T8ueE+vH09eU80aQQzdGbF93yy8qOn9d3yEnfvSBvq0iU2PLVT+M8YQnzKA46c5yR3ocKBlcxtOn6veim2KJnzDzWcNRYF7qB50URl9+pD8B0JdkaFAPWwMBcCgDG2/BQXQdB04t89/1O/w1cDnyilFU="
)
LINE_CHANNEL_SECRET = os.environ.get(
    "LINE_CHANNEL_SECRET",
    "a3926ce21639f4d64e293eb822d9c807"
)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

HOSPITALS = {
    "三總": {
        "name": "三軍總醫院",
        "pharmacy": "躍獅寶湖藥局",
        "address": "114台北市內湖區寶湖里民權東路6段123巷28號",
        "phone": "02-87928335"
    },
    "基隆長庚": {
        "name": "基隆長庚醫院",
        "pharmacy": "宏仁藥局",
        "address": "基隆市安樂區安樂路2段130號",
        "phone": "02-24321739"
    },
    "汐止國泰": {
        "name": "汐止國泰醫院",
        "pharmacy": "躍獅寶湖藥局（由內湖支援）",
        "address": "114台北市內湖區寶湖里民權東路6段123巷28號",
        "phone": "02-87928335"
    }
}

user_profiles = {}

def get_onboarding_step1_flex():
    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": "#991B1B",
            "contents": [
                {"type": "text", "text": "✨ 新病友開戶建檔", "weight": "bold", "color": "#FFFFFF", "size": "md"},
                {"type": "text", "text": "【步驟 1/4】請點選您的主治就診醫院", "color": "#FEE2E2", "size": "xs", "margin": "xs"}
            ]
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                {"type": "text", "text": "請直接點選下方任一家醫院按鈕：", "size": "xs", "color": "#64748B"},
                {"type": "button", "style": "primary", "color": "#991B1B", "height": "sm", "action": {"type": "postback", "label": "🏥 三軍總醫院（內湖/汀州/松山）", "data": "set_hosp=三總", "displayText": "三軍總醫院"}},
                {"type": "button", "style": "primary", "color": "#B91C1C", "height": "sm", "action": {"type": "postback", "label": "🏥 基隆長庚醫院（基隆/情人湖）", "data": "set_hosp=基隆長庚", "displayText": "基隆長庚醫院"}},
                {"type": "button", "style": "primary", "color": "#DC2626", "height": "sm", "action": {"type": "postback", "label": "🏥 汐止國泰醫院", "data": "set_hosp=汐止國泰", "displayText": "汐止國泰醫院"}}
            ]
        }
    }

def get_onboarding_step2_flex(hospital_name):
    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": "#991B1B",
            "contents": [
                {"type": "text", "text": "✨ 新病友開戶建檔", "weight": "bold", "color": "#FFFFFF", "size": "md"},
                {"type": "text", "text": f"已選醫院：{hospital_name} ｜ 【步驟 2/4】治療類型", "color": "#FEE2E2", "size": "xs", "margin": "xs"}
            ]
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                {"type": "text", "text": "請依主治醫師診斷點選您的治療階段：", "size": "xs", "color": "#64748B"},
                {"type": "button", "style": "primary", "color": "#059669", "height": "sm", "action": {"type": "postback", "label": "🌸 早期乳癌（EBC・3年方案）", "data": "set_cancer=早期乳癌", "displayText": "早期乳癌"}},
                {"type": "button", "style": "primary", "color": "#D97706", "height": "sm", "action": {"type": "postback", "label": "🎗️ 轉移晚期乳癌（MBC・5年方案）", "data": "set_cancer=晚期乳癌", "displayText": "晚期乳癌"}}
            ]
        }
    }

def get_onboarding_step3_flex(cancer_type):
    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": "#991B1B",
            "contents": [
                {"type": "text", "text": "✨ 新病友開戶建檔", "weight": "bold", "color": "#FFFFFF", "size": "md"},
                {"type": "text", "text": f"已選類型：{cancer_type} ｜ 【步驟 3/4】每日劑量", "color": "#FEE2E2", "size": "xs", "margin": "xs"}
            ]
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                {"type": "text", "text": "請依醫師處方點選每日服用顆數：", "size": "xs", "color": "#64748B"},
                {"type": "button", "style": "primary", "color": "#1E293B", "height": "sm", "action": {"type": "postback", "label": "💊 每日 3 顆（600 mg 起始劑量）", "data": "set_dose=3", "displayText": "每日 3 顆"}},
                {"type": "button", "style": "primary", "color": "#334155", "height": "sm", "action": {"type": "postback", "label": "💊 每日 2 顆（400 mg 標準/一級減量）", "data": "set_dose=2", "displayText": "每日 2 顆"}},
                {"type": "button", "style": "primary", "color": "#475569", "height": "sm", "action": {"type": "postback", "label": "💊 每日 1 顆（200 mg 二級減量）", "data": "set_dose=1", "displayText": "每日 1 顆"}}
            ]
        }
    }

def get_onboarding_step4_flex(dose_str):
    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": "#991B1B",
            "contents": [
                {"type": "text", "text": "✨ 新病友開戶建檔", "weight": "bold", "color": "#FFFFFF", "size": "md"},
                {"type": "text", "text": f"已選劑量：{dose_str} ｜ 【步驟 4/4】現有存藥", "color": "#FEE2E2", "size": "xs", "margin": "xs"}
            ]
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": "請直接在下方聊天室輸入您手邊「目前剩餘的確切顆數」：",
                    "size": "sm",
                    "weight": "bold",
                    "color": "#0F172A",
                    "wrap": True
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#F8FAFC",
                    "cornerRadius": "md",
                    "paddingAll": "md",
                    "borderWidth": "light",
                    "borderColor": "#CBD5E1",
                    "contents": [
                        {"type": "text", "text": "👉 請直接打數字並送出，例如：", "size": "xs", "color": "#64748B"},
                        {"type": "text", "text": "「14」 或 「25」 或 「40」", "size": "lg", "weight": "bold", "color": "#991B1B", "margin": "sm"}
                    ]
                },
                {
                    "type": "text",
                    "text": "💡 每個病人購買的顆數都不一樣，系統會依您輸入的數字為您精準試算剩餘天數並啟動安全警報！",
                    "size": "xs",
                    "color": "#64748B",
                    "wrap": True
                }
            ]
        }
    }

def get_profile_summary_flex(user_id):
    p = user_profiles.get(user_id, {
        "hosp": "三軍總醫院", "cancer": "早期乳癌", "dose": 2, "stock": 21, "code": "KSQ-8821", "pharmacy": "躍獅寶湖藥局"
    })
    dose = p.get("dose", 2)
    stock = p.get("stock", 21)
    days = stock // dose if dose > 0 else 999
    is_alert = days <= 14 and dose > 0

    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#065F46" if not is_alert else "#B45309",
            "contents": [
                {"type": "text", "text": "🎉 建檔完成！您的專屬擊癌利存摺", "weight": "bold", "color": "#FFFFFF", "size": "sm"},
                {"type": "text", "text": f"病友專屬代號：{p.get('code', 'KSQ-8821')}", "color": "#E6FFFA", "size": "xs", "margin": "xs"}
            ]
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {
                    "type": "box", "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "就診醫院", "size": "xs", "color": "#64748B", "flex": 2},
                        {"type": "text", "text": p.get("hosp", "三軍總醫院"), "size": "xs", "color": "#0F172A", "weight": "bold", "flex": 4}
                    ]
                },
                {
                    "type": "box", "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "治療類型", "size": "xs", "color": "#64748B", "flex": 2},
                        {"type": "text", "text": p.get("cancer", "早期乳癌"), "size": "xs", "color": "#0F172A", "flex": 4}
                    ]
                },
                {
                    "type": "box", "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "每日劑量", "size": "xs", "color": "#64748B", "flex": 2},
                        {"type": "text", "text": f"每日 {dose} 顆 ({dose*200}mg)", "size": "xs", "color": "#0F172A", "weight": "bold", "flex": 4}
                    ]
                },
                {
                    "type": "box", "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "手邊存藥", "size": "xs", "color": "#64748B", "flex": 2},
                        {"type": "text", "text": f"{stock} 顆（預估可服 {days} 天）", "size": "xs", "color": "#B91C1C" if is_alert else "#0F172A", "weight": "bold", "flex": 4}
                    ]
                },
                {
                    "type": "box", "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "對應藥局", "size": "xs", "color": "#64748B", "flex": 2},
                        {"type": "text", "text": p.get("pharmacy", "躍獅寶湖藥局"), "size": "xs", "color": "#047857", "weight": "bold", "flex": 4}
                    ]
                },
                {"type": "separator", "margin": "md"},
                {
                    "type": "text",
                    "text": "⚠️【安全提醒】目前存藥不足兩週！回診請記得請醫師補開處方！" if is_alert else "✅ 存藥充足（大於兩週），請依醫囑安心服藥！",
                    "size": "xs", "color": "#B45309" if is_alert else "#059669", "wrap": True
                }
            ]
        },
        "footer": {
            "type": "box", "layout": "horizontal", "spacing": "sm",
            "contents": [
                {
                    "type": "button", "style": "primary", "color": "#991B1B", "height": "sm",
                    "action": {"type": "uri", "label": "📱 開啟完整存摺", "uri": "https://kisqali-care-bot.onrender.com/"}
                },
                {
                    "type": "button", "style": "secondary", "height": "sm",
                    "action": {"type": "postback", "label": "⚙️ 重新建檔", "data": "action=onboard"}
                }
            ]
        }
    }

@app.route("/", methods=["GET"])
def index():
    if os.path.exists("index.html"):
        return send_from_directory(".", "index.html")
    return jsonify({"status": "online", "system": "擊癌利病患照護小管家"}), 200

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        app.logger.error(f"Error handling webhook: {e}")

    return "OK", 200

@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data
    user_id = event.source.user_id
    reply_token = event.reply_token

    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "hosp": "三軍總醫院", "cancer": "早期乳癌", "dose": 2, "stock": 21, "code": "KSQ-8821", "pharmacy": "躍獅寶湖藥局"
        }

    # 六宮格按鍵 6: 病友建檔
    if data == "action=onboard":
        flex = get_onboarding_step1_flex()
        line_bot_api.reply_message(reply_token, FlexSendMessage(alt_text="✨ 新病友開戶建檔", contents=flex))

    # 步驟 1 點選醫院
    elif data.startswith("set_hosp="):
        hosp_key = data.replace("set_hosp=", "").strip()
        hosp_info = HOSPITALS.get(hosp_key, HOSPITALS["三總"])
        user_profiles[user_id]["hosp"] = hosp_info["name"]
        user_profiles[user_id]["pharmacy"] = hosp_info["pharmacy"]

        flex = get_onboarding_step2_flex(hosp_info["name"])
        line_bot_api.reply_message(reply_token, FlexSendMessage(alt_text="✨ 請選擇治療類型", contents=flex))

    # 步驟 2 點選治療類型
    elif data.startswith("set_cancer="):
        c_type = data.replace("set_cancer=", "").strip()
        user_profiles[user_id]["cancer"] = c_type

        flex = get_onboarding_step3_flex(c_type)
        line_bot_api.reply_message(reply_token, FlexSendMessage(alt_text="✨ 請選擇每日劑量", contents=flex))

    # 步驟 3 點選劑量
    elif data.startswith("set_dose="):
        dose_val = int(data.replace("set_dose=", "").strip())
        user_profiles[user_id]["dose"] = dose_val

        flex = get_onboarding_step4_flex(f"每日 {dose_val} 顆")
        line_bot_api.reply_message(reply_token, FlexSendMessage(alt_text="✨ 請輸入現有存藥顆數", contents=flex))

    # 六宮格按鍵 1: 我的存摺
    elif data == "action=passbook":
        flex = get_profile_summary_flex(user_id)
        line_bot_api.reply_message(reply_token, FlexSendMessage(alt_text="📕 您的擊癌利存摺", contents=flex))

    # 六宮格按鍵 4: 劑量調整
    elif data == "action=dose":
        dose_flex = {
            "type": "bubble",
            "header": {
                "type": "box", "layout": "vertical", "backgroundColor": "#C2410C",
                "contents": [
                    {"type": "text", "text": "⚙️ 醫師調整劑量", "weight": "bold", "color": "#FFFFFF", "size": "md"},
                    {"type": "text", "text": "回報副作用不適・依醫囑調整每日顆數", "color": "#FFEDD5", "size": "xs", "margin": "xs"}
                ]
            },
            "body": {
                "type": "box", "layout": "vertical", "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "請直接點選本次門診醫師開立之最新劑量：", "size": "xs", "color": "#64748B"},
                    {"type": "button", "style": "primary", "color": "#1E293B", "height": "sm", "action": {"type": "postback", "label": "3 顆 / 天 (600mg 起始劑量)", "data": "set_dose=3", "displayText": "改為 3 顆"}},
                    {"type": "button", "style": "primary", "color": "#334155", "height": "sm", "action": {"type": "postback", "label": "2 顆 / 天 (400mg 標準/一級減量)", "data": "set_dose=2", "displayText": "改為 2 顆"}},
                    {"type": "button", "style": "primary", "color": "#475569", "height": "sm", "action": {"type": "postback", "label": "1 顆 / 天 (200mg 二級減量)", "data": "set_dose=1", "displayText": "改為 1 顆"}},
                    {"type": "button", "style": "primary", "color": "#D97706", "height": "sm", "action": {"type": "postback", "label": "暫停服藥 (副作用休養，不扣庫存)", "data": "set_dose=0", "displayText": "暫停服藥"}}
                ]
            }
        }
        line_bot_api.reply_message(reply_token, FlexSendMessage(alt_text="⚙️ 醫師調整劑量", contents=dose_flex))

    # 六宮格按鍵 3: 門診速報
    elif data == "action=doctor":
        p = user_profiles.get(user_id, {"hosp": "三軍總醫院", "cancer": "早期乳癌", "dose": 2, "stock": 21, "code": "KSQ-8821"})
        dose = p.get("dose", 2)
        stock = p.get("stock", 21)
        days = stock // dose if dose > 0 else 999
        doc_flex = {
            "type": "bubble",
            "header": {
                "type": "box", "layout": "vertical", "backgroundColor": "#1E293B",
                "contents": [
                    {"type": "text", "text": "🏥 擊癌利門診速報卡", "weight": "bold", "color": "#FFFFFF", "size": "md"},
                    {"type": "text", "text": "出示供主治醫師快速評估療程", "color": "#94A3B8", "size": "xs", "margin": "xs"}
                ]
            },
            "body": {
                "type": "box", "layout": "vertical", "spacing": "sm",
                "contents": [
                    {"type": "text", "text": f"病友代號：{p.get('code', 'KSQ-8821')} ｜ 醫院：{p.get('hosp', '三軍總醫院')}", "size": "xs", "weight": "bold", "color": "#991B1B"},
                    {"type": "text", "text": f"治療類型：{p.get('cancer', '早期乳癌')} (第 1 階段 買 1 送 1)", "size": "xs", "color": "#334155"},
                    {"type": "text", "text": f"目前劑量：每日 {dose} 顆 ({dose*200}mg)", "size": "sm", "weight": "bold", "color": "#0F172A"},
                    {"type": "text", "text": f"手邊存藥：{stock} 顆（預估剩餘 {days} 天）", "size": "sm", "weight": "bold", "color": "#B91C1C" if days <= 14 else "#0F172A"},
                    {"type": "separator", "margin": "md"},
                    {"type": "text", "text": "⚠️ 建議醫師本次門診開立自費處方補藥！" if days <= 14 else "✅ 存藥充足（大於兩週）", "size": "xs", "weight": "bold", "color": "#B45309" if days <= 14 else "#059669"}
                ]
            }
        }
        line_bot_api.reply_message(reply_token, FlexSendMessage(alt_text="🏥 擊癌利門診速報卡", contents=doc_flex))

    # 六宮格按鍵 5: 領藥流程
    elif data == "action=sop":
        p = user_profiles.get(user_id, {"hosp": "三軍總醫院", "pharmacy": "躍獅寶湖藥局"})
        hosp_key = "基隆長庚" if "長庚" in p.get("hosp", "") else ("汐止國泰" if "國泰" in p.get("hosp", "") else "三總")
        ph_info = HOSPITALS.get(hosp_key, HOSPITALS["三總"])
        sop_flex = {
            "type": "bubble",
            "header": {
                "type": "box", "layout": "vertical", "backgroundColor": "#854D0E",
                "contents": [
                    {"type": "text", "text": "📬 贈藥申請 ＆ 領藥流程", "weight": "bold", "color": "#FFFFFF", "size": "md"},
                    {"type": "text", "text": f"您指定的領藥藥局：{ph_info['pharmacy']}", "color": "#FEF3C7", "size": "xs", "margin": "xs"}
                ]
            },
            "body": {
                "type": "box", "layout": "vertical", "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "1️⃣ 填寫同意書：醫師黃框(日期必手寫) + 病患紅框 + 粉紅聯撕下自留", "size": "xs", "wrap": True, "color": "#334155"},
                    {"type": "text", "text": "2️⃣ 摺疊免郵信封：免貼郵票投郵筒，寄至【永欣生技顧問】(02-8780-3236)", "size": "xs", "wrap": True, "color": "#334155"},
                    {"type": "text", "text": "3️⃣ 接獲 SMS 簡訊：攜帶簡訊與健保卡至指定院外藥局領藥 (3個月內有效)", "size": "xs", "wrap": True, "color": "#334155"},
                    {"type": "separator", "margin": "sm"},
                    {"type": "text", "text": f"📍 藥局地址：{ph_info['address']}", "size": "xs", "color": "#0F172A", "weight": "bold", "wrap": True},
                    {"type": "text", "text": f"☎️ 藥局電話：{ph_info['phone']}", "size": "xs", "color": "#991B1B", "weight": "bold"}
                ]
            },
            "footer": {
                "type": "box", "layout": "horizontal",
                "contents": [
                    {"type": "button", "style": "primary", "color": "#854D0E", "height": "sm", "action": {"type": "uri", "label": "📞 致電藥局", "uri": f"tel:{ph_info['phone'].replace('-', '')}"}}
                ]
            }
        }
        line_bot_api.reply_message(reply_token, FlexSendMessage(alt_text="📬 贈藥申請與領藥流程", contents=sop_flex))

    # 六宮格按鍵 2: 購藥登記
    elif data == "action=receipt":
        line_bot_api.reply_message(reply_token, TextSendMessage(text="🧾【購藥收據登記】\n請直接在聊天室輸入本次購買顆數，例如打「21」或「14」！多出的顆數將自動為您滾入下一期繼續累積！"))

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id
    reply_token = event.reply_token

    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "hosp": "三軍總醫院", "cancer": "早期乳癌", "dose": 2, "stock": 21, "code": "KSQ-8821", "pharmacy": "躍獅寶湖藥局"
        }

    # 只要使用者輸入純數字，立即當作【手邊存藥顆數】並秒產出專屬存摺卡片！
    if any(c.isdigit() for c in text):
        num = int("".join([c for c in text if c.isdigit()]))
        user_profiles[user_id]["stock"] = num
        flex = get_profile_summary_flex(user_id)
        line_bot_api.reply_message(reply_token, FlexSendMessage(alt_text="🎉 建檔完成！您的專屬擊癌利存摺", contents=flex))
    else:
        flex = get_onboarding_step1_flex()
        line_bot_api.reply_message(reply_token, FlexSendMessage(alt_text="✨ 歡迎使用擊癌利小管家", contents=flex))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
