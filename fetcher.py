import requests
import random
import re
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
    date_api = f"{d}{m}{y}"
    display_date = f"{d}/{m}/{y}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9",
        "Referer": "https://kqxs.vn/"
    }

    # ==========================================
    # NGUỒN CHÍNH: KQXS.VN — CẢI THIỆN PHÂN TÍCH
    # ==========================================
    try:
        url = f"https://kqxs.vn/xsmb/{y}-{m}-{d}"
        print(f"🔍 Đang lấy dữ liệu từ: {url}")
        r = requests.get(url, headers=headers, timeout=20)
        
        if r.status_code == 200 and len(r.text) > 1000:
            html = r.text
            
            # Lấy Đặc Biệt — cải thiện regex
            db_patterns = [
                r'Giải Đặc biệt.*?<div[^>]*class="[^"]*result[^"]*"[^>]*>(\d{5,6})</div>',
                r'Đặc biệt.*?(\d{5,6})',
                r'class="special[^>]*>(\d{5,6})'
            ]
            db = None
            for pat in db_patterns:
                m = re.search(pat, html, re.DOTALL)
                if m:
                    db = m.group(1)
                    break
            
            # Lấy Giải Nhất
            g1_patterns = [
                r'Giải nhất.*?(\d{5})',
                r'class="prize-1[^>]*>(\d{5})'
            ]
            g1 = None
            for pat in g1_patterns:
                m = re.search(pat, html, re.DOTALL)
                if m:
                    g1 = m.group(1)
                    break
            
            # Lấy tất cả số 2 chữ số (loto)
            lotos = re.findall(r'>(\d{2})<', html)
            lotos = [n for n in lotos if n.isdigit() and n != '00' and len(n) == 2]
            lotos = list(set(lotos))  # Loại bỏ trùng lặp
            
            if db and g1 and len(lotos) >= 15:
                print(f"✅ [KQXS.vn] {display_date} | ĐB: {db} | G1: {g1} | Lô: {len(lotos)} số")
                return {
                    "date": display_date,
                    "special": db,
                    "g1": g1,
                    "loto": lotos,
                    "source": "KQXS.vn"
                }
            else:
                print(f"⚠️ KQXS.vn thiếu dữ liệu — ĐB:{db}, G1:{g1}, Lô:{len(lotos)}")
    except Exception as e:
        print(f"❌ [KQXS.vn] Lỗi: {str(e)[:60]}")

    # ==========================================
    # NGUỒN DỰ PHÒNG 2: XOSO.COM.VN
    # ==========================================
    try:
        url = f"https://xoso.com.vn/xsmb-{d}/{m}/{y}.html"
        print(f"🔍 Thử nguồn 2: {url}")
        r = requests.get(url, headers=headers, timeout=20)
        
        if r.status_code == 200 and len(r.text) > 500:
            html = r.text
            db_match = re.search(r'Đặc biệt.*?(\d{5})', html, re.DOTALL)
            g1_match = re.search(r'Giải nhất.*?(\d{5})', html, re.DOTALL)
            if db_match and g1_match:
                db = db_match.group(1)
                g1 = g1_match.group(1)
                lotos = re.findall(r'>(\d{2})<', html)
                lotos = list(set([n for n in lotos if n.isdigit() and n != '00' and len(n) == 2]))
                if len(lotos) >= 10:
                    print(f"✅ [Xoso.com.vn] {display_date} | ĐB: {db}")
                    return {
                        "date": display_date, "special": db, "g1": g1,
                        "loto": lotos, "source": "Xoso.com.vn"
                    }
    except Exception as e:
        print(f"❌ [Xoso.com.vn] Lỗi: {str(e)[:60]}")

    # ==========================================
    # NGUỒN DỰ PHÒNG 3: XOSO.WAP.VN
    # ==========================================
    try:
        url = f"https://xoso.wap.vn/xsmb/{y}/{m}/{d}"
        print(f"🔍 Thử nguồn 3: {url}")
        r = requests.get(url, headers=headers, timeout=20)
        
        if r.status_code == 200 and len(r.text) > 300:
            html = r.text
            db_match = re.search(r'Đặc biệt.*?(\d{5,6})', html, re.DOTALL)
            g1_match = re.search(r'Giải nhất.*?(\d{5})', html, re.DOTALL)
            if db_match:
                db = db_match.group(1)
                g1 = g1_match.group(1) if g1_match else "-----"
                lotos = re.findall(r'>(\d{2})<', html)
                lotos = list(set([n for n in lotos if n.isdigit() and n != '00' and len(n) == 2]))
                print(f"✅ [Xoso.wap.vn] {display_date} | ĐB: {db}")
                return {
                    "date": display_date, "special": db, "g1": g1,
                    "loto": lotos, "source": "Xoso.wap.vn"
                }
    except Exception as e:
        print(f"❌ [Xoso.wap.vn] Lỗi: {str(e)[:60]}")

    # ==========================================
    # TẤT CẢ NGUỒN LỖI → TRẢ LỖI THÔNG BÁO LỖI
    # ==========================================
    print(f"❌ TẤT CẢ NGUỒN ĐỀU KHÔNG LẤY ĐƯỢC DỮ LIỆU NGÀY {display_date}")
    return None  # Trả về None thay vì dữ liệu giả → biết rõ là lỗi

# === DỰ BÁO ===
def get_xsmb_prediction(target_date_str=None):
    if not target_date_str:
        target_date_str = get_now_vn().strftime("%d/%m/%Y")
    parts = target_date_str.split("/")
    if len(parts) != 3:
        return None
    d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
    random.seed(int(f"{y}{m}{d}") + 999)
    return {
        "date": f"{d}/{m}/{y}",
        "bach_thu": str(random.randint(0, 99)).zfill(2),
        "song_thu": [str(random.randint(0, 99)).zfill(2) for _ in range(2)],
        "lo_xiu": [str(random.randint(0, 99)).zfill(2) for _ in range(4)]
    }
