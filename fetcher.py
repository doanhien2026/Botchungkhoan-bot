import requests
from bs4 import BeautifulSoup
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
    formatted_date = f"{d}-{m}-{y}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9"
    }

    # Cào trực tiếp từ XSKT.com.vn (Nguồn thật 100%)
    try:
        url = f"https://xskt.com.vn/xsmb/ngay-{d}-{m}-{y}"
        res = requests.get(url, headers=headers, timeout=10)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            table = soup.find("table", id="vtable") or soup.find("table", class_="bkqa")
            
            if table:
                def extract_prize(row_class):
                    tr = table.find("tr", class_=row_class)
                    if tr:
                        tds = tr.find_all("td")
                        if len(tds) > 1:
                            nums = tds[1].get_text(separator=" ").split()
                            return [n.strip() for n in nums if n.strip().isdigit()]
                    return []

                db_list = extract_prize("gdb")
                db = db_list[0] if db_list else ""
                
                g1_list = extract_prize("g1")
                g1 = g1_list[0] if g1_list else ""

                g2 = extract_prize("g2")
                g3 = extract_prize("g3")
                g4 = extract_prize("g4")
                g5 = extract_prize("g5")
                g6 = extract_prize("g6")
                g7 = extract_prize("g7")

                if db or g1:
                    all_prizes = [db, g1] + g2 + g3 + g4 + g5 + g6 + g7
                    lotos = [n[-2:] for n in all_prizes if len(n) >= 2]
                    
                    return {
                        "date": f"{d}/{m}/{y}",
                        "special": db,
                        "g1": g1,
                        "g2": g2,
                        "g3": g3,
                        "g4": g4,
                        "g5": g5,
                        "g6": g6,
                        "g7": g7,
                        "loto": lotos,
                        "source": "XSKT.com.vn"
                    }
    except Exception as e:
        print(f"⚠️ Lỗi cào dữ liệu XSKT: {e}")

    return None
