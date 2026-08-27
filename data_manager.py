import json
import os
from datetime import datetime

DATA_FILE = "xsmb_data.json"

def load_all_data():
    if not os.path.exists(DATA_FILE):
        print(f"📂 File {DATA_FILE} chưa tồn tại — sẽ tự tạo khi có dữ liệu")
        return {"history": [], "last_updated": ""}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Lỗi đọc file: {e} — tạo mới")
        return {"history": [], "last_updated": ""}

def save_result(result):
    if not result or "date" not in result or "special" not in result:
        print("❌ Dữ liệu không hợp lệ — không lưu")
        return False
    data = load_all_data()
    data["history"] = [item for item in data["history"] if item["date"] != result["date"]]
    data["history"].append(result)
    data["last_updated"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    if len(data["history"]) > 90:
        data["history"] = data["history"][-90:]
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Đã lưu: {result['date']} | ĐB: {result['special']} | Tổng: {len(data['history'])} ngày")
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu file: {e}")
        return False

def get_saved_result(date_str):
    data = load_all_data()
    return next((item for item in data["history"] if item["date"] == date_str), None)

def get_all_dates():
    data = load_all_data()
    return [item["date"] for item in data["history"]]

