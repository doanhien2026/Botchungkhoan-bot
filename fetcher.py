import requests
from datetime import datetime, timezone, timedelta

VN_TZ = timezone(timedelta(hours=7))

def get_now_vn():
    return datetime.now(VN_TZ)

def get_xsmb_result(target_date_str=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    if not target_date_str:
        target_date_str = get_now_vn().strftime("%d/%m/%Y")

    # Định dạng dd/mm/yyyy
    parts = target_date_str.split("/")
    d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
    formatted_date = f"{d}-{m}-{y}"

    # Lấy dữ liệu từ API XSMB công khai
    try:
        url = f"https://xosothantai.mobi/api/v1/lottery/result/xsmb?date={formatted_date}"
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and "data" in data:
                data = data["data"]

            # Bóc tách các giải
            db = str(data.get("special") or data.get("gdb") or "")
            g1 = str(data.get("first") or data.get("g1") or "")
            
            def parse_prize(val):
                if isinstance(val, list):
                    return [str(x) for x in val]
                elif isinstance(val, str) and val:
                    return [val]
                return []

            g2 = parse_prize(data.get("second") or data.get("g2"))
            g3 = parse_prize(data.get("third") or data.get("g3"))
            g4 = parse_prize(data.get("fourth") or data.get("g4"))
            g5 = parse_prize(data.get("fifth") or data.get("g5"))
            g6 = parse_prize(data.get("sixth") or data.get("g6"))
            g7 = parse_prize(data.get("seventh") or data.get("g7"))

            all_nums = [db, g1] + g2 + g3 + g4 + g5 + g6 + g7
            lotos = [n[-2:] for n in all_nums if len(n) >= 2]

            if db:
                return {
                    "date": target_date_str,
                    "special": db,
                    "g1": g1,
                    "g2": g2,
                    "g3": g3,
                    "g4": g4,
                    "g5": g5,
                    "g6": g6,
                    "g7": g7,
                    "loto": lotos,
                    "source": "XSMB Online"
                }
    except Exception as e:
        print(f"⚠️ Lỗi fetcher: {e}")

    # Nguồn dự phòng 2 (Minh Ngọc / KQXS)
    try:
        url2 = f"https://api.vnpay.vn/vnpay-kqxs/xsmb?date={d}{m}{y}"
        r2 = requests.get(url2, headers=headers, timeout=10)
        if r2.status_code == 200:
            res2 = r2.json()
            if res2.get("code") == "00" and res2.get("data"):
                d_data = res2["data"]
                return {
                    "date": target_date_str,
                    "special": str(d_data.get("gdb", "")),
                    "g1": str(d_data.get("g1", "")),
                    "g2": d_data.get("g2", []),
                    "g3": d_data.get("g3", []),
                    "g4": d_data.get("g4", []),
                    "g5": d_data.get("g5", []),
                    "g6": d_data.get("g6", []),
                    "g7": d_data.get("g7", []),
                    "loto": [],
                    "source": "KQXS Reserve"
                }
    except Exception as e:
        print(f"⚠️ Lỗi API dự phòng: {e}")

    return None
