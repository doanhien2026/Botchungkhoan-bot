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

# ==============================================
# ✅ KIỂM TRA SỐ GIẢ — CHÍNH XÁC
# ==============================================
def is_dummy_number(num_str):
    if not num_str or len(num_str) != 5:
        return True
    dummy_list = {"99999", "00000", "11111", "12345", "54321", "88888"}
    if num_str in dummy_list:
        return True
    if all(c == num_str[0] for c in num_str):
        return True
    return False

# ==============================================
# ✅ LẤY DỮ LIỆU TỪ XOSODAIPHAT — CẢI THIỆN
# ==============================================
def lay_tu_xosodaiphat(d, m, y):
    try:
        url = f"https://xosodaiphat.com/xsmb-{d}-{m}-{y}.html"
        print(f"🔍 [XOSODAIPHAT] Đang lấy: {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        
        if r.status_code != 200:
            print(f"❌ Trang trả mã lỗi: {r.status_code}")
            return None
        
        # ✅ Kiểm tra trang có tồn tại kết quả không
        if "Không tìm thấy kết quả" in r.text or "ngày không tồn tại" in r.text:
            print(f"⚠️ Trang không có dữ liệu ngày {d}/{m}/{y}")
            return None
        
        # ✅ Lấy tất cả số 5 chữ số
        all_5digit = re.findall(r'\b\d{5}\b', r.text)
        print(f"📋 Tìm thấy {len(all_5digit)} số 5 chữ số trên trang")
        
        if len(all_5digit) < 3:
            print(f"⚠️ Không đủ dữ liệu (chỉ có {len(all_5digit)} số)")
            return None
        
        # ✅ Lọc bỏ số giả trước
        real_numbers = [n for n in all_5digit if not is_dummy_number(n)]
        print(f"✅ Số hợp lệ sau lọc: {len(real_numbers)}")
        
        if len(real_numbers) < 2:
            print(f"⚠️ Chưa có kết quả thực tế (chỉ thấy số giả)")
            return None
        
        # ✅ Lấy Đặc Biệt = số đầu tiên KHÔNG phải giả
        db = real_numbers[0]
        g1 = real_numbers[1] if len(real_numbers) >= 2 else ""
        
        # ✅ Lấy 2 chữ số cuối làm lô
        lotos = sorted(set(
            n[-2:] for n in real_numbers
            if n[-2:] != '00'
        ))
        
        print(f"🏆 ĐB:{db} | 🥈 G1:{g1 or '---'} | 🎯 Lô:{len(lotos)} số")
        return {
            "date": f"{d}/{m}/{y}",
            "special": db,
            "g1": g1,
            "loto": lotos,
            "source": "XOSODAIPHAT.com"
        }
    except Exception as e:
        print(f"❌ Lỗi XOSODAIPHAT: {str(e)}")
        return None

# ==============================================
# ✅ NGUỒN DỰ PHÒNG — XOSO.COM.VN
# ==============================================
def lay_tu_xosocomvn(d, m, y):
    try:
        url = f"https://xoso.com.vn/ket-qua-theo-ngay.html?date={d}-{m}-{y}"
        print(f"🔍 [XOSO.com.vn] Đang lấy: {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        
        if r.status_code != 200 or len(r.text) < 500:
            return None
        
        all_5digit = re.findall(r'\b\d{5}\b', r.text)
        real_numbers = [n for n in all_5digit if not is_dummy_number(n)]
        
        if len(real_numbers) < 2:
            return None
        
        db = real_numbers[0]
        g1 = real_numbers[1] if len(real_numbers) >= 2 else ""
        lotos = sorted(set(n[-2:] for n in real_numbers if n[-2:] != '00'))
        
        return {
            "date": f"{d}/{m}/{y}",
            "special": db,
            "g1": g1,
            "loto": lotos,
            "source": "XOSO.com.vn"
        }
    except Exception as e:
        print(f"❌ Lỗi XOSO.com.vn: {str(e)}")
        return None

# ==============================================
# ✅ CHỨC NĂNG CHÍNH — THỨ TỰ ƯU TIÊN
# ==============================================
def get_xsmb_result(target_date_str=None):
    if not target_date_str:
        target_date_str = get_now_vn().strftime("%d/%m/%Y")
    parts = target_date_str.split("/")
    if len(parts) != 3:
        return None
    d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
    
    # ✅ Kiểm tra ngày có hợp lệ không
    try:
        target_dt = datetime(int(y), int(m), int(d), tzinfo=VN_TZ)
        now = get_now_vn()
        # Nếu là hôm nay và chưa đến 18:40 → chưa có kết quả
        if target_dt.date() == now.date() and now.hour < 18 or (now.hour == 18 and now.minute < 35):
            print(f"⏳ Hôm nay chưa đến 18:35 → chưa có kết quả")
            return None
        # Nếu là ngày tương lai → chưa có kết quả
        if target_dt.date() > now.date():
            print(f"⏳ Ngày tương lai → chưa có kết quả")
            return None
    except:
        return None
    
    # Thử nguồn 1
    result = lay_tu_xosodaiphat(d, m, y)
    # Thử nguồn 2 nếu nguồn 1 thất bại
    if not result:
        print("🔄 Chuyển nguồn dự phòng...")
        result = lay_tu_xosocomvn(d, m, y)
    
    return result
