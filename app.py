from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

app = Flask(__name__)

# ✅ 從環境變數讀取金鑰（避免寫死）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ 初始化 LINE 與 OpenAI
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    # ✅ 印出請求內容與簽名方便 debug
    print("📩 [Request Body]:", body)
    print("🔐 [X-Line-Signature]:", signature)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ 驗證失敗：InvalidSignatureError")
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    print(f"🗣️ 收到用戶訊息：{user_message}")

    try:
        # 發送至 OpenAI ChatGPT 並取得回覆
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一個友善的校園助理。"},
                {"role": "user", "content": user_message}
            ]
        )
        reply_text = response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        reply_text = f"抱歉，GPT 連線錯誤：{e}"

    # 回覆用戶
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
