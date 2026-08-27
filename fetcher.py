import requests
from datetime import datetime, timezone, timedelta

VN_TZ = timezone(timedelta(hours=7))

def get_now_vn():
    return datetime.now(VN_TZ)

def get_xsmb_result(target_date_str=None):
    if not target_date_str:
        target_date_str = get_now_vn().strftime("%d/%m/%Y")

    # Làm sạch chuỗi ngày
    target_date_str = target_date_str.strip()
    parts = target_date_str.split("/")
    if len(parts) != 3:
        return None
        
    d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
    
    # Sử dụng API JSON trực tiếp không bị Cloudflare chặn
    url = f"https://api.vnpay.vn/vnpay-kqxs/xsmb?date={d}{m}{y}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }

    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            data_json = res.json()
            # Bóc tách dữ liệu JSON
            if data_json.get("code") == "00" or "data" in data_json:
                data = data_json.get("data", {})
                db = str(data.get("gdb") or "").strip()
                g1 = str(data.get("g1") or "").strip()
                
                if db or g1:
                    g2 = [str(x) for x in data.get("g2", [])]
                    g3 = [str(x) for x in data.get("g3", [])]
                    g4 = [str(x) for x in data.get("g4", [])]
                    g5 = [str(x) for x in data.get("g5", [])]
                    g6 = [str(x) for x in data.get("g6", [])]
                    g7 = [str(x) for x in data.get("g7", [])]

                    all_nums = [db, g1] + g2 + g3 + g4 + g5 + g6 + g7
                    lotos = [n[-2:] for n in all_nums if len(n) >= 2]

                    return {
                        "date": f"{d}/{m}/{y}",
                        "special": db, "g1": g1, "g2": g2, "g3": g3,
                        "g4": g4, "g5": g5, "g6": g6, "g7": g7,
                        "loto": lotos, "source": "VNPAY"
                    }
    except Exception as e:
        print(f"⚠️ Lỗi API 1: {e}")

    # Nguồn dự phòng 2: API KQXS
    try:
        url2 = f"https://xosothantai.mobi/api/v1/lottery/result/xsmb?date={d}-{m}-{y}"
        res2 = requests.get(url2, headers=headers, timeout=8)
        if res2.status_code == 200:
            data2 = res2.json().get("data", {})
            if isinstance(data2, dict) and (data2.get("special") or data2.get("gdb")):
                db = str(data2.get("special") or data2.get("gdb") or "").strip()
                g1 = str(data2.get("first") or data2.get("g1") or "").strip()
                g2 = [str(x) for x in (data2.get("second") or data2.get("g2") or [])]
                g3 = [str(x) for x in (data2.get("third") or data2.get("g3") or [])]
                g4 = [str(x) for x in (data2.get("fourth") or data2.get("g4") or [])]
                g5 = [str(x) for x in (data2.get("fifth") or data2.get("g5") or [])]
                g6 = [str(x) for x in (data2.get("sixth") or data2.get("g6") or [])]
                g7 = [str(x) for x in (data2.get("seventh") or data2.get("g7") or [])]

                all_nums = [db, g1] + g2 + g3 + g4 + g5 + g6 + g7
                lotos = [n[-2:] for n in all_nums if len(n) >= 2]

                return {
                    "date": f"{d}/{m}/{y}",
                    "special": db, "g1": g1, "g2": g2, "g3": g3,
                    "g4": g4, "g5": g5, "g6": g6, "g7": g7,
                    "loto": lotos, "source": "XoSoThanTai"
                }
    except Exception as e:
        print(f"⚠️ Lỗi API 2: {e}")

    return None
