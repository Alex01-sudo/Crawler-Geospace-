import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.io import MemoryFile
import io   
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.discovery import build
from google.oauth2 import service_account

def align_nass_to_sentinel(sentinel_path: str, nass_path: str):
    
    
    
    with rasterio.open(sentinel_path) as src_sentinel:
        master_profile = src_sentinel.profile
        master_crs = src_sentinel.crs
        master_transform = src_sentinel.transform
        master_width = src_sentinel.width
        master_height = src_sentinel.height

    with rasterio.open(nass_path) as src_nass:
        
        out_profile = master_profile.copy()
        out_profile.update({
            'dtype': 'uint8',
            'count': 1, 
            'nodata': 0
        })

        
        with MemoryFile() as memfile:
                with memfile.open(**out_profile) as dst:
                    
                    reproject(
                        source=rasterio.band(src_nass, 1),
                        destination=rasterio.band(dst, 1),
                        src_transform=src_nass.transform,
                        src_crs=src_nass.crs,
                        dst_transform=master_transform,
                        dst_crs=master_crs,
                        resampling=Resampling.nearest 
                    )
                    
                    aligned_mask = dst.read(1)
        
    return aligned_mask