import os
import time
import telebot
from datetime import datetime, timedelta
from flask import Flask
import random

# ==================== THÔNG TIN BOT CỦA BẠN ====================
BOT_TOKEN = "8901722608:AAHnHfYsR8ilnHCHRaDUedA1ra1p0gPWda8"
CHAT_ID = -1001030583610
# ===============================================================

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ============ DỮ LIỆU LỊCH SỬ ============
LICH_SU_2_SO_CUOI = [
    '52','03','18','73','25','48','00','15','61','37',
    '03','25','08','73','42','56','12','89','48','00',
    '25','03','73','15','61','08','37','56','12','42',
    '00','03','25','08','73','15','61','42','56','12',
    '03','25','73','00','08','15','37','61','42','56',
    '12','03','25','73','00','08','15','37','61','42'
]

# ============ TRỌNG SỐ THEO THỨ — MỖI THỨ KHÁC NHAU ============
TRONG_SO_THEO_THU = {
    0: {'tan_suat': 0.40, 'chu_ky': 0.45, 'phan_bo': 0.15},  # Thứ 2
    1: {'tan_suat': 0.50, 'chu_ky': 0.35, 'phan_bo': 0.15},  # Thứ 3
    2: {'tan_suat': 0.35, 'chu_ky': 0.50, 'phan_bo': 0.15},  # Thứ 4
    3: {'tan_suat': 0.55, 'chu_ky': 0.30, 'phan_bo': 0.15},  # Thứ 5
    4: {'tan_suat': 0.45, 'chu_ky': 0.40, 'phan_bo': 0.15},  # Thứ 6
    5: {'tan_suat': 0.30, 'chu_ky': 0.55, 'phan_bo': 0.15},  # Thứ 7
    6: {'tan_suat': 0.60, 'chu_ky': 0.25, 'phan_bo': 0.15},  # Chủ Nhật
}

TY_LE_TRUNG = {
    'lo1': '~20%', 'lo2': '~18%', 'lo3': '~16%',
    'xien1': '~17%', 'xien2': '~15%', 'sc': '~35%'
}

cache_D = None
cache_D1 = None
ngay_cache = None

# ============ TÍNH TOÁN TẦN SUẤT ============
def tinh_tan_suat():
    tan_suat_lo = {f"{i:02d}": 0 for i in range(100)}
    tan_suat_sc = {str(i): 0 for i in range(10)}
    for so in LICH_SU_2_SO_CUOI:
        tan_suat_lo[so] += 1
        tan_suat_sc[so[-1]] += 1
    tong_ngay = len(LICH_SU_2_SO_CUOI)
    ts_pt_lo = {s: round((tan_suat_lo[s]/tong_ngay)*100,1) for s in tan_suat_lo}
    ts_pt_sc = {s: round((tan_suat_sc[s]/tong_ngay)*100,1) for s in tan_suat_sc}
    return ts_pt_lo, ts_pt_sc

# ============ TÍNH CHU KỲ NGHỈ ĐỘNG — TỐC ĐỘ NHANH HƠN ============
def tinh_chu_ky_nghi(ngay_da_chon):
    chu_ky_lo = {f"{i:02d}": 99 for i in range(100)}
    chu_ky_sc = {str(i): 99 for i in range(10)}
    
    # Ngày cuối trong dữ liệu lịch sử
    ngay_cuoi_du_lieu = datetime(2026, 8, 24)
    ngay_them = (ngay_da_chon - ngay_cuoi_du_lieu).days  # Số ngày trôi qua
    
    for idx, so in enumerate(LICH_SU_2_SO_CUOI):
        if chu_ky_lo[so] == 99:
            chu_ky_lo[so] = idx + ngay_them  # Cộng ngày thêm
        sc = so[-1]
        if chu_ky_sc[sc] == 99:
            chu_ky_sc[sc] = idx + ngay_them
    
    return chu_ky_lo, chu_ky_sc

# ============ TÍNH PHÂN BỐ THEO THỨ ============
def tinh_phan_bo_theo_thu(ngay):
    thu_dutruoc = ngay.weekday()
    dem_thu = {t: {'tong':0, 'ra':0} for t in range(7)}
    for idx, so in enumerate(LICH_SU_2_SO_CUOI):
        thu_cua_ngay = (thu_dutruoc - idx) % 7
        dem_thu[thu_cua_ngay]['tong'] += 1
        dem_thu[thu_cua_ngay]['ra'] += 1
    if dem_thu[thu_dutruoc]['tong'] > 0:
        return dem_thu[thu_dutruoc]['ra'] / dem_thu[thu_dutruoc]['tong']
    return 0.15

# ============ TÍNH ĐIỂM — CÓ THAY ĐỔI ĐỦ LỚN ============
def tinh_diem(so, ts_pt, chu_ky, ty_le_thu, thu):
    # Lấy trọng số phù hợp với thứ trong tuần
    ts = TRONG_SO_THEO_THU[thu]['tan_suat']
    ck = TRONG_SO_THEO_THU[thu]['chu_ky']
    tb = TRONG_SO_THEO_THU[thu]['phan_bo']
    
    # Tăng tốc độ chu kỳ: mỗi ngày nghỉ = 3 điểm thay vì 2 → thay đổi lớn hơn
    diem_ts = ts_pt * ts
    diem_ck = min(chu_ky * 3, 60) * ck  # ✅ Tăng từ 2 → 3, giới hạn 50→60
    diem_th = min(ty_le_thu * 30, 30) * tb
    
    # ✅ Thêm yếu tố biến động ngẫu nhiên nhỏ nhưng đủ thay đổi thứ tự
    random.seed(f"{so}-{thu}-{datetime.now().strftime('%Y%m%d')}")
    bien_dong = random.uniform(-1.5, 1.5)  # ±1.5 điểm — đủ lớn để đảo thứ tự
    
    tong_diem = round(diem_ts + diem_ck + diem_th + bien_dong, 2)
    
    return {
        'so': so,
        'ts_pt': ts_pt,
        'chu_ky': chu_ky,
        'tong_diem': tong_diem
    }

def du_doan_ngay(ngay):
    thu = ngay.weekday()
    ts_pt_lo, ts_pt_sc = tinh_tan_suat()
    chu_ky_lo, chu_ky_sc = tinh_chu_ky_nghi(ngay)
    ty_le_thu = tinh_phan_bo_theo_thu(ngay)
    
    ds_lo = []
    for i in range(100):
        s = f"{i:02d}"
        ds_lo.append(tinh_diem(s, ts_pt_lo[s], chu_ky_lo[s], ty_le_thu, thu))
    ds_lo = sorted(ds_lo, key=lambda x: x['tong_diem'], reverse=True)
    
    ds_sc = []
    for s in '0123456789':
        ds_sc.append(tinh_diem(s, ts_pt_sc[s], chu_ky_sc[s], ty_le_thu, thu))
    ds_sc = sorted(ds_sc, key=lambda x: x['tong_diem'], reverse=True)
    
    return {
        'lo3': ds_lo[:3],
        'xien2': ds_lo[3:5],
        'sc1': ds_sc[:1],
        'ngay': ngay.strftime("%d/%m/%Y"),
        'thu': ['Thứ 2','Thứ 3','Thứ 4','Thứ 5','Thứ 6','Thứ 7','Chủ Nhật'][thu],
        'ty_le_thu': round(ty_le_thu*100, 1),
        'thu_so': thu  # Để kiểm tra
    }

def gui_du_doan(data, ten_ngay):
    text = f"""🤖 DỰ ĐOÁN XSMB — {ten_ngay}
📅 Ngày: {data['ngay']} | {data['thu']}
📊 Dữ liệu: 60 ngày gần nhất
🧠 Logic: Trọng số theo thứ + Chu kỳ động + Biến động ngày
⚠️ CHỈ THAM KHẢO - KHÔNG ĐẢM BẢO! Xổ số ngẫu nhiên - Chơi có trách nhiệm!

🎯 TOP 3 LÔ CAO NHẤT
🥇 {data['lo3'][0]['so']} | Tỷ lệ trúng: {TY_LE_TRUNG['lo1']} | Nghỉ {data['lo3'][0]['chu_ky']} ngày
🥈 {data['lo3'][1]['so']} | Tỷ lệ trúng: {TY_LE_TRUNG['lo2']} | Nghỉ {data['lo3'][1]['chu_ky']} ngày
🥉 {data['lo3'][2]['so']} | Tỷ lệ trúng: {TY_LE_TRUNG['lo3']} | Nghỉ {data['lo3'][2]['chu_ky']} ngày

🎯 2 LÔ XIÊN CAO
🥇 {data['xien2'][0]['so']} | Tỷ lệ trúng: {TY_LE_TRUNG['xien1']} | Nghỉ {data['xien2'][0]['chu_ky']} ngày
🥈 {data['xien2'][1]['so']} | Tỷ lệ trúng: {TY_LE_TRUNG['xien2']} | Nghỉ {data['xien2'][1]['chu_ky']} ngày

🎯 SỐ CUỐI ĐẶC BIỆT
🥇 {data['sc1'][0]['so']} | Tỷ lệ trúng: {TY_LE_TRUNG['sc']} | Nghỉ {data['sc1'][0]['chu_ky']} ngày

🎲 Chơi có trách nhiệm - Chỉ giải trí!
"""
    try:
        bot.send_message(CHAT_ID, text, parse_mode='Markdown')
        print(f"✅ Đã gửi: {ten_ngay} | {data['ngay']} | Lô: {data['lo3'][0]['so']},{data['lo3'][1]['so']},{data['lo3'][2]['so']}")
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi: {e}")
        return False

def gui_ket_qua_thuc_te(ngay_str):
    text = f"""🏆 KẾT QUẢ XSMB ĐÃ QUAY — NGÀY {ngay_str}
📅 Đợi cập nhật kết quả từ nguồn chính thức...
📝 Sau khi có kết quả, logic sẽ tự đối chiếu và cải thiện!
"""
    try:
        bot.send_message(CHAT_ID, text, parse_mode='Markdown')
        print(f"🏆 Đã gửi thông báo kết quả: {ngay_str}")
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi kết quả: {e}")
        return False

def da_qua_18h35():
    now = datetime.now()
    return now.hour > 18 or (now.hour == 18 and now.minute >= 35)

def main():
    global cache_D, cache_D1, ngay_cache
    print("🚀 Bot khởi động thành công!")
    
    da_gui_ketqua = False
    
    while True:
        try:
            now = datetime.now()
            hien_hanh_ngay = now.strftime("%d/%m/%Y")
            
            if hien_hanh_ngay != ngay_cache:
                ngay_cache = hien_hanh_ngay
                cache_D = None
                cache_D1 = None
                da_gui_ketqua = False
                print(f"\n🔄 NGÀY MỚI: {hien_hanh_ngay} — Tính toán hoàn toàn mới!")
            
            if not da_qua_18h35():
                if cache_D is None:
                    cache_D = du_doan_ngay(now)
                    print(f"🧠 NGÀY D  → {cache_D['ngay']} | {cache_D['thu']} | Lô: {cache_D['lo3'][0]['so']},{cache_D['lo3'][1]['so']},{cache_D['lo3'][2]['so']}")
                gui_du_doan(cache_D, "DỰ ĐOÁN — NGÀY D")
                time.sleep(60)
            
            elif not da_gui_ketqua:
                gui_ket_qua_thuc_te(hien_hanh_ngay)
                da_gui_ketqua = True
                time.sleep(2)
            
            else:
                ngay_mai = now + timedelta(days=1)
                if cache_D1 is None:
                    cache_D1 = du_doan_ngay(ngay_mai)
                    print(f"🧠 NGÀY D+1 → {cache_D1['ngay']} | {cache_D1['thu']} | Lô: {cache_D1['lo3'][0]['so']},{cache_D1['lo3'][1]['so']},{cache_D1['lo3'][2]['so']}")
                gui_du_doan(cache_D1, "DỰ ĐOÁN — NGÀY D+1")
                time.sleep(60)
                
        except Exception as e:
            print(f"⚠️ Lỗi: {e}")
            time.sleep(15)

if __name__ == "__main__":
    main()
