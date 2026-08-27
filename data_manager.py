import json
import os
from datetime import datetime
from config import DATA_FILE

def init_data_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

def save_result(result):
    init_data_file()
    date_key = result.get("date")
    if not date_key:
        return False
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data[date_key] = result
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Đã lưu: {date_key}")
    return True

def get_saved_result(date_str):
    init_data_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(date_str)

def get_all_dates():
    init_data_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return list(data.keys())
