# Testing result
<br>

## Edit 1
- โหลดโมเดลจากไฟล์ .h5 แทน .pkl
```python
# Edit 1 : **************************************************EDIT*************************************************
# โหลดโมเดลจากไฟล์ .h5 แทน .pkl
from tensorflow.keras.models import load_model
model = load_model('thai_spam_model.h5')
# model = joblib.load('thai_spam_naive_bayes_model.pkl') อันเก่า
# Edit 1 : **************************************************EDIT*************************************************
```
<br>


## Edit 2
- เกิดการสลับ ค่า ตอนส่งออกเป็น json
```python
def predict_spam(text):


    # Edit 2 : **************************************************EDIT*************************************************
    """
        จากเงื่อนไข จะทำให้เกิดการกำหนดค่า probability เป็นของ กรณีนั้นๆ(ham / spam)
        แต่ตอนนำไปใช้งานต่อจะต้องฟิกว่า ให้ return เป็น probability ของ spam สเมอ
        ไม่เช่นนั้น จะเกิดการสลับ ค่า ตอนส่งออกเป็น json
    """
    # probability = prediction[0][0] if predicted_label == 1 else 1 - prediction[0][0] อันเก่า
    probability = prediction[0][0] # แก้ใหม่ ฟิกเป็น probability ของ spam สเมอ

    # Edit 2 : **************************************************EDIT*************************************************
```
<br>

## Edit 3
- error: reply_text undefine
```python
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):


        # Edit 3 : **************************************************EDIT*************************************************
        """
           เกิด Bug เมื่อ ไม่ใข้ แสปม ตัวแปร reply_text ไม่ถูกสร้าง
           เมื่อข้ามไป ตรง ตอบกลับผู้ใช้ จึง error: reply_text undefine
        """

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

```
<br>

## Edit 4
- เกิด Bug เช็คว่า เป็น spam ตลอดเวลา
```python
@app.route('/predict', methods=['POST'])
def check_spam():


    # Edit 4 : **************************************************EDIT*************************************************
    """
        เกิด Bug เช็คว่า เป็น spam ตลอดเวลา
        predict_spam(text) จะ return ["สแปม"/"ไม่ใช่สแปม"] ไม่ใช่ [0/1]
        สาเหตุ : เพราะเงื่อนไข prediction == 1 เป็น การเทียบ (str)["สแปม"/"ไม่ใช่สแปม"] == (int)[1] ให้ผลลัพธฺ์เป็น true เสมอ
    """

    # prediction_text = "Spam" if prediction == 1 else "Not Spam" อันเก่า
    prediction_text = "Spam" if prediction == "สแปม" else "Not Spam" # แก้ใหม่

    # Edit 4 : **************************************************EDIT*************************************************

```
