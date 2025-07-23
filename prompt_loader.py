# prompt_loader.py
import json
import os

def load_prompt_blocks(json_path="prompt_blocks.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "blocks" in data:
        return data["blocks"]
    else:
        return []

