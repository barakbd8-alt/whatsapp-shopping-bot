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

def analyze_text_with_gemini(user_text):
    """פונקציה חסינה לפנייה ל-Gemini"""
    # שליפת המפתח בצורה בטוחה
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY is missing in Render Environment!")
        return "חלב, אורז"  # גיבוי זמני כדי שהבוט יעבוד גם אם המפתח חסר
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        תפקידך לזהות מתוך הטקסט של המשתמש אך ורק את מוצרי הבסיס הבאים: חלב, קפה, חיתולים, אורז, שמן זית.
        תחזיר כפלט אך ורק את המילים המדויקות מתוך הרשימה הזו, מופרדות בפסיקים. אם אין אף מוצר, תחזיר 'רירק'.
        טקסט המשתמש: "{user_text}"
        """
        
        response = model.generate_content(prompt)
        print(f"🤖 Gemini response: {response.text}")
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        # אם יש שגיאת תקשורת עם גוגל, נעשה בדיקה ידנית פשוטה כגיבוי למילים עצמן
        return user_text

@app.route("/bot", methods=["POST"])
def whatsapp_bot():
    user_msg = request.values.get('Body', '').strip()
    print(f"📱 New WhatsApp message: {user_msg}")
    
    gemini_analysis = analyze_text_with_gemini(user_msg)
    
    resp = MessagingResponse()
    msg = resp.message()
    
    reply = "🤖 סוכן ה-AI מצא את המחירים הבאים:\n\n"
    found_any = False
    
    for item in MOCK_PRICES.keys():
        if item in gemini_analysis or item in user_msg:
            found_any = True
            reply += f"🛒 מצרך: *{item}*\n"
            for store, price in MOCK_PRICES[item].items():
                reply += f"- ב-{store} זה עולה ₪{price}\n"
            reply += "\n"
            
    if not found_any:
        reply = f"היי! קיבלתי: '{user_msg}'. לא זיהיתי מוצרים מהרשימה (חלב, קפה, חיתולים, אורז, שמן זית)."

    msg.body(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)

