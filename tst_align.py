from Utils.Get_google_drive import get_tif_from_drive
from dotenv import load_dotenv
from Utils.Align_masks import align_nass_to_sentinel
from Utils.Read_rasterio import normalization, read_rasterio
import os
import rasterio
import matplotlib.pyplot as plt
import numpy as np
import io

load_dotenv()



raw_data1 = get_tif_from_drive("S2_41.93_-104.76.tif", os.getenv("GOOGLE_CLOUD_CREDENTIALS"))
print(f"Raw data type: {type(raw_data1)}")
raw_data2 = get_tif_from_drive("NASS_41.93_-104.76.tif", os.getenv("GOOGLE_CLOUD_CREDENTIALS"))
if raw_data1:
    file_tif = io.BytesIO(raw_data1)
    file_tif_NASS = io.BytesIO(raw_data2)
    
    mask = align_nass_to_sentinel(file_tif, file_tif_NASS)

    band1 = read_rasterio(raw_data1)
    band1 = normalization(band1)
            
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

   
    im1 =axes[0].imshow(band1)
    axes[0].set_title("Sentinel-2 (Immagine Satellitare RGB)")
    axes[0].axis('off')  

    fig.colorbar(im1, ax=axes[0], shrink=0.7, label="Codice Classe")
    
    im2 = axes[1].imshow(mask)
    axes[1].set_title("USDA NASS CDL (Maschera Uso del Suolo)")
    axes[1].axis('off')

    
    fig.colorbar(im2, ax=axes[1], shrink=0.7, label="Codice Classe")
    
    
    plt.tight_layout()
    plt.show()


else:
    print("Errore: Impossibile scaricare il file TIFF da Google Drive.")


