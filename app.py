import os
import json
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests

app = Flask(__name__)

# קובץ מקומי קטן שישמש כ"זיכרון" זמני של השרת
MEMORY_FILE = "user_memory.json"

def save_user_location(phone, lat, lng):
    """שומר את המיקום האחרון של המשתמש לפי מספר הטלפון שלו"""
    data = {}
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
    data[phone] = {"lat": lat, "lng": lng}
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f)

def get_user_location(phone):
    """שולף את המיקום השמור של המשתמש"""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
            return data.get(phone)
    return None

def get_nearby_stores(lat, lng):
    """מוצא סופרמרקטים ברדיוס של 20 דקות נסיעה באמצעות Google Maps"""
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return ["שופרסל (דוגמה)", "רמי לוי (דוגמה)"] # גיבוי אם אין מפתח
        
    # 1. חיפוש סופרמרקטים ברדיוס של 5 ק"מ (בערך 15-20 דקות נסיעה עירונית)
    places_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=5000&type=supermarket&key={api_key}"
    
    try:
        response = requests.get(places_url).json()
        results = response.get("results", [])
        
        stores = []
        for place in results[:4]: # ניקח את 4 הסופרים הקרובים ביותר
            stores.append(place["name"])
        return stores if stores else ["שופרסל מקומי", "רמי לוי מקומי"]
    except Exception as e:
        print(f"Error fetching from Google Maps: {e}")
        return ["סופרמרקט מקומי"]

@app.route("/bot", methods=["POST"])
def whatsapp_bot():
    phone = request.values.get('From', '') # מספר הטלפון של המשתמש
    latitude = request.values.get('Latitude')
    longitude = request.values.get('Longitude')
    
    resp = MessagingResponse()
    msg = resp.message()
    
    # תרחיש א': המשתמש שלח מיקום
    if latitude and longitude:
        save_user_location(phone, latitude, longitude)
        reply = "📍 המיקום שלך נשמר במערכת!\n\nעכשיו שלח לי את רשימת הקניות שלך (למשל: 'חלב ואורז') ואני אבדוק את הסופרים הכי זולים בטווח נסיעה שלך."
        msg.body(reply)
        return str(resp)

    # תרחיש ב': המשתמש שלח טקסט (רשימת קניות)
    user_msg = request.values.get('Body', '').strip()
    
    # בדיקה האם יש לנו מיקום שמור עבור המשתמש הזה
    saved_location = get_user_location(phone)
    
    if not saved_location:
        # אם אין מיקום שמור, נבקש קודם כל מיקום
        reply = "👋 היי! כדי שאוכל למצוא עבורך סופרים בטווח של 20 דקות נסיעה, אנא שלח לי קודם כל את המיקום שלך בוואטסאפ (לחץ על ה-'+' -> מיקום)."
        msg.body(reply)
        return str(resp)
        
    # אם יש מיקום שמור, נשלוף את הסופרים הקרובים אליו באמת
    nearby_stores = get_nearby_stores(saved_location["lat"], saved_location["lng"])
    
    # סימולציית מחירים זמנית על הסופרים האמיתיים שמצאנו סביבו
    reply = f"🤖 מצאתי {len(nearby_stores)} סופרמרקטים בטווח נסיעה ממך!\nהנה השוואת מחירים עבור: *{user_msg}*\n\n"
    
    # רשימת מחירים מדומה שמושלכת על החנויות האמיתיות מהמפה
    mock_prices = {"חלב": 6.40, "אורז": 8.90, "קפה": 18.50}
    
    for store in nearby_stores:
        reply += f"🏪 *{store}*:\n"
        total_price = 0
        for item, price in mock_prices.items():
            if item in user_msg:
                reply += f"  - {item}: ₪{price}\n"
                total_price += price
        if total_price > 0:
            reply += f"  💰 *סך הכל מוערך: ₪{total_price}*\n\n"
        else:
            reply += "  - לא נמצאו מחירי מוצרים מוגדרים.\n\n"

    msg.body(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)
