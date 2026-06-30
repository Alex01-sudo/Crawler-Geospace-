
import os

from dotenv import load_dotenv
from Utils.Read_rasterio import plot_rasterio 
from Software_Crawler.Storage import ArangoStorageManager
from Utils.Get_google_drive import get_tif_from_drive
from Utils.Read_rasterio import plot_rasterio


load_dotenv()

class RetrievalSystem:
    def __init__(self):
        
        self.storage = ArangoStorageManager()
        self.db = self.storage.db

    def define_index(self):
       
        self.storage.set_up_index()
        
    def retrieve_answer_set(self, query_lan_lon_range: list) -> dict:
        
        query = """
                FOR doc IN capitals
                SORT DISTANCE(doc.coordinates[1], doc.coordinates[0], @query_lat, @query_lon) ASC
                LIMIT 10
                RETURN {
                 city : doc.city,
                 histogram : doc.histogram,
                 }
                """
                
        bind_vars = {
            "query_lat": query_lan_lon_range[0],
            "query_lon": query_lan_lon_range[1],
        }
        cusror = self.db.aql.execute(query, bind_vars=bind_vars)
        results = []
        for doc in cusror:
            results.append(doc)
        
        #print(f"Results for query {query_lan_lon_range}: {results}")
        return results
        
    def ranking_function(self, query : list, label : str) -> list:
        
        ranked_results = []
        self.define_index()
        answer_set = self.retrieve_answer_set(query)
        for answer in answer_set:
            answer_histogram = answer["histogram"]
            score = answer_histogram.get(label, 0)
            ranked_results.append((answer["city"], score))
            
        ranked_results.sort(key=lambda x: x[1], reverse=True)    
        return ranked_results 
    
    
    def print_images(self, query: list, label: str):
        ranked_results = self.ranking_function(query, label)
        print(f"Ranked results for query {query} and label {label}:")
        print(ranked_results)
        raw_data_list = []
        for city, score in ranked_results:
            city_key = city.lower().replace(' ', '_')
            cloud_filename = f"S2_{city_key}.tif"
            raw_data = get_tif_from_drive(cloud_filename, os.getenv("GOOGLE_CLOUD_CREDENTIALS"))
            raw_data_list.append(raw_data)
        
        plot_rasterio(raw_data_list, ranked_results)