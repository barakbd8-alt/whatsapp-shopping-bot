import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai

app = Flask(__name__)

# הגדרת החיבור ל-Gemini באמצעות המפתח הסודי שהגדרנו ב-Render
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# מסד נתונים זמני מורחב (חלב, קפה, חיתולים)
MOCK_PRICES = {
    "חלב": {"סופר זול": 6.20, "מגה סופר": 6.80},
    "קפה": {"סופר זול": 16.90, "מגה סופר": 21.00},
    "חיתולים": {"סופר זול": 32.00, "מגה סופר": 38.00},
    "אורז": {"סופר זול": 8.50, "מגה סופר": 9.90},
    "שמן זית": {"סופר זול": 29.90, "מגה סופר": 34.90}
}

def analyze_text_with_gemini(user_text):
    """פונקציה ששולחת את הטקסט החופשי ל-Gemini ומבקשת ממנו לחלץ רק את מוצרי הבסיס"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    אתה עוזר קניות חכם. המשתמש כתב הודעה חופשית בוואטסאפ לגבי מוצרים שהוא צריך לקנות.
    התפקיד שלך הוא לזהות מתוך הטקסט שלו רק את מוצרי הבסיס הבאים שנמצאים במאגר שלנו: חלב, קפה, חיתולים, אורז, שמן זית.
    תחזיר כפלט אך ורק את המילים המדויקות מתוך הרשימה הזו, מופרדות בפסיקים. אם אין אף מוצר, תחזיר את המילה 'רירק'.
    הודעת המשתמש: "{user_text}"
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return "רירק"

@app.route("/bot", methods=["POST"])
def whatsapp_bot():
    user_msg = request.values.get('Body', '').strip()
    
    # שליחת ההודעה החופשית ל-Gemini כדי שיבין מה המשתמש רוצה
    gemini_analysis = analyze_text_with_gemini(user_msg)
    
    resp = MessagingResponse()
    msg = resp.message()
    
    reply = "🤖 סוכן ה-AI ניתח את ההודעה שלך:\n\n"
    found_any = False
    
    # מעבר על המוצרים ש-Gemini זיהה
    for item in MOCK_PRICES.keys():
        if item in gemini_analysis:
            found_any = True
            reply += f"🛒 מצאתי מחירים עבור *{item}*:\n"
            for store, price in MOCK_PRICES[item].items():
                reply += f"- ב-{store} זה עולה ₪{price}\n"
            reply += "\n"
            
    if not found_any:
        reply = f"היי! קיבלתי את ההודעה: '{user_msg}'. לא הצלחתי לזהות מוצרים מוכרים מהרשימה (חלב, קפה, חיתולים, אורז, שמן זית). נסה לכתוב משפט כמו: 'אני חייב לקנות דחוף חלב ואורז'."

    msg.body(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)
