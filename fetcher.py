# ==========================================================
# FILE: fetcher.py — V10.0 | ✅ 2 NGUỒN API + KIỂM TRA DỮ LIỆU
# Nguồn 1: api.xoso.me | Nguồn 2: ketquaxoso.net/api
# ==========================================================
import requests
from datetime import datetime
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

def kiem_tra_du_lieu(dac_biet, giai_nhat, loto, ngay_str):
    if not dac_biet or len(dac_biet) != 5 or not dac_biet.isdigit():
        print(f"❌ {ngay_str} | Đặc biệt sai: {dac_biet}")
        return False
    if not giai_nhat or len(giai_nhat) != 5 or not giai_nhat.isdigit():
        print(f"❌ {ngay_str} | Giải nhất sai: {giai_nhat}")
        return False
    if not loto or len(loto) < 15:
        print(f"⚠️ {ngay_str} | Ít lô: {len(loto)} — vẫn chấp nhận")
    return True

def lay_ket_qua_xsmb(ngay_str=None):
    if not ngay_str:
        ngay_str = datetime.now().strftime("%d/%m/%Y")
    try:
        d, m, y = ngay_str.split("/")
        d, m = d.zfill(2), m.zfill(2)
        ymd = f"{y}-{m}-{d}"
        print(f"🔍 Lấy dữ liệu: {ngay_str} ({ymd})")
    except Exception as e:
        print(f"❌ Sai định dạng ngày: {ngay_str} — {e}")
        return None

    # === NGUỒN 1: api.xoso.me ===
    try:
        url = f"https://api.xoso.me/xsmb?date={ymd}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            db = str(data.get("dacbiet") or data.get("special", "")).strip()
            g1 = str(data.get("giainhut") or data.get("prize1", "")).strip()
            tat_ca_so = []
            for k, v in data.items():
                if isinstance(v, str) and len(v) == 5 and v.isdigit():
                    tat_ca_so.append(v)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, str) and len(item) == 5 and item.isdigit():
                            tat_ca_so.append(item)
            if db: tat_ca_so.append(db)
            if g1: tat_ca_so.append(g1)
            loto = sorted(list(set([n[-2:] for n in tat_ca_so if len(n) == 5 and n.isdigit()])))
            if kiem_tra_du_lieu(db, g1, loto, ngay_str):
                print(f"✅ Nguồn 1 OK | {ngay_str} | ĐB:{db} G1:{g1} | {len(loto)} lô")
                return {"date":ngay_str,"special":db,"g1":g1,"loto":loto,"source":"api.xoso.me"}
    except Exception as e:
        print(f"⚠️ Nguồn 1 lỗi: {e}")

    # === NGUỒN 2: ketquaxoso.net ===
    try:
        url = f"https://ketquaxoso.net/api/xsmb/{ymd}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            db = str(data.get("dac_biet", "")).strip()
            g1 = str(data.get("giai_nhat", "")).strip()
            loto_raw = data.get("loto", [])
            loto = sorted(list(set([str(x).zfill(2) for x in loto_raw if str(x).isdigit()])))
            if kiem_tra_du_lieu(db, g1, loto, ngay_str):
                print(f"✅ Nguồn 2 OK | {ngay_str} | ĐB:{db} G1:{g1} | {len(loto)} lô")
                return {"date":ngay_str,"special":db,"g1":g1,"loto":loto,"source":"api.ketquaxoso.net"}
    except Exception as e:
        print(f"⚠️ Nguồn 2 lỗi: {e}")

    print(f"❌ TẤT CẢ NGUỒN THẤT BẠI — {ngay_str}")
    return None
