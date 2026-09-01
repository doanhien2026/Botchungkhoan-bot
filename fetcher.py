# ==========================================================
# FILE: fetcher.py — V11.0 | ✅ 3 NGUỒN API + DEBUG RÕ RÀNG
# Sửa lỗi: luôn trả None → không lưu được dữ liệu
# ==========================================================
import requests
from datetime import datetime
import time
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

def kiem_tra_du_lieu(dac_biet, giai_nhat, loto, ngay_str):
    """✅ KIỂM TRA DỮ LIỆU TRƯỚC KHI TRẢ VỀ"""
    errors = []
    if not dac_biet or not isinstance(dac_biet, str) or len(dac_biet) != 5 or not dac_biet.isdigit():
        errors.append(f"Đặc biệt sai: '{dac_biet}' (cần 5 chữ số)")
    if not giai_nhat or not isinstance(giai_nhat, str) or len(giai_nhat) != 5 or not giai_nhat.isdigit():
        errors.append(f"Giải nhất sai: '{giai_nhat}' (cần 5 chữ số)")
    if not loto or len(loto) < 10:
        errors.append(f"Ít số lô: {len(loto)} con")
    if errors:
        print(f"⚠️ {ngay_str} | " + " | ".join(errors))
        return False
    return True

def lay_ket_qua_xsmb(ngay_str=None):
    """✅ LẤY KẾT QUẢ — 3 NGUỒN + LOG RÕ MỖI BƯỚC"""
    if not ngay_str:
        ngay_str = datetime.now().strftime("%d/%m/%Y")
    
    # Định dạng ngày: dd/mm/yyyy → yyyy-mm-dd
    try:
        d, m, y = ngay_str.split("/")
        d, m = d.zfill(2), m.zfill(2)
        ymd = f"{y}-{m}-{d}"
        ymd_short = f"{y}{m}{d}"
        print(f"🔍 === Lấy dữ liệu: {ngay_str} | {ymd} ===")
    except Exception as e:
        print(f"❌ Sai định dạng ngày '{ngay_str}': {e}")
        return None

    # ========== ✅ NGUỒN 1: xosodaiphat.com — HTML (đáng tin cậy nhất) ==========
    try:
        url = f"https://xosodaiphat.com/xsmb-{ymd_short}.html"
        print(f"📡 Nguồn 1: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=20)
        
        if resp.status_code == 200:
            html = resp.text
            # Tìm Đặc biệt
            db_match = re.search(r'class="special-prize[^>]*>(\d{5})<', html)
            g1_match = re.search(r'class="prize-1[^>]*>(\d{5})<', html)
            db = db_match.group(1) if db_match else ""
            g1 = g1_match.group(1) if g1_match else ""
            
            # Lấy tất cả số 5 chữ số → trích lô
            all_5digit = re.findall(r'>(\d{5})<', html)
            loto = sorted(list(set([n[-2:] for n in all_5digit if len(n)==5 and n.isdigit()])))
            
            if kiem_tra_du_lieu(db, g1, loto, ngay_str):
                print(f"✅ ✅ NGUỒN 1 THÀNH CÔNG | {ngay_str} | ĐB:{db} G1:{g1} | {len(loto)} lô")
                return {
                    "date": ngay_str,
                    "special": db,
                    "g1": g1,
                    "loto": loto,
                    "source": "xosodaiphat.com"
                }
        else:
            print(f"⚠️ Nguồn 1 lỗi HTTP: {resp.status_code}")
    except Exception as e:
        print(f"⚠️ Nguồn 1 lỗi: {str(e)[:100]}")

    # ========== ✅ NGUỒN 2: xsmb.vn API ==========
    try:
        url = f"https://xsmb.vn/api/result?date={ymd}"
        print(f"📡 Nguồn 2: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            db = str(data.get("dacbiet", "")).strip()
            g1 = str(data.get("giai_nhat", "")).strip()
            loto_list = data.get("loto", [])
            loto = sorted(list(set([str(x).zfill(2) for x in loto_list if str(x).isdigit()])))
            
            if kiem_tra_du_lieu(db, g1, loto, ngay_str):
                print(f"✅ ✅ NGUỒN 2 THÀNH CÔNG | {ngay_str} | ĐB:{db} G1:{g1} | {len(loto)} lô")
                return {
                    "date": ngay_str,
                    "special": db,
                    "g1": g1,
                    "loto": loto,
                    "source": "xsmb.vn"
                }
        else:
            print(f"⚠️ Nguồn 2 lỗi HTTP: {resp.status_code}")
    except Exception as e:
        print(f"⚠️ Nguồn 2 lỗi: {str(e)[:100]}")

    # ========== ✅ NGUỒN 3: xosomienbac.net — dự phòng cuối ==========
    try:
        url = f"https://xosomienbac.net/ngay/{ymd}"
        print(f"📡 Nguồn 3: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=20)
        
        if resp.status_code == 200:
            html = resp.text
            db_match = re.search(r'Đặc biệt.*?(\d{5})', html)
            g1_match = re.search(r'Giải nhất.*?(\d{5})', html)
            db = db_match.group(1) if db_match else ""
            g1 = g1_match.group(1) if g1_match else ""
            all_5digit = re.findall(r'(\d{5})', html)
            loto = sorted(list(set([n[-2:] for n in all_5digit if len(n)==5 and n.isdigit()])))
            
            if kiem_tra_du_lieu(db, g1, loto, ngay_str):
                print(f"✅ ✅ NGUỒN 3 THÀNH CÔNG | {ngay_str} | ĐB:{db} G1:{g1} | {len(loto)} lô")
                return {
                    "date": ngay_str,
                    "special": db,
                    "g1": g1,
                    "loto": loto,
                    "source": "xosomienbac.net"
                }
        else:
            print(f"⚠️ Nguồn 3 lỗi HTTP: {resp.status_code}")
    except Exception as e:
        print(f"⚠️ Nguồn 3 lỗi: {str(e)[:100]}")

    # ========== ❌ TẤT CẢ THẤT BẠI ==========
    print(f"❌ ❌ TẤT CẢ 3 NGUỒN ĐỀU THẤT BẠI — {ngay_str}")
    print(f"💡 Lý do: Ngày chưa có kết quả (chưa đến 18:30), hoặc API tạm bảo trì")
    return None
