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
    display_date = f"{d}/{m}/{y}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9"
    }

    # ==========================================
    # NGUỒN CHÍNH: KETQUA.NET — DỄ PARSE NHẤT
    # ==========================================
    try:
        url = f"https://ketqua.net/xsmb/ngay/{d}-{m}-{y}"
        print(f"🔍 [KETQUA.net] Đang lấy: {url}")
        r = requests.get(url, headers=headers, timeout=20)
        
        if r.status_code == 200 and len(r.text) > 500:
            html = r.text
            
            # Đặc biệt
            db_match = re.search(r'id="rs_0_0".*?>(\d{5})<', html)
            # Giải nhất
            g1_match = re.search(r'id="rs_1_0".*?>(\d{5})<', html)
            # Giải nhì
            g2_matches = re.findall(r'id="rs_2_\d".*?>(\d{5})<', html)
            # Giải ba
            g3_matches = re.findall(r'id="rs_3_\d".*?>(\d{5})<', html)
            # Giải tư
            g4_matches = re.findall(r'id="rs_4_\d".*?>(\d{4})<', html)
            # Giải năm
            g5_matches = re.findall(r'id="rs_5_\d".*?>(\d{4})<', html)
            # Giải sáu
            g6_matches = re.findall(r'id="rs_6_\d".*?>(\d{3})<', html)
            # Giải bảy
            g7_matches = re.findall(r'id="rs_7_\d".*?>(\d{2})<', html)
            
            if db_match and g1_match:
                db = db_match.group(1)
                g1 = g1_match.group(1)
                
                # Tính LÔ: lấy 2 số cuối của TẤT CẢ các giải
                all_prizes = [db, g1] + g2_matches + g3_matches + g4_matches
                all_prizes += g5_matches + g6_matches + g7_matches
                lotos = [p[-2:] for p in all_prizes if len(p) >= 2]
                lotos = sorted(list(set(lotos)))  # Loại trùng
                
                print(f"✅ [KETQUA.net] {display_date} | ĐB: {db} | Lô: {len(lotos)} số")
                return {
                    "date": display_date,
                    "special": db,
                    "g1": g1,
                    "g2": g2_matches,
                    "g3": g3_matches,
                    "g4": g4_matches,
                    "g5": g5_matches,
                    "g6": g6_matches,
                    "g7": g7_matches,
                    "loto": lotos,
                    "source": "KETQUA.net"
                }
    except Exception as e:
        print(f"❌ [KETQUA.net] Lỗi: {str(e)[:60]}")

    # ==========================================
    # NGUỒN 2: XOSO.WAP.VN
    # ==========================================
    try:
        url = f"https://xoso.wap.vn/xsmb/{y}/{m}/{d}"
        print(f"🔍 [Xoso.wap.vn] Đang lấy: {url}")
        r = requests.get(url, headers=headers, timeout=20)
        
        if r.status_code == 200 and len(r.text) > 300:
            html = r.text
            db_match = re.search(r'Đặc biệt.*?(\d{5})', html, re.DOTALL)
            g1_match = re.search(r'Giải nhất.*?(\d{5})', html, re.DOTALL)
            if db_match and g1_match:
                db = db_match.group(1)
                g1 = g1_match.group(1)
                # Lấy lô từ các giải
                all_nums = re.findall(r'(\d{5})|(\d{4})|(\d{3})|(\d{2})', html)
                all_nums = [''.join(g) for g in all_nums if any(g)]
                lotos = [n[-2:] for n in all_nums if len(n) >= 2 and n.isdigit()]
                lotos = [n for n in lotos if n != '00']
                lotos = sorted(list(set(lotos)))
                if len(lotos) >= 20:
                    print(f"✅ [Xoso.wap.vn] {display_date} | ĐB: {db} | Lô: {len(lotos)} số")
                    return {
                        "date": display_date, "special": db, "g1": g1,
                        "loto": lotos, "source": "Xoso.wap.vn"
                    }
    except Exception as e:
        print(f"❌ [Xoso.wap.vn] Lỗi: {str(e)[:60]}")

    # ==========================================
    # TẤT CẢ NGUỒN LỖI → TRẢ None
    # ==========================================
    print(f"❌ KHÔNG LẤY ĐƯỢC DỮ LIỆU NGÀY {display_date}")
    return None

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
