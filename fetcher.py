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

def lay_tu_ketquanet(d, m, y):
    try:
        url = f"https://ketqua.net/ngay-xsmb-{y}-{m}-{d}"
        print(f"🔍 [KETQUA.net] Đang lấy: {url}")
        
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200 or len(r.text) < 500:
            print(f"⚠️ [KETQUA.net] Mã lỗi: {r.status_code} hoặc nội dung quá ngắn")
            return None
        
        html = r.text
        
        db_match = re.search(r'id="rs_0_0"[^>]*>(\d{5})<', html)
        if not db_match:
            db_match = re.search(r'Đặc biệt.*?<td[^>]*>(\d{5})</td>', html, re.DOTALL)
        if not db_match:
            print("❌ [KETQUA.net] Không tìm thấy Giải Đặc Biệt")
            return None
        db = db_match.group(1)
        
        g1_match = re.search(r'id="rs_1_0"[^>]*>(\d{5})<', html)
        if not g1_match:
            g1_match = re.search(r'Giải nhất.*?<td[^>]*>(\d{5})</td>', html, re.DOTALL)
        if not g1_match:
            print("❌ [KETQUA.net] Không tìm thấy Giải Nhất")
            return None
        g1 = g1_match.group(1)
        
        g2 = re.findall(r'id="rs_2_\d+"[^>]*>(\d{5})<', html)
        g3 = re.findall(r'id="rs_3_\d+"[^>]*>(\d{5})<', html)
        g4 = re.findall(r'id="rs_4_\d+"[^>]*>(\d{4})<', html)
        g5 = re.findall(r'id="rs_5_\d+"[^>]*>(\d{4})<', html)
        g6 = re.findall(r'id="rs_6_\d+"[^>]*>(\d{3})<', html)
        g7 = re.findall(r'id="rs_7_\d+"[^>]*>(\d{2})<', html)
        
        if len(g2) == 0 or len(g3) == 0:
            print(f"⚠️ [KETQUA.net] Dữ liệu chưa đầy đủ — G2:{len(g2)}, G3:{len(g3)}")
            return None
        
        all_prizes = [db, g1] + g2 + g3 + g4 + g5 + g6 + g7
        lotos = list(set(n[-2:] for n in all_prizes if len(n) >= 2))
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
        print(f"❌ [KETQUA.net] Lỗi: {str(e)[:80]}")
        return None

def get_xsmb_result(target_date_str=None):
    if not target_date_str:
        target_date_str = get_now_vn().strftime("%d/%m/%Y")
    
    parts = target_date_str.split("/")
    if len(parts) != 3:
        return None
    
    d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
    
    saved = get_saved_result(f"{d}/{m}/{y}")
    if saved:
        print(f"📂 Đọc từ file: {saved['date']} | ĐB: {saved['special']}")
        return saved
    
    result = lay_tu_ketquanet(d, m, y)
    
    if result:
        save_result(result)
        return result
    
    print(f"❌ KHÔNG LẤY ĐƯỢC DỮ LIỆU NGÀY {d}/{m}/{y}")
    return None
