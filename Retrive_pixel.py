from Software_Crawler.download import calculate_agricultural_density
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

def main ():
    dataframe = pd.read_csv("fao_gaul_usa_grid_with_states.csv")
    
    final_results = []
    for index, row in dataframe.iterrows():
        lat = row['lat']
        lon = row['lon']
        buffer_m = 10000  
        result = calculate_agricultural_density(lat, lon, buffer_m)
        
        final_results.append(result)

    
    final_df = pd.DataFrame(final_results)
    final_df.sort_values(by=['useful_crop_percentage'], ascending=False, inplace=True)
    final_df.to_csv('agricultural_density_results.csv', index=False)
    
    
    
if __name__ == "__main__":
    main()
    