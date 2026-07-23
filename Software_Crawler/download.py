from __future__ import annotations
import argparse
import os
from pathlib import Path
import ee
import time





def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download a Sentinel-2 composite from Google Earth Engine using a square buffer"
    )
    parser.add_argument("--lat", type=float, required=True, help="Latitude in decimal degrees")
    parser.add_argument("--lon", type=float, required=True, help="Longitude in decimal degrees")
    parser.add_argument(
        "--buffer-m",
        type=float,
        default=1000.0,
        help="Buffer radius in meters before converting to square bounds",
    )
    parser.add_argument("--start", default="2023-06-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2023-08-31", help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--cloud-max",
        type=float,
        default=10.0,
        help="Maximum CLOUDY_PIXEL_PERCENTAGE",
    )
    parser.add_argument(
        "--bands",
        type=str,
        nargs="+",
        default=["B2", "B3", "B4", "B8", "B11", "B12"],
        help="Sentinel-2 bands to export",
    )
    parser.add_argument("--scale", type=float, default=10.0, help="Export pixel size in meters")
    parser.add_argument(
        "--output",
        default="data/raw/S2_square_gee.tif",
        help="Output GeoTIFF path",
    )
    parser.add_argument(
        "--roi-json",
        default="data/raw/S2_square_roi.geojson",
        help="Path to save the square ROI as GeoJSON",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="Optional GEE Cloud project id used in ee.Initialize(project=...)",
    )
    parser.add_argument(
        "--service-account",
        default=None,
        help="Service account email for non-interactive auth",
    )
    parser.add_argument(
        "--service-account-key",
        default=None,
        help="Path to service account JSON key for non-interactive auth",
    )
    return parser


import ee

def initialize_ee(
    project: str | None,
    service_account: str | None,
    service_account_key: str | None,
) -> None:
    try:
        
        if service_account and service_account_key:
            print("Service Account credentials found. Initializing GEE with Service Account...")
            credentials = ee.ServiceAccountCredentials(service_account, service_account_key)
            if project:
                ee.Initialize(credentials=credentials, project=project)
            else:
                ee.Initialize(credentials=credentials)
            return

        
        print(" Using local user credentials for GEE initialization...")
        
        
        if project:
            
            try:
                ee.Initialize(project=project)
            except Exception:
                credentials = ee.data.get_persistent_credentials()
                ee.Initialize(credentials=credentials, project=project)
        else:
            try:
                ee.Initialize()
            except Exception:
                credentials = ee.data.get_persistent_credentials()
                ee.Initialize(credentials=credentials)
                
       

    except Exception as init_error:
        raise RuntimeError(
            "Google Earth Engine init failed. Assicurati di aver lanciato 'earthengine authenticate' "
            "nel terminale dell'ambiente virtuale attivo, oppure verifica che le variabili d'ambiente "
            "del Service Account nel file .env siano caricate correttamente tramite load_dotenv()."
        ) from init_error


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)




def download_sentinel_composite_to_drive(
    lat: float,
    lon: float,
    buffer_m: float = 10000.0,
    start_date: str = "2023-06-01",
    end_date: str = "2023-08-31",
    cloud_max: float = 10.0,
    bands: list[str] = ["B2", "B3", "B4", "B8", "B11", "B12"],
    scale: float = 10.0,
    drive_folder: str = "GEE_Crawler_Outputs_thesis",
    project: str | None = None,
    service_account: str | None = None,
    service_account_key: str | None = None,
) -> int:
    
    
    project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
    service_account = service_account or os.getenv("GEE_SERVICE_ACCOUNT")
    service_account_key = service_account_key or os.getenv("GEE_SERVICE_ACCOUNT_KEY")
    
    initialize_ee(project, service_account, service_account_key)

    point = ee.Geometry.Point([lon, lat])
    square = point.buffer(buffer_m).bounds()

    image_collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(square)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_max))
    )

    image_count = int(image_collection.size().getInfo())
    if image_count == 0:
        raise RuntimeError(
            f"No Sentinel-2 images found for coordinates ({lat}, {lon}) with current constraints."
        )

    composite_image = image_collection.median().select(bands).clip(square)
    file_prefix = f"S2_{round(lat, 2)}_{round(lon, 2)}"

    
    image_task = ee.batch.Export.image.toDrive(
        image=composite_image,
        description=f"{file_prefix}_image",
        folder=drive_folder,
        fileNamePrefix=file_prefix,
        region=square,
        scale=scale,
        fileFormat="GeoTIFF",
        maxPixels=1e9
    )

    roi_feature = ee.Feature(square, {
        "lat": lat,
        "lon": lon,
        "buffer_m": buffer_m,
        "start_date": start_date,
        "end_date": end_date,
        "cloud_max": cloud_max,
        "image_count": image_count
    })
    roi_collection = ee.FeatureCollection([roi_feature])

    table_task = ee.batch.Export.table.toDrive(
        collection=roi_collection,
        description=f"{file_prefix}_roi",
        folder=drive_folder,
        fileNamePrefix=f"{file_prefix}_roi",
        fileFormat="GeoJSON"
    )

    
    image_task.start()
    table_task.start()
    print(f" Tasks started in the Cloud for {lat}, {lon}.")
    print(f"   Image Task ID: {image_task.id}")
    print(f"   ROI Table Task ID: {table_task.id}")
    
    while image_task.active() or table_task.active():
        print(f" Processing {lat}, {lon} on Google servers...")
        print(f"  [Image Status: {image_task.status()['state']}] [ROI Status: {table_task.status()['state']}]")
        time.sleep(15)  
        
    
    final_image_status = image_task.status()
    final_table_status = table_task.status()

    if final_image_status['state'] == 'COMPLETED' and final_table_status['state'] == 'COMPLETED':
        print(f" Success! Both files for {lat}, {lon} are now saved in your Google Drive under '{drive_folder}'")
    else:
        error_msg = f"Image Error: {final_image_status.get('errorMessage', 'None')} | Table Error: {final_table_status.get('errorMessage', 'None')}"
        raise RuntimeError(f" Earth Engine tasks failed for {lat}, {lon}. Details: {error_msg}")

    return image_count

def main() -> None:
    """Mantiene la compatibilità per l'esecuzione diretta da Terminale."""
    args = build_parser().parse_args()
    
    
    download_sentinel_composite_to_drive(**vars(args))



def download_NASS_dataset_to_drive(
    lat: float,
    lon: float,
    buffer_m: float = 10000.0,
    year: int = 2023,
    scale: float = 10.0,
    drive_folder: str = "GEE_NASS_Outputs_thesis",
    project: str | None = None,
    service_account: str | None = None,
    service_account_key: str | None = None,
) -> int:
    
    
    project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
    service_account = service_account or os.getenv("GEE_SERVICE_ACCOUNT")
    service_account_key = service_account_key or os.getenv("GEE_SERVICE_ACCOUNT_KEY")
    
    initialize_ee(project, service_account, service_account_key)

    point = ee.Geometry.Point([lon, lat])
    square = point.buffer(buffer_m).bounds()
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    image_cl = (
        ee.ImageCollection("USDA/NASS/CDL")
        .filterBounds(square)
        .filterDate(start_date, end_date)
        .select("cropland")
        .first()
    )
    
    image_to_export = image_cl.clip(square)
    
    image_to_export = image_to_export.uint8().set({"cropland_class_names": None})

    
    try:
        image_to_export.bandNames().getInfo()
    except Exception as e:
        raise RuntimeError(
            f"No NASS images found for coordinates ({lat}, {lon}) in year {year} with current constraints."
        ) from e
    
    
    
    file_prefix = f"NASS_{round(lat, 2)}_{round(lon, 2)}"

    
    image_task = ee.batch.Export.image.toDrive(
        image=image_to_export,
        description=f"{file_prefix}_image",
        folder=drive_folder,
        fileNamePrefix=file_prefix,
        region=square,
        scale=scale,
        fileFormat="GeoTIFF",
        maxPixels=1e9
    )

    roi_feature = ee.Feature(square, {
        "lat": lat,
        "lon": lon,
        "buffer_m": buffer_m,
        "year": year,
        "scale": scale
    })
    roi_collection = ee.FeatureCollection([roi_feature])

    table_task = ee.batch.Export.table.toDrive(
        collection=roi_collection,
        description=f"{file_prefix}_roi",
        folder=drive_folder,
        fileNamePrefix=f"{file_prefix}_roi",
        fileFormat="GeoJSON"
    )

    
    image_task.start()
    table_task.start()
    print(f" Tasks started in the Cloud for {file_prefix}.")
    print(f"   Image Task ID: {image_task.id}")
    print(f"   ROI Table Task ID: {table_task.id}")
    
    while image_task.active() or table_task.active():
        print(f" Processing {file_prefix} on Google servers...")
        print(f"  [Image Status: {image_task.status()['state']}] [ROI Status: {table_task.status()['state']}]")
        time.sleep(15)  
        
    
    final_image_status = image_task.status()
    final_table_status = table_task.status()

    if final_image_status['state'] == 'COMPLETED' and final_table_status['state'] == 'COMPLETED':
        print(f" Success! Both files for {file_prefix} are now saved in your Google Drive under '{drive_folder}'")
    else:
        error_msg = f"Image Error: {final_image_status.get('errorMessage', 'None')} | Table Error: {final_table_status.get('errorMessage', 'None')}"
        raise RuntimeError(f" Earth Engine tasks failed for {file_prefix}. Details: {error_msg}")

    
import ee

def extract_era5_climate_data(
    lat: float,
    lon: float,
    buffer_m: float = 10000.0, 
    start_date: str = "2023-06-01",
    end_date: str = "2023-08-31",
    project: str | None = None,
    service_account: str | None = None,
    service_account_key: str | None = None,) -> dict:
    
   
    project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
    service_account = service_account or os.getenv("GEE_SERVICE_ACCOUNT")
    service_account_key = service_account_key or os.getenv("GEE_SERVICE_ACCOUNT_KEY")

    initialize_ee(project, service_account, service_account_key)

    era5 = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY") \
        .filterDate(start_date, end_date) \
        .select([
            'temperature_2m', 
            'total_precipitation', 
            'total_evaporation', 
            'volumetric_soil_water_layer_1',
            'surface_net_solar_radiation',
            'leaf_area_index_high_vegetation',
            'leaf_area_index_low_vegetation'
        ])
    
    mean_image = era5.mean()
    point = ee.Geometry.Point([lon, lat])
    geometry = point.buffer(buffer_m).bounds()
    
    
    reduced_data = mean_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=10000,
        maxPixels=1e9
    )
    
    
    climate_dict = reduced_data.getInfo()
    

    return climate_dict


def calculate_agricultural_density(
    lat: float,
    lon: float,
    buffer_m: float = 10000.0,
    year: int = 2023,
    project: str | None = None,
    service_account: str | None = None,
    service_account_key: str | None = None,
) -> dict:
    
    
    
    project = project or os.getenv("GOOGLE_CLOUD_PROJECT") 
    service_account = service_account or os.getenv("GEE_SERVICE_ACCOUNT") 
    service_account_key = service_account_key or os.getenv("GEE_SERVICE_ACCOUNT_KEY") 
    
    initialize_ee(project, service_account, service_account_key) 

    point = ee.Geometry.Point([lon, lat])
    roi = point.buffer(buffer_m)
    
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"


    dataset = (
        ee.ImageCollection("USDA/NASS/CDL")
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .first()
    )
    cropland = dataset.select("cropland")

    
    non_crop_classes = [
        111, 112, 121, 122, 123, 124, 131, 
        141, 142, 143, 152, 176, 190, 195
    ]
    
    
    zero_values = ee.List.repeat(0, len(non_crop_classes))

    
    is_crop_binary = cropland.remap(
        from_=non_crop_classes,
        to=zero_values,
        defaultValue=1 
    ).rename('crop_pixel')

    
    stats = is_crop_binary.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=roi,
        scale=30, 
        maxPixels=1e9
    )

    
    stats_dict = stats.getInfo()
    
    
    mean_val = stats_dict.get('crop_pixel')
    
    
    if mean_val is None:
        mean_val = 0.0

    
    useful_perc = mean_val * 100.0
    useless_perc = 100.0 - useful_perc

    return {
        "lat": lat,
        "lon": lon,
        "useful_crop_percentage": round(useful_perc, 2),
        "useless_non_crop_percentage": round(useless_perc, 2)
    }




if __name__ == "__main__":
    main()