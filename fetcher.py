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
    date_api = f"{d}{m}{y}"
    display_date = f"{d}/{m}/{y}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9"
    }

    # NGUỒN 1: VNPAY API
    try:
        url = f"https://api.vnpay.vn/vnpay-kqxs/xsmb?date={date_api}"
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200:
            data = r.json().get("data", {})
            if data and data.get("gdb"):
                db = str(data.get("gdb", ""))
                g1 = str(data.get("g1", ""))
                g2 = [str(x) for x in data.get("g2", [])]
                g3 = [str(x) for x in data.get("g3", [])]
                g4 = [str(x) for x in data.get("g4", [])]
                g5 = [str(x) for x in data.get("g5", [])]
                g6 = [str(x) for x in data.get("g6", [])]
                g7 = [str(x) for x in data.get("g7", [])]
                
                all_nums = [db, g1] + g2 + g3 + g4 + g5 + g6 + g7
                lotos = [n[-2:] for n in all_nums if len(n) >= 2]
                
                print(f"✅ [VNPAY] {display_date} | GĐB: {db}")
                return {
                    "date": display_date, "special": db, "g1": g1, "g2": g2, "g3": g3,
                    "g4": g4, "g5": g5, "g6": g6, "g7": g7, "loto": lotos, "source": "VNPAY API"
                }
    except Exception as e:
        print(f"⚠️ [VNPAY] Lỗi: {str(e)[:40]}")

    # NGUỒN 2: KQXS.VN
    try:
        url = f"https://kqxs.vn/xsmb/{y}-{m}-{d}"
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200 and len(r.text) > 500:
            html = r.text
            db_m = re.search(r'(?:Giải Đặc biệt|Đặc biệt)[\s\S]{0,100}?(\d{5,6})', html, re.I)
            g1_m = re.search(r'(?:Giải nhất|Giai 1)[\s\S]{0,100}?(\d{5})', html, re.I)
            if db_m:
                db = db_m.group(1)
                g1 = g1_m.group(1) if g1_m else "------"
                lotos = re.findall(r'lottery-result-item[^>]*>(\d{2})<', html)
                if not lotos:
                    lotos = re.findall(r'>(\d{2})<', html)
                    lotos = [n for n in lotos if n.isdigit() and n != '00' and len(n) == 2][:27]
                if len(lotos) >= 20:
                    print(f"✅ [KQXS.vn] {display_date} | GĐB: {db}")
                    return {"date": display_date, "special": db, "g1": g1, "loto": lotos, "source": "KQXS.vn"}
    except Exception as e:
        print(f"⚠️ [KQXS.vn] Lỗi: {str(e)[:40]}")

    # NGUỒN 3: XOSO.WAP.VN
    try:
        url = f"https://xoso.wap.vn/xsmb/{y}/{m}/{d}"
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200 and len(r.text) > 300:
            html = r.text
            db_m = re.search(r'Đặc biệt.*?(\d{5,6})', html, re.I)
            g1_m = re.search(r'Giải nhất.*?(\d{5})', html, re.I)
            if db_m:
                db = db_m.group(1)
                g1 = g1_m.group(1) if g1_m else "------"
                lotos = re.findall(r'>(\d{2})<', html)
                lotos = [n for n in lotos if n.isdigit() and n != '00' and len(n) == 2][:27]
                if len(lotos) >= 20:
                    print(f"✅ [Xoso.wap.vn] {display_date} | GĐB: {db}")
                    return {"date": display_date, "special": db, "g1": g1, "loto": lotos, "source": "Xoso.wap.vn"}
    except Exception as e:
        print(f"⚠️ [Xoso.wap.vn] Lỗi: {str(e)[:40]}")

    # TẤT CẢ NGUỒN LỖI → DỮ LIỆU MẪU
    print(f"⚠️ Tạo dữ liệu mẫu {display_date}")
    seed_value = int(f"{y}{m}{d}")
    random.seed(seed_value)
    
    gen = lambda l: str(random.randint(0, 10**l - 1)).zfill(l)
    db, g1 = gen(5), gen(5)
    g2, g3 = [gen(5) for _ in range(2)], [gen(5) for _ in range(6)]
    g4, g5 = [gen(4) for _ in range(4)], [gen(4) for _ in range(6)]
    g6, g7 = [gen(3) for _ in range(3)], [gen(2) for _ in range(4)]
    
    all_nums = [db, g1] + g2 + g3 + g4 + g5 + g6 + g7
    lotos = [n[-2:] for n in all_nums]

    return {
        "date": display_date, "special": db, "g1": g1, "g2": g2, "g3": g3,
        "g4": g4, "g5": g5, "g6": g6, "g7": g7, "loto": lotos, "source": "Dữ liệu mẫu"
    }

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
