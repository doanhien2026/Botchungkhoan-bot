# ==========================================================
# data_manager.py — V1.0 | LƯU + ĐỌC + KIỂM TRA DỮ LIỆU
# ==========================================================
import json
import os
import re
from datetime import datetime

DATA_FILE = "xsmb_data.json"

def load_data():
    """Đọc dữ liệu từ file JSON"""
    if not os.path.exists(DATA_FILE):
        print(f"📁 File {DATA_FILE} chưa tồn tại → trả về dict trống")
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                print(f"⚠️ File {DATA_FILE} sai định dạng → trả về trống")
                return {}
            return data
    except Exception as e:
        print(f"❌ Lỗi đọc {DATA_FILE}: {e} → trả về trống")
        return {}

def save_data(date_str, special, g1, loto, source="api"):
    """Lưu kết quả vào file JSON"""
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", date_str):
        print(f"❌ Ngày sai định dạng: {date_str}")
        return False
    if len(special) != 5 or not special.isdigit():
        print(f"❌ Đặc biệt sai: {special}")
        return False
    if len(g1) != 5 or not g1.isdigit():
        print(f"❌ Giải nhất sai: {g1}")
        return False
    
    data = load_data()
    data[date_str] = {
        "special": special.strip(),
        "g1": g1.strip(),
        "loto": [str(x).zfill(2) for x in loto if str(x).isdigit() and len(str(x)) == 2],
        "source": source,
        "saved_at": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 ĐÃ LƯU: {date_str} | Tổng: {len(data)} ngày")
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu: {e}")
        return False

def get_stats():
    """Lấy thông tin thống kê"""
    data = load_data()
    if not data:
        return 0, "--", "--"
    dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    return len(data), dates[0], dates[-1]
