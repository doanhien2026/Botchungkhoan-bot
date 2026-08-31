# ==========================================================
# FILE: fetcher.py — LẤY KẾT QUẢ XSMB THẬT TỪ NGUỒN CHÍNH THỨC
# ✅ Không bịa đặt số liệu nữa!
# ==========================================================
import requests
from datetime import datetime, timedelta
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

def lay_ket_qua_xsmb_th ngay(ngay_str=None):
    """Lấy kết quả XSMB THẬT từ nguồn API chính thống"""
    if not ngay_str:
        ngay_str = datetime.now().strftime("%d/%m/%Y")
    
    # Chuyển định dạng: dd/mm/yyyy → yyyy-mm-dd cho API
    try:
        d, m, y = ngay_str.split("/")
        date_obj = datetime(int(y), int(m), int(d))
        yyyymmdd = date_obj.strftime("%Y%m%d")
    except:
        return None
    
    # Nguồn 1: API xosomobile.vn
    try:
        url = f"https://api.xosomobile.vn/api/v1/result?date={yyyymmdd}&province=MB"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success" and "data" in data:
                kq = data["data"]
                dac_biet = str(kq.get("special", "")).strip()
                giai_nhat = str(kq.get("first", "")).strip()
                loto = []
                # Lấy 2 số cuối tất cả giải
                for key in ["special", "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth"]:
                    val = kq.get(key, "")
                    if isinstance(val, str) and len(val)>=2:
                        loto.append(val[-2:])
                    elif isinstance(val, list):
                        for v in val:
                            if isinstance(v, str) and len(v)>=2:
                                loto.append(v[-2:])
                loto = sorted(list(set([x.zfill(2) for x in loto if x.isdigit() and len(x)==2])))
                return {
                    "date": ngay_str,
                    "special": dac_biet,
                    "g1": giai_nhat,
                    "loto": loto,
                    "source": "xosomobile.vn"
                }
    except Exception as e:
        print(f"⚠️ Nguồn 1 lỗi: {e}")
    
    # Nguồn 2: XS Daiphat (dự phòng)
    try:
        url = f"https://xosodaiphat.com/xsmb-{d}-{m}-{y}.html"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200 and "Đặc biệt" in resp.text:
            # Tìm số đặc biệt 5 chữ số
            db_match = re.search(r'Đặc biệt[^>]*>(\d{5})<', resp.text)
            g1_match = re.search(r'Giải nhất[^>]*>(\d{5})<', resp.text)
            if db_match and g1_match:
                dac_biet = db_match.group(1)
                giai_nhat = g1_match.group(1)
                # Lấy lô 2 số cuối
                loto = []
                numbers = re.findall(r'>(\d{2})<', resp.text)
                loto = sorted(list(set([n.zfill(2) for n in numbers if n.isdigit() and len(n)==2])))
                return {
                    "date": ngay_str,
                    "special": dac_biet,
                    "g1": giai_nhat,
                    "loto": loto,
                    "source": "xosodaiphat.com"
                }
    except Exception as e:
        print(f"⚠️ Nguồn 2 lỗi: {e}")
    
    return None

def kiem_tra_90_ngay():
    """Kiểm tra & lấy 90 ngày kết quả THẬT"""
    print("🚀 ĐANG LẤY KẾT QUẢ THẬT 90 NGÀY...")
    today = datetime.now()
    dem_thuc = 0
    dem_that_bai = 0
    for offset in range(1, 91):
        target = today - timedelta(days=offset)
        ngay_str = target.strftime("%d/%m/%Y")
        kq = lay_ket_qua_xsmb_th ngay(ngay_str)
        if kq:
            dem_thuc += 1
            print(f"✅ {ngay_str} | ĐB: {kq['special']} | Nguồn: {kq['source']}")
        else:
            dem_that_bai += 1
            print(f"⚠️ {ngay_str} | KHÔNG LẤY ĐƯỢC")
    print(f"\n✅ XONG! Lấy được {dem_thuc}/{90} ngày thật | Thất bại: {dem_that_bai}")
    return dem_thuc
