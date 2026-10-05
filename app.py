"""
擊癌利病患照護小管家 (Kisqali Care Bot) - 伺服器主程式
專屬責任醫院：基隆長庚醫院、三軍總醫院、汐止國泰醫院
"""

import os
import json
import logging
from flask import Flask, request, abort, jsonify, send_from_directory
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, ReplyMessageRequest,
    FlexMessage, FlexContainer, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

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

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
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
                {"type": "button", "style": "primary", "color": "#991B1B", "height": "sm", "action": {"type": "message", "label": "🏥 三軍總醫院（內湖/汀州/松山）", "text": "設定醫院：三總"}},
                {"type": "button", "style": "primary", "color": "#B91C1C", "height": "sm", "action": {"type": "message", "label": "🏥 基隆長庚醫院（基隆/情人湖）", "text": "設定醫院：基隆長庚"}},
                {"type": "button", "style": "primary", "color": "#DC2626", "height": "sm", "action": {"type": "message", "label": "🏥 汐止國泰醫院", "text": "設定醫院：汐止國泰"}}
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
                {"type": "text", "text": f"已選擇：{hospital_name} ｜ 【步驟 2/4】治療類型", "color": "#FEE2E2", "size": "xs", "margin": "xs"}
            ]
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                {"type": "text", "text": "請依主治醫師診斷點選您的治療階段：", "size": "xs", "color": "#64748B"},
                {"type": "button", "style": "primary", "color": "#059669", "height": "sm", "action": {"type": "message", "label": "🌸 早期乳癌（EBC・3年方案）", "text": "設定類型：早期乳癌"}},
                {"type": "button", "style": "primary", "color": "#D97706", "height": "sm", "action": {"type": "message", "label": "🎗️ 轉移晚期乳癌（MBC・5年方案）", "text": "設定類型：晚期乳癌"}}
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
                {"type": "text", "text": f"已選擇：{cancer_type} ｜ 【步驟 3/4】每日劑量", "color": "#FEE2E2", "size": "xs", "margin": "xs"}
            ]
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                {"type": "text", "text": "請依醫師處方點選每日服用顆數：", "size": "xs", "color": "#64748B"},
                {"type": "button", "style": "primary", "color": "#1E293B", "height": "sm", "action": {"type": "message", "label": "💊 每日 3 顆（600 mg）", "text": "設定劑量：3顆"}},
                {"type": "button", "style": "primary", "color": "#334155", "height": "sm", "action": {"type": "message", "label": "💊 每日 2 顆（400 mg）", "text": "設定劑量：2顆"}},
                {"type": "button", "style": "primary", "color": "#475569", "height": "sm", "action": {"type": "message", "label": "💊 每日 1 顆（200 mg）", "text": "設定劑量：1顆"}}
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
                {"type": "text", "text": f"已選擇劑量：{dose_str} ｜ 【步驟 4/4】手邊存藥", "color": "#FEE2E2", "size": "xs", "margin": "xs"}
            ]
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "text", "text": "請點選目前手邊約有多少顆藥，或直接輸入數字：", "size": "xs", "color": "#64748B"},
                {
                    "type": "box", "layout": "horizontal", "spacing": "sm",
                    "contents": [
                        {"type": "button", "style": "secondary", "height": "sm", "action": {"type": "message", "label": "14 顆", "text": "設定庫存：14"}},
                        {"type": "button", "style": "secondary", "height": "sm", "action": {"type": "message", "label": "21 顆", "text": "設定庫存：21"}},
                        {"type": "button", "style": "secondary", "height": "sm", "action": {"type": "message", "label": "42 顆", "text": "設定庫存：42"}}
                    ]
                },
                {
                    "type": "box", "layout": "horizontal", "spacing": "sm",
                    "contents": [
                        {"type": "button", "style": "secondary", "height": "sm", "action": {"type": "message", "label": "63 顆 (1盒)", "text": "設定庫存：63"}},
                        {"type": "button", "style": "secondary", "height": "sm", "action": {"type": "message", "label": "0 顆 (剛拿處方)", "text": "設定庫存：0"}}
                    ]
                },
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": "💡 亦可在聊天室直接輸入如「28」快速登記！", "size": "xxs", "color": "#94A3B8", "align": "center"}
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
                    "action": {"type": "message", "label": "⚙️ 重新建檔", "text": "病友建檔"}
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

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id
    reply_token = event.reply_token

    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "hosp": "三軍總醫院", "cancer": "早期乳癌", "dose": 2, "stock": 20, "code": "KSQ-8821", "pharmacy": "躍獅寶湖藥局"
        }

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        # 1. 點選「病友建檔」按鍵 ➔ 觸發【步驟 1：選擇醫院按鈕】
        if "建檔" in text:
            flex = get_onboarding_step1_flex()
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[FlexMessage(alt_text="✨ 新病友建檔 - 請選擇醫院", contents=FlexContainer.from_dict(flex))]
            ))

        # 接收醫院點選 (支援點擊「設定醫院：三總」或「三總」、「基隆長庚」、「汐止國泰」)
        elif "三總" in text or "長庚" in text or "國泰" in text:
            hosp_key = "基隆長庚" if "長庚" in text else ("汐止國泰" if "國泰" in text else "三總")
            hosp_info = HOSPITALS[hosp_key]
            user_profiles[user_id]["hosp"] = hosp_info["name"]
            user_profiles[user_id]["pharmacy"] = hosp_info["pharmacy"]

            flex = get_onboarding_step2_flex(hosp_info["name"])
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[FlexMessage(alt_text="✨ 請選擇治療類型", contents=FlexContainer.from_dict(flex))]
            ))

        # 接收類型點選 (支援「早期」或「晚期」)
        elif "早期" in text or "晚期" in text or "EBC" in text or "MBC" in text:
            c_type = "早期乳癌 (EBC)" if ("早期" in text or "EBC" in text) else "晚期乳癌 (MBC)"
            user_profiles[user_id]["cancer"] = c_type

            flex = get_onboarding_step3_flex(c_type)
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[FlexMessage(alt_text="✨ 請選擇每日劑量", contents=FlexContainer.from_dict(flex))]
            ))

        # 接收劑量點選 (支援「3顆」、「2顆」、「1顆」、「暫停」)
        elif any(k in text for k in ["3顆", "2顆", "1顆", "3 顆", "2 顆", "1 顆", "暫停"]):
            if "3" in text:
                dose = 3
            elif "1" in text:
                dose = 1
            elif "暫停" in text or "0" in text:
                dose = 0
            else:
                dose = 2
            user_profiles[user_id]["dose"] = dose

            flex = get_onboarding_step4_flex(f"{dose} 顆/天" if dose > 0 else "暫停服藥")
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[FlexMessage(alt_text="✨ 請選擇手邊存藥顆數", contents=FlexContainer.from_dict(flex))]
            ))

        # 接收庫存點選 (支援「庫存」、「顆」或純數字)
        elif "庫存" in text or "顆" in text or text.isdigit():
            num_part = "".join([c for c in text if c.isdigit()])
            stock_num = int(num_part) if num_part else 21
            user_profiles[user_id]["stock"] = stock_num

            flex = get_profile_summary_flex(user_id)
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[FlexMessage(alt_text="🎉 建檔成功！您的擊癌利存摺", contents=FlexContainer.from_dict(flex))]
            ))

        # 2. 擊癌利存摺
        elif "存摺" in text:
            flex = get_profile_summary_flex(user_id)
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[FlexMessage(alt_text="📕 您的擊癌利存摺", contents=FlexContainer.from_dict(flex))]
            ))

        # 3. 劑量調整
        elif "劑量" in text:
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
                        {"type": "button", "style": "primary", "color": "#1E293B", "height": "sm", "action": {"type": "message", "label": "3 顆 / 天 (600mg 起始劑量)", "text": "3顆"}},
                        {"type": "button", "style": "primary", "color": "#334155", "height": "sm", "action": {"type": "message", "label": "2 顆 / 天 (400mg 標準/一級減量)", "text": "2顆"}},
                        {"type": "button", "style": "primary", "color": "#475569", "height": "sm", "action": {"type": "message", "label": "1 顆 / 天 (200mg 二級減量)", "text": "1顆"}},
                        {"type": "button", "style": "primary", "color": "#D97706", "height": "sm", "action": {"type": "message", "label": "暫停服藥 (副作用休養，不扣庫存)", "text": "暫停服藥"}}
                    ]
                }
            }
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[FlexMessage(alt_text="⚙️ 醫師調整劑量", contents=FlexContainer.from_dict(dose_flex))]
            ))

        # 4. 門診速報
        elif "門診" in text or "速報" in text:
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
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[FlexMessage(alt_text="🏥 擊癌利門診速報卡", contents=FlexContainer.from_dict(doc_flex))]
            ))

        # 5. 領藥流程
        elif "領藥" in text or "流程" in text:
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
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[FlexMessage(alt_text="📬 贈藥申請與領藥流程", contents=FlexContainer.from_dict(sop_flex))]
            ))

        # 6. 購藥登記
        elif "購藥" in text or "收據" in text:
            rec_flex = {
                "type": "bubble",
                "header": {
                    "type": "box", "layout": "vertical", "backgroundColor": "#065F46",
                    "contents": [
                        {"type": "text", "text": "🧾 零存整付・購藥收據登記", "weight": "bold", "color": "#FFFFFF", "size": "md"},
                        {"type": "text", "text": "滿 63 顆贈送 1 盒 ｜ 多餘顆數自動滾入下期", "color": "#D1FAE5", "size": "xs", "margin": "xs"}
                    ]
                },
                "body": {
                    "type": "box", "layout": "vertical", "spacing": "sm",
                    "contents": [
                        {"type": "text", "text": "請直接點選本次購買顆數快速登記：", "size": "xs", "color": "#64748B"},
                        {
                            "type": "box", "layout": "horizontal", "spacing": "sm",
                            "contents": [
                                {"type": "button", "style": "primary", "color": "#059669", "height": "sm", "action": {"type": "message", "label": "+ 14 顆", "text": "14顆"}},
                                {"type": "button", "style": "primary", "color": "#059669", "height": "sm", "action": {"type": "message", "label": "+ 21 顆", "text": "21顆"}},
                                {"type": "button", "style": "primary", "color": "#059669", "height": "sm", "action": {"type": "message", "label": "+ 42 顆", "text": "42顆"}}
                            ]
                        },
                        {"type": "button", "style": "primary", "color": "#047857", "height": "sm", "action": {"type": "message", "label": "+ 63 顆 (自費整盒)", "text": "63顆"}}
                    ]
                }
            }
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[FlexMessage(alt_text="🧾 零存整付購藥登記", contents=FlexContainer.from_dict(rec_flex))]
            ))

        else:
            flex = get_onboarding_step1_flex()
            line_bot_api.reply_message(ReplyMessageRequest(
                reply_token=reply_token,
                messages=[FlexMessage(alt_text="✨ 歡迎使用擊癌利小管家", contents=FlexContainer.from_dict(flex))]
            ))
