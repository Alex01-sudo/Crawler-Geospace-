from arango import ArangoClient, cursor
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
password = os.getenv("ARANGO_ROOT_PASSWORD")

if not password:
    raise ValueError("ARANGO_ROOT_PASSWORD not found. Check the .env file.")

class ArangoStorageManager:
    def __init__(self, hosts="http://localhost:8529", username="root", password= password, db_name="ThesisDatabase"):
        
        self.client = ArangoClient(hosts=hosts)
        
        sys_db = self.client.db("_system", username=username, password=password)
        if not sys_db.has_database(db_name):
            sys_db.create_database(db_name)
        
        self.db = self.client.db(db_name, username=username, password=password)
        self.init_graph_structure()

    def init_graph_structure(self):
        
         
        if not self.db.has_collection("nodes"):
            self.db.create_collection("nodes")
            
        
        if not self.db.has_collection("distances"):
            self.db.create_collection("distances", edge=True)

        """
        if not self.db.has_graph("UsaCapitalsGraph"):
            self.db.create_graph(
                "UsaCapitalsGraph",
                edge_definitions=[
                    {
                        "edge_collection": "distances",
                        "from_vertex_collections": ["nodes"],
                        "to_vertex_collections": ["nodes"]
                    }
                ]
            )
        """

    def upsert_node(self, state: str, lat: float, lon: float, buffer_m: int, scale: float, useful_crop_percentage: float | None = None):
        
        nodes_coll = self.db.collection("nodes")
        key = f"{round(lat, 2)}_{round(lon, 2)}"

        
        documento = {
            "_key": key,
            "State": state,
            "coordinates": [lon, lat],
            "buffer_m": buffer_m,
            "scale": scale,
            "visited": False,
            "file_tif_path": None,
            "file_geojson_path": None,
            "image_count": 0,
            "useful_crop_percentage": useful_crop_percentage,
        }
        
        try:
            nodes_coll.insert(documento, overwrite=True)
            
        except Exception as e:
            print(f"Error while inserting node for {key}: {e}")

    def add_edge(self, city_A: str, city_B: str, distance_km: float):
        
        edge_coll = self.db.collection("distances")
        
        key_A = city_A.lower().replace(" ", "_")
        key_B = city_B.lower().replace(" ", "_")
        
        arco = {
            "_from": f"nodes/{key_A}",
            "_to": f"nodes/{key_B}",
            "distance_km": distance_km
        }
        
        
        arco["_key"] = f"{key_A}_to_{key_B}"
        edge_coll.insert(arco, overwrite=True)

    def node_to_visit(self) -> list:
        query = """
        FOR c IN nodes
            FILTER c.visited == false
            RETURN c
        """
        cursor = self.db.aql.execute(query)
        return [doc for doc in cursor]
    
    def node_visited(self) -> list:
        query = """
        FOR c IN nodes
            FILTER c.visited == true
            RETURN c
        """
        cursor = self.db.aql.execute(query)
        return [doc for doc in cursor]

    def set_visited(self, lat: float, lon: float, drive_tif_path: str, drive_geojson_path: str, img_count: int):
        """Updates the node document marking it as visited and storing the Google Drive cloud paths."""
        key = f"{round(lat, 2)}_{round(lon, 2)}"
        nodes_coll = self.db.collection("nodes")
        
        update_data = {
            "_key": key,
            "visited": True,
            "download_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file_tif_path": str(drive_tif_path),
            "file_geojson_path": str(drive_geojson_path),
            "image_count": img_count
        }
        nodes_coll.update(update_data)
        
    def get_first_capital(self) -> dict | None:
        query = """
        FOR c IN nodes
            LIMIT 1
            RETURN c
        """
        cursor = self.db.aql.execute(query)
        
        return cursor.next()
    
    def reset_visited_status(self):
        
        query = """
        FOR c IN nodes
            UPDATE c WITH { visited: false} IN nodes
        """
        self.db.aql.execute(query)
    
    def change_visited_status(self, lat: float, lon: float, visited: bool):
        key = f"{round(lat, 2)}_{round(lon, 2)}"
        nodes_coll = self.db.collection("nodes")
        
        update_data = {
            "_key": key,
            "visited": visited
        }
        nodes_coll.update(update_data)   
       
    def add_attribute(self, lat: float, lon: float, attribute_name: str = None, attribute_value = None, extra_attributes: dict = None):
        
        key = f"{round(lat, 2)}_{round(lon, 2)}"
        nodes_coll = self.db.collection("nodes")
        
        update_data = {
            "_key": key
        }

        if attribute_name is not None:
            update_data[attribute_name] = attribute_value
        
            
        nodes_coll.update(update_data)
            
        
    def set_up_index(self):
        
        try:
        
            collection = self.db.collection("nodes")
            collection.add_geo_index(fields=['coordinates'])
        
        except Exception as e:
            print(f"Error setting up index: {e}")
            
            
    def find_next_neighbour(self, current_node: str) -> dict | None:
        query = """
        LET start_doc = DOCUMENT(@start_node)
       
        FOR doc IN nodes
            FILTER doc._id != start_doc._id
            FILTER doc.visited == false
            SORT DISTANCE(start_doc.coordinates[1], start_doc.coordinates[0], doc.coordinates[1], doc.coordinates[0]) ASC
            LIMIT 1
            RETURN doc
        """
        bind_vars = {"start_node": current_node}
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        
        try:
            return cursor.next()
        except StopIteration:
            return None
        