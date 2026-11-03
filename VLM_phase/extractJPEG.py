import rasterio
import numpy as np
from PIL import Image

def extract_and_compress_s2_jpeg(input_tif, output_jpeg, quality=85, scale_factor=2.5):
    """
    Estrae le bande RGB da un GeoTIFF Sentinel-2 e salva l'immagine in formato JPEG compresso.

    Parametri:
    -----------
    input_tif : str
        Percorso del file GeoTIFF di input.
    output_jpeg : str
        Percorso del file JPEG di output (es. 'output.jpg').
    quality : int (default: 85)
        Livello di qualita JPEG (da 1 a 95). Valori piu bassi aumentano la compressione
        e riducono la dimensione del file.
    scale_factor : float (default: 2.5)
        Fattore di moltiplicazione per aumentare la luminosita visiva dei canali RGB.
    """
    print(f"1. Apertura del file: {input_tif}")
    
    with rasterio.open(input_tif) as src:
        # Assumiamo la convenzione standard multibanda per le bande Sentinel-2:
        # Banda 3 = Rosso (B4), Banda 2 = Verde (B3), Banda 1 = Blu (B2)
        # Nota: adatta gli indici (1, 2, 3) se il tuo TIF ha un ordine di bande differente.
        red = src.read(3).astype(np.float32)
        green = src.read(2).astype(np.float32)
        blue = src.read(1).astype(np.float32)

    print("2. Normalizzazione e regolazione del contrasto...")
    # Convertiamo da Digital Numbers (DN) a valori di riflettanza [0, 1]
    red /= 10000.0
    green /= 10000.0
    blue /= 10000.0

    # Ricomponiamo le 3 bande in un unico array (Altezza, Larghezza, 3)
    rgb = np.dstack((red, green, blue))

    # Moltiplichiamo per lo scale_factor e limitiamo i valori nell'intervallo [0, 1]
    rgb_brightened = np.clip(rgb * scale_factor, 0.0, 1.0)

    # 3. Conversione da float [0, 1] a interi 8-bit [0, 255] richiesti per il JPEG
    rgb_8bit = (rgb_brightened * 255).astype(np.uint8)

    print(f"3. Creazione e salvataggio JPEG con qualita={quality}...")
    # Creiamo l'oggetto Immagine PIL
    img = Image.fromarray(rgb_8bit, mode='RGB')

    # Salviamo l'immagine in JPEG regolando la qualita/compressione
    img.save(output_jpeg, 'JPEG', quality=quality, optimize=True)
    
    print(f"Completato! Immagine salvata in: {output_jpeg}")

    

# --- ESEMPIO PRATICO DI UTILIZZO ---
if __name__ == "__main__":
    file_input = "Kansas.tif"  # Percorso del tuo file GeoTIFF
    file_output = "sentinel2_rgb.jpg"    # Nome del file JPEG finale

    # Esegui la funzione con qualita JPEG pari a 80 per un ottimo compromesso
    # tra qualita visiva e dimensione ridotta del file.
    extract_and_compress_s2_jpeg(
        input_tif=file_input, 
        output_jpeg=file_output, 
        quality=80, 
        scale_factor=2.5
    )


    with Image.open(file_output) as img: 
        print(f"Dimensioni JPEG risultante: {img.size[0]} x {img.size[1]} pixel") 
