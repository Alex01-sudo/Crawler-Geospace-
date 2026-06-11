from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import ee
import requests
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


def initialize_ee(
    project: str | None,
    service_account: str | None,
    service_account_key: str | None,
) -> None:
    try:
        if service_account and service_account_key:
            credentials = ee.ServiceAccountCredentials(service_account, service_account_key)
            if project:
                ee.Initialize(credentials=credentials, project=project)
            else:
                ee.Initialize(credentials=credentials)
            return
        if project:
            ee.Initialize(project=project)
        else:
            ee.Initialize()
    except Exception as init_error:
        raise RuntimeError(
            "Google Earth Engine init failed. Use interactive auth with earthengine authenticate, "
            "or pass --service-account and --service-account-key (or env vars "
            "GEE_SERVICE_ACCOUNT and GEE_SERVICE_ACCOUNT_KEY)."
        ) from init_error


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)




def download_sentinel_composite_to_drive(
    lat: float,
    lon: float,
    buffer_m: float = 1000.0,
    start_date: str = "2023-06-01",
    end_date: str = "2023-08-31",
    cloud_max: float = 10.0,
    bands: list[str] = ["B2", "B3", "B4", "B8", "B11", "B12"],
    scale: float = 10.0,
    city_name: str = "capital_task",
    drive_folder: str = "GEE_Crawler_Outputs",
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
    file_prefix = f"S2_{city_name.lower().replace(' ', '_')}"

    
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
    print(f" Tasks started in the Cloud for {city_name}.")
    print(f"   Image Task ID: {image_task.id}")
    print(f"   ROI Table Task ID: {table_task.id}")
    
    while image_task.active() or table_task.active():
        print(f" Processing {city_name} on Google servers...")
        print(f"  [Image Status: {image_task.status()['state']}] [ROI Status: {table_task.status()['state']}]")
        time.sleep(15)  
        
    
    final_image_status = image_task.status()
    final_table_status = table_task.status()

    if final_image_status['state'] == 'COMPLETED' and final_table_status['state'] == 'COMPLETED':
        print(f" Success! Both files for {city_name} are now saved in your Google Drive under '{drive_folder}'")
    else:
        error_msg = f"Image Error: {final_image_status.get('errorMessage', 'None')} | Table Error: {final_table_status.get('errorMessage', 'None')}"
        raise RuntimeError(f" Earth Engine tasks failed for {city_name}. Details: {error_msg}")

    return image_count

def main() -> None:
    """Mantiene la compatibilità per l'esecuzione diretta da Terminale."""
    args = build_parser().parse_args()
    
    
    download_sentinel_composite_to_drive(**vars(args))


if __name__ == "__main__":
    main()