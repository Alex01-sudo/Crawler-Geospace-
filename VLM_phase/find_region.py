import geopandas as gpd
import requests
from shapely.geometry import Point

NASS_API_KEY = "50BF6E22-04F0-3AA8-BA1E-43457BEA21AF"
STATE_FIPS = {
    "ALABAMA": "01",
    "ALASKA": "02",
    "ARIZONA": "04",
    "ARKANSAS": "05",
    "CALIFORNIA": "06",
    "COLORADO": "08",
    "CONNECTICUT": "09",
    "DELAWARE": "10",
    "FLORIDA": "12",
    "GEORGIA": "13",
    "HAWAII": "15",
    "IDAHO": "16",
    "ILLINOIS": "17",
    "INDIANA": "18",
    "IOWA": "19",
    "KANSAS": "20",
    "KENTUCKY": "21",
    "LOUISIANA": "22",
    "MAINE": "23",
    "MARYLAND": "24",
    "MASSACHUSETTS": "25",
    "MICHIGAN": "26",
    "MINNESOTA": "27",
    "MISSISSIPPI": "28",
    "MISSOURI": "29",
    "MONTANA": "30",
    "NEBRASKA": "31",
    "NEVADA": "32",
    "NEW HAMPSHIRE": "33",
    "NEW JERSEY": "34",
    "NEW MEXICO": "35",
    "NEW YORK": "36",
    "NORTH CAROLINA": "37",
    "NORTH DAKOTA": "38",
    "OHIO": "39",
    "OKLAHOMA": "40",
    "OREGON": "41",
    "PENNSYLVANIA": "42",
    "RHODE ISLAND": "44",
    "SOUTH CAROLINA": "45",
    "SOUTH DAKOTA": "46",
    "TENNESSEE": "47",
    "TEXAS": "48",
    "UTAH": "49",
    "VERMONT": "50",
    "VIRGINIA": "51",
    "WASHINGTON": "53",
    "WEST VIRGINIA": "54",
    "WISCONSIN": "55",
    "WYOMING": "56",
}

def get_asd_desc(lat: float, lon: float, state_name: str) -> str:
    """Finds the USDA NASS Agricultural District name (asd_desc) for a coordinate.

    Parameters:
    - lat (float): Latitude of the point.
    - lon (float): Longitude of the point.
    - state_fips (str): 2-digit State FIPS code (e.g., '19' for Iowa, '17' for Illinois).

    Returns:
    - str: asd_desc (e.g., 'NORTH CENTRAL', 'SOUTH EAST')
    """
    
    clean_state_name = state_name.strip().upper()

    if clean_state_name not in STATE_FIPS:
        raise ValueError(f"State name '{state_name}' is invalid or not found.")

    state_fips = STATE_FIPS[clean_state_name]
    
    state_fips = str(state_fips).zfill(2)

    
    census_url = f"https://www2.census.gov/geo/tiger/TIGER2023/COUNTY/tl_2023_us_county.zip"
    counties_gdf = gpd.read_file(census_url)

    
    state_counties = counties_gdf[counties_gdf["STATEFP"] == state_fips]

    
    point = Point(lon, lat)
    point_gdf = gpd.GeoDataFrame(
        geometry=[point], crs="EPSG:4269"
    )  

    joined = gpd.sjoin(point_gdf, state_counties, how="inner", predicate="within")

    if joined.empty:
        raise ValueError(
            f"Point ({lat}, {lon}) does not fall inside state FIPS {state_fips}"
        )

    county_fips = joined.iloc[0]["COUNTYFP"]

    
    nass_url = f"https://quickstats.nass.usda.gov/api/api_GET/?key={NASS_API_KEY}&state_fips_code={state_fips}&county_code={county_fips}&agg_level_desc=COUNTY&format=JSON"

    res = requests.get(nass_url).json()

    if "data" in res and len(res["data"]) > 0:
        return res["data"][0]["asd_desc"]
    else:
        raise ValueError("Could not retrieve ASD metadata from NASS API.")


