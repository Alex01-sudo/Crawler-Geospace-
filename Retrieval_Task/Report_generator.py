import os
import numpy as np
from dotenv import load_dotenv
import rasterio
import io
from Software_Crawler.Storage import ArangoStorageManager
from Utils.Align_masks import align_nass_to_sentinel
from Utils.Get_google_drive import get_tif_from_drive
from Utils.Veg_indexes import NDVI, NDWI, LAI, CHL_green



NASS_CLASSES = {
    0: "Background",
    1: "Corn",
    2: "Cotton",
    3: "Rice",
    4: "Sorghum",
    5: "Soybeans",
    6: "Sunflower",
    10: "Peanuts",
    11: "Tobacco",
    12: "Sweet Corn",
    13: "Pop or Orn Corn",
    14: "Mint",
    21: "Barley",
    22: "Durum Wheat",
    23: "Spring Wheat",
    24: "Winter Wheat",
    25: "Other Small Grains",
    26: "Dbl Crop WinWht/Soybeans",
    27: "Rye",
    28: "Oats",
    29: "Millet",
    30: "Speltz",
    31: "Canola",
    32: "Flaxseed",
    33: "Safflower",
    34: "Rape Seed",
    35: "Mustard",
    36: "Alfalfa",
    37: "Other Hay/Non Alfalfa",
    38: "Camelina",
    39: "Buckwheat",
    41: "Sugarbeets",
    42: "Dry Beans",
    43: "Potatoes",
    44: "Other Crops",
    45: "Sugarcane",
    46: "Sweet Potatoes",
    47: "Misc Vegs & Fruits",
    48: "Watermelons",
    49: "Onions",
    50: "Cucumbers",
    51: "Chick Peas",
    52: "Lentils",
    53: "Peas",
    54: "Tomatoes",
    55: "Caneberries",
    56: "Hops",
    57: "Herbs",
    58: "Clover/Wildflowers",
    59: "Sod/Grass Seed",
    60: "Switchgrass",
    61: "Fallow/Idle Cropland",
    63: "Forest",
    64: "Shrubland",
    65: "Barren",
    66: "Cherries",
    67: "Peaches",
    68: "Apples",
    69: "Grapes",
    70: "Christmas Trees",
    71: "Other Tree Crops",
    72: "Citrus",
    74: "Pecans",
    75: "Almonds",
    76: "Walnuts",
    77: "Pears",
    81: "Clouds/No Data",
    82: "Developed",
    83: "Water",
    87: "Wetlands",
    88: "Nonag/Undefined",
    92: "Aquaculture",
    111: "Open Water",
    112: "Perennial Ice/Snow",
    121: "Developed/Open Space",
    122: "Developed/Low Intensity",
    123: "Developed/Med Intensity",
    124: "Developed/High Intensity",
    131: "Barren",
    141: "Deciduous Forest",
    142: "Evergreen Forest",
    143: "Mixed Forest",
    152: "Shrubland",
    176: "Grass/Pasture",
    190: "Woody Wetlands",
    195: "Herbaceous Wetlands",
    204: "Pistachios",
    205: "Triticale",
    206: "Carrots",
    207: "Asparagus",
    208: "Garlic",
    209: "Cantaloupes",
    210: "Prunes",
    211: "Olives",
    212: "Oranges",
    213: "Honeydew Melons",
    214: "Broccoli",
    215: "Avocados",
    216: "Peppers",
    217: "Pomegranates",
    218: "Nectarines",
    219: "Greens",
    220: "Plums",
    221: "Strawberries",
    222: "Squash",
    223: "Apricots",
    224: "Vetch",
    225: "Dbl Crop WinWht/Corn",
    226: "Dbl Crop Oats/Corn",
    227: "Lettuce",
    228: "Dbl Crop Triticale/Corn",
    229: "Pumpkins",
    230: "Dbl Crop Lettuce/Durum Wht",
    231: "Dbl Crop Lettuce/Cantaloupe",
    232: "Dbl Crop Lettuce/Cotton",
    233: "Dbl Crop Lettuce/Barley",
    234: "Dbl Crop Durum Wht/Sorghum",
    235: "Dbl Crop Barley/Sorghum",
    236: "Dbl Crop WinWht/Sorghum",
    237: "Dbl Crop Barley/Corn",
    238: "Dbl Crop WinWht/Cotton",
    239: "Dbl Crop Soybeans/Cotton",
    240: "Dbl Crop Soybeans/Oats",
    241: "Dbl Crop Corn/Soybeans",
    242: "Blueberries",
    243: "Cabbage",
    244: "Cauliflower",
    245: "Celery",
    246: "Radishes",
    247: "Turnips",
    248: "Eggplants",
    249: "Gourds",
    250: "Cranberries",
    254: "Dbl Crop Barley/Soybeans"
}



load_dotenv()

class ReportGenerator:
    def __init__(self):
        
        self.storage = ArangoStorageManager()
        self.db = self.storage.db
    
    def retrieve_starting_node(self) -> dict | None:
        
        node_not_visited = self.storage.node_to_visit()
        if node_not_visited:
            return node_not_visited[0] 
        return None
    
            
    def  generate_report(self):
            
            self.storage.reset_visited_status()
            current_node = self.retrieve_starting_node()
            while current_node is not None:
                lon , lat = current_node["coordinates"][0], current_node["coordinates"][1]
                cloud_filename = f"Aligned_NASS_{round(lat, 2)}_{round(lon, 2)}"
                S2_file_name = current_node["file_tif_path"].split("/")[-1]
                NASS_file_name = current_node["nass_tif_path"].split("/")[-1]
                raw_data1 = get_tif_from_drive(S2_file_name, os.getenv("GOOGLE_CLOUD_CREDENTIALS"))
                raw_data2 = get_tif_from_drive(NASS_file_name, os.getenv("GOOGLE_CLOUD_CREDENTIALS"))

                file_tif = io.BytesIO(raw_data1)
                file_tif_NASS = io.BytesIO(raw_data2)
                try:
                    
                    mask = align_nass_to_sentinel(file_tif, file_tif_NASS)
                    print(f"Generating report for {lat}, {lon}...")
                    
                    classes, counts = np.unique(mask, return_counts=True)
                                        
                    total_pixels = np.sum(counts)

                    histogram = {}
                    
                    for k, count_val in zip(classes, counts):
                        class_id = int(k)
                        percentage = round((count_val / total_pixels) * 100, 2)
                        
                        class_name = NASS_CLASSES.get(class_id, f"Unknown_Class_{class_id}")
                        
                        histogram[class_name] = percentage
                    
                    
                    self.storage.add_attribute(lat, lon, "histogram", histogram)
                    self.storage.change_visited_status(lat, lon, True)

                    
                except Exception as e:
                    print(f"Error processing Histogram of {lat}, {lon}: {e}")
                    break       
                    
                
                
                try:
                    NVDI_value = NDVI(file_tif)
                    NDWI_value = NDWI(file_tif)
                    LAI_value = LAI(file_tif)
                    Chl_green_value = CHL_green(file_tif)
                    
                    dict = {
                        "NDVI": NVDI_value,
                        "NDWI": NDWI_value,
                        "LAI": LAI_value,
                        "CHL_green": Chl_green_value
                    }
                    
                    self.storage.add_attribute(lat, lon,attribute_name = "indexes", attribute_value=dict)
                except Exception as e:
                    print(f"Error processing Vegetation Indexes of {lat}, {lon}: {e}")
                    break 
                    
                next_node = self.storage.find_next_neighbour(current_node)
                
                if next_node:
                
                    current_node = next_node
                else:
                
                    current_node = None
                    
                    
            
                    

