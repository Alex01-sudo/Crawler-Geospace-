import networkx as nx
import json
from download import download_sentinel_composite 
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
input_path = BASE_DIR / "data" / "capitals_usa.json"
output_path_tif = BASE_DIR / "data" / "raw" / "S2_square_gee.tif"
output_path_geojson = BASE_DIR / "data" / "raw" / "S2_square_roi.geojson"





def run_spider():
    
    with open(input_path, "r") as f:
        capitali = json.load(f)
        
    G = nx.Graph()
    
    for cap in capitali:
        G.add_node(cap["city"], **cap, visited=False)
    
    
    # nx.add_path(G, ...) o calcolare i vicini
    
    print(f"Spider pronto. Grafo caricato con {G.number_of_nodes()} nodi.")
    
    # 4. Lo Spider attraversa il grafo ed esegue il download
    for nodo in G.nodes:
        info_citta = G.nodes[nodo]
        
        if not info_citta["visited"]:
            print(f"Spider on: {nodo} ({info_citta['state']})")
            
            try:
                # Esegui il download usando i parametri custoditi nel nodo
                download_sentinel_composite(
                     lat=info_citta["lat"], 
                     lon=info_citta["lon"], 
                     buffer_m=info_citta["buffer_m"],
                     output=output_path_tif,
                     roi_json=output_path_geojson
                     
                 )
                
                # Segna il nodo come completato nel grafo
                G.nodes[nodo]["visited"] = True
                print(f"Image downloaded for {nodo}. Marked as visited.")
                
            except Exception as e:
                print(f"Error during crawling {nodo}: {e}")

if __name__ == "__main__":
    run_spider()