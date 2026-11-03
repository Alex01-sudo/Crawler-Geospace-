import json

def remove_key_recursive(data, key_to_remove="embedding_vector"):
    """
    Rimuove ricorsivamente una chiave specifica da tutti i dizionari
    presenti in una struttura dati JSON (dizionari o liste).
    """
    if isinstance(data, dict):
        return {
            key: remove_key_recursive(value, key_to_remove)
            for key, value in data.items()
            if key != key_to_remove
        }
    elif isinstance(data, list):
        return [remove_key_recursive(item, key_to_remove) for item in data]
    else:
        return data

def process_json(input_filepath, output_filepath):
    # Leggi il file JSON originale
    with open(input_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Rimuovi la chiave desiderata
    cleaned_data = remove_key_recursive(data, key_to_remove="embedding_vector")
    
    # Salva il nuovo JSON nel file di output
    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=4, ensure_ascii=False)
        
    print(f"File processato con successo! Risultato salvato in: {output_filepath}")

# Esempio d'uso:
if __name__ == "__main__":
    file_input = "Query_dataset.json"
    file_output = "Dataset_noEmb.json"
    
    process_json(file_input, file_output)