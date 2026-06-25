import os

from dotenv import load_dotenv
import rasterio
import io
from Software_Crawler.Storage import ArangoStorageManager
from Utils.Align_masks import align_nass_to_sentinel
from Utils.Get_google_drive import get_tif_from_drive, get_drive_folder_id_by_name


load_dotenv()

class RetrievalSystem:
    def __init__(self):
        
        self.storage = ArangoStorageManager()
        self.db = self.storage.db
    
    def retrieve_starting_node(self) -> dict | None:
        
        capitals_not_visited = self.storage.capitals_visited()
        if capitals_not_visited:
            return capitals_not_visited[0] # update later for a better strategy
        return None
    
    def retrieve_next_neighbour(self, current_node: str) -> dict | None:
        query = """
        FOR vertex, edge IN 1..1 OUTBOUND @start_node GRAPH UsaCapitalsGraph
            FILTER vertex.visited == true
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
    
    def  retrieve_city(self):
            
            current_node = self.retrieve_starting_node()
            while current_node is not None:
                city = current_node["city"]
                cloud_filename = f"Aligned_NASS_{city.lower().replace(' ', '_')}"
                S2_file_name = current_node["file_tif_path"].split("/")[-1]
                NASS_file_name = current_node["nass_tif_path"].split("/")[-1]
                raw_data1 = get_tif_from_drive(S2_file_name, os.getenv("GOOGLE_CLOUD_CREDENTIALS"))
                raw_data2 = get_tif_from_drive(NASS_file_name, os.getenv("GOOGLE_CLOUD_CREDENTIALS"))

                try:
                    file_tif = io.BytesIO(raw_data1)
                    file_tif_NASS = io.BytesIO(raw_data2)
                    id_folder = get_drive_folder_id_by_name("GEE_NASS_Aligned", os.getenv("GOOGLE_CLOUD_CREDENTIALS"))
                    mask  = align_nass_to_sentinel(file_tif, file_tif_NASS)

                    
                except Exception as e:
                    print(f"Error processing {city}: {e}")
                    break       
                
                next_node = self.retrieve_next_neighbour(current_node)
                
                if next_node:
                
                    current_node = next_node
                else:
                
                    current_node = None
                    
                    
            
                    

