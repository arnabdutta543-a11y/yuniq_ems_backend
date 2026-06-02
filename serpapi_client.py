import requests
from typing import Dict, List, Any
from config import settings

# MOCK DATASETS FOR MOCK_MODE
MOCK_FLIGHTS = {
    "SFO": [
        {"flight_num": "UA 830", "carrier": "United Airlines", "price": 980.0, "departure": "BOM 09:30 AM", "arrival": "SFO 01:15 PM", "duration": "17h 45m", "class": "Economy"},
        {"flight_num": "AI 173", "carrier": "Air India", "price": 850.0, "departure": "BOM 02:30 PM", "arrival": "SFO 07:00 PM", "duration": "16h 30m", "class": "Economy"},
        {"flight_num": "EK 225", "carrier": "Emirates", "price": 1200.0, "departure": "BOM 04:30 AM", "arrival": "SFO 02:00 PM (1 stop)", "duration": "21h 30m", "class": "Economy"},
    ],
    "LHR": [
        {"flight_num": "BA 198", "carrier": "British Airways", "price": 620.0, "departure": "BOM 01:15 PM", "arrival": "LHR 05:55 PM", "duration": "9h 10m", "class": "Economy"},
        {"flight_num": "VS 351", "carrier": "Virgin Atlantic", "price": 590.0, "departure": "BOM 10:10 AM", "arrival": "LHR 03:00 PM", "duration": "9h 20m", "class": "Economy"},
    ],
    "NRT": [
        {"flight_num": "JL 748", "carrier": "Japan Airlines", "price": 750.0, "departure": "DEL 07:00 PM", "arrival": "NRT 06:30 AM (+1)", "duration": "8h 00m", "class": "Economy"},
        {"flight_num": "NH 830", "carrier": "All Nippon Airways", "price": 820.0, "departure": "DEL 08:20 PM", "arrival": "NRT 07:50 AM (+1)", "duration": "8h 00m", "class": "Economy"},
    ],
}

MOCK_HOTELS = {
    "San Francisco": [
        {"name": "Hilton San Francisco Union Square", "price_per_night": 220.0, "rating": 4.2, "reviews": 1200, "thumbnail": "https://images.unsplash.com/photo-1566073771259-6a8506099945", "amenities": ["Free Wi-Fi", "Pool", "Gym", "Restaurant"]},
        {"name": "InterContinental San Francisco", "price_per_night": 290.0, "rating": 4.5, "reviews": 850, "thumbnail": "https://images.unsplash.com/photo-1540518614846-7eded433c457", "amenities": ["Free Wi-Fi", "Spa", "Pet-Friendly", "Bar"]},
        {"name": "The Marker San Francisco", "price_per_night": 180.0, "rating": 4.0, "reviews": 600, "thumbnail": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4", "amenities": ["Free Wi-Fi", "Bicycles", "Wine Hour"]},
    ],
    "London": [
        {"name": "The Tower Hotel London", "price_per_night": 195.0, "rating": 4.3, "reviews": 3200, "thumbnail": "https://images.unsplash.com/photo-1517840901100-8179e982acb7", "amenities": ["Free Wi-Fi", "Tower Bridge View", "Gym"]},
        {"name": "CitizenM Tower of London", "price_per_night": 160.0, "rating": 4.6, "reviews": 1500, "thumbnail": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa", "amenities": ["Free Wi-Fi", "Rooftop Bar", "iPad Control"]},
    ],
    "Tokyo": [
        {"name": "Shinjuku Granbell Hotel", "price_per_night": 140.0, "rating": 4.1, "reviews": 950, "thumbnail": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26", "amenities": ["Free Wi-Fi", "Rooftop Terrace", "Art Rooms"]},
        {"name": "Park Hyatt Tokyo", "price_per_night": 550.0, "rating": 4.8, "reviews": 1400, "thumbnail": "https://images.unsplash.com/photo-1596394516093-501ba68a0ba6", "amenities": ["Free Wi-Fi", "Indoor Pool", "Luxury Spa", "New York Grill"]},
    ]
}

def search_flights(departure_id: str, arrival_id: str, date: str) -> List[Dict[str, Any]]:
    """
    Search flights via SerpAPI Google Flights. Falls back to mock data if key not set.
    """
    if settings.is_mock_mode or not settings.SERPAPI_KEY:
        # Match arrival_id in mock database
        dest = arrival_id.upper()
        for key in MOCK_FLIGHTS:
            if key in dest or dest in key:
                return MOCK_FLIGHTS[key]
        # Return SFO default
        return MOCK_FLIGHTS["SFO"]
        
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_flights",
            "departure_id": departure_id,
            "arrival_id": arrival_id,
            "outbound_date": date,
            "currency": "USD",
            "hl": "en",
            "api_key": settings.SERPAPI_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        flights = []
        if "best_flights" in data:
            for flight in data["best_flights"]:
                legs = flight.get("flights", [])
                leg = legs[0] if legs else {}
                flights.append({
                    "flight_num": f"{leg.get('airline', 'Flight')} {leg.get('flight_number', '')}",
                    "carrier": leg.get("airline", "Carrier"),
                    "price": flight.get("price", 0.0),
                    "departure": f"{leg.get('departure_airport', {}).get('id', '')} {leg.get('departure_airport', {}).get('time', '')}",
                    "arrival": f"{leg.get('arrival_airport', {}).get('id', '')} {leg.get('arrival_airport', {}).get('time', '')}",
                    "duration": flight.get("duration", "N/A"),
                    "class": leg.get("class", "Economy")
                })
        return flights
    except Exception as e:
        print(f"Error querying SerpAPI Flights: {e}. Returning mock data.")
        return MOCK_FLIGHTS["SFO"]

def search_hotels(location: str, check_in_date: str, check_out_date: str) -> List[Dict[str, Any]]:
    """
    Search hotels via SerpAPI Google Hotels. Falls back to mock data if key not set.
    """
    if settings.is_mock_mode or not settings.SERPAPI_KEY:
        # Match location to mock keys
        loc_clean = location.lower()
        for city, hotels in MOCK_HOTELS.items():
            if city.lower() in loc_clean:
                return hotels
        return MOCK_HOTELS["San Francisco"]
        
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_hotels",
            "q": location,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "currency": "USD",
            "api_key": settings.SERPAPI_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        hotels = []
        if "properties" in data:
            for prop in data["properties"]:
                hotels.append({
                    "name": prop.get("name", "Hotel"),
                    "price_per_night": prop.get("rate_per_night", {}).get("lowest", 0.0),
                    "rating": prop.get("overall_rating", 0.0),
                    "reviews": prop.get("reviews", 0),
                    "thumbnail": prop.get("images", [{}])[0].get("thumbnail", ""),
                    "amenities": prop.get("amenities", [])[:4]
                })
        return hotels
    except Exception as e:
        print(f"Error querying SerpAPI Hotels: {e}. Returning mock data.")
        return MOCK_HOTELS["San Francisco"]
