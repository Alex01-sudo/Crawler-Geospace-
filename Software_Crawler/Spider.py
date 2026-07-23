import os
import time
import io
import rasterio
import numpy as np
from PIL import Image
from pathlib import Path
from dotenv import load_dotenv
from Software_Crawler.Storage import ArangoStorageManager
from Software_Crawler.download import download_NASS_dataset_to_drive, download_sentinel_composite_to_drive, extract_era5_climate_data
from Utils.Get_google_drive import get_tif_from_drive
from Utils.Features_extractor import load_hf_model_and_processor, extract_embedding_vector
from Utils.Read_rasterio import read_rasterio, normalization




load_dotenv()

class GraphSpider:
    def __init__(self):
        
        self.storage = ArangoStorageManager()
          

    def find_starting_node(self) -> dict | None:
        
        nodes_not_visited = self.storage.node_to_visit()
        if nodes_not_visited:
            return nodes_not_visited[0] # update later for a better strategy
        return None

    

    def execute_crawl(self):
        print("Execute crawling...")
        
        self.storage.set_up_index()
        current_node = self.find_starting_node()
        
        while current_node is not None:
            
            key = current_node["_key"]
            nodo_id = f"nodes/{key}"
            lat, lon = current_node["coordinates"][1], current_node["coordinates"][0]
            
            print(f"\n Spider located in: {current_node['coordinates']}")
            
            try:
                
                drive_folder = "GEE_Crawler_Outputs_thesis"
                
                print(f" Calling gee for {current_node['coordinates']}...")
                img_count = download_sentinel_composite_to_drive(
                    lat=lat,
                    lon=lon,
                    buffer_m=current_node["buffer_m"],
                    scale=current_node["scale"],
                    drive_folder=drive_folder
                )
                
                
                file_prefix = f"S2_{round(lat, 2)}_{round(lon, 2)}"

                
                predicted_tif_path = f"{drive_folder}/{file_prefix}.tif"
                predicted_geojson_path = f"{drive_folder}/{file_prefix}_roi.geojson"
                
                self.storage.set_visited(
                    lat=lat,
                    lon=lon,
                    drive_tif_path=predicted_tif_path, 
                    drive_geojson_path=predicted_geojson_path,
                    img_count=img_count
                    
                   
                )
                print(f"{lat}, {lon} saved in the storage.")
                
            except Exception as e:
                print(f" error while crawling in  {lat}, {lon}: {e}")
                continue

            next_node = self.storage.find_next_neighbour(current_node)
            
            if next_node:
                
                current_node = next_node
            else:
                current_node = None
                
            
            time.sleep(2)

        print("\n Crawling completated. ")


    def extract_features(self):
        
        processor, model = load_hf_model_and_processor("google/vit-base-patch16-224")  
        
        self.storage.reset_visited_status()
        current_node = self.find_starting_node()
        while current_node is not None:
            path_tif = current_node["file_tif_path"]
            name_tif = Path(path_tif).name if path_tif else "None"
            
            if name_tif is not None:
                print(f"Extracting features for {current_node['coordinates']}...")
                raw_data = get_tif_from_drive(name_tif, os.getenv("GOOGLE_CLOUD_CREDENTIALS"))
                if raw_data:
                    
                    image = read_rasterio(raw_data)
                    image_rgb = normalization(image)

                    image_uint8 = (image_rgb * 255.0).astype(np.uint8)
                    input = Image.fromarray(image_uint8)
                
                
                    embedding = extract_embedding_vector(input, processor, model)

                    self.storage.add_attribute(current_node["coordinates"][1],current_node["coordinates"][0], "embedding_vector", embedding.tolist())

                    self.storage.change_visited_status(current_node["coordinates"][1],current_node["coordinates"][0], True)
        
            next_node = self.storage.find_next_neighbour(current_node)
        
            if next_node:
                current_node = next_node
            else:
                current_node = None

            

    def crawling_Nass_classification(self):
        print("Starting crawling on Nass classification...")
        drive_folder = "GEE_NASS_Outputs_thesis"
        #self.storage.reset_visited_status()
        current_node = self.find_starting_node()                    
        
        
        while current_node is not None:
            
            try:
                
                file_prefix = f"NASS_{round(current_node['coordinates'][1], 2)}_{round(current_node['coordinates'][0], 2)}"
                lat = current_node["coordinates"][1]
                lon = current_node["coordinates"][0]
                download_NASS_dataset_to_drive(lat = lat, lon = lon, drive_folder = drive_folder, year = 2023)
                self.storage.add_attribute(lat, lon, attribute_name="nass_geojson_path", attribute_value=f"{drive_folder}/{file_prefix}_roi.geojson")
                self.storage.add_attribute(lat, lon, attribute_name="nass_tif_path", attribute_value=f"{drive_folder}/{file_prefix}.tif")
                self.storage.change_visited_status(lat, lon, True)

            except Exception as e:
                print(f"Error while crawling on NASS classification for {lat}, {lon}: {e}")
                next_node = self.storage.find_next_neighbour(current_node)        
                current_node = next_node if next_node else None   
                time.sleep(2)
                continue
            
            next_node = self.storage.find_next_neighbour(current_node)        
            current_node = next_node if next_node else None   
            time.sleep(2)
        
        print("\n Crawling on NASS classification completed.")    
    
    
    def ERA_crawling (self):
        print("Starting crawling on ERA5 climate data...")
        self.storage.reset_visited_status()
        current_node = self.find_starting_node()                    
        
        
        while current_node is not None:
            
            try:
                
                lat = current_node["coordinates"][1]
                lon = current_node["coordinates"][0]
                climate_data = extract_era5_climate_data(lat=lat, lon=lon, buffer_m=current_node["buffer_m"])
                self.storage.add_attribute(lat, lon, attribute_name="climate_data", attribute_value=climate_data)
                self.storage.change_visited_status(lat, lon, True)

            except Exception as e:
                print(f"Error while crawling on ERA5 climate data for {lat}, {lon}: {e}")
                next_node = self.storage.find_next_neighbour(current_node)        
                current_node = next_node if next_node else None   
                time.sleep(2)
                continue
            
            next_node = self.storage.find_next_neighbour(current_node)        
            current_node = next_node if next_node else None   
            time.sleep(2)
        
        print("\n Crawling on ERA5 climate data completed.")
        
        