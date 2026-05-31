from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# מסד נתונים זמני לבדיקה (חלב, קפה, חיתולים)
MOCK_PRICES = {
    "חלב": {"סופר זול": 6.20, "מגה סופר": 6.80},
    "קפה": {"סופר זול": 16.90, "מגה סופר": 21.00},
    "חיתולים": {"סופר זול": 32.00, "מגה סופר": 38.00}
}

@app.route("/bot", methods=["POST"])
def whatsapp_bot():
    # קבלת ההודעה שהמשתמש שלח בוואטסאפ
    user_msg = request.values.get('Body', '').strip().lower()
    
    # הכנת תגובה אוטומטית
    resp = MessagingResponse()
    msg = resp.message()
    
    reply = "היי! אני סוכן הקניות שלך. 🛒\n\n"
    
    # בדיקה פשוטה: אם המשתמש רשם מוצר שקיים אצלנו
    found = False
    for item, stores in MOCK_PRICES.items():
        if item in user_msg:
            found = True
            reply += f"מצאתי מחירים עבור *{item}*:\n"
            for store, price in stores.items():
                reply += f"- ב-{store} זה עולה ₪{price}\n"
    
    if not found:
        reply += f"קיבלתי את ההודעה: '{user_msg}'. בשלב הבא אני אלמד לחפש את זה בכל הסופרים בארץ הגדרת ה-AI!"

    msg.body(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)
