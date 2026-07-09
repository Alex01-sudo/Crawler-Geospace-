



import io
import numpy as np
import rasterio
import matplotlib.pyplot as plt


def read_rasterio(raw_data: bytes):

    if raw_data:
        file_tif = io.BytesIO(raw_data)
        
    with rasterio.open(file_tif) as src:
        band1 = src.read(1)
        band2 = src.read(2)
        band3 = src.read(3)
    return np.dstack((band3, band2, band1))

def normalization(img):
    if np.max(img) <= 255:
        return img
        
    
    p_min, p_max = np.nanpercentile(img, (2, 98))
    
    
    img_norm = np.clip((img - p_min) / (p_max - p_min), 0, 1)
    
    return img_norm
    
def plot_rasterio(list_answers_ranked: bytes, ranked_results: list):            
    
    list_img = []
    
    for band in list_answers_ranked:
        img = read_rasterio(band)
        list_img.append(img)
        
    
    layout = """
        AAAAAAABBBBBBBCCCCCCC
        DDDEEEFFFGGGHHHIIIJJJ
        """
    fig, ax_dict = plt.subplot_mosaic(layout, figsize=(16, 8))
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']

    
    for i, letter in enumerate(letters):
        ax = ax_dict[letter]
        
        
         
        
        
        city = ranked_results[i][0]
        
        img = normalization(list_img[i])
        ax.imshow(img)
        
        if i < 3:
            ax.set_title(f"{i+1}. {city}", fontsize=14, fontweight='bold')
        else:
            ax.set_title(f"{i+1}. {city}", fontsize=11)
            
        ax.axis('off')

    
    plt.tight_layout()
    plt.show()