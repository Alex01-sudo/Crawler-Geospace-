
from dotenv import load_dotenv

from Software_Crawler.download import download_NASS_dataset_to_drive



load_dotenv()

if __name__ == "__main__":
    
    
    lat = 42.6511674 
    lon = -73.754968
    buffer_m = 10000
    year = 2023
    scale = 10.0
    city_name = "Washington_DC"
    drive_folder = "Test_NASS_Outputs"

    try:
        img_count = download_NASS_dataset_to_drive(
            lat=lat,
            lon=lon,
            buffer_m=buffer_m,
            year=year,
            scale=scale,
            city_name=city_name,
            drive_folder=drive_folder
        )
        print(f"Download completed successfully. Number of images: {img_count}")
    except Exception as e:
        print(f"An error occurred during download: {e}")