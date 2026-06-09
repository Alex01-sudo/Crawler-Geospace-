import json
import time
from pathlib import Path
from geopy.geocoders import Nominatim
from Calculate_dist import Metric_distance 

Capitals = [
    {"city": "Montgomery", "state": "Alabama"},
    {"city": "Juneau", "state": "Alaska"},
    {"city": "Phoenix", "state": "Arizona"},
    {"city": "Little Rock", "state": "Arkansas"},
    {"city": "Sacramento", "state": "California"},
    {"city": "Denver", "state": "Colorado"},
    {"city": "Hartford", "state": "Connecticut"},  
    {"city": "Dover", "state": "Delaware"},
    {"city": "Tallahassee", "state": "Florida"},
    {"city": "Atlanta", "state": "Georgia"},
    {"city": "Honolulu", "state": "Hawaii"},
    {"city": "Boise", "state": "Idaho"},
    {"city": "Springfield", "state": "Illinois"},
    {"city": "Indianapolis", "state": "Indiana"},
    {"city": "Des Moines", "state": "Iowa"},
    {"city": "Topeka", "state": "Kansas"},
    {"city": "Frankfort", "state": "Kentucky"},
    {"city": "Baton Rouge", "state": "Louisiana"},
    {"city": "Augusta", "state": "Maine"},
    {"city": "Annapolis", "state": "Maryland"},
    {"city": "Boston", "state": "Massachusetts"},
    {"city": "Lansing", "state": "Michigan"},
    {"city": "Saint Paul", "state": "Minnesota"},
    {"city": "Jackson", "state": "Mississippi"},
    {"city": "Jefferson City", "state": "Missouri"},
    {"city": "Helena", "state": "Montana"},
    {"city": "Lincoln", "state": "Nebraska"},
    {"city": "Carson City", "state": "Nevada"},
    {"city": "Concord", "state": "New Hampshire"},
    {"city": "Trenton", "state": "New Jersey"},
    {"city": "Santa Fe", "state": "New Mexico"},
    {"city": "Albany", "state": "New York"},
    {"city": "Raleigh", "state": "North Carolina"},
    {"city": "Bismarck", "state": "North Dakota"},
    {"city": "Columbus", "state": "Ohio"},
    {"city": "Oklahoma City", "state": "Oklahoma"},
    {"city": "Salem", "state": "Oregon"},
    {"city": "Harrisburg", "state": "Pennsylvania"},
    {"city": "Providence", "state": "Rhode Island"},
    {"city": "Columbia", "state": "South Carolina"},
    {"city": "Pierre", "state": "South Dakota"},
    {"city": "Nashville", 	"state":"Tennessee"},
    {"city":"Austin","state":"Texas"},
    {"city":"Salt Lake City","state":"Utah"},
    {"city":"Montpelier","state":"Vermont"},
    {"city":"Richmond","state":"Virginia"},
    {"city":"Olympia","state":"Washington"},
    {"city":"Charleston","state":"West Virginia"},
    {"city":"Madison","state":"Wisconsin"},
    {"city":"Cheyenne","state":"Wyoming"}
    
]

geolocator = Nominatim(user_agent="usa_capitals_crawler")
dataset = []

print("Recovering coordinates from OpenStreetMap...")
for cap in Capitals:
    query = f"{cap['city']}, {cap['state']}, USA"
    try:
        location = geolocator.geocode(query, addressdetails=True)
        if location:
            bbox = location.raw.get("boundingbox", [])
            
            buffer_stimato = 10000 

            dataset.append({
                "city": cap["city"],
                "state": cap["state"],
                "lat": location.latitude,
                "lon": location.longitude,
                "buffer_m": buffer_stimato,
                "scale": 10.0,
                "distances" : []}
            )
            
            print(f"Found: {cap['city']}, {cap['state']} at ({location.latitude}, {location.longitude})")
        else:
            print(f"Location not found for {cap['city']}, {cap['state']}")
        
        
        time.sleep(1)
        
    except Exception as e:
        print(f"Error with {cap['city']}: {e}")
        
for entry in dataset:
    list_of_distances = []
    for other_entry in dataset:
        if entry != other_entry:
            distance = Metric_distance(
                entry["lat"], entry["lon"], other_entry["lat"], other_entry["lon"]
            )
            list_of_distances.append({
                "city": other_entry["city"],
                "distance_km": distance
            })
    entry["distances"] = list_of_distances
    



BASE_DIR = Path(__file__).resolve().parent.parent


output_path = BASE_DIR / "data" / "capitals_usa.json"


output_path.parent.mkdir(parents=True, exist_ok=True)


with open(output_path, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=4)

print(f"\nFile '{output_path}' created successfully!")