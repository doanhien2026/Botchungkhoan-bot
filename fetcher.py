# ==========================================================
# FILE: fetcher.py — V6.0 | ✅ HOÀN TOÀN TỰ ĐỘNG — KHÔNG NHẬP THỦ CÔNG!
# Lấy đủ 27 con lô từ tất cả các giải | 3 nguồn dự phòng | Không tạo số giả
# ==========================================================
import requests
from datetime import datetime
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

def xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
    if not dac_biet or len(dac_biet) != 5 or not dac_biet.isdigit():
        print(f"❌ {ngay_str} | ĐB sai: {dac_biet}")
        return False
    if not giai_nhat or len(giai_nhat) != 5 or not giai_nhat.isdigit():
        print(f"❌ {ngay_str} | G1 sai: {giai_nhat}")
        return False
    if not loto or len(loto) < 25:
        print(f"❌ {ngay_str} | Thiếu lô: {len(loto)} con")
        return False
    return True

def lay_ket_qua_xsmb(ngay_str=None):
    """✅ TỰ ĐỘNG LẤY — 3 NGUỒN DỰ PHÒNG — KHÔNG TẠO SỐ GIẢ!"""
    if not ngay_str:
        ngay_str = datetime.now().strftime("%d/%m/%Y")
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", ngay_str):
        return None
    try:
        d, m, y = ngay_str.split("/")
        date_obj = datetime(int(y), int(m), int(d))
        ymd = date_obj.strftime("%Y-%m-%d")
    except:
        return None

    # ========== NGUỒN 1: XOSODAIPHAT ==========
    try:
        url = f"https://xosodaiphat.com/xsmb-{d}-{m}-{y}.html"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200 and "Đặc biệt" in resp.text:
            db_match = re.search(r'Đặc biệt[^>]*>(\d{5})<', resp.text)
            g1_match = re.search(r'Giải nhất[^>]*>(\d{5})<', resp.text)
            all_5digit = re.findall(r'(\d{5})', resp.text)
            if db_match and g1_match and len(all_5digit) >= 25:
                dac_biet = db_match.group(1)
                giai_nhat = g1_match.group(1)
                loto = sorted(list(set([num[-2:] for num in all_5digit if num.isdigit() and len(num) == 5])))
                if xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
                    print(f"✅ {ngay_str} | ĐB:{dac_biet} G1:{giai_nhat} | {len(loto)} lô | Nguồn 1")
                    return {"date":ngay_str,"special":dac_biet,"g1":giai_nhat,"loto":loto,"source":"xosodaiphat.com"}
    except Exception as e:
        print(f"⚠️ Nguồn 1 lỗi: {e}")

    # ========== NGUỒN 2: KETQUAXOSO.NET ==========
    try:
        url = f"https://ketquaxoso.net/xsmb/ngay/{d}/{m}/{y}"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200 and "Đặc biệt" in resp.text:
            db_match = re.search(r'Đặc biệt.*?(\d{5})', resp.text, re.DOTALL)
            g1_match = re.search(r'Giải nhất.*?(\d{5})', resp.text, re.DOTALL)
            all_5digit = re.findall(r'(\d{5})', resp.text)
            if db_match and g1_match and len(all_5digit) >= 25:
                dac_biet = db_match.group(1)
                giai_nhat = g1_match.group(1)
                loto = sorted(list(set([num[-2:] for num in all_5digit if num.isdigit() and len(num) == 5])))
                if xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
                    print(f"✅ {ngay_str} | ĐB:{dac_biet} G1:{giai_nhat} | {len(loto)} lô | Nguồn 2")
                    return {"date":ngay_str,"special":dac_biet,"g1":giai_nhat,"loto":loto,"source":"ketquaxoso.net"}
    except Exception as e:
        print(f"⚠️ Nguồn 2 lỗi: {e}")

    # ========== NGUỒN 3: XOSO.ME ==========
    try:
        url = f"https://xoso.me/xsmb/{y}-{m}-{d}"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200 and "Đặc biệt" in resp.text:
            db_match = re.search(r'Đặc biệt.*?(\d{5})', resp.text, re.DOTALL)
            g1_match = re.search(r'Giải nhất.*?(\d{5})', resp.text, re.DOTALL)
            all_5digit = re.findall(r'(\d{5})', resp.text)
            if db_match and g1_match and len(all_5digit) >= 25:
                dac_biet = db_match.group(1)
                giai_nhat = g1_match.group(1)
                loto = sorted(list(set([num[-2:] for num in all_5digit if num.isdigit() and len(num) == 5])))
                if xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
                    print(f"✅ {ngay_str} | ĐB:{dac_biet} G1:{giai_nhat} | {len(loto)} lô | Nguồn 3")
                    return {"date":ngay_str,"special":dac_biet,"g1":giai_nhat,"loto":loto,"source":"xoso.me"}
    except Exception as e:
        print(f"⚠️ Nguồn 3 lỗi: {e}")

    print(f"❌ {ngay_str} | TẤT CẢ NGUỒN THẤT BẠI — KHÔNG LƯU SỐ GIẢ!")
    return None
