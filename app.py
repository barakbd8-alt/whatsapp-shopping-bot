import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai

app = Flask(__name__)

# מסד נתונים זמני
MOCK_PRICES = {
    "חלב": {"סופר זול": 6.20, "מגה סופר": 6.80},
    "קפה": {"סופר זול": 16.90, "מגה סופר": 21.00},
    "חיתולים": {"סופר זול": 32.00, "מגה סופר": 38.00},
    "אורז": {"סופר זול": 8.50, "מגה סופר": 9.90},
    "שמן זית": {"סופר זול": 29.90, "מגה סופר": 34.90}
}

@app.route("/bot", methods=["POST"])
def whatsapp_bot():
    # בדיקה האם המשתמש שלח מיקום (וואטסאפ שולח קווי רוחב ואורך)
    latitude = request.values.get('Latitude')
    longitude = request.values.get('Longitude')
    
    resp = MessagingResponse()
    msg = resp.message()
    
    if latitude and longitude:
        # המשתמש שלח מיקום!
        print(f"📍 Received location: Lat {latitude}, Lng {longitude}")
        reply = f"📍 המיקום שלך התקבל בהצלחה!\nקו רוחב: {latitude}\nקו אורך: {longitude}\n\nבשלב הבא אני אסרוק את הסופרים ברדיוס של 20 דקות מהנקודה הזו!"
        msg.body(reply)
        return str(resp)

    # אם זה טקסט רגיל ולא מיקום, נריץ את הלוגיקה הרגילה של הבוט
    user_msg = request.values.get('Body', '').strip()
    print(f"📱 New WhatsApp message: {user_msg}")
    
    reply = "🤖 סוכן ה-AI מצא את המחירים הבאים:\n\n"
    found_any = False
    
    for item in MOCK_PRICES.keys():
        if item in user_msg:
            found_any = True
            reply += f"🛒 מצרך: *{item}*\n"
            for store, price in MOCK_PRICES[item].items():
                reply += f"- ב-{store} זה עולה ₪{price}\n"
            reply += "\n"
            
    if not found_any:
        reply = f"היי! כדי שאדע אילו סופרים קרובים אליך ברדיוס של 20 דקות, אנא שלח לי את המיקום הנוכחי שלך בוואטסאפ (באמצעות כפתור ה'+' -> מיקום)."

    msg.body(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)
