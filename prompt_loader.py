import json
import os

def load_prompt_blocks(file_path="prompt_blocks.json"):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} 파일을 찾을 수 없습니다.")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["blocks"]
