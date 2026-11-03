import os
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

class NASSQuickStatsClient:
    

    BASE_URL = "https://quickstats.nass.usda.gov/api/api_GET/"
    COUNT_URL = "https://quickstats.nass.usda.gov/api/get_counts/"

    def __init__(self, api_key: Optional[str] = "YOUR_API_KEY_HERE"):
        
        self.api_key = api_key or os.getenv("NASS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is missing! Pass it to the constructor or set NASS_API_KEY env variable."
            )

    def get_record_count(self, params: Dict[str, Any]) -> int:
        query_params = params.copy()
        query_params["key"] = self.api_key

        response = requests.get(self.COUNT_URL, params=query_params)
        response.raise_for_status()

        data = response.json()
        return int(data.get("count", 0))

    def fetch_detailed_crop_data(
        self,
        state_alpha: str,
        Ag_District: str,
        commodities: list[str],
        year: str
    ) -> List[Dict[str, Any]]:
        
        metrics = ["AREA HARVESTED", "YIELD"]

        parsed_results = []

        for crop in commodities:
            for metric in metrics:
                params = {
                    "key": self.api_key,
                    "format": "JSON",
                    "source_desc": "SURVEY",
                    "sector_desc": "CROPS",
                    "commodity_desc": crop,
                    "statisticcat_desc": metric,
                    "state_alpha": state_alpha,
                    "asd_desc" : Ag_District, 
                    "agg_level_desc": "COUNTY",
                    "reference_period_desc" : "YEAR",
                    "year": year
                }

                response = requests.get(self.BASE_URL, params=params)

                if response.status_code == 200:
                    
                    records = response.json().get("data", [])
                    for rec in records:
                        parsed_results.append({
                            "commodity": rec.get("commodity_desc"),
                            "class": rec.get("class_desc"),
                            "practice": rec.get("prodn_practice_desc"),
                            "metric": rec.get("statisticcat_desc"),
                            "data_item": rec.get("short_desc"),  
                            "value": rec.get("Value"),
                            "unit": rec.get("unit_desc"),
                            "year": rec.get("year"),
                            "AG_District": rec.get("asd_desc"),
                            "state": rec.get("state_alpha")
                        })

        return parsed_results




if __name__ == "__main__":
    

    fetcher = NASSQuickStatsClient()

  
    commodity = ["CORN"]
    
    

    results = fetcher.fetch_detailed_crop_data(
        state_alpha="NE",
        Ag_District="NORTHEAST",
        commodities=commodity,
        year="2023"
    )

    
    
    print(f"Retrieved {len(results)} detailed entries:\n")
    for item in results:
        list_ditems = item['data_item'].split(",")
        print(f"• Data Item: {item['data_item']} | AG District {item['AG_District']}")
        print(f"  Value: {item['value']} {item['unit']}")
        print(f"  Class: {item['class']} | Practice: {item['practice']} | Metric: {item['metric']}\n")

