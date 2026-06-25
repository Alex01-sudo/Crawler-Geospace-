from Utils.Get_google_drive import get_tif_from_drive
from dotenv import load_dotenv
from Utils.Align_masks import align_nass_to_sentinel
import os
import rasterio
import matplotlib.pyplot as plt
import numpy as np
import io

load_dotenv()



raw_data1 = get_tif_from_drive("S2_albany.tif", os.getenv("GOOGLE_CLOUD_CREDENTIALS"))
print(f"Raw data type: {type(raw_data1)}")
raw_data2 = get_tif_from_drive("NASS_washington_dc.tif", os.getenv("GOOGLE_CLOUD_CREDENTIALS"))
if raw_data1:
    file_tif = io.BytesIO(raw_data1)
    file_tif_NASS = io.BytesIO(raw_data2)
    
    align_nass_to_sentinel(file_tif, file_tif_NASS, "aligned_nass.tif")

    with rasterio.open(file_tif) as src:
        print(f"Numero di bande: {src.count}")
        print(f"Risoluzione: {src.width}x{src.height}")
        
        # Se vuoi leggere una banda specifica (es. la prima) come array NumPy:
        band1 = src.read(1)

        print(f"Valori della prima banda: {band1}")
        

    with rasterio.open("aligned_nass.tif") as src:
        print(f"Numero di bande: {src.count}")
        print(f"Risoluzione: {src.width}x{src.height}")
        
        # Se vuoi leggere una banda specifica (es. la prima) come array NumPy:
        band2 = src.read(1)

        print(f"Valori della seconda banda: {band2}")
    
        
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # --- IMMAGINE 1 (Sinistra): Sentinel-2 ---
    # axes[0] indica il primo riquadro a sinistra
    im1 =axes[0].imshow(band1)
    axes[0].set_title("Sentinel-2 (Immagine Satellitare RGB)")
    axes[0].axis('off')  # Rimuove i bordi con le coordinate dei pixel se vuoi una vista pulita

    fig.colorbar(im1, ax=axes[0], shrink=0.7, label="Codice Classe")
    # --- IMMAGINE 2 (Destra): NASS CDL ---
    # axes[1] indica il secondo riquadro a destra
    # Usiamo una mappa di colore qualitativa ('tab20') perché i dati sono categorici
    im2 = axes[1].imshow(band2)
    axes[1].set_title("USDA NASS CDL (Maschera Uso del Suolo)")
    axes[1].axis('off')

    # Opzionale: Aggiungiamo una barra dei colori solo per la maschera NASS per vedere i codici
    fig.colorbar(im2, ax=axes[1], shrink=0.7, label="Codice Classe")
    
    # 3. Ottimizza lo spazio tra le due immagini ed esegue il plot
    plt.tight_layout()
    plt.show()


else:
    print("Errore: Impossibile scaricare il file TIFF da Google Drive.")


