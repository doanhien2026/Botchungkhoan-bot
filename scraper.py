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

# ==========================================
# NGUỒN 1: XOSODAIPHAT.COM — NGUỒN CHÍNH
# ==========================================
def lay_tu_xosodaiphat(d, m, y):
    try:
        formatted_date = f"{d}-{m}-{y}"
        url = f"https://xosodaiphat.com/xsmb-{formatted_date}.html"
        print(f"🔍 [XOSODAIPHAT] Đang lấy: {url}")
        
        r = requests.get(url, headers=HEADERS, timeout=15)
        print(f"📡 Status: {r.status_code} | Độ dài: {len(r.text)} ký tự")
        
        if r.status_code != 200 or len(r.text) < 1000:
            print(f"⚠️ [XOSODAIPHAT] Không truy cập được hoặc nội dung quá ngắn")
            return None
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # === LẤY GIẢI ĐẶC BIỆT ===
        all_5digit = re.findall(r'\b\d{5}\b', r.text)
        if len(all_5digit) < 5:
            print(f"❌ [XOSODAIPHAT] Không đủ dữ liệu: {len(all_5digit)} số")
            return None
        
        db = all_5digit[0]
        g1 = all_5digit[1] if len(all_5digit) >= 2 else ""
        
        # === TÍNH LÔ: 2 số cuối tất cả giải ===
        lotos = list(set(n[-2:] for n in all_5digit if n != '00000'))
        lotos = sorted([n for n in lotos if n != '00'])
        
        print(f"✅ [XOSODAIPHAT] {d}/{m}/{y} | ĐB: {db} | G1: {g1 or '---'} | Lô: {len(lotos)} số")
        
        return {
            "date": f"{d}/{m}/{y}",
            "special": db,
            "g1": g1 or "",
            "loto": lotos,
            "source": "XOSODAIPHAT.com"
        }
    except Exception as e:
        print(f"❌ [XOSODAIPHAT] Lỗi: {str(e)[:100]}")
        return None

# ==========================================
# NGUỒN 2: XOSO.COM.VN — DỰ PHÒNG
# ==========================================
def lay_tu_xosocomvn(d, m, y):
    try:
        formatted_date = f"{d}-{m}-{y}"
        url = f"https://xoso.com.vn/ket-qua-theo-ngay.html?date={formatted_date}"
        print(f"🔍 [XOSO.com.vn] Đang lấy: {url}")
        
        r = requests.get(url, headers=HEADERS, timeout=15)
        print(f"📡 Status: {r.status_code} | Độ dài: {len(r.text)} ký tự")
        
        if r.status_code != 200 or len(r.text) < 1000:
            print(f"⚠️ [XOSO.com.vn] Không truy cập được hoặc nội dung quá ngắn")
            return None
        
        all_5digit = re.findall(r'\b\d{5}\b', r.text)
        if len(all_5digit) < 5:
            print(f"❌ [XOSO.com.vn] Không đủ dữ liệu: {len(all_5digit)} số")
            return None
        
        db = all_5digit[0]
        g1 = all_5digit[1] if len(all_5digit) >= 2 else ""
        
        # === TÍNH LÔ ===
        lotos = list(set(n[-2:] for n in all_5digit if n != '00000'))
        lotos = sorted([n for n in lotos if n != '00'])
        
        print(f"✅ [XOSO.com.vn] {d}/{m}/{y} | ĐB: {db} | G1: {g1 or '---'} | Lô: {len(lotos)} số")
        
        return {
            "date": f"{d}/{m}/{y}",
            "special": db,
            "g1": g1 or "",
            "loto": lotos,
            "source": "XOSO.com.vn"
        }
    except Exception as e:
        print(f"❌ [XOSO.com.vn] Lỗi: {str(e)[:100]}")
        return None

# ==========================================
# CHỨC NĂNG CHÍNH — GỌI TỪ BOT
# ==========================================
def get_xsmb_result(target_date_str=None):
    if not target_date_str:
        target_date_str = get_now_vn().strftime("%d/%m/%Y")
    
    parts = target_date_str.split("/")
    if len(parts) != 3:
        return None
    
    d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
    
    # Thử NGUỒN 1 — XOSODAIPHAT
    result = lay_tu_xosodaiphat(d, m, y)
    
    # Thử NGUỒN 2 — XOSO.com.vn
    if not result:
        print("🔄 Chuyển sang nguồn dự phòng XOSO.com.vn...")
        result = lay_tu_xosocomvn(d, m, y)
    
    if result:
        return result
    
    print(f"❌ CẢ 2 NGUỒN ĐỀU KHÔNG LẤY ĐƯỢC DỮ LIỆU NGÀY {d}/{m}/{y}")
    return None
