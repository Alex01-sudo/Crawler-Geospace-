from arango import ArangoClient, cursor
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
password = os.getenv("ARANGO_ROOT_PASSWORD")

if not password:
    raise ValueError("ARANGO_ROOT_PASSWORD not found. Check the .env file.")

class ArangoStorageManager:
    def __init__(self, hosts="http://localhost:8529", username="root", password= password, db_name="GeospaceCrawler"):
        
        self.client = ArangoClient(hosts=hosts)
        
        sys_db = self.client.db("_system", username=username, password=password)
        if not sys_db.has_database(db_name):
            sys_db.create_database(db_name)
        
        self.db = self.client.db(db_name, username=username, password=password)
        self.init_graph_structure()

    def init_graph_structure(self):
        
         
        if not self.db.has_collection("capitals"):
            self.db.create_collection("capitals")
            
        
        if not self.db.has_collection("distances"):
            self.db.create_collection("distances", edge=True)

       
        if not self.db.has_graph("UsaCapitalsGraph"):
            self.db.create_graph(
                "UsaCapitalsGraph",
                edge_definitions=[
                    {
                        "edge_collection": "distances",
                        "from_vertex_collections": ["capitals"],
                        "to_vertex_collections": ["capitals"]
                    }
                ]
            )

    def upsert_capital(self, city: str, state: str, lat: float, lon: float, buffer_m: int, scale: float):
        
        capitals_coll = self.db.collection("capitals")
        
        
        key = city.lower().replace(" ", "_")
        
        documento = {
            "_key": key,
            "city": city,
            "state": state,
            "lat": lat,
            "lon": lon,
            "buffer_m": buffer_m,
            "scale": scale,
            "visited": False,
            "file_tif_path": None,
            "file_path_geojson": None,
            "image_count": 0
        }
        
        
        capitals_coll.insert(documento, overwrite=True)

    def get_lon_lat(self, citta: str):
        capitals_coll = self.db.collection("capitals")
        key = citta.lower().replace(" ", "_")
        query = f"""FOR cap IN capitals
                    FILTER cap._key == "{key}"
                    RETURN {{"lat": cap.lat, "lon" : cap.lon}}"""
        cursor = self.db.aql.execute(query)
        result = cursor.next()
        return result 

    def add_edge(self, city_A: str, city_B: str, distance_km: float):
        
        edge_coll = self.db.collection("distances")
        
        key_A = city_A.lower().replace(" ", "_")
        key_B = city_B.lower().replace(" ", "_")
        
        arco = {
            "_from": f"capitals/{key_A}",
            "_to": f"capitals/{key_B}",
            "distance_km": distance_km
        }
        
        
        arco["_key"] = f"{key_A}_to_{key_B}"
        edge_coll.insert(arco, overwrite=True)

    def capitals_to_visit(self) -> list:
        query = """
        FOR c IN capitals
            FILTER c.visited == false
            RETURN c
        """
        cursor = self.db.aql.execute(query)
        return [doc for doc in cursor]

    def set_visited(self, city: str, drive_tif_path: str, drive_geojson_path: str, img_count: int):
        """Updates the capital document marking it as visited and storing the Google Drive cloud paths."""
        key = city.lower().replace(" ", "_")
        capitals_coll = self.db.collection("capitals")
        
        update_data = {
            "_key": key,
            "visited": True,
            "download_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file_tif_path": str(drive_tif_path),
            "file_geojson_path": str(drive_geojson_path),
            "images_count": img_count
        }
        capitals_coll.update(update_data)
        
    def get_first_capital(self) -> dict | None:
        query = """
        FOR c IN capitals
            LIMIT 1
            RETURN c
        """
        cursor = self.db.aql.execute(query)
        
        return cursor.next()
    
    def reset_visited_status(self):
        
        query = """
        FOR c IN capitals
            UPDATE c WITH { visited: false} IN capitals
        """
        self.db.aql.execute(query)
       