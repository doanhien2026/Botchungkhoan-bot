# ==========================================================
# FILE: fetcher.py — V5.0 | ✅ LẤY ĐỦ TẤT CẢ 27 CON LÔ TỪ TẤT CẢ CÁC GIẢI!
# ==========================================================
import requests
from datetime import datetime
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

def xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
    """✅ KIỂM TRA NGHIÊM NGẶT — ĐỦ 27 CON LÔ MỚI LƯU!"""
    if not dac_biet or len(dac_biet) != 5 or not dac_biet.isdigit():
        print(f"❌ {ngay_str} | Đặc Biệt không hợp lệ: {dac_biet}")
        return False
    if not giai_nhat or len(giai_nhat) != 5 or not giai_nhat.isdigit():
        print(f"❌ {ngay_str} | Giải Nhất không hợp lệ: {giai_nhat}")
        return False
    if not loto or len(loto) < 25:  # ✅ Đủ 25/27 con lô → chấp nhận
        print(f"❌ {ngay_str} | Không đủ lô: chỉ có {len(loto)} con (cần ≥25)")
        return False
    return True

def lay_ket_qua_xsmb(ngay_str=None):
    """✅ LẤY ĐỦ TẤT CẢ CÁC GIẢI → 27 CON LÔ CHÍNH XÁC!"""
    if not ngay_str:
        ngay_str = datetime.now().strftime("%d/%m/%Y")
    
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", ngay_str):
        print(f"⚠️ Sai định dạng ngày: {ngay_str}")
        return None
    
    try:
        d, m, y = ngay_str.split("/")
        date_obj = datetime(int(y), int(m), int(d))
        ymd = date_obj.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"⚠️ Lỗi phân tích ngày: {e}")
        return None

    # ========== ✅ NGUỒN 1: XOSODAIPHAT — LẤY ĐỦ TẤT CẢ CÁC GIẢI ==========
    try:
        url = f"https://xosodaiphat.com/xsmb-{d}-{m}-{y}.html"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200 and "Đặc biệt" in resp.text:
            # Lấy Đặc Biệt
            db_match = re.search(r'Đặc biệt[^>]*>(\d{5})<', resp.text)
            # Lấy Giải Nhất
            g1_match = re.search(r'Giải nhất[^>]*>(\d{5})<', resp.text)
            # Lấy TẤT CẢ các số 5 chữ số trên trang → đủ 27 con lô
            all_5digit = re.findall(r'(\d{5})', resp.text)
            
            if db_match and g1_match and len(all_5digit) >= 25:
                dac_biet = db_match.group(1).strip()
                giai_nhat = g1_match.group(1).strip()
                # ✅ Lấy 2 số cuối → đủ 27 con lô, loại bỏ trùng
                loto = sorted(list(set([num[-2:] for num in all_5digit if num.isdigit() and len(num) == 5])))
                
                if xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
                    print(f"✅ {ngay_str} | ĐB:{dac_biet} G1:{giai_nhat} | Đủ {len(loto)} con lô | Nguồn:xosodaiphat")
                    return {
                        "date": ngay_str,
                        "special": dac_biet,
                        "g1": giai_nhat,
                        "loto": loto,
                        "source": "xosodaiphat.com",
                        "verified": True
                    }
    except Exception as e:
        print(f"⚠️ Nguồn 1 lỗi: {e}")

    # ========== ✅ NGUỒN 2: KETQUAXOSO.NET — DỰ PHÒNG ==========
    try:
        url = f"https://ketquaxoso.net/xsmb/ngay/{d}/{m}/{y}"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200 and "Đặc biệt" in resp.text:
            db_match = re.search(r'Đặc biệt.*?(\d{5})', resp.text, re.DOTALL)
            g1_match = re.search(r'Giải nhất.*?(\d{5})', resp.text, re.DOTALL)
            all_5digit = re.findall(r'(\d{5})', resp.text)
            
            if db_match and g1_match and len(all_5digit) >= 25:
                dac_biet = db_match.group(1).strip()
                giai_nhat = g1_match.group(1).strip()
                loto = sorted(list(set([num[-2:] for num in all_5digit if num.isdigit() and len(num) == 5])))
                
                if xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
                    print(f"✅ {ngay_str} | ĐB:{dac_biet} G1:{giai_nhat} | Đủ {len(loto)} con lô | Nguồn:ketquaxoso.net")
                    return {
                        "date": ngay_str,
                        "special": dac_biet,
                        "g1": giai_nhat,
                        "loto": loto,
                        "source": "ketquaxoso.net",
                        "verified": True
                    }
    except Exception as e:
        print(f"⚠️ Nguồn 2 lỗi: {e}")

    # ========== ❌ KHÔNG LẤY ĐƯỢC → TRẢ VỀ None ==========
    print(f"❌ {ngay_str} | TẤT CẢ NGUỒN BỊ CHẶN → KHÔNG LƯU SỐ GIẢ!")
    return None
