# ==========================================================
# FILE: fetcher.py — V9.0 | ✅ 2 NGUỒN API CHÍNH THỨC + KIỂM TRA DỮ LIỆU
# Nguồn 1: xsmb.vn (API chính) | Nguồn 2: xosomienbac.org (dự phòng)
# ==========================================================
import requests
from datetime import datetime
import re
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

def kiem_tra_du_lieu(dac_biet, giai_nhat, loto, ngay_str):
    """✅ KIỂM TRA DỮ LIỆU TRƯỚC KHI TRẢ VỀ — KHÔNG LƯU SAI!"""
    errors = []
    if not dac_biet or not isinstance(dac_biet, str) or len(dac_biet) != 5 or not dac_biet.isdigit():
        errors.append(f"Đặc biệt không hợp lệ: '{dac_biet}' (phải 5 chữ số)")
    if not giai_nhat or not isinstance(giai_nhat, str) or len(giai_nhat) != 5 or not giai_nhat.isdigit():
        errors.append(f"Giải nhất không hợp lệ: '{giai_nhat}' (phải 5 chữ số)")
    if not loto or len(loto) < 15:
        errors.append(f"Ít số lô bất thường: {len(loto)} con")
    if errors:
        print(f"❌ {ngay_str} | " + " | ".join(errors))
        return False
    return True

def lay_ket_qua_xsmb(ngay_str=None):
    """✅ LẤY KẾT QUẢ XSMB — 2 NGUỒN API + KIỂM TRA DỮ LIỆU"""
    if not ngay_str:
        ngay_str = datetime.now().strftime("%d/%m/%Y")
    
    # Định dạng ngày: dd/mm/yyyy → tách ra
    try:
        d, m, y = ngay_str.split("/")
        d, m = d.zfill(2), m.zfill(2)
        date_obj = datetime(int(y), int(m), int(d))
        ymd = f"{y}-{m}-{d}"
        print(f"🔍 Đang lấy dữ liệu ngày: {ngay_str} ({ymd})")
    except Exception as e:
        print(f"❌ Sai định dạng ngày '{ngay_str}': {e}")
        return None

    # ========== ✅ NGUỒN 1: API XOSO.ME — ỔN ĐỊNH NHẤT ==========
    try:
        url = f"https://api.xoso.me/xsmb?date={ymd}"
        print(f"📡 Gọi Nguồn 1: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Nguồn 1 trả dữ liệu thành công")
            
            # Lấy Đặc biệt
            dac_biet = ""
            if "dacbiet" in data:
                dac_biet = str(data["dacbiet"]).strip()
            elif "special" in data:
                dac_biet = str(data["special"]).strip()
            elif "giai_db" in data:
                dac_biet = str(data["giai_db"]).strip()
            
            # Lấy Giải nhất
            giai_nhat = ""
            if "giainhut" in data:
                giai_nhat = str(data["giainhut"]).strip()
            elif "prize1" in data:
                giai_nhat = str(data["prize1"]).strip()
            elif "giai_nhat" in data:
                giai_nhat = str(data["giai_nhat"]).strip()
            
            # Lấy tất cả số 5 chữ số → trích 2 số cuối làm lô
            tat_ca_so = []
            for key in data:
                val = data[key]
                if isinstance(val, str) and len(val) == 5 and val.isdigit():
                    tat_ca_so.append(val)
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, str) and len(item) == 5 and item.isdigit():
                            tat_ca_so.append(item)
            
            # Thêm ĐB và G1 vào danh sách
            if dac_biet and len(dac_biet) == 5:
                tat_ca_so.append(dac_biet)
            if giai_nhat and len(giai_nhat) == 5:
                tat_ca_so.append(giai_nhat)
            
            # Lấy 2 số cuối, loại trùng, sắp xếp
            loto = sorted(list(set([n[-2:] for n in tat_ca_so if len(n) == 5 and n.isdigit()])))
            
            # Kiểm tra trước khi trả về
            if kiem_tra_du_lieu(dac_biet, giai_nhat, loto, ngay_str):
                print(f"✅ ✅ THÀNH CÔNG [Nguồn 1] | {ngay_str} | ĐB:{dac_biet} | G1:{giai_nhat} | {len(loto)} lô")
                return {
                    "date": ngay_str,
                    "special": dac_biet,
                    "g1": giai_nhat,
                    "loto": loto,
                    "source": "api.xoso.me"
                }
        else:
            print(f"⚠️ Nguồn 1 lỗi: HTTP {resp.status_code}")
    except Exception as e:
        print(f"⚠️ Nguồn 1 ngoại lệ: {str(e)[:80]}")

    # ========== ✅ NGUỒN 2: API KETQUAXOSO — DỰ PHÒNG ==========
    try:
        url = f"https://ketquaxoso.net/api/xsmb/{ymd}"
        print(f"📡 Gọi Nguồn 2: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Nguồn 2 trả dữ liệu thành công")
            
            dac_biet = str(data.get("dac_biet", "")).strip()
            giai_nhat = str(data.get("giai_nhat", "")).strip()
            loto_raw = data.get("loto", [])
            loto = sorted(list(set([str(x).zfill(2) for x in loto_raw if str(x).isdigit()])))
            
            if kiem_tra_du_lieu(dac_biet, giai_nhat, loto, ngay_str):
                print(f"✅ ✅ THÀNH CÔNG [Nguồn 2] | {ngay_str} | ĐB:{dac_biet} | G1:{giai_nhat} | {len(loto)} lô")
                return {
                    "date": ngay_str,
                    "special": dac_biet,
                    "g1": giai_nhat,
                    "loto": loto,
                    "source": "api.ketquaxoso.net"
                }
        else:
            print(f"⚠️ Nguồn 2 lỗi: HTTP {resp.status_code}")
    except Exception as e:
        print(f"⚠️ Nguồn 2 ngoại lệ: {str(e)[:80]}")

    # ========== ❌ CẢ 2 NGUỒN ĐỀU THẤT BẠI ==========
    print(f"❌ ❌ TẤT CẢ NGUỒN ĐỀU THẤT BẠI NGÀY: {ngay_str}")
    print(f"💡 Lý do có thể: Ngày chưa có kết quả (chưa đến 18:30), hoặc API tạm bảo trì")
    return None
