import rasterio
import numpy as np
from Utils.Read_rasterio import normalization 


def NDVI(file_tif):
    with rasterio.open(file_tif) as src:
        band_red = src.read(3).astype(float)
        band_nir = src.read(4).astype(float)

    ndvi = np.where(band_nir + band_red == 0, np.nan, (band_nir - band_red) / (band_nir + band_red))
    return np.nanmean(ndvi)

def NDWI(file_tif):
    with rasterio.open(file_tif) as src:
        band_green = src.read(2).astype(float)
        band_nir = src.read(4).astype(float)

    ndwi = np.where(band_green + band_nir == 0, np.nan, (band_green - band_nir) / (band_green + band_nir))
    return np.nanmean(ndwi)


def LAI(file_tif):
    with rasterio.open(file_tif) as src:
        band_red = src.read(3).astype(float)
        band_nir = src.read(4).astype(float)
        band_blue = src.read(1).astype(float)
        
    band_red = normalization(band_red)
    band_nir = normalization(band_nir)  
    band_blue = normalization(band_blue)

    denominator = band_nir + (band_red * 6.0) - (band_blue * 7.5) + 1.0
    
    EVA = np.where(denominator == 0, np.nan, 2.5 * ((band_nir - band_red) / denominator))
    lai = (5.4 * EVA) - 0.2
   
    if np.isnan(lai).all():
        return 0
    
    return np.nanmean(lai)

def CHL_green(file_tif):
    with rasterio.open(file_tif) as src:
        band_nir = src.read(4).astype(float)
        band_green = src.read(2).astype(float)

    chl_green = np.where(band_green == 0, np.nan, (band_nir/band_green) - 1)
    return np.nanmean(chl_green)