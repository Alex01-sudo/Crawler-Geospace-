import time
import random # Importiamo la libreria standard di Python per campionamenti univoci
from dotenv import load_dotenv

from Utils.Calculate_dist import Metric_distance 
from Software_Crawler.Storage import ArangoStorageManager
import pandas as pd
import numpy as np

load_dotenv()

def main():
    dataset = ArangoStorageManager()
    grid_file = "Final_points.csv"
    
    df_points = pd.read_csv(grid_file)
    
    for index, row in df_points.iterrows():

        state = row['State']
        lat = row['lat']
        lon = row['lon']  
        perc = row['useful_crop_percentage']           
            
        try:
            
            if lat and lon:
                dataset.upsert_node(
                    state=state,
                    lat=lat,
                    lon=lon,
                    buffer_m=10000,
                    scale=10.0,
                    useful_crop_percentage=perc
                )
                     
            else:
                print(f"Not valid coordinates for {state}: {lat}, {lon}")    
        
        except Exception as e:
            print(f"Errore while saving node for {state}: {e}")
    
    print(f"Completed processing nodes")

if __name__ == "__main__":
    main()