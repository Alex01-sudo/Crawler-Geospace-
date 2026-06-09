from arango import ArangoClient
import os
password = os.getenv("ARANGO_ROOT_PASSWORD", "password_di_backup")

class ArangoStorageManager:
    def __init__(self, hosts="http://localhost:8529", username="root", password= password, db_name="GeospaceCrawler"):
        # Inizializza il client ArangoDB
        self.client = ArangoClient(hosts=hosts)
        
        # Connettiti al database di sistema per verificare/creare il tuo database dedicato
        sys_db = self.client.db("_system", username=username, password=password)
        if not sys_db.has_database(db_name):
            sys_db.create_database(db_name)
        
        # Connettiti al database del progetto
        self.db = self.client.db(db_name, username=username, password=password)
        self.init_graph_structure()

    def init_graph_structure(self):
        """Crea le collezioni di documenti, archi e la definizione del grafo se non esistono."""
        # 1. Crea la collezione dei Nodi (Capitali)
        if not self.db.has_collection("capitali"):
            self.db.create_collection("capitali")
            
        # 2. Crea la collezione degli Archi (Collegamenti) con tipo 'edge'
        if not self.db.has_collection("collegamenti_distanza"):
            self.db.create_collection("collegamenti_distanza", edge=True)

        # 3. Definisce il grafo all'interno di ArangoDB
        if not self.db.has_graph("UsaCapitalsGraph"):
            self.db.create_graph(
                "UsaCapitalsGraph",
                edge_definitions=[
                    {
                        "edge_collection": "collegamenti_distanza",
                        "from_vertex_collections": ["capitali"],
                        "to_vertex_collections": ["capitali"]
                    }
                ]
            )

    def upsert_capitale(self, citta: str, stato: str, lat: float, lon: float, buffer_m: int, scale: float):
        """Inserisce o aggiorna i dati di input di una capitale (Nodo)."""
        capitali_coll = self.db.collection("capitali")
        
        # Usiamo il nome della città pulito come chiave univoca (_key) di ArangoDB
        key = citta.lower().replace(" ", "_")
        
        documento = {
            "_key": key,
            "citta": citta,
            "stato": stato,
            "lat": lat,
            "lon": lon,
            "buffer_m": buffer_m,
            "scale": scale,
            "visited": False,
            "file_tif_path": None,
            "immagini_utilizzate": 0
        }
        
        # Inserisce o aggiorna se già esistente
        capitali_coll.insert(documento, overwrite=True)

    def aggiungi_collegamento(self, citta_A: str, citta_B: str, distanza_metri: float):
        """Crea un arco pesato tra due capitali nel grafo."""
        edge_coll = self.db.collection("collegamenti_distanza")
        
        key_A = citta_A.lower().replace(" ", "_")
        key_B = citta_B.lower().replace(" ", "_")
        
        arco = {
            "_from": f"capitali/{key_A}",
            "_to": f"capitali/{key_B}",
            "distanza_m": distanza_metri
        }
        
        # Generiamo una chiave univoca per l'arco basata sui due nodi per evitare duplicati
        arco["_key"] = f"{key_A}_to_{key_B}"
        edge_coll.insert(arco, overwrite=True)

    def ottieni_capitali_da_visitare(self) -> list:
        """Esegue una query AQL per estrarre tutti i documenti non ancora visitati."""
        query = """
        FOR c IN capitali
            FILTER c.visited == false
            RETURN c
        """
        cursor = self.db.aql.execute(query)
        return [doc for doc in cursor]

    def segna_come_completato(self, citta: str, tif_path: str, img_count: int):
        """Aggiorna lo stato del nodo una volta completato il download da GEE."""
        from datetime import datetime
        key = citta.lower().replace(" ", "_")
        capitali_coll = self.db.collection("capitali")
        
        aggiornamento = {
            "_key": key,
            "visited": True,
            "data_download": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file_tif_path": str(tif_path),
            "immagini_utilizzate": img_count
        }
        capitali_coll.update(aggiornamento)