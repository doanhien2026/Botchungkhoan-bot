import requests
import random
import re
from datetime import datetime, timezone, timedelta

VN_TZ = timezone(timedelta(hours=7))

def get_now_vn():
    return datetime.now(VN_TZ)

def get_xsmb_result(target_date_str=None):
    if not target_date_str:
        target_date_str = get_now_vn().strftime("%d/%m/%Y")

    parts = target_date_str.split("/")
    if len(parts) != 3:
        return None
        
    d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
    date_api = f"{d}/{m}/{y}"
    display_date = f"{d}/{m}/{y}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*"
    }

    # ==========================================
    # NGUỒN 1: API XOSO.ME — TRẢ JSON, CHÍNH XÁC NHẤT
    # ==========================================
    try:
        url = f"https://api.xoso.me/xsmb?date={y}-{m}-{d}"
        print(f"🔍 [API XOSO.ME] Đang lấy: {url}")
        r = requests.get(url, headers=headers, timeout=20)
        
        if r.status_code == 200:
            data = r.json()
            if data and data.get("status") == "success" and data.get("result"):
                res = data["result"]
                db = str(res.get("special", ""))
                g1 = str(res.get("first", ""))
                g2 = [str(x) for x in res.get("second", [])]
                g3 = [str(x) for x in res.get("third", [])]
                g4 = [str(x) for x in res.get("fourth", [])]
                g5 = [str(x) for x in res.get("fifth", [])]
                g6 = [str(x) for x in res.get("sixth", [])]
                g7 = [str(x) for x in res.get("seventh", [])]
                
                # Tính LÔ: 2 số cuối tất cả giải
                all_prizes = [db, g1] + g2 + g3 + g4 + g5 + g6 + g7
                lotos = [p[-2:] for p in all_prizes if len(str(p)) >= 2]
                lotos = sorted(list(set(lotos)))
                
                print(f"✅ [API XOSO.ME] {display_date} | ĐB: {db} | Lô: {len(lotos)} số")
                return {
                    "date": display_date,
                    "special": db,
                    "g1": g1,
                    "g2": g2,
                    "g3": g3,
                    "g4": g4,
                    "g5": g5,
                    "g6": g6,
                    "g7": g7,
                    "loto": lotos,
                    "source": "API XOSO.ME"
                }
    except Exception as e:
        print(f"❌ [API XOSO.ME] Lỗi: {str(e)[:60]}")

    # ==========================================
    # NGUỒN 2: KETQUA.NET API — DỰ PHÒNG
    # ==========================================
    try:
        url = f"https://ketqua.net/api?date={d}-{m}-{y}"
        print(f"🔍 [KETQUA.net API] Đang lấy: {url}")
        r = requests.get(url, headers=headers, timeout=20)
        
        if r.status_code == 200:
            data = r.json()
            if data.get("data"):
                res = data["data"]
                db = str(res.get("DB", ""))
                g1 = str(res.get("G1", ""))
                g2 = res.get("G2", [])
                g3 = res.get("G3", [])
                g4 = res.get("G4", [])
                g5 = res.get("G5", [])
                g6 = res.get("G6", [])
                g7 = res.get("G7", [])
                
                all_prizes = [db, g1] + g2 + g3 + g4 + g5 + g6 + g7
                lotos = [str(p)[-2:] for p in all_prizes if len(str(p)) >= 2]
                lotos = sorted(list(set(lotos)))
                
                print(f"✅ [KETQUA.net API] {display_date} | ĐB: {db} | Lô: {len(lotos)} số")
                return {
                    "date": display_date,
                    "special": db,
                    "g1": g1,
                    "g2": g2,
                    "g3": g3,
                    "g4": g4,
                    "g5": g5,
                    "g6": g6,
                    "g7": g7,
                    "loto": lotos,
                    "source": "KETQUA.net API"
                }
    except Exception as e:
        print(f"❌ [KETQUA.net API] Lỗi: {str(e)[:60]}")

    # ==========================================
    # TẤT CẢ NGUỒN LỖI → TRẢ None (KHÔNG TẠO SỐ GIẢ!)
    # ==========================================
    print(f"❌ KHÔNG LẤY ĐƯỢC DỮ LIỆU NGÀY {display_date}")
    return None

# === DỰ BÁO ===
def get_xsmb_prediction(target_date_str=None):
    if not target_date_str:
        target_date_str = get_now_vn().strftime("%d/%m/%Y")
    parts = target_date_str.split("/")
    if len(parts) != 3:
        return None
    d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
    random.seed(int(f"{y}{m}{d}") + 999)
    return {
        "date": f"{d}/{m}/{y}",
        "bach_thu": str(random.randint(0, 99)).zfill(2),
        "song_thu": [str(random.randint(0, 99)).zfill(2) for _ in range(2)],
        "lo_xiu": [str(random.randint(0, 99)).zfill(2) for _ in range(4)]
    }
