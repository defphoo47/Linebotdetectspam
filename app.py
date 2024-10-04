from flask import Flask, request, abort
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from linebot import LineBotApi, WebhookHandler
from pythainlp.tokenize import word_tokenize
from tensorflow.keras.preprocessing.sequence import pad_sequences
import joblib

#model = keras.models.load_model('thai_spam_naive_bayes_model.pkl')

model = joblib.load('thai_spam_naive_bayes_model.pkl')
tokenizer = joblib.load('tokenizer.pkl')

app = Flask(__name__)

# ใส่ Channel Access Token และ Channel Secret ที่ได้จาก LINE Developers Console
line_bot_api = LineBotApi('3bNl87afW/9Tvtm6Qul5kCWNadqXzCTBxrEUA2pb21oHT8rS8c8qviCTaTq9USfTCieDE9AWDx6uHin/D0cp1nzLE3MUTsXghmem9EIVKdAuBUpushZu8ivx8JjQip9bJSp3OyB+kT2/B2TJpCqgagdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('2b350201322be0a84b137e8f990971f2')

def predict_spam(text):
    # ตัดคำและแปลงข้อความเป็น sequence
    text_tokenized = ' '.join(word_tokenize(text, engine='newmm'))
    text_seq = tokenizer.texts_to_sequences([text_tokenized])

    # แปลง sequence ให้มีขนาดเท่ากับที่ใช้ในการฝึกโมเดล
    max_len = 100  # ความยาว sequence ที่ใช้ในการฝึกโมเดล
    text_pad = pad_sequences(text_seq, maxlen=max_len)

    # ขั้นตอนที่ 3: ทำนายผลลัพธ์ด้วยโมเดล
    prediction = model.predict(text_pad)

    # แปลงผลลัพธ์ให้อยู่ในรูปแบบของ binary (0 หรือ 1)
    predicted_label = (prediction > 0.5).astype(int)
    return "สแปม" if predicted_label == 1 else "ไม่ใช่สแปม"


@app.route("/callback", methods=['POST'])
def callback():
    # รับ X-Line-Signature จาก Header
    signature = request.headers['X-Line-Signature']

    # รับ request body
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    
    user_message = event.message.text
    # ตรวจสอบข้อความว่าสแปมหรือไม่
    prediction = predict_spam(user_message)
    
    if user_message.lower() == "start":  
        liff_url = "https://liff.line.me/2006400968-Egavp321"  # ใส่ LIFF ID ของคุณใน URL นี้
        
        # สร้าง Flex Message สำหรับเปิด LIFF
        flex_message = FlexSendMessage(
            alt_text='บอทกากเองจั๊ฟ~',
            contents={
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": "https://cdn.discordapp.com/attachments/1289990276269473816/1289991201327415416/bot.png?ex=66fad56d&is=66f983ed&hm=800703b9aa397b06b02020d169c596cd935cb87103d18c29b76e33fe5a289517&",  # แทนที่ด้วย URL ของภาพที่ต้องการ
                    "size": "full",
                    "aspectRatio": "20:13",
                    "aspectMode": "cover"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "บอทกากสวัสดีจั๊ฟ~",
                            "weight": "bold",
                            "size": "xl",
                            "margin": "md",
                            "color": "#000000"
                        },
                        {
                            "type": "text",
                            "text": "BotKAK",
                            "size": "md",
                            "color": "#666666"
                        },
                        {
                            "type": "separator"
                        },
                        {
                            "type": "text",
                            "text": "ยินดีที่ได้รู้จัก\nเรียกใช้บอทกากได้ตลอดเลยจั๊ฟ ❤️\nบอทกากช่วยทำได้ไม่กี่อย่างเอง 😭",
                            "wrap": True,
                            "margin": "md",
                            "color": "#000000"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "md",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "• ตรวจสอบข้อความว่าเป็นสแปมไหม",
                                    "wrap": True
                                },
                                {
                                    "type": "text",
                                    "text": "• ความจริงก็อยากจะเตะคนทิ้งด้วยแหละ",
                                    "wrap": True
                                },
                                {
                                    "type": "text",
                                    "text": "• แต่บอทกากสมชื่อ",
                                    "wrap": True
                                },
                            ]
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary",
                            "action": {
                                "type": "uri",
                                "label": "คลิกเพื่อดูเว็บ BotKAK",
                                "uri": liff_url  # แทนที่ด้วย URL ที่ต้องการ
                            },
                            "color": "#FFBB33"
                        }
                    ]
                }
            }
        )

        # ส่ง Flex Message เพื่อเปิด LIFF
        line_bot_api.reply_message(
            event.reply_token,flex_message
        )
    else : 
        if prediction == "สแปม":
            reply_text = f"ข้อความนี้อาจเป็นสแปม: ''{user_message}'' "
        else:
            #reply_text = "ข้อความของคุณได้รับการตรวจสอบแล้วและไม่เป็นสแปม"
            pass
            # ตอบกลับผู้ใช้
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
    )

if __name__ == '__main__':
    app.run(debug=True)
