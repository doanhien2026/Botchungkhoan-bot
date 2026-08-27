import requests
import re
from datetime import datetime, timezone, timedelta

VN_TZ = timezone(timedelta(hours=7))
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
}

def get_now_vn():
    return datetime.now(VN_TZ)

# ==============================================
# ✅ HÀM KIỂM TRA SỐ GIẢ — TẠO 1 LẦN, DÙNG Ở 2 NGUỒN
# ==============================================
def is_dummy_number(num_str):
    """Kiểm tra xem có phải số mặc định/giả không"""
    if not num_str or len(num_str) != 5:
        return True
    # Các số mặc định thường gặp
    dummy_list = {"99999", "00000", "11111", "12345", "54321", "88888"}
    if num_str in dummy_list:
        return True
    # Kiểm tra số lặp toàn bộ (99999, 11111...)
    if all(c == num_str[0] for c in num_str):
        return True
    return False

# ========== NGUỒN 1: XOSODAIPHAT.COM ==========
def lay_tu_xosodaiphat(d, m, y):
    try:
        url = f"https://xosodaiphat.com/xsmb-{d}-{m}-{y}.html"
        print(f"🔍 [XOSODAIPHAT] {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200 or len(r.text) < 1000:
            return None
        
        # Lấy tất cả số 5 chữ số
        all_5digit = re.findall(r'\b\d{5}\b', r.text)
        if len(all_5digit) < 5:
            return None
        
        db = all_5digit[0]
        
        # ==============================================
        # ✅ KIỂM TRA SỐ GIẢ → NẾU CÓ → TRẢ VỀ NGAY None
        # ==============================================
        if is_dummy_number(db):
            print(f"⚠️ [XOSODAIPHAT] Chưa có kết quả thực tế! Đặc biệt = {db} (số giả/mặc định)")
            return None
        
        g1 = all_5digit[1] if len(all_5digit) >= 2 else ""
        if is_dummy_number(g1):
            g1 = ""
        
        # Lọc số lô — BỎ SỐ GIẢ
        lotos = sorted(set(
            n[-2:] for n in all_5digit
            if not is_dummy_number(n) and n[-2:] != '00'
        ))
        
        print(f"✅ ĐB:{db} | G1:{g1 or '---'} | Lô:{len(lotos)} số")
        return {
            "date": f"{d}/{m}/{y}",
            "special": db,
            "g1": g1,
            "loto": lotos,
            "source": "XOSODAIPHAT.com"
        }
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
        
        # ✅ CÙNG KIỂM TRA SỐ GIẢ
        if is_dummy_number(db):
            print(f"⚠️ [XOSO.com.vn] Chưa có kết quả thực tế! Đặc biệt = {db}")
            return None
        
        g1 = all_5digit[1] if len(all_5digit) >= 2 else ""
        if is_dummy_number(g1):
            g1 = ""
        
        lotos = sorted(set(
            n[-2:] for n in all_5digit
            if not is_dummy_number(n) and n[-2:] != '00'
        ))
        
        print(f"✅ ĐB:{db} | G1:{g1 or '---'} | Lô:{len(lotos)} số")
        return {
            "date": f"{d}/{m}/{y}",
            "special": db,
            "g1": g1,
            "loto": lotos,
            "source": "XOSO.com.vn"
        }
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
    # Thử nguồn 2 nếu nguồn 1 trả None (chưa có kết quả)
    if not result:
        print("🔄 Chuyển nguồn dự phòng XOSO.com.vn...")
        result = lay_tu_xosocomvn(d, m, y)
    
    # Nếu cả 2 nguồn đều chưa có kết quả → trả None
    if not result:
        print(f"❌ Cả 2 nguồn đều chưa có kết quả thực tế cho ngày {target_date_str}")
    
    return result
