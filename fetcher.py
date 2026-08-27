import requests
import re
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

    parts = target_date_str.split("/")
    d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]

    try:
        url = f"https://www.minhngoc.com.vn/getkhung/mien-bac/{d}-{m}-{y}.html"
        r = requests.get(url, headers=headers, timeout=12)
        
        if r.status_code == 200 and len(r.text) > 200:
            numbers = re.findall(r'\b\d{2,5}\b', r.text)
            if len(numbers) >= 27:
                return {
                    "date": target_date_str,
                    "special": numbers[0],
                    "g1": numbers[1],
                    "g2": numbers[2:4],
                    "g3": numbers[4:10],
                    "g4": numbers[10:14],
                    "g5": numbers[14:20],
                    "g6": numbers[20:23],
                    "g7": numbers[23:27],
                    "loto": [n[-2:] for n in numbers[:27]],
                    "source": "Minh Ngọc"
                }
    except Exception as e:
        print(f"⚠️ Lỗi fetcher: {e}")

    return None
