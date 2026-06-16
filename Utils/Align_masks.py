import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling

def align_nass_to_sentinel(sentinel_path: str, nass_path: str, output_path: str):
    # 1. Apriamo l'immagine Sentinel-2 (Il nostro "Master" di riferimento)
    with rasterio.open(sentinel_path) as src_sentinel:
        master_profile = src_sentinel.profile
        master_crs = src_sentinel.crs
        master_transform = src_sentinel.transform
        master_width = src_sentinel.width
        master_height = src_sentinel.height

    # 2. Apriamo l'immagine NASS CDL (Quella storta da allineare)
    with rasterio.open(nass_path) as src_nass:
        # Prepariamo il profilo del nuovo file di output copiando quello di Sentinel
        # Ma impostiamo il tipo di dato a uint8 (visto che il NASS è a 8-bit)
        out_profile = master_profile.copy()
        out_profile.update({
            'dtype': 'uint8',
            'count': 1, # Il NASS ha una sola banda
            'nodata': 0
        })

        # 3. Creiamo il nuovo file TIF allineato
        with rasterio.open(output_path, 'w', **out_profile) as dst:
            # Eseguiamo la riproiezione (Warp) nel Cloud locale di Python
            reproject(
                source=rasterio.band(src_nass, 1),
                destination=rasterio.band(dst, 1),
                src_transform=src_nass.transform,
                src_crs=src_nass.crs,
                dst_transform=master_transform,
                dst_crs=master_crs,
                # CRUCIAL: Usiamo Nearest Neighbor perché il NASS è categorico!
                # Non possiamo fare la media dei pixel (es. classe 121 + classe 111 non deve fare 116!)
                resampling=Resampling.nearest 
            )
            
    