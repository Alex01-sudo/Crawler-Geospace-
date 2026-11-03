from arango import ArangoClient
import pandas as pd

client = ArangoClient(hosts='https://clavicle-luminance-obscure.ngrok-free.dev')


db = client.db('ThesisDatabase', username='root', password='1234')

print("Connesso ad ArangoDB versione:", db.version())


if db.has_collection("nodes"):
    
    query = f"FOR doc IN nodes RETURN doc"

    
    cursor = db.aql.execute(query)


    dati = [doc for doc in cursor]
    df = pd.DataFrame(dati)

    print(f"Dati caricati! Righe: {df.shape[0]}, Colonne: {df.shape[1]}")
    print(df.head())

    column_to_get = ["State", "coordinates", "embedding_vector", "climate_data", "histogram", "indexes"]

    final_df = df[column_to_get]

    final_df.to_json("Query_dataset.json", orient = "records")