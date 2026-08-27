import requests
from datetime import datetime, timezone, timedelta

VN_TZ = timezone(timedelta(hours=7))

def get_now_vn():
    return datetime.now(VN_TZ)

def get_xsmb_result(target_date_str=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*"
    }

    if not target_date_str:
        target_date_str = get_now_vn().strftime("%d/%m/%Y")

    parts = target_date_str.split("/")
    d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
    formatted_date = f"{d}-{m}-{y}"

    # Nguồn API JSON ổn định không bị cản IP
    try:
        url = f"https://api.xosothantai.mobi/api/v1/lottery/result/xsmb?date={formatted_date}"
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            res = r.json()
            data = res.get("data") or res
            
            if data and ("special" in data or "gdb" in data):
                db = str(data.get("special") or data.get("gdb") or "")
                if isinstance(db, list): db = db[0]
                
                g1 = str(data.get("first") or data.get("g1") or "")
                if isinstance(g1, list): g1 = g1[0]

                def to_list(val):
                    if isinstance(val, list): return [str(x) for x in val]
                    return [str(val)] if val else []

                g2 = to_list(data.get("second") or data.get("g2"))
                g3 = to_list(data.get("third") or data.get("g3"))
                g4 = to_list(data.get("fourth") or data.get("g4"))
                g5 = to_list(data.get("fifth") or data.get("g5"))
                g6 = to_list(data.get("sixth") or data.get("g6"))
                g7 = to_list(data.get("seventh") or data.get("g7"))

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
                        "source": "Xosothantai API"
                    }
    except Exception as e:
        print(f"⚠️ API 1 Lỗi: {e}")

    # Nguồn dự phòng 2: API KQXS
    try:
        url2 = f"https://xskt.com.vn/rss-feed/mien-bac-xsmb.rss"
        r2 = requests.get(f"https://api.vnpay.vn/xsmb/{formatted_date}", headers=headers, timeout=8)
        if r2.status_code == 200:
            res2 = r2.json()
            if res2.get("db"):
                return {
                    "date": target_date_str,
                    "special": res2.get("db"),
                    "g1": res2.get("g1"),
                    "g2": res2.get("g2", []),
                    "g3": res2.get("g3", []),
                    "g4": res2.get("g4", []),
                    "g5": res2.get("g5", []),
                    "g6": res2.get("g6", []),
                    "g7": res2.get("g7", []),
                    "loto": [str(x)[-2:] for x in res2.get("all", [])],
                    "source": "KQXS Direct API"
                }
    except Exception as e:
        print(f"⚠️ API 2 Lỗi: {e}")

    return None
