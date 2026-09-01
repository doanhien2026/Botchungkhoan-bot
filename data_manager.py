# ==========================================================
# data_manager.py — LƯU + ĐỌC + THỐNG KÊ DỮ LIỆU
# ==========================================================
import json
import os
import re
from datetime import datetime
from config import DATA_FILE

def load_data():
    if not os.path.exists(DATA_FILE):
        print(f"📁 File {DATA_FILE} chưa tồn tại")
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"❌ Lỗi đọc {DATA_FILE}: {e}")
        return {}

def save_data(date_str, special, g1, loto, source="api"):
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", date_str):
        return False
    if len(special) != 5 or len(g1) != 5:
        return False
    data = load_data()
    data[date_str] = {
        "special": special.strip(),
        "g1": g1.strip(),
        "loto": [str(x).zfill(2) for x in loto if str(x).isdigit()],
        "source": source,
        "saved_at": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 LƯU OK: {date_str} | Tổng: {len(data)} ngày")
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu: {e}")
        return False

def get_stats():
    data = load_data()
    if not data:
        return 0, "--", "--"
    dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    return len(data), dates[0], dates[-1]
