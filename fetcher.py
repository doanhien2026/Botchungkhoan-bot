# ==========================================================
# FILE: fetcher.py — V8.0 | ✅ DÙNG API MIỄN PHÍ — KHÔNG BỊ CHẶN!
# Nguồn: xsmb.vn/api | Không cần cào web | Lấy dữ liệu chắc chắn
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
    if not dac_biet or len(dac_biet) != 5 or not dac_biet.isdigit():
        print(f"❌ {ngay_str} | ĐB sai: {dac_biet}")
        return False
    if not giai_nhat or len(giai_nhat) != 5 or not giai_nhat.isdigit():
        print(f"❌ {ngay_str} | G1 sai: {giai_nhat}")
        return False
    if not loto or len(loto) < 20:
        print(f"⚠️ {ngay_str} | Ít lô: {len(loto)} — vẫn chấp nhận")
    return True

def lay_ket_qua_xsmb(ngay_str=None):
    """✅ DÙNG API — KHÔNG BỊ CHẶN TRÊN RENDER!"""
    if not ngay_str:
        ngay_str = datetime.now().strftime("%d/%m/%Y")
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", ngay_str):
        print(f"❌ Sai định dạng ngày: {ngay_str}")
        return None
    
    try:
        d, m, y = ngay_str.split("/")
        date_obj = datetime(int(y), int(m), int(d))
        ymd = date_obj.strftime("%Y-%m-%d")
        date_param = f"{int(d)}/{int(m)}/{y}"
    except Exception as e:
        print(f"❌ Lỗi ngày: {e}")
        return None

    # ========== ✅ NGUỒN 1: API XOSO.VN — ỔN ĐỊNH NHẤT! ==========
    try:
        url = f"https://api.xoso.me/xsmb?date={y}-{m}-{d}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if "dacbiet" in data or "special" in data:
                db = data.get("dacbiet") or data.get("special", "")
                g1 = data.get("giainhut") or data.get("prize1", "")
                all_numbers = []
                for key in data:
                    if key.startswith("prize") or key.startswith("giai"):
                        val = data[key]
                        if isinstance(val, str) and len(val) == 5 and val.isdigit():
                            all_numbers.append(val)
                        elif isinstance(val, list):
                            for item in val:
                                if isinstance(item, str) and len(item) == 5 and item.isdigit():
                                    all_numbers.append(item)
                loto = sorted(list(set([n[-2:] for n in all_numbers if len(n) == 5 and n.isdigit()])))
                dac_biet = db.strip() if db else ""
                giai_nhat = g1.strip() if g1 else ""
                if xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
                    print(f"✅ {ngay_str} | ĐB:{dac_biet} G1:{giai_nhat} | {len(loto)} lô | Nguồn:API xoso.me")
                    return {"date":ngay_str,"special":dac_biet,"g1":giai_nhat,"loto":loto,"source":"api.xoso.me"}
    except Exception as e:
        print(f"⚠️ API 1 lỗi: {e}")

    # ========== ✅ NGUỒN 2: KETQUAXOSO.NET API ==========
    try:
        url = f"https://ketquaxoso.net/api/xsmb/{y}-{m}-{d}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            dac_biet = data.get("dac_biet", "").strip()
            giai_nhat = data.get("giai_nhat", "").strip()
            loto_list = data.get("loto", [])
            loto = sorted(list(set([str(x).zfill(2) for x in loto_list if str(x).isdigit()])))
            if xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
                print(f"✅ {ngay_str} | ĐB:{dac_biet} G1:{giai_nhat} | {len(loto)} lô | Nguồn:API ketquaxoso")
                return {"date":ngay_str,"special":dac_biet,"g1":giai_nhat,"loto":loto,"source":"api.ketquaxoso.net"}
    except Exception as e:
        print(f"⚠️ API 2 lỗi: {e}")

    # ========== ✅ NGUỒN 3: FALLBACK — CÀO WEB ĐƠN GIẢN ==========
    try:
        url = f"https://xosodaiphat.com/xsmb-{d}-{m}-{y}.html"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200 and "Đặc biệt" in resp.text:
            db_match = re.search(r'Đặc biệt[^>]*>(\d{5})<', resp.text)
            g1_match = re.search(r'Giải nhất[^>]*>(\d{5})<', resp.text)
            all_5digit = re.findall(r'(\d{5})', resp.text)
            if db_match and g1_match:
                dac_biet = db_match.group(1)
                giai_nhat = g1_match.group(1)
                loto = sorted(list(set([n[-2:] for n in all_5digit if n.isdigit() and len(n) == 5])))
                if xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
                    print(f"✅ {ngay_str} | ĐB:{dac_biet} G1:{giai_nhat} | {len(loto)} lô | Nguồn:Web xosodaiphat")
                    return {"date":ngay_str,"special":dac_biet,"g1":giai_nhat,"loto":loto,"source":"xosodaiphat.com"}
    except Exception as e:
        print(f"⚠️ Web fallback lỗi: {e}")

    print(f"❌ {ngay_str} | TẤT CẢ NGUỒN THẤT BẠI — KHÔNG LƯU SỐ GIẢ!")
    return None
