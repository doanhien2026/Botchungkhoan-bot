# ==========================================================
# FILE: fetcher.py — LẤY KẾT QUẢ XSMB THẬT & CHÍNH XÁC
# ==========================================================
import requests
from datetime import datetime, timedelta
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

def lay_ket_qua_xsmb(ngay_str=None):
    """Lấy kết quả XSMB THẬT — 2 nguồn dự phòng, kiểm tra định dạng nghiêm ngặt"""
    if not ngay_str:
        ngay_str = datetime.now().strftime("%d/%m/%Y")
    
    # ✅ KIỂM TRA ĐỊNH DẠNG NGAY TRƯỚC KHI LẤY
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", ngay_str):
        print(f"⚠️ Định dạng ngày sai: {ngay_str}")
        return None
    
    try:
        d, m, y = ngay_str.split("/")
        date_obj = datetime(int(y), int(m), int(d))
        yyyymmdd = date_obj.strftime("%Y%m%d")
    except Exception as e:
        print(f"⚠️ Lỗi phân tích ngày {ngay_str}: {e}")
        return None

    # ========== NGUỒN 1: XOSO.WIN — NGUỒN DỮ LIỆU ỔN ĐỊNH ==========
    try:
        url = f"https://xoso.win/xsmb/ngay/{y}-{m}-{d}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            # Tìm số Đặc Biệt (5 chữ số)
            db_match = re.search(r'Đặc biệt.*?(\d{5})', resp.text, re.DOTALL)
            g1_match = re.search(r'Giải nhất.*?(\d{5})', resp.text, re.DOTALL)
            if db_match and g1_match:
                dac_biet = db_match.group(1).strip()
                giai_nhat = g1_match.group(1).strip()
                # Lấy tất cả số 2 chữ số cuối → lô tô
                all_5digit = re.findall(r'>(\d{5})<', resp.text)
                loto = sorted(list(set([num[-2:] for num in all_5digit if num.isdigit() and len(num)==5])))
                if len(dac_biet)==5 and len(giai_nhat)==5 and len(loto)>=15:
                    return {
                        "date": ngay_str,
                        "special": dac_biet,
                        "g1": giai_nhat,
                        "loto": loto,
                        "source": "xoso.win"
                    }
    except Exception as e:
        print(f"⚠️ Nguồn 1 (xoso.win) lỗi: {e}")

    # ========== NGUỒN 2: XOSODAIPHAT — DỰ PHÒNG ==========
    try:
        url = f"https://xosodaiphat.com/xsmb-{d}-{m}-{y}.html"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200 and "Đặc biệt" in resp.text:
            db_match = re.search(r'Đặc biệt[^>]*>(\d{5})<', resp.text)
            g1_match = re.search(r'Giải nhất[^>]*>(\d{5})<', resp.text)
            if db_match and g1_match:
                dac_biet = db_match.group(1)
                giai_nhat = g1_match.group(1)
                all_5digit = re.findall(r'>(\d{5})<', resp.text)
                loto = sorted(list(set([num[-2:] for num in all_5digit if num.isdigit() and len(num)==5])))
                if len(dac_biet)==5 and len(giai_nhat)==5 and len(loto)>=15:
                    return {
                        "date": ngay_str,
                        "special": dac_biet,
                        "g1": giai_nhat,
                        "loto": loto,
                        "source": "xosodaiphat.com"
                    }
    except Exception as e:
        print(f"⚠️ Nguồn 2 (xosodaiphat) lỗi: {e}")

    print(f"❌ Không lấy được dữ liệu ngày {ngay_str}")
    return None
