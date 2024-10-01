from flask import Flask, request, abort
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
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

if __name__ == "__main__":
    app.run()
