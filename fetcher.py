import requests
import re
from datetime import datetime, timezone, timedelta
from data_manager import save_result, get_saved_result

VN_TZ = timezone(timedelta(hours=7))
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
}

def get_now_vn():
    return datetime.now(VN_TZ)

# ==========================================
# NGUỒN 1: DÙNG API KETQUA365 — NHANH & ỔN ĐỊNH NHẤT
# ==========================================
def lay_tu_ketqua365(d, m, y):
    try:
        date_str_api = f"{y}-{m}-{d}"
        url = f"https://api.ketqua365.com/api/xsmb?date={date_str_api}"
        print(f"🔍 [KETQUA365] Đang lấy: {url}")
        
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"⚠️ [KETQUA365] Mã lỗi: {r.status_code}")
            return None
        
        data = r.json()
        if not data or 'data' not in data or not data['data']:
            print("⚠️ [KETQUA365] Chưa có dữ liệu")
            return None
        
        result_data = data['data']
        
        db = result_data.get('special_prize', '')
        g1 = result_data.get('first_prize', '')
        
        if not db or not g1 or len(db) != 5 or len(g1) != 5:
            print(f"⚠️ [KETQUA365] Dữ liệu không đầy đủ — ĐB:{db}, G1:{g1}")
            return None
        
        # Tất cả các giải → tính lô
        all_prizes = [db, g1]
        for key in ['second_prize', 'third_prize', 'fourth_prize', 'fifth_prize', 'sixth_prize', 'seventh_prize']:
            val = result_data.get(key, [])
            if isinstance(val, list):
                all_prizes.extend(val)
            elif isinstance(val, str):
                all_prizes.append(val)
        
        lotos = list(set(n[-2:] for n in all_prizes if isinstance(n, str) and len(n) >= 2))
        lotos = sorted([n for n in lotos if n != '00'])
        
        print(f"✅ [KETQUA365] {d}/{m}/{y} | ĐB: {db} | G1: {g1} | Lô: {len(lotos)} số")
        
        return {
            "date": f"{d}/{m}/{y}",
            "special": db,
            "g1": g1,
            "loto": lotos,
            "source": "KETQUA365.com"
        }
    except Exception as e:
        print(f"❌ [KETQUA365] Lỗi: {str(e)[:100]}")
        return None

# ==========================================
# NGUỒN 2: KETQUA.NET — ĐÚNG URL ĐỊNH DẠNG
# ==========================================
def lay_tu_ketquanet(d, m, y):
    try:
        # ✅ Đúng định dạng URL của ketqua.net
        url = f"https://ketqua.net/ngay/{d}-{m}-{y}"
        print(f"🔍 [KETQUA.net] Đang lấy: {url}")
        
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200 or len(r.text) < 2000:
            print(f"⚠️ [KETQUA.net] Mã lỗi: {r.status_code} hoặc nội dung quá ngắn")
            return None
        
        html = r.text
        
        # === Tìm Giải Đặc Biệt ===
        db = None
        # Thử nhiều mẫu khác nhau
        patterns = [
            r'Đặc biệt.*?<td[^>]*?id="[^"]*rs_0_0[^"]*"[^>]*?>(\d{5})<',
            r'id="rs_0_0"[^>]*?>(\d{5})<',
            r'class="[^"]*dacbiet[^"]*"[^>]*?>(\d{5})<',
            r'Giải Đặc biệt.*?(\d{5})',
        ]
        for pat in patterns:
            match = re.search(pat, html, re.DOTALL)
            if match:
                db = match.group(1) if len(match.groups()) == 1 else match.group(2)
                if db and len(db) == 5:
                    break
        
        if not db:
            print("❌ [KETQUA.net] Không tìm thấy Giải Đặc Biệt")
            return None
        
        # === Tìm Giải Nhất ===
        g1 = None
        patterns_g1 = [
            r'id="rs_1_0"[^>]*?>(\d{5})<',
            r'Giải nhất.*?(\d{5})',
        ]
        for pat in patterns_g1:
            match = re.search(pat, html, re.DOTALL)
            if match:
                g1 = match.group(1)
                if g1 and len(g1) == 5:
                    break
        
        if not g1:
            print("❌ [KETQUA.net] Không tìm thấy Giải Nhất")
            return None
        
        # === Tìm tất cả số 5 chữ số trên trang ===
        all_5digit = re.findall(r'\b\d{5}\b', html)
        if len(all_5digit) < 10:
            print(f"⚠️ [KETQUA.net] Quá ít số 5 chữ số: {len(all_5digit)}")
            return None
        
        # === Tính lô ===
        lotos = list(set(n[-2:] for n in all_5digit if n != '00000'))
        lotos = sorted([n for n in lotos if n != '00'])
        
        print(f"✅ [KETQUA.net] {d}/{m}/{y} | ĐB: {db} | G1: {g1} | Lô: {len(lotos)} số")
        
        return {
            "date": f"{d}/{m}/{y}",
            "special": db,
            "g1": g1,
            "loto": lotos,
            "source": "KETQUA.net"
        }
    except Exception as e:
        print(f"❌ [KETQUA.net] Lỗi: {str(e)[:100]}")
        return None

# ==========================================
# CHỨC NĂNG CHÍNH — THỨ TỰ ƯU TIÊN
# ==========================================
def get_xsmb_result(target_date_str=None):
    if not target_date_str:
        target_date_str = get_now_vn().strftime("%d/%m/%Y")
    
    parts = target_date_str.split("/")
    if len(parts) != 3:
        return None
    
    d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
    
    # Bước 1: Đọc từ file đã lưu
    saved = get_saved_result(f"{d}/{m}/{y}")
    if saved:
        print(f"📂 Đọc từ file: {saved['date']} | ĐB: {saved['special']}")
        return saved
    
    # Bước 2: Thử NGUỒN 1 — API KETQUA365 (nhanh & ổn định nhất)
    result = lay_tu_ketqua365(d, m, y)
    
    # Bước 3: Nếu thất bại → Thử NGUỒN 2 — KETQUA.net
    if not result:
        print("🔄 Chuyển sang nguồn KETQUA.net...")
        result = lay_tu_ketquanet(d, m, y)
    
    # Bước 4: Nếu thành công → Lưu
    if result:
        save_result(result)
        return result
    
    # ❌ Cả 2 nguồn đều thất bại
    print(f"❌ KHÔNG LẤY ĐƯỢC DỮ LIỆU NGÀY {d}/{m}/{y} — Cả 2 nguồn đều không truy cập được")
    return None
