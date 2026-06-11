import json
import time
from pathlib import Path
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from Utils.Calculate_dist import Metric_distance 
from Software_Crawler.Storage import ArangoStorageManager




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




def main():


    geolocator = Nominatim(user_agent="usa_capitals_crawler")
    dataset = ArangoStorageManager()
    
    distances = []

    print("Recovering coordinates from OpenStreetMap...")
    for cap in Capitals:
        query = f"{cap['city']}, {cap['state']}, USA"
        try:
            location = geolocator.geocode(query, addressdetails=True)
            if location:
                bbox = location.raw.get("boundingbox", [])
                
                buffer_stimato = 10000 

                dataset.upsert_capital(
                    citta=cap["city"],
                    stato=cap["state"],
                    lat=location.latitude,
                    lon=location.longitude,
                    buffer_m=buffer_stimato,
                    scale=10.0
                )
                distances.append({
                    "city": cap["city"],
                    "lat": location.latitude,
                    "lon": location.longitude
                })
                print(f"Found: {cap['city']}, {cap['state']} at ({location.latitude}, {location.longitude})")
            else:
                print(f"Location not found for {cap['city']}, {cap['state']}")
            
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error with {cap['city']}: {e}")
    
    
    for entry in distances:
        for other_entry in distances:
            if entry != other_entry:
                distance = Metric_distance(
                    entry["lat"], entry["lon"], other_entry["lat"], other_entry["lon"]
                )
                dataset.add_edge(entry["city"], other_entry["city"], distance)
                print(f"Distance between {entry['city']} and {other_entry['city']}: {distance:.2f} Km")
    


if __name__ == "__main__":
    main()
    



