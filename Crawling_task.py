import os
import time
from pathlib import Path
from dotenv import load_dotenv
from geopy.geocoders import Nominatim

from Software_Crawler.Storage import ArangoStorageManager
from Software_Crawler.Spider import GraphSpider

load_dotenv()

def main():
    Spider = GraphSpider()
    Spider.execute_crawl()   


if __name__ == "__main__":
    main()
    



# Aggiungere parte di features extraction per la classificazione 
# Aggiungere piu dataset ( http://developers.google.com/earth-engine/datasets/catalog/USDA_NASS_CDL#description) 

#ciao sono qui per classificare 
