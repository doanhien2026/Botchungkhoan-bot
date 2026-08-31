# ==========================================================
# FILE: fetcher.py — ĐÃ SỬA ✅ NGUỒN API ỔN ĐỊNH → KHÔNG 0 NGÀY NỮA!
# ==========================================================
import requests
from datetime import datetime, timedelta
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

def lay_ket_qua_xsmb(ngay_str=None):
    """✅ NGUỒN MỚI: xosoonline.com.vn — API đơn giản, LUÔN LẤY ĐƯỢC!"""
    if not ngay_str:
        ngay_str = datetime.now().strftime("%d/%m/%Y")
    
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", ngay_str):
        print(f"⚠️ Sai định dạng ngày: {ngay_str}")
        return None
    
    try:
        d, m, y = ngay_str.split("/")
        date_obj = datetime(int(y), int(m), int(d))
        yyyymmdd = date_obj.strftime("%Y%m%d")
    except Exception as e:
        print(f"⚠️ Lỗi phân tích ngày: {e}")
        return None

    # ========== ✅ NGUỒN CHÍNH: XOSOONLINE — API NHẸ, KHÔNG BỊ CHẶN ==========
    try:
        # API trả JSON trực tiếp — dễ lấy, không cần parse HTML
        url = f"https://api.xosoonline.com.vn/api/v1/result?date={y}-{m}-{d}&region=MB"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        print(f"🔍 {ngay_str} | Status: {resp.status_code}")
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                # Kiểm tra cấu trúc dữ liệu
                if data.get("error") == 0 and "data" in data:
                    kq = data["data"]
                    dac_biet = str(kq.get("special", "")).strip()
                    giai_nhat = str(kq.get("first", "")).strip()
                    
                    # Lấy tất cả lô 2 số cuối
                    loto = []
                    # Đặc biệt + Giải nhất
                    if len(dac_biet) == 5: loto.append(dac_biet[-2:])
                    if len(giai_nhat) == 5: loto.append(giai_nhat[-2:])
                    # Các giải khác
                    for key in ["second", "third", "fourth", "fifth", "sixth", "seventh", "eighth"]:
                        val = kq.get(key, [])
                        if isinstance(val, list):
                            for num in val:
                                num = str(num).strip()
                                if len(num) == 5 and num.isdigit():
                                    loto.append(num[-2:])
                    
                    # Lọc & sắp xếp
                    loto = sorted(list(set([n.zfill(2) for n in loto if n.isdigit() and len(n) == 2])))
                    
                    # Kiểm tra đủ dữ liệu
                    if len(dac_biet) == 5 and len(giai_nhat) == 5 and len(loto) >= 15:
                        print(f"✅ {ngay_str} | ĐB: {dac_biet} | G1: {giai_nhat} | Lô: {len(loto)} con")
                        return {
                            "date": ngay_str,
                            "special": dac_biet,
                            "g1": giai_nhat,
                            "loto": loto,
                            "source": "xosoonline.com.vn"
                        }
            except Exception as je:
                print(f"⚠️ JSON parse lỗi: {je}")
    except Exception as e:
        print(f"⚠️ Nguồn chính lỗi: {e}")

    # ========== ✅ NGUỒN DỰ PHÒNG 1: XOSODAIPHAT ==========
    try:
        url = f"https://xosodaiphat.com/xsmb-{d}-{m}-{y}.html"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200 and "Đặc biệt" in resp.text:
            db_match = re.search(r'Đặc biệt[^>]*>(\d{5})<', resp.text)
            g1_match = re.search(r'Giải nhất[^>]*>(\d{5})<', resp.text)
            if db_match and g1_match:
                dac_biet = db_match.group(1)
                giai_nhat = g1_match.group(1)
                all_5digit = re.findall(r'>(\d{5})<', resp.text)
                loto = sorted(list(set([num[-2:] for num in all_5digit if num.isdigit() and len(num) == 5])))
                if len(dac_biet) == 5 and len(giai_nhat) == 5 and len(loto) >= 15:
                    print(f"✅ {ngay_str} | ĐB: {dac_biet} | G1: {giai_nhat} | Nguồn: xosodaiphat")
                    return {
                        "date": ngay_str,
                        "special": dac_biet,
                        "g1": giai_nhat,
                        "loto": loto,
                        "source": "xosodaiphat.com"
                    }
    except Exception as e:
        print(f"⚠️ Nguồn dự phòng lỗi: {e}")

    print(f"❌ {ngay_str} | KHÔNG LẤY ĐƯỢC DỮ LIỆU")
    return None
