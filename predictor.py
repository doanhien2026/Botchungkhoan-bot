# ==========================================================
# predictor.py — PHÂN TÍCH 90 NGÀY → DỰ ĐOÁN + TỶ LỆ
# ==========================================================
from datetime import datetime, timedelta
from collections import Counter
from data_manager import load_data
from config import ANALYSIS_DAYS

def tinh_du_doan():
    data = load_data()
    tong = len(data)
    if tong < 30:
        return f"⚠️ Cần ít nhất 30 ngày dữ liệu. Hiện có {tong} ngày.\n👉 Gõ /lay90 để lấy dữ liệu!"
    
    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    so_ngay = min(ANALYSIS_DAYS, tong)
    ds = sap_xep[:so_ngay]
    
    tat_ca_lo, tat_ca_dau = [], []
    for ngay in ds:
        kq = data[ngay]
        for lo in kq.get("loto", []):
            if len(lo) == 2 and lo.isdigit():
                tat_ca_lo.append(lo)
        db = kq.get("special", "")
        if len(db) == 5 and db.isdigit():
            tat_ca_lo.append(db[-2:])
            tat_ca_dau.append(db[0])
    
    if not tat_ca_lo:
        return "⚠️ Dữ liệu lô trống. Gõ /lay90 trước!"
    
    dem_lo = Counter(tat_ca_lo)
    ds_lo = [{"so": s, "lan": c, "ty_le": round(c / so_ngay * 100, 1)} for s, c in dem_lo.items()]
    ds_lo.sort(key=lambda x: -x["ty_le"])
    top3 = ds_lo[:3]
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3) >= 2 else ["00", "01"]
    
    dau_de, ty_le_dau = "9", 10.0
    if tat_ca_dau:
        d = Counter(tat_ca_dau).most_common(1)[0]
        dau_de, ty_le_dau = d[0], round(d[1] / len(tat_ca_dau) * 100, 1)
    
    ngay_mai = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    return f"""
📊 *DỰ ĐOÁN NGÀY MAI (D+1): {ngay_mai}*
📈 Phân tích: {so_ngay} ngày dữ liệu THẬT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 *3 CON LÔ TỶ LỆ CAO NHẤT:*
   1 • `{top3[0]['so']}` → {top3[0]['lan']} lần | Tỷ lệ: {top3[0]['ty_le']}%
   2 • `{top3[1]['so']}` → {top3[1]['lan']} lần | Tỷ lệ: {top3[1]['ty_le']}%
   3 • `{top3[2]['so']}` → {top3[2]['lan']} lần | Tỷ lệ: {top3[2]['ty_le']}%

🔀 *CẶP LÔ XIÊN:*
   → `{xien[0]}` + `{xien[1]}`

🔢 *ĐẦU SỐ ĐỀ DỰ KIẾN:*
   → `{dau_de}` | Tỷ lệ: {ty_le_dau}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Dữ liệu từ nguồn thật — Chỉ tham khảo!
"""
