import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

VN_TZ = timezone(timedelta(hours=7))

def get_now_vn():
    return datetime.now(VN_TZ)

def get_xsmb_result(target_date_str=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    if not target_date_str:
        target_date_str = get_now_vn().strftime("%d/%m/%Y")

    parts = target_date_str.split("/")
    if len(parts) != 3:
        return None
        
    d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
    formatted_date_dash = f"{d}-{m}-{y}"
    formatted_date_slash = f"{d}/{m}/{y}"

    # Nguồn 1: API XSMB Minh Ngọc / KQXS
    try:
        url = f"https://xosothantai.mobi/api/v1/lottery/result/xsmb?date={formatted_date_dash}"
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            res_json = r.json()
            data = res_json.get("data") if isinstance(res_json, dict) and "data" in res_json else res_json
            
            if isinstance(data, dict):
                db = str(data.get("special") or data.get("gdb") or "").strip()
                g1 = str(data.get("first") or data.get("g1") or "").strip()
                
                def parse_list(val):
                    if isinstance(val, list):
                        return [str(x).strip() for x in val if x]
                    elif isinstance(val, str) and val:
                        return [val.strip()]
                    return []

                g2 = parse_list(data.get("second") or data.get("g2"))
                g3 = parse_list(data.get("third") or data.get("g3"))
                g4 = parse_list(data.get("fourth") or data.get("g4"))
                g5 = parse_list(data.get("fifth") or data.get("g5"))
                g6 = parse_list(data.get("sixth") or data.get("g6"))
                g7 = parse_list(data.get("seventh") or data.get("g7"))

                if db or g1:
                    all_nums = [db, g1] + g2 + g3 + g4 + g5 + g6 + g7
                    lotos = [n[-2:] for n in all_nums if len(n) >= 2]
                    return {
                        "date": formatted_date_slash,
                        "special": db, "g1": g1, "g2": g2, "g3": g3,
                        "g4": g4, "g5": g5, "g6": g6, "g7": g7,
                        "loto": lotos, "source": "API XoSoThanTai"
                    }
    except Exception as e:
        print(f"⚠️ Nguồn 1 lỗi: {e}")

    # Nguồn 2: Scraping HTML trực tiếp từ xosodaiphat.com
    try:
        url_html = f"https://xosodaiphat.com/xsmb-{d}-{m}-{y}.html"
        r_html = requests.get(url_html, headers=headers, timeout=8)
        if r_html.status_code == 200:
            soup = BeautifulSoup(r_html.text, "html.parser")
            table = soup.find("table", class_="table-result")
            if table:
                def get_prizes(class_name):
                    elems = table.find_all("span", class_=class_name)
                    return [e.text.strip() for e in elems if e.text.strip()]

                db_list = get_prizes("v-gdb")
                db = db_list[0] if db_list else ""
                g1_list = get_prizes("v-g1")
                g1 = g1_list[0] if g1_list else ""
                
                g2 = get_prizes("v-g2")
                g3 = get_prizes("v-g3")
                g4 = get_prizes("v-g4")
                g5 = get_prizes("v-g5")
                g6 = get_prizes("v-g6")
                g7 = get_prizes("v-g7")

                if db or g1:
                    all_nums = [db, g1] + g2 + g3 + g4 + g5 + g6 + g7
                    lotos = [n[-2:] for n in all_nums if len(n) >= 2]
                    return {
                        "date": formatted_date_slash,
                        "special": db, "g1": g1, "g2": g2, "g3": g3,
                        "g4": g4, "g5": g5, "g6": g6, "g7": g7,
                        "loto": lotos, "source": "XoSoDaiPhat"
                    }
    except Exception as e:
        print(f"⚠️ Nguồn 2 lỗi: {e}")

    return None
