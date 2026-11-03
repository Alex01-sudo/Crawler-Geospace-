import json
import find_region as fr


usa_states_to_code = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Carolina Del Nord": "NC",
    "Carolina Del Sud": "SC",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Dakota Del Nord": "ND",
    "Dakota Del Sud": "SD",
    "Delaware": "DE",
    "Distretto Di Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Virginia Occidentale": "WV",
    "Washington": "WA",
    "Wisconsin": "WI",
    "Wyoming": "WY"
}


def read_and_preprocess(Num_query : int):
    
    with open("Query_dataset.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    

    actual = data[Num_query]
    histogram = actual['histogram']
    top_3_keys = sorted(histogram, key=histogram.get, reverse=True)[:3]
    final_crop_list = [crop.upper() for crop in top_3_keys]
    State = actual["State"]
    St = usa_states_to_code.get(State)
    lat, lon = actual["coordinates"][1], actual["coordinates"][0]
    AG_zone = fr.get_asd_desc(lat, lon, State)
    return actual, final_crop_list, AG_zone, St

if __name__ == "__main__":
    read_and_preprocess(0)  