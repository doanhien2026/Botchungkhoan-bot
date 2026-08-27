import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

VN_TZ = timezone(timedelta(hours=7))
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
}

def get_now_vn():
    return datetime.now(VN_TZ)

# ========== NGUỒN 1: XOSODAIPHAT.COM ==========
def lay_tu_xosodaiphat(d, m, y):
    try:
        url = f"https://xosodaiphat.com/xsmb-{d}-{m}-{y}.html"
        print(f"🔍 [XOSODAIPHAT] {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200 or len(r.text) < 1000:
            return None
        all_5digit = re.findall(r'\b\d{5}\b', r.text)
        if len(all_5digit) < 5:
            return None
        db = all_5digit[0]
        g1 = all_5digit[1] if len(all_5digit) >= 2 else ""
        lotos = sorted(set(n[-2:] for n in all_5digit if n != '00000' and n[-2:] != '00'))
        print(f"✅ ĐB:{db} | G1:{g1} | Lô:{len(lotos)} số")
        return {"date":f"{d}/{m}/{y}", "special":db, "g1":g1, "loto":lotos, "source":"XOSODAIPHAT.com"}
    except Exception as e:
        print(f"❌ XOSODAIPHAT lỗi: {str(e)[:80]}")
        return None

# ========== NGUỒN 2: XOSO.COM.VN — DỰ PHÒNG ==========
def lay_tu_xosocomvn(d, m, y):
    try:
        url = f"https://xoso.com.vn/ket-qua-theo-ngay.html?date={d}-{m}-{y}"
        print(f"🔍 [XOSO.com.vn] {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200 or len(r.text) < 1000:
            return None
        all_5digit = re.findall(r'\b\d{5}\b', r.text)
        if len(all_5digit) < 5:
            return None
        db = all_5digit[0]
        g1 = all_5digit[1] if len(all_5digit) >= 2 else ""
        lotos = sorted(set(n[-2:] for n in all_5digit if n != '00000' and n[-2:] != '00'))
        print(f"✅ ĐB:{db} | G1:{g1} | Lô:{len(lotos)} số")
        return {"date":f"{d}/{m}/{y}", "special":db, "g1":g1, "loto":lotos, "source":"XOSO.com.vn"}
    except Exception as e:
        print(f"❌ XOSO.com.vn lỗi: {str(e)[:80]}")
        return None

# ========== CHỨC NĂNG CHÍNH ==========
def get_xsmb_result(target_date_str=None):
    if not target_date_str:
        target_date_str = get_now_vn().strftime("%d/%m/%Y")
    parts = target_date_str.split("/")
    if len(parts) != 3:
        return None
    d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
    # Thử nguồn 1
    result = lay_tu_xosodaiphat(d, m, y)
    # Thử nguồn 2 nếu nguồn 1 lỗi
    if not result:
        print("🔄 Chuyển nguồn dự phòng...")
        result = lay_tu_xosocomvn(d, m, y)
    return result
