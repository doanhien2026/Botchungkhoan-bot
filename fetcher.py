# ==========================================================
# FILE: fetcher.py — V4.1 | ✅ CHỈ LẤY DỮ LIỆU THẬT, KHÔNG TẠO SỐ GIẢ!
# ==========================================================
import requests
from datetime import datetime
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

def xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
    """✅ KIỂM TRA NGHIÊM NGẶT TRƯỚC KHI TRẢ VỀ — KHÔNG LƯU SAI!"""
    if not dac_biet or len(dac_biet) != 5 or not dac_biet.isdigit():
        print(f"❌ {ngay_str} | Đặc Biệt sai: {dac_biet}")
        return False
    if not giai_nhat or len(giai_nhat) != 5 or not giai_nhat.isdigit():
        print(f"❌ {ngay_str} | Giải Nhất sai: {giai_nhat}")
        return False
    if not loto or len(loto) < 15:
        print(f"❌ {ngay_str} | Không đủ lô: {len(loto)}")
        return False
    for so in loto:
        if len(so) != 2 or not so.isdigit():
            print(f"❌ {ngay_str} | Lô sai định dạng: {so}")
            return False
    return True

def lay_ket_qua_xsmb(ngay_str=None):
    """✅ LẤY DỮ LIỆU THẬT — NẾU KHÔNG LẤY ĐƯỢC → TRẢ VỀ None, KHÔNG TẠO SỐ GIẢ!"""
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

    # ========== NGUỒN 1: API XOSOONLINE — TRẢ JSON, ÍT BỊ CHẶN NHẤT ==========
    try:
        url = f"https://api.xosoonline.com.vn/api/v1/result?date={ymd}&region=MB"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        print(f"🔍 {ngay_str} | API Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("error") == 0 and "data" in data:
                kq = data["data"]
                dac_biet = str(kq.get("special", "")).strip()
                giai_nhat = str(kq.get("first", "")).strip()
                
                loto = []
                if len(dac_biet) == 5: loto.append(dac_biet[-2:])
                if len(giai_nhat) == 5: loto.append(giai_nhat[-2:])
                
                for key in ["second", "third", "fourth", "fifth", "sixth", "seventh", "eighth"]:
                    val = kq.get(key, [])
                    if isinstance(val, list):
                        for num in val:
                            num = str(num).strip()
                            if len(num) == 5 and num.isdigit():
                                loto.append(num[-2:])
                
                loto = sorted(list(set([n.zfill(2) for n in loto if n.isdigit() and len(n) == 2])))
                
                if xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
                    print(f"✅ {ngay_str} | ĐB:{dac_biet} G1:{giai_nhat} | Lô:{len(loto)} con | API xosoonline")
                    return {
                        "date": ngay_str,
                        "special": dac_biet,
                        "g1": giai_nhat,
                        "loto": loto,
                        "source": "api.xosoonline.com.vn",
                        "verified": True
                    }
    except Exception as e:
        print(f"⚠️ Nguồn API 1 lỗi: {e}")

    # ========== NGUỒN 2: XOSO.ME — DỰ PHÒNG ==========
    try:
        url = f"https://xoso.me/xsmb/{y}-{m}-{d}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200 and "Đặc biệt" in resp.text:
            db_match = re.search(r'Đặc biệt.*?(\d{5})', resp.text, re.DOTALL)
            g1_match = re.search(r'Giải nhất.*?(\d{5})', resp.text, re.DOTALL)
            if db_match and g1_match:
                dac_biet = db_match.group(1).strip()
                giai_nhat = g1_match.group(1).strip()
                all_5digit = re.findall(r'(\d{5})', resp.text)
                loto = sorted(list(set([num[-2:] for num in all_5digit if num.isdigit() and len(num) == 5])))
                
                if xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
                    print(f"✅ {ngay_str} | ĐB:{dac_biet} G1:{giai_nhat} | Nguồn:xoso.me")
                    return {
                        "date": ngay_str,
                        "special": dac_biet,
                        "g1": giai_nhat,
                        "loto": loto,
                        "source": "xoso.me",
                        "verified": True
                    }
    except Exception as e:
        print(f"⚠️ Nguồn 2 lỗi: {e}")

    # ========== ❌ KHÔNG LẤY ĐƯỢC → TRẢ VỀ None, KHÔNG TẠO SỐ GIẢ! ==========
    print(f"❌ {ngay_str} | TẤT CẢ NGUỒN ĐỀU KHÔNG LẤY ĐƯỢC → KHÔNG LƯU SỐ GIẢ!")
    return None
