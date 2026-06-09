from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import ee
import requests


BASE_DIR = Path(__file__).resolve().parent.parent


output_path_tif = BASE_DIR / "data" / "raw" / "S2_square_gee.tif"
outputh_path_geojson = BASE_DIR / "data" / "raw" / "S2_square_roi.geojson"



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


def download_sentinel_composite(
    lat: float,
    lon: float,
    buffer_m: float = 1000.0,
    start: str = "2023-06-01",
    end: str = "2023-08-31",
    cloud_max: float = 10.0,
    bands: list[str] = ["B2", "B3", "B4", "B8", "B11", "B12"],
    scale: float = 10.0,
    output: str = output_path_tif,
    roi_json: str = outputh_path_geojson,
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

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(square)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_max))
    )

    image_count = int(collection.size().getInfo())
    if image_count == 0:
        raise RuntimeError(
            f"No Sentinel-2 images found for coordinates ({lat}, {lon}) with current constraints."
        )

    composite = collection.median().select(bands).clip(square)

    # Salvataggio GeoTIFF locale
    output_path = Path(output)
    ensure_parent(output_path)

    download_url = composite.getDownloadURL(
        {
            "name": output_path.stem,
            "region": square,
            "scale": scale,
            "format": "GEO_TIFF",
        }
    )

    response = requests.get(download_url, timeout=300)
    response.raise_for_status()
    output_path.write_bytes(response.content)

    
    roi_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "lat": lat,
                    "lon": lon,
                    "buffer_m": buffer_m,
                    "start": start,
                    "end": end,
                    "cloud_max": cloud_max,
                },
                "geometry": square.getInfo(),
            }
        ],
    }
    roi_path = Path(roi_json)
    ensure_parent(roi_path)
    roi_path.write_text(json.dumps(roi_geojson, indent=2), encoding="utf-8")

    print(f"-> Earth Engine download completed for ({lat}, {lon}). Images used: {image_count}")
    return image_count


def main() -> None:
    """Mantiene la compatibilità per l'esecuzione diretta da Terminale."""
    args = build_parser().parse_args()
    
    
    download_sentinel_composite(**vars(args))


if __name__ == "__main__":
    main()