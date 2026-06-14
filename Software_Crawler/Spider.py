import os
import time
import io
import rasterio
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from Software_Crawler.Storage import ArangoStorageManager
from Software_Crawler.download import download_sentinel_composite_to_drive
from Utils.Get_google_drive import get_tif_from_drive



load_dotenv()

class GraphSpider:
    def __init__(self):
        
        self.storage = ArangoStorageManager()
        self.db = self.storage.db  

    def find_starting_node(self) -> dict | None:
        
        capitals_not_visited = self.storage.capitals_to_visit()
        if capitals_not_visited:
            return capitals_not_visited[0] # update later for a better strategy
        return None

    def find_next_neighbour(self, current_node: str) -> dict | None:
        query = """
        FOR vertex, edge IN 1..1 OUTBOUND @start_node GRAPH UsaCapitalsGraph
            FILTER vertex.visited == false
            SORT edge.distance_km ASC
            LIMIT 1
            RETURN vertex
        """
        bind_vars = {"start_node": current_node}
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        try: 
        
            risultato = cursor.next()
        except StopIteration:
           
            return None
       
        return risultato

    def execute_crawl(self):
        print("Execute crawling...")
        
        
        current_node = self.find_starting_node()
        
        while current_node is not None:
            city = current_node["city"]
            key = current_node["_key"]
            nodo_id = f"capitals/{key}"
            
            print(f"\n Spider located in: {city} ({current_node['state']})")
            
            try:
                
                drive_folder = "GEE_Crawler_Outputs"
                
                print(f" Calling gee for {city}...")
                img_count = download_sentinel_composite_to_drive(
                    lat=current_node["lat"],
                    lon=current_node["lon"],
                    buffer_m=current_node["buffer_m"],
                    scale=current_node["scale"],
                    city_name=city,
                    drive_folder=drive_folder
                )
                
                
                file_prefix = f"S2_{city.lower().replace(' ', '_')}"

                
                predicted_tif_path = f"{drive_folder}/{file_prefix}.tif"
                predicted_geojson_path = f"{drive_folder}/{file_prefix}_roi.geojson"
                
                self.storage.set_visited(
                    city=city, 
                    drive_tif_path=predicted_tif_path, 
                    drive_geojson_path=predicted_geojson_path,
                    img_count=img_count
                    
                   
                )
                print(f"{city} saved in the storage.")
                
            except Exception as e:
                print(f" error while crawling in  {city}: {e}")
                break 

            next_node = self.find_next_neighbour(nodo_id)
            
            if next_node:
                
                current_node = next_node
            else:
                current_node = self.find_starting_node()
                
            
            time.sleep(2)

        print("\n Crawling completated. ")


    def extract_features(self):
        
        print("Extracting features...")
        self.storage.reset_visited_status()
        current_node = self.find_starting_node()
        while current_node is not None:
            path_tif = current_node["file_tif_path"]
            name_tif = Path(path_tif).name if path_tif else "None"
            
            if name_tif is not None:
                print(f"Extracting features for {current_node['city']}...")
                raw_data = get_tif_from_drive(name_tif, os.getenv("GOOGLE_CLOUD_CREDENTIALS"))
                if raw_data:
                    file_tif = io.BytesIO(raw_data)

                    with rasterio.open(file_tif) as src:
                        band_R = np.array(src.read(1))
                        band_G = np.array(src.read(2))
                        band_B = np.array(src.read(3))  
        
                        image_RGB = np.stack((band_R, band_G, band_B), axis=-1)
                        
                    
                        
            
            
            
        
        