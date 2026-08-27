import requests
import re
from bs4 import BeautifulSoup
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
# NGUỒN 1: XOSO.COM.VN — NGUỒN CHÍNH (đã xác nhận truy cập được)
# ==========================================
def lay_tu_xosocomvn(d, m, y):
    """Lấy kết quả từ xoso.com.vn — định dạng ngày: dd/mm/yyyy"""
    try:
        url = f"https://xoso.com.vn/ket-qua-theo-ngay.html?date={d}/{m}/{y}"
        print(f"🔍 [XOSO.COM.VN] Đang lấy: {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        
        if r.status_code != 200 or len(r.text) < 500:
            print("⚠️ [XOSO.COM.VN] Không truy cập được hoặc nội dung quá ngắn")
            return None
        
        html = r.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # Lấy Đặc Biệt — nhiều selector
        db = None
        db_selectors = ['.v-gdb', '.gdb', '.dacbiet', 'span:contains("Đặc biệt") + span', 
                        '.special-prize span', '#db']
        for sel in db_selectors:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True).isdigit() and len(el.get_text(strip=True)) == 5:
                db = el.get_text(strip=True)
                break
        
        if not db:
            # Fallback: tìm regex 5 số liên tiếp sau "Đặc biệt"
            m = re.search(r'Đặc biệt.*?(\d{5})', html, re.DOTALL)
            if m: db = m.group(1)
        
        # Lấy Giải Nhất
        g1 = None
        g1_selectors = ['.v-g1', '.g1', '.gia-nhat', '.prize-first span']
        for sel in g1_selectors:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True).isdigit() and len(el.get_text(strip=True)) == 5:
                g1 = el.get_text(strip=True)
                break
        if not g1:
            m = re.search(r'Giải nhất.*?(\d{5})', html, re.DOTALL)
            if m: g1 = m.group(1)
        
        # Lấy tất cả các giải để tính LÔ
        all_prize_elements = soup.select('.table-result span, .prize-cell, td')
        all_numbers = []
        for el in all_prize_elements:
            txt = el.get_text(strip=True)
            if txt.isdigit() and len(txt) >= 2 and len(txt) <= 6:
                all_numbers.append(txt)
        
        # Lọc lấy các giải chuẩn (5, 4, 3, 2 chữ số)
        valid_prizes = [n for n in all_numbers if len(n) in (2,3,4,5)]
        
        if not db or not g1 or len(valid_prizes) < 20:
            print(f"⚠️ [XOSO.COM.VN] Dữ liệu không đủ — ĐB:{db}, G1:{g1}, Số giải:{len(valid_prizes)}")
            return None
        
        # Tính LÔ: 2 số cuối tất cả giải
        lotos = list(set(n[-2:] for n in valid_prizes if len(n) >= 2))
        lotos = sorted([n for n in lotos if n != '00'])
        
        print(f"✅ [XOSO.COM.VN] {d}/{m}/{y} | ĐB: {db} | Lô: {len(lotos)} số")
        return {
            "date": f"{d}/{m}/{y}",
            "special": db,
            "g1": g1,
            "loto": lotos,
            "source": "XOSO.COM.VN"
        }
    except Exception as e:
        print(f"❌ [XOSO.COM.VN] Lỗi: {str(e)[:60]}")
        return None

# ==========================================
# NGUỒN 2: KETQUA.NET — DỰ PHÒNG CHÍNH
# ==========================================
def lay_tu_ketquanet(d, m, y):
    """Lấy từ ketqua.net — nguồn rất ổn định"""
    try:
        url = f"https://ketqua.net/xsmb/ngay/{d}-{m}-{y}"
        print(f"🔍 [KETQUA.net] Đang lấy: {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        
        if r.status_code != 200 or len(r.text) < 500:
            print("⚠️ [KETQUA.net] Không truy cập được")
            return None
        
        html = r.text
        
        # Đặc biệt — ID cố định
        db_match = re.search(r'id="rs_0_0"[^>]*>(\d{5})<', html)
        g1_match = re.search(r'id="rs_1_0"[^>]*>(\d{5})<', html)
        
        if not db_match or not g1_match:
            print("⚠️ [KETQUA.net] Không tìm thấy kết quả")
            return None
        
        db = db_match.group(1)
        g1 = g1_match.group(1)
        
        # Lấy tất cả các giải
        g2 = re.findall(r'id="rs_2_\d+"[^>]*>(\d{5})<', html)
        g3 = re.findall(r'id="rs_3_\d+"[^>]*>(\d{5})<', html)
        g4 = re.findall(r'id="rs_4_\d+"[^>]*>(\d{4})<', html)
        g5 = re.findall(r'id="rs_5_\d+"[^>]*>(\d{4})<', html)
        g6 = re.findall(r'id="rs_6_\d+"[^>]*>(\d{3})<', html)
        g7 = re.findall(r'id="rs_7_\d+"[^>]*>(\d{2})<', html)
        
        all_prizes = [db, g1] + g2 + g3 + g4 + g5 + g6 + g7
        lotos = list(set(n[-2:] for n in all_prizes if len(n) >= 2))
        lotos = sorted([n for n in lotos if n != '00'])
        
        print(f"✅ [KETQUA.net] {d}/{m}/{y} | ĐB: {db} | Lô: {len(lotos)} số")
        return {
            "date": f"{d}/{m}/{y}",
            "special": db,
            "g1": g1,
            "loto": lotos,
            "source": "KETQUA.net"
        }
    except Exception as e:
        print(f"❌ [KETQUA.net] Lỗi: {str(e)[:60]}")
        return None

# ==========================================
# CHỨC NĂNG CHÍNH — LẤY KẾT QUẢ
# ==========================================
def get_xsmb_result(target_date_str=None):
    """Lấy kết quả: File → Nguồn 1 → Nguồn 2 → None (KHÔNG TẠO SỐ GIẢ)"""
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
    
    # Bước 2: Thử nguồn chính
    result = lay_tu_xosocomvn(d, m, y)
    if not result:
        # Bước 3: Thử nguồn dự phòng
        result = lay_tu_ketquanet(d, m, y)
    
    if result:
        save_result(result)  # Lưu vào file
        return result
    
    # ❌ KHÔNG LẤY ĐƯỢC → KHÔNG TẠO SỐ GIẢ!
    print(f"❌ TẤT CẢ NGUỒN ĐỀU THẤT BẠI NGÀY {d}/{m}/{y} — KHÔNG TẠO SỐ GIẢ")
    return None
