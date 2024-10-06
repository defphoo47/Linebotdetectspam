from flask import Flask, request, abort, jsonify
from flask_cors import CORS
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from linebot import LineBotApi, WebhookHandler
from pythainlp.tokenize import word_tokenize
from tensorflow.keras.preprocessing.sequence import pad_sequences
import joblib

model = joblib.load('thai_spam_naive_bayes_model.pkl')
tokenizer = joblib.load('tokenizer.pkl')

app = Flask(__name__)

# เปิดใช้งาน CORS สำหรับทุกเส้นทาง (route)
CORS(app)

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

    # ทำนายผลลัพธ์ด้วยโมเดล
    prediction = model.predict(text_pad)

    # แปลงผลลัพธ์ให้อยู่ในรูปแบบของ binary (0 หรือ 1)
    predicted_label = (prediction > 0.5).astype(int)

    # คำนวณความน่าจะเป็น
    probability = prediction[0][0] if predicted_label == 1 else 1 - prediction[0][0]
    percentage = probability * 100  # แปลงเป็นเปอร์เซ็นต์
    return "สแปม" if predicted_label == 1 else "ไม่ใช่สแปม", round(percentage, 2)  # ปัดเศษ 2 ตำแหน่ง


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
    prediction, probability = predict_spam(user_message)
    
    if user_message.lower() == "start":  
        liff_url = "https://liff.line.me/2006400968-Egavp321"  # ใส่ LIFF ID ของคุณใน URL นี้
        
        # สร้าง Flex Message สำหรับเปิด LIFF
        flex_message = FlexSendMessage(
            alt_text='บอทกากเองจั๊ฟ~',
            contents={
                # เนื้อหา Flex Message
            }
        )

        # ส่ง Flex Message เพื่อเปิด LIFF
        line_bot_api.reply_message(
            event.reply_token, flex_message
        )
    else: 
        if prediction == "สแปม":
            reply_text = f"ข้อความนี้อาจเป็นสแปม: ''{user_message}'' "
        else:
            reply_text = "ข้อความของคุณไม่เป็นสแปม"

        # ตอบกลับผู้ใช้
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )

# สร้าง API ที่รับข้อมูลจาก front-end และทำนายสแปม
@app.route('/predict', methods=['POST'])
def check_spam():
    data = request.json
    if 'text' not in data:
        return jsonify({'error': 'กรุณาใส่ข้อความที่ต้องการตรวจสอบ'}), 400

    text = data['text']
    prediction, probability = predict_spam(text)
    
    # แปลง label เป็นข้อความที่ต้องการ
    prediction_text = "Spam" if prediction == 1 else "Not Spam"
    probability_percentage = probability   # เปลี่ยนเป็นเปอร์เซ็นต์
    not_spam_probability = 100 - probability_percentage  # ความน่าจะเป็นที่ไม่ใช่สแปม

    # สร้างการตอบกลับในรูปแบบที่ต้องการ
    response = {
        'message': text,
        'prediction': [
            prediction_text,
            probability_percentage,  # ความน่าจะเป็นในรูปแบบเปอร์เซ็นต์
            not_spam_probability  # ความน่าจะเป็นที่ไม่ใช่สแปม
        ]
    }
    
    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True)
