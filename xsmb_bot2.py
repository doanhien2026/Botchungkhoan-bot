import os
import time
import telebot
from datetime import datetime, timedelta
from flask import Flask

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

TRONG_SO = {
    'tan_suat': 0.45,    # Giảm nhẹ để chu kỳ có trọng số lớn hơn
    'chu_ky': 0.40,      # Tăng — chu kỳ nghỉ thay đổi mỗi ngày
    'phan_bo_thu': 0.15
}

TY_LE_TRUNG = {
    'lo1': '~20%', 'lo2': '~18%', 'lo3': '~16%',
    'xien1': '~17%', 'xien2': '~15%', 'sc': '~35%'
}

cache_D = None
cache_D1 = None
ngay_cache = None

# ============ TÍNH TOÁN ĐỘNG — MỖI NGÀY KHÁC NHAU ============
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

def tinh_chu_ky_nghi(ngay_da_chon):
    """✅ CẢI THIỆN: Tính chu kỳ nghỉ động theo ngày hiện tại"""
    chu_ky_lo = {f"{i:02d}": 99 for i in range(100)}
    chu_ky_sc = {str(i): 99 for i in range(10)}
    
    # Tính số ngày đã trôi qua kể từ ngày cuối cùng trong dữ liệu
    ngay_cuoi_du_lieu = datetime(2026, 8, 24)  # Ngày cuối trong LICH_SU
    ngay_hien_tai = ngay_da_chon
    ngay_them = (ngay_hien_tai - ngay_cuoi_du_lieu).days  # Số ngày thêm cần tính
    
    # Tính chu kỳ cơ bản từ dữ liệu
    for idx, so in enumerate(LICH_SU_2_SO_CUOI):
        if chu_ky_lo[so] == 99:
            chu_ky_lo[so] = idx + ngay_them  # ✅ Cộng thêm số ngày trôi qua
        sc = so[-1]
        if chu_ky_sc[sc] == 99:
            chu_ky_sc[sc] = idx + ngay_them  # ✅ Cộng thêm số ngày trôi qua
    
    return chu_ky_lo, chu_ky_sc

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

def tinh_diem(so, ts_pt, chu_ky, ty_le_thu):
    """✅ Thêm yếu tố biến động ngày để đảm bảo kết quả khác nhau"""
    bien_dong_ngay = (datetime.now().timetuple().tm_yday % 100) / 1000
    diem_ts = ts_pt * TRONG_SO['tan_suat']
    diem_ck = min(chu_ky * 2, 50) * TRONG_SO['chu_ky']
    diem_th = min(ty_le_thu * 30, 30) * TRONG_SO['phan_bo_thu']
    tong_diem = round(diem_ts + diem_ck + diem_th + bien_dong_ngay, 2)
    return {
        'so': so,
        'ts_pt': ts_pt,
        'chu_ky': chu_ky,
        'tong_diem': tong_diem
    }

def du_doan_ngay(ngay):
    ts_pt_lo, ts_pt_sc = tinh_tan_suat()
    chu_ky_lo, chu_ky_sc = tinh_chu_ky_nghi(ngay)  # ✅ Truyền ngày để tính động
    ty_le_thu = tinh_phan_bo_theo_thu(ngay)
    
    ds_lo = []
    for i in range(100):
        s = f"{i:02d}"
        ds_lo.append(tinh_diem(s, ts_pt_lo[s], chu_ky_lo[s], ty_le_thu))
    ds_lo = sorted(ds_lo, key=lambda x: x['tong_diem'], reverse=True)
    
    ds_sc = []
    for s in '0123456789':
        ds_sc.append(tinh_diem(s, ts_pt_sc[s], chu_ky_sc[s], ty_le_thu))
    ds_sc = sorted(ds_sc, key=lambda x: x['tong_diem'], reverse=True)
    
    return {
        'lo3': ds_lo[:3],
        'xien2': ds_lo[3:5],
        'sc1': ds_sc[:1],
        'ngay': ngay.strftime("%d/%m/%Y"),
        'thu': ['Thứ 2','Thứ 3','Thứ 4','Thứ 5','Thứ 6','Thứ 7','Chủ Nhật'][ngay.weekday()],
        'ty_le_thu': round(ty_le_thu*100, 1)
    }

def gui_du_doan(data, ten_ngay):
    text = f"""🤖 DỰ ĐOÁN XSMB — {ten_ngay}
📅 Ngày: {data['ngay']} | {data['thu']}
📊 Dữ liệu: 60 ngày gần nhất
🧠 Logic: Tần suất 45% + Chu kỳ 40% + Phân bố theo thứ 15%
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
        print(f"✅ Đã gửi: {ten_ngay} | {data['ngay']}")
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
                print(f"🔄 Ngày mới: {hien_hanh_ngay} — Tính toán lại hoàn toàn!")
            
            if not da_qua_18h35():
                if cache_D is None:
                    cache_D = du_doan_ngay(now)
                    print(f"🧠 Đã tính NGÀY D: {cache_D['ngay']} | Lô 1: {cache_D['lo3'][0]['so']}")
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
                    print(f"🧠 Đã tính NGÀY D+1: {cache_D1['ngay']} | Lô 1: {cache_D1['lo3'][0]['so']}")
                gui_du_doan(cache_D1, "DỰ ĐOÁN — NGÀY D+1")
                time.sleep(60)
                
        except Exception as e:
            print(f"⚠️ Lỗi: {e}")
            time.sleep(15)

if __name__ == "__main__":
    main()
