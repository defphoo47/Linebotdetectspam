from flask import Flask, request, abort, jsonify
from flask_cors import CORS
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from linebot import LineBotApi, WebhookHandler
from pythainlp.tokenize import word_tokenize
import joblib
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Edit 1 : **************************************************EDIT*************************************************
# โหลดโมเดลจากไฟล์ .h5 แทน .pkl
from tensorflow.keras.models import load_model
model = load_model('thai_spam_model.h5')
# model = joblib.load('thai_spam_naive_bayes_model.pkl') อันเก่า
# Edit 1 : **************************************************EDIT*************************************************

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

    # Edit 2 : **************************************************EDIT*************************************************
    # จากเงื่อนไข จะทำให้เกิดการกำหนดค่า probability เป็นของ กรณีนั้นๆ(ham / spam)
    # แต่ตอนนำไปใช้งานต่อจะต้องฟิกว่า ให้ return เป็น probability ของ spam สเมอ
    # ไม่เช่นนั้น จะเกิดการสลับ ค่า ตอนส่งออกเป็น json

    # probability = prediction[0][0] if predicted_label == 1 else 1 - prediction[0][0] อันเก่า
    probability = prediction[0][0] # แก้ใหม่ ฟิกเป็น probability ของ spam สเมอ

    # Edit 2 : **************************************************EDIT*************************************************


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
            alt_text='ขุนทองภู่เอง~',
            contents={
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": "https://raw.githubusercontent.com/anasedf/AI_Frontend/refs/heads/main/src/assets/pro.jpg",  # แทนที่ด้วย URL ของภาพที่ต้องการ
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
                            "text": "ขุนทองภู่สวัสดี~",
                            "weight": "bold",
                            "size": "xl",
                            "margin": "md",
                            "color": "#000000"
                        },
                        {
                            "type": "text",
                            "text": "KhunThongPhu",
                            "weight": "bold",
                            "size": "md",
                            "color": "#8d414c"
                        },
                        {
                            "type": "separator"
                        },
                        {
                            "type": "text",
                            "text": "ยินดีที่ได้รู้จัก\nเรียกใช้ขุนทองภู่ได้ตลอดเลยนะ ❤️\n",
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
                                    "text": "• เพิ่มขุนทองภู่ลงในกลุ่มที่ต้องการเช็คเลย",
                                    "wrap": True
                                },
                                {
                                    "type": "text",
                                    "text": "• ตรวจสอบข้อความว่าเป็นสแปมไหม",
                                    "wrap": True
                                },
                                {
                                    "type": "text",
                                    "text": "• สามารถเยี่ยมชมเว็บไซต์ของเราได้",
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
                                "label": "คลิกเพื่อดูเว็บไซต์ KhunThongPhu",
                                "uri": liff_url  # แทนที่ด้วย URL ที่ต้องการ
                            },
                            "color": "#8d414c"
                        }
                    ]
                }
            }
        )

        # ส่ง Flex Message เพื่อเปิด LIFF
        line_bot_api.reply_message(
            event.reply_token, flex_message
        )
    else:

        # Edit 3 : **************************************************EDIT*************************************************
        # เกิด Bug เมื่อ ไม่ใข้ แสปม ตัวแปร reply_text ไม่ถูกสร้าง
        # เมื่อข้ามไป ตรง ตอบกลับผู้ใช้ จึง error: reply_text undefine

        if prediction == "สแปม":
            reply_text = f"ข้อความนี้อาจเป็นสแปม: ''{user_message}'' "

            # ตอบกลับผู้ใช้ แก้ใหม่
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )

        else:
            #reply_text = "ข้อความของคุณไม่เป็นสแปม"
            pass

        # ตอบกลับผู้ใช้   อันเก่าอยู่ตรงนี้
        # line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text=reply_text)
        # )
        # Edit 3 : **************************************************EDIT*************************************************
        

# สร้าง API ที่รับข้อมูลจาก front-end และทำนายสแปม
@app.route('/predict', methods=['POST'])
def check_spam():
    data = request.json
    if 'text' not in data:
        return jsonify({'error': 'กรุณาใส่ข้อความที่ต้องการตรวจสอบ'}), 400

    text = data['text']
    prediction, probability = predict_spam(text) # return ["สแปม"/"ไม่ใช่สแปม"]

    # แปลง label เป็นข้อความที่ต้องการ


    # Edit 4 : **************************************************EDIT*************************************************
    # เกิด Bug เช็คว่า เป็น spam ตลอดเวลา
    # predict_spam(text) จะ return ["สแปม"/"ไม่ใช่สแปม"] ไม่ใช่ [0/1]
    # สาเหตุ : เพราะเงื่อนไข prediction == 1 เป็น การเทียบ (str)["สแปม"/"ไม่ใช่สแปม"] == (int)[1] ให้ผลลัพธฺ์เป็น true เสมอ

    # prediction_text = "Spam" if prediction == 1 else "Not Spam" อันเก่า
    prediction_text = "Spam" if prediction == "สแปม" else "Not Spam" # แก้ใหม่

    # Edit 4 : **************************************************EDIT*************************************************

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
