import os
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

def get_nearby_supermarkets(lat, lng):
    """פונקציה שפונה לגוגל מפות ומוצאת סופרים קרובים ברדיוס של כ-10 קילומטר (כ-20 דקות נסיעה)"""
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return ["❌ חסר מפתח הגדרה של Google Maps בשרת"]
        
    # רדיוס של 10,000 מטרים (10 ק"מ) תואם לטווח נסיעה של כ-20 דקות עירוני/פרברי
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=10000&type=supermarket&language=he&key={api_key}"
    
    try:
        response = requests.get(url).json()
        results = response.get("results", [])
        
        stores = []
        # לוקחים את 3 הסופרים הראשונים שהכי קרובים/פופולריים
        for place in results[:3]:
            name = place.get("name")
            vicinity = place.get("vicinity", "כתובת לא ידועה")
            stores.append(f"🏪 *{name}* - {vicinity}")
            
        if not stores:
            return ["לא מצאתי סופרמרקטים ברדיוס הקרוב אליך."]
        return stores
    except Exception as e:
        print(f"Error calling Google Places API: {e}")
        return ["שגיאה בסריקת החנויות סביבך."]

@app.route("/bot", methods=["POST"])
def whatsapp_bot():
    latitude = request.values.get('Latitude')
    longitude = request.values.get('Longitude')
    
    resp = MessagingResponse()
    msg = resp.message()
    
    if latitude and longitude:
        print(f"📍 Received location: Lat {latitude}, Lng {longitude}")
        
        # שליפת חנויות אמיתיות מגוגל מפות על בסיס המיקום של המשתמש
        nearby_stores = get_nearby_supermarkets(latitude, longitude)
        
        reply = "📍 המיקום שלך נקלט! הנה הסופרמרקטים הכי קרובים אליך בטווח נסיעה:\n\n"
        for store in nearby_stores:
            reply += f"{store}\n"
            
        reply += "\n🛒 שלח לי עכשיו את רשימת המוצרים שלך (למשל: 'חלב ואורז') כדי שנבדוק איפה הכי זול לקנות אותם מביניהם!"
        msg.body(reply)
        return str(resp)

    # לוגיקת הודעת טקסט רגילה (אם המשתמש שלח מוצרים)
    user_msg = request.values.get('Body', '').strip()
    reply = f"קיבלתי את הרשימה: '{user_msg}'. כדי שאדע להגיד לך איזה סופר מהסופרים באזור שלך הכי זול, שלח לי קודם את המיקום שלך בלחיצה על ה-'+' בוואטסאפ."
    msg.body(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)
