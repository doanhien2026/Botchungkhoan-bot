# ==========================================================
# fetcher.py — V12.0 | ĐƠN GIẢN + 2 NGUỒN CHÍNH THỨC
# ==========================================================
import requests
from datetime import datetime
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def lay_ket_qua_xsmb(ngay_str=None):
    """Lấy kết quả XSMB — trả dict hoặc None"""
    if not ngay_str:
        ngay_str = datetime.now().strftime("%d/%m/%Y")
    
    try:
        d, m, y = ngay_str.split("/")
        d, m = d.zfill(2), m.zfill(2)
        ymd = f"{y}-{m}-{d}"
        ymd_short = f"{y}{m}{d}"
        print(f"🔍 Lấy: {ngay_str} | {ymd}")
    except Exception as e:
        print(f"❌ Sai định dạng ngày: {ngay_str} — {e}")
        return None

    # === NGUỒN 1: XOSO.ME API ===
    try:
        url = f"https://api.xoso.me/xsmb?date={ymd}"
        print(f"📡 Nguồn 1: {url}")
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
            
            if len(db) == 5 and db.isdigit() and len(g1) == 5 and g1.isdigit() and len(loto) >= 10:
                print(f"✅ ✅ NGUỒN 1 OK | {ngay_str} | ĐB:{db} G1:{g1} | {len(loto)} lô")
                return {"date": ngay_str, "special": db, "g1": g1, "loto": loto, "source": "api.xoso.me"}
            else:
                print(f"⚠️ Nguồn 1 dữ liệu thiếu: ĐB={db}, G1={g1}, lô={len(loto)}")
        else:
            print(f"⚠️ Nguồn 1 lỗi HTTP: {resp.status_code}")
    except Exception as e:
        print(f"⚠️ Nguồn 1 lỗi: {str(e)[:80]}")

    # === NGUỒN 2: XOSODAIPHAT (HTML) ===
    try:
        url = f"https://xosodaiphat.com/xsmb-{ymd_short}.html"
        print(f"📡 Nguồn 2: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=20)
        
        if resp.status_code == 200:
            html = resp.text
            db_match = re.search(r'class="special-prize[^>]*>(\d{5})<', html)
            g1_match = re.search(r'class="prize-1[^>]*>(\d{5})<', html)
            db = db_match.group(1) if db_match else ""
            g1 = g1_match.group(1) if g1_match else ""
            all_5digit = re.findall(r'>(\d{5})<', html)
            loto = sorted(list(set([n[-2:] for n in all_5digit if len(n)==5 and n.isdigit()])))
            
            if len(db) == 5 and db.isdigit() and len(g1) == 5 and g1.isdigit() and len(loto) >= 10:
                print(f"✅ ✅ NGUỒN 2 OK | {ngay_str} | ĐB:{db} G1:{g1} | {len(loto)} lô")
                return {"date": ngay_str, "special": db, "g1": g1, "loto": loto, "source": "xosodaiphat.com"}
            else:
                print(f"⚠️ Nguồn 2 dữ liệu thiếu: ĐB={db}, G1={g1}, lô={len(loto)}")
        else:
            print(f"⚠️ Nguồn 2 lỗi HTTP: {resp.status_code}")
    except Exception as e:
        print(f"⚠️ Nguồn 2 lỗi: {str(e)[:80]}")

    print(f"❌ TẤT CẢ NGUỒN THẤT BẠI — {ngay_str}")
    return None
