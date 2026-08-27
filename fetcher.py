import requests
import re
from datetime import datetime, timezone, timedelta
from data_manager import save_result, get_saved_result

VN_TZ = timezone(timedelta(hours=7))

def get_now_vn():
    return datetime.now(VN_TZ)

def fetch_from_website(d, m, y):
    """Lấy kết quả TRỰC TIẾP từ KETQUA.net — KHÔNG TẠO SỐ GIẢ"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9"
    }
    
    url = f"https://ketqua.net/xsmb/ngay/{d}-{m}-{y}"
    print(f"🔍 TRUY CẬP: {url}")
    
    try:
        r = requests.get(url, headers=headers, timeout=20)
        print(f"📡 Mã trạng thái: {r.status_code} | Độ dài: {len(r.text)} ký tự")
        
        if r.status_code != 200:
            print("❌ Trang không truy cập được")
            return None
            
        if len(r.text) < 500:
            print("❌ Trang quá ngắn — chưa có kết quả")
            return None
        
        html = r.text

        # === LẤY ĐẶC BIỆT ===
        db = None
        db_patterns = [
            r'id="rs_0_0"[^>]*>(\d{5})<',
            r'Đặc biệt.*?<b[^>]*>(\d{5})</b>',
            r'class="special[^>]*>(\d{5})'
        ]
        for pat in db_patterns:
            m = re.search(pat, html, re.DOTALL)
            if m:
                db = m.group(1)
                break

        # === LẤY GIẢI NHẤT ===
        g1 = None
        g1_patterns = [
            r'id="rs_1_0"[^>]*>(\d{5})<',
            r'Giải nhất.*?<b[^>]*>(\d{5})</b>'
        ]
        for pat in g1_patterns:
            m = re.search(pat, html, re.DOTALL)
            if m:
                g1 = m.group(1)
                break

        if not db or not g1:
            print(f"⚠️ Chưa tìm thấy kết quả — ĐB:{db}, G1:{g1}")
            return None

        # === LẤY TẤT CẢ GIẢI → TÍNH LÔ ===
        g2 = re.findall(r'id="rs_2_\d+"[^>]*>(\d{5})<', html)
        g3 = re.findall(r'id="rs_3_\d+"[^>]*>(\d{5})<', html)
        g4 = re.findall(r'id="rs_4_\d+"[^>]*>(\d{4})<', html)
        g5 = re.findall(r'id="rs_5_\d+"[^>]*>(\d{4})<', html)
        g6 = re.findall(r'id="rs_6_\d+"[^>]*>(\d{3})<', html)
        g7 = re.findall(r'id="rs_7_\d+"[^>]*>(\d{2})<', html)

        # Tính LÔ: 2 số cuối của tất cả giải
        all_prizes = [db, g1] + g2 + g3 + g4 + g5 + g6 + g7
        lotos = []
        for p in all_prizes:
            s = str(p).strip()
            if len(s) >= 2 and s.isdigit():
                lotos.append(s[-2:])
        lotos = sorted(list(set(lotos)))

        if len(lotos) < 20:
            print(f"⚠️ Số lô quá ít: {len(lotos)} — chưa có kết quả")
            return None

        # === TẠO KẾT QUẢ ===
        result = {
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
            "source": "KETQUA.net (trực tiếp)"
        }

        print(f"✅ LẤY THÀNH CÔNG! ĐB: {db} | Lô: {len(lotos)} số")
        return result

    except Exception as e:
        print(f"❌ Lỗi truy cập: {str(e)[:80]}")
        return None

def get_xsmb_result(target_date_str=None):
    """Lấy kết quả: Ưu tiên file lưu → nếu không thì lấy từ web → KHÔNG TẠO SỐ GIẢ"""
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

    # Bước 2: Lấy từ trang web
    result = fetch_from_website(d, m, y)
    if result:
        save_result(result)  # Lưu vào file ngay
        return result

    # ❌ Không lấy được → TRẢ None, KHÔNG TẠO SỐ GIẢ!
    print(f"❌ KHÔNG LẤY ĐƯỢC DỮ LIỆU NGÀY {d}/{m}/{y} — KHÔNG TẠO SỐ GIẢ")
    return None
