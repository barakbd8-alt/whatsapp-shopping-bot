import os
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# מאגר מחירים זמני (בהמשך נחליף למאגר ארצי)
MOCK_PRICES = {
    "חלב": {"שופרסל שלי": 6.20, "רמי לוי": 5.90, "יוחננוף": 5.90, "ויקטורי": 6.10},
    "קפה": {"שופרסל שלי": 19.90, "רמי לוי": 16.90, "יוחננוף": 17.50, "ויקטורי": 18.00},
    "אורז": {"שופרסל שלי": 9.90, "רמי לוי": 7.90, "יוחננוף": 8.20, "ויקטורי": 8.50}
}

def get_nearby_stores(lat, lng):
    """מוצא סופרמרקטים ברדיוס נסיעה של עד 20 דקות באמצעות Google Maps"""
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return []
        
    # 1. חיפוש סופרמרקטים קרובים פיזית
    places_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=5000&type=supermarket&key={api_key}"
    try:
        places_res = requests.get(places_url).json()
        results = places_res.get('results', [])[:5] # ניקח את 5 הסופרים הכי קרובים
        
        if not results:
            return []
            
        # 2. חישוב זמן נסיעה באוטו לכל סופרמרקט
        destinations = "|".join([f"{r['geometry']['location']['lat']},{r['geometry']['location']['lng']}" for r in results])
        dist_url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={lat},{lng}&destinations={destinations}&mode=driving&key={api_key}"
        dist_res = requests.get(dist_url).json()
        
        valid_stores = []
        rows = dist_res.get('rows', [{}])[0].get('elements', [])
        
        for i, element in enumerate(rows):
            if element.get('status') == 'OK':
                duration_mins = element['duration']['value'] / 60 # המרה לשקות
                # פילטר: רק חנויות בטווח של 20 דקות נסיעה באוטו
                if duration_mins <= 20:
                    store_name = results[i]['name']
                    # ננסה "לנרמל" את השם לרשתות מוכרות
                    matched_chain = "רמי לוי"
                    if "shufersal" in store_name.lower() or "שופרסל" in store_name:
                        matched_chain = "שופרסל שלי"
                    elif "yochananof" in store_name.lower() or "יוחננוף" in store_name:
                        matched_chain = "יוחננוף"
                    elif "victory" in store_name.lower() or "ויקטורי" in store_name:
                        matched_chain = "ויקטורי"
                        
                    valid_stores.append({
                        "name": store_name,
                        "chain": matched_chain,
                        "duration": round(duration_mins)
                    })
        return valid_stores
    except Exception as e:
        print(f"Maps API Error: {e}")
        return []

@app.route("/bot", methods=["POST"])
def whatsapp_bot():
    latitude = request.values.get('Latitude')
    longitude = request.values.get('Longitude')
    
    resp = MessagingResponse()
    msg = resp.message()
    
    # אם המשתמש שלח מיקום
    if latitude and longitude:
        stores = get_nearby_stores(latitude, longitude)
        if not stores:
            reply = "📍 קיבלתי מיקום, אך לא מצאתי סופרמרקטים ברדיוס של 20 דקות נסיעה, או שמפתח המפות חסר."
        else:
            reply = "📍 *מצאתי את הסופרים הבאים בטווח של 20 דקות נסיעה:* \n\n"
            for s in stores:
                reply += f"🏪 *{s['name']}* ({s['duration']} דקות נסיעה באוטו)\n"
            reply += "\n🛒 שלח לי עכשיו רשימת מוצרים (למשל: 'חלב ואורז') כדי שאחשב איפה הכי זול לך לקנות!"
            
        msg.body(reply)
        return str(resp)

    # אם המשתמש שלח טקסט (רשימת מוצרים)
    user_msg = request.values.get('Body', '').strip()
    
    reply = "🛒 *תוצאות השוואת המחירים עבור הסל שלך:* \n\n"
    found_any = False
    
    # חישוב עלויות כלליות לפי רשת
    totals = {"שופרסל שלי": 0, "רמי לוי": 0, "יוחננוף": 0, "ויקטורי": 0}
    
    for item in MOCK_PRICES.keys():
        if item in user_msg:
            found_any = True
            reply += f"🔹 *{item}:*\n"
            for chain, price in MOCK_PRICES[item].items():
                reply += f" - {chain}: ₪{price}\n"
                totals[chain] += price
            reply += "\n"
            
    if found_any:
        reply += "📊 *סך הכל עבור כל הסל שלך:*\n"
        cheapest_chain = min(totals, key=totals.get)
        for chain, total in totals.items():
            if chain == cheapest_chain:
                reply += f"🏆 *{chain}: ₪{round(total, 2)} (הכי זול!)*\n"
            else:
                reply += f" ⁃ {chain}: ₪{round(total, 2)}\n"
    else:
        reply = "היי! כדי להתחיל, שלח לי קודם את המיקום שלך בוואטסאפ 📍 כדי שאמצא חנויות בטווח של 20 דקות."

    msg.body(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)
