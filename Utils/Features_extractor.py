import io
import os
from pathlib import Path
import numpy as np
import rasterio
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModel

# -----------------------------------------------------------------------------
# CONFIGURAZIONE CACHE (Opzionale)
# -----------------------------------------------------------------------------
# Se vuoi forzare Hugging Face a non usare la cartella di default (es. su server),
# puoi decommentare la riga sotto e puntare a una cartella temporanea (/tmp)
# os.environ["HF_HOME"] = "/tmp/huggingface_cache"

MODEL_NAME = "google/vit-base-patch16-224"


def load_hf_model_and_processor(model_name: str = MODEL_NAME):
    
    print(f"Loading Hugging Face components for: {model_name}...")
    processor = AutoImageProcessor.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()  
    return processor, model



def extract_embedding_vector(pil_image: Image.Image, processor, model) -> np.ndarray:
    
    # Run the Hugging Face image processor (Handles resizing and scaling automatically)
    inputs = processor(images=pil_image, return_tensors="pt")
    
    # Disable gradient calculations to save massive amounts of RAM
    with torch.no_grad():
        outputs = model(**inputs)
        
        cls_features = outputs.last_hidden_state[:, 0, :]
        
        
        return cls_features.squeeze().numpy()