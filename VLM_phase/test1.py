import json
import Read_and_preprocess as Rp
from NASS_connect import NASSQuickStatsClient
import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
from qwen_vl_utils import process_vision_info


model_name = "Qwen/Qwen2-VL-7B-Instruct" 

quickstats_client = NASSQuickStatsClient()

# Carica Processor e Modello Vision
processor = AutoProcessor.from_pretrained(model_name)
model = Qwen2VLForConditionalGeneration.from_pretrained(
    model_name, torch_dtype=torch.bfloat16, device_map="auto"
)

# ... [il tuo codice per recuperare i dati JSON] ...
dict_ara, crops, district, State = Rp.read_and_preprocess(82)
raw_Nass = quickstats_client.fetch_detailed_crop_data(State, district, crops, 2024)

json_payload_query = json.dumps(dict_ara, indent=2)
json_payload_Nass = json.dumps(raw_Nass, indent=2)

# Carica l'immagine con PIL
image_path = "sentinel2_rgb.jpg"
image = Image.open(image_path)

system_prompt = (
    "You are an expert agricultural advisor. Your job is to suggest the most suitable crop "
    "to plant based on geographical, optical imagery, historical yield data, and soil information."
)

user_prompt = f"""Based on the provided optical image, location, and USDA NASS historical data, recommend the best crop to plant and add a crop rotation that may be suitable:

```json
{json_payload_query}
{json_payload_Nass}
```"""


messages = [
    {"role": "system", "content": system_prompt},
    {
        "role": "user",
        "content": [
            {"type": "image", "image": image},  
            {"type": "text", "text": user_prompt},
        ],
    },
]

# 3. Prepara gli input usando il processor invece del tokenizer
text = processor.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)
image_inputs, video_inputs = process_vision_info(messages)

inputs = processor(
    text=[text],
    images=[image],
    padding=True,
    return_tensors="pt"
).to(model.device)

# 4. Generazione
generated_ids = model.generate(**inputs, max_new_tokens=2048)

# Decodifica escludendo il prompt iniziale
generated_ids_trimmed = [
    out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
]
output_text = processor.batch_decode(
    generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
)

print("\n--- CROP RECOMMENDATION ---")
print(output_text[0])