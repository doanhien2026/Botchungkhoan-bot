# ====================== 📊 DỰ ĐOÁN THEO ĐÚNG ĐỊNH DẠNG ======================
def tinh_du_doan():
    data = load_data()
    tong = len(data)
    PHAN_TICH_NGAY = 60  # ✅ Dựa trên 60 ngày như trong ảnh
    
    if tong < 30:
        return f"⚠️ Cần ít nhất 30 ngày dữ liệu. Hiện có {tong} ngày.\n👉 Gõ /lay90 để lấy dữ liệu!"
    
    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    so_ngay = min(PHAN_TICH_NGAY, tong)
    ds = sap_xep[:so_ngay]
    
    # === BƯỚC 1: Thu thập tất cả lô và ngày xuất hiện gần nhất ===
    thong_tin_lo = {}  # { "12": {"lan": 18, "ngay_gan_nhat": 5, "dau_so": []} }
    tat_ca_dau_de = []
    
    for idx, ngay in enumerate(ds):
        kq = data[ngay]
        # Lấy lô
        for lo in kq.get("loto", []):
            if len(lo) == 2 and lo.isdigit():
                if lo not in thong_tin_lo:
                    thong_tin_lo[lo] = {"lan": 0, "ngay_gan_nhat": idx, "dau": lo[0]}
                thong_tin_lo[lo]["lan"] += 1
                thong_tin_lo[lo]["ngay_gan_nhat"] = min(thong_tin_lo[lo]["ngay_gan_nhat"], idx)
        # Lấy đầu số đề
        db = kq.get("special", "")
        if len(db) == 5 and db.isdigit():
            tat_ca_dau_de.append(db[0])
            # Thêm 2 số cuối đề vào lô
            lo_de = db[-2:]
            if lo_de not in thong_tin_lo:
                thong_tin_lo[lo_de] = {"lan": 0, "ngay_gan_nhat": idx, "dau": lo_de[0]}
            thong_tin_lo[lo_de]["lan"] += 1
            thong_tin_lo[lo_de]["ngay_gan_nhat"] = min(thong_tin_lo[lo_de]["ngay_gan_nhat"], idx)
    
    if not thong_tin_lo:
        return "⚠️ Dữ liệu lô trống. Gõ /lay90 trước!"
    
    # === BƯỚC 2: Tính TẦN SUẤT + CHU KỲ NGHỈ → ĐIỂM TỔNG HỢP ===
    ds_diem = []
    for so, info in thong_tin_lo.items():
        tan_suat = info["lan"]
        ty_le = round(tan_suat / so_ngay * 100, 1)
        chu_ky_ngu = info["ngay_gan_nhat"]  # Số ngày chưa về
        # Công thức điểm: tần suất cao + nghỉ lâu → điểm cao
        diem_tong_hop = round(tan_suat * 1.5 + chu_ky_ngu * 2)
        ds_diem.append({
            "so": so,
            "lan": tan_suat,
            "ty_le": ty_le,
            "ngu": chu_ky_ngu,
            "diem": diem_tong_hop
        })
    
    # === BƯỚC 3: Sắp xếp theo ĐIỂM TỔNG HỢP giảm dần ===
    ds_diem.sort(key=lambda x: -x["diem"])
    top3 = ds_diem[:3]
    
    # === BƯỚC 4: 1 CẶP LÔ XIÊN = 2 con cao nhất ===
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3) >= 2 else ["00", "01"]
    
    # === BƯỚC 5: ĐẦU SỐ ĐỀ DỰ KIẾN ===
    dau_de, ty_le_dau = "9", 20.0
    if tat_ca_dau_de:
        from collections import Counter
        d = Counter(tat_ca_dau_de).most_common(1)[0]
        dau_de = d[0]
        ty_le_dau = round(d[1] / len(tat_ca_dau_de) * 100, 1)
    
    # === BƯỚC 6: ĐỊNH DẠNG ĐÚNG NHƯ ẢNH BẠN GỬI ===
    ngay_mai = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    return f"""
📊 **DỰ ĐOÁN KẾT QUẢ – DỰA TRÊN {PHAN_TICH_NGAY} NGÀY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **3 CON LÔ TỶ LỆ CAO NHẤT:**
   (Theo tần suất + chu kỳ nghỉ)
   1. `{top3[0]['so']}` – {top3[0]['lan']} lần, tỷ lệ {top3[0]['ty_le']}%, nghỉ {top3[0]['ngu']} ngày
   2. `{top3[1]['so']}` – {top3[1]['lan']} lần, tỷ lệ {top3[1]['ty_le']}%, nghỉ {top3[1]['ngu']} ngày
   3. `{top3[2]['so']}` – {top3[2]['lan']} lần, tỷ lệ {top3[2]['ty_le']}%, nghỉ {top3[2]['ngu']} ngày

🔄 **1 CẶP LÔ XIÊN:**
   → Kết hợp 2 con cao nhất: `{xien[0]} - {xien[1]}`

🔢 **DỰ KIẾN ĐẦU SỐ ĐỀ:**
   → Đầu số `{dau_de}` – xuất hiện {d[1]} lần → {ty_le_dau}%

🧠 **Cách tính:** Tần suất xuất hiện + số ngày chưa về → điểm tổng hợp cao nhất

⚠️ *Chỉ tham khảo – Chơi có trách nhiệm!*
"""
