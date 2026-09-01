# ==========================================================
# FILE: fetcher.py — V7.0 | ✅ SỬA LỖI DỮ LIỆU + 3 NGUỒN TỐI ƯU
# ==========================================================
import requests
from datetime import datetime
import re
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com/",
}

def xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
    if not dac_biet or len(dac_biet) != 5 or not dac_biet.isdigit():
        print(f"❌ {ngay_str} | Đặc Biệt sai: {dac_biet}")
        return False
    if not giai_nhat or len(giai_nhat) != 5 or not giai_nhat.isdigit():
        print(f"❌ {ngay_str} | Giải Nhất sai: {giai_nhat}")
        return False
    if not loto or len(loto) < 20:
        print(f"⚠️ {ngay_str} | Ít lô: {len(loto)} — vẫn chấp nhận")
    return True

def lay_ket_qua_xsmb(ngay_str=None):
    if not ngay_str:
        ngay_str = datetime.now().strftime("%d/%m/%Y")
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", ngay_str):
        print(f"❌ Sai định dạng ngày: {ngay_str}")
        return None
    try:
        d, m, y = ngay_str.split("/")
        date_obj = datetime(int(y), int(m), int(d))
        ymd = date_obj.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"❌ Lỗi ngày: {e}")
        return None

    # ========== NGUỒN 1: XOSODAIPHAT ==========
    try:
        url = f"https://xosodaiphat.com/xsmb-{d}-{m}-{y}.html"
        resp = requests.get(url, headers=HEADERS, timeout=25)
        if resp.status_code == 200 and "Đặc biệt" in resp.text:
            db_match = re.search(r'Đặc biệt[^>]*>(\d{5})<', resp.text)
            g1_match = re.search(r'Giải nhất[^>]*>(\d{5})<', resp.text)
            all_5digit = re.findall(r'(\d{5})', resp.text)
            if db_match and g1_match:
                dac_biet = db_match.group(1)
                giai_nhat = g1_match.group(1)
                loto = sorted(list(set([n[-2:] for n in all_5digit if n.isdigit() and len(n)==5])))
                if xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
                    print(f"✅ {ngay_str} | ĐB:{dac_biet} G1:{giai_nhat} | {len(loto)} lô | Nguồn 1")
                    return {"date":ngay_str,"special":dac_biet,"g1":giai_nhat,"loto":loto,"source":"xosodaiphat.com"}
    except Exception as e:
        print(f"⚠️ Nguồn 1 lỗi: {e}")
    time.sleep(0.5)

    # ========== NGUỒN 2: KETQUAXOSO.NET ==========
    try:
        url = f"https://ketquaxoso.net/xsmb/ngay/{d}/{m}/{y}"
        resp = requests.get(url, headers=HEADERS, timeout=25)
        if resp.status_code == 200 and "Đặc biệt" in resp.text:
            db_match = re.search(r'Đặc biệt.*?(\d{5})', resp.text, re.DOTALL)
            g1_match = re.search(r'Giải nhất.*?(\d{5})', resp.text, re.DOTALL)
            all_5digit = re.findall(r'(\d{5})', resp.text)
            if db_match and g1_match:
                dac_biet = db_match.group(1)
                giai_nhat = g1_match.group(1)
                loto = sorted(list(set([n[-2:] for n in all_5digit if n.isdigit() and len(n)==5])))
                if xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
                    print(f"✅ {ngay_str} | ĐB:{dac_biet} G1:{giai_nhat} | {len(loto)} lô | Nguồn 2")
                    return {"date":ngay_str,"special":dac_biet,"g1":giai_nhat,"loto":loto,"source":"ketquaxoso.net"}
    except Exception as e:
        print(f"⚠️ Nguồn 2 lỗi: {e}")
    time.sleep(0.5)

    # ========== NGUỒN 3: XOSO.ME ==========
    try:
        url = f"https://xoso.me/xsmb/{y}-{m}-{d}"
        resp = requests.get(url, headers=HEADERS, timeout=25)
        if resp.status_code == 200 and "Đặc biệt" in resp.text:
            db_match = re.search(r'Đặc biệt.*?(\d{5})', resp.text, re.DOTALL)
            g1_match = re.search(r'Giải nhất.*?(\d{5})', resp.text, re.DOTALL)
            all_5digit = re.findall(r'(\d{5})', resp.text)
            if db_match and g1_match:
                dac_biet = db_match.group(1)
                giai_nhat = g1_match.group(1)
                loto = sorted(list(set([n[-2:] for n in all_5digit if n.isdigit() and len(n)==5])))
                if xac_minh_dulieu(dac_biet, giai_nhat, loto, ngay_str):
                    print(f"✅ {ngay_str} | ĐB:{dac_biet} G1:{giai_nhat} | {len(loto)} lô | Nguồn 3")
                    return {"date":ngay_str,"special":dac_biet,"g1":giai_nhat,"loto":loto,"source":"xoso.me"}
    except Exception as e:
        print(f"⚠️ Nguồn 3 lỗi: {e}")

    print(f"❌ {ngay_str} | TẤT CẢ NGUỒN THẤT BẠI — KHÔNG LƯU SỐ GIẢ!")
    return None
