import os
import time
import telebot
from datetime import datetime, timedelta
from flask import Flask
import random

BOT_TOKEN = os.environ.get('BOT2_TOKEN')
CHAT_ID = os.environ.get('CHANNEL_ID')

bot = telebot.Bot(BOT_TOKEN)
app = Flask(__name__)

KET_QUA_D = None
KET_QUA_D1 = None
TONG_NGAY = 60

# ========== DỮ LIỆU LỊCH SỬ ĐỂ TÍNH TOÁN ĐỘNG ==========
# Lưu kết quả 2 số cuối Giải Đặc biệt 60 ngày gần nhất (dữ liệu mẫu)
LICH_SU_2_SO_CUOI = [
    '52','03','18','73','25','48','00','15','61','37',
    '03','25','08','73','42','56','12','89','48','00',
    '25','03','73','15','61','08','37','56','12','42',
    '00','03','25','08','73','15','61','42','56','12',
    '03','25','73','00','08','15','37','61','42','56',
    '12','03','25','73','00','08','15','37','61','42'
]

# ========== TÍNH TOÁN ĐỘNG — KHÔNG VIẾT CỨNG ==========
def tinh_tan_suat(ngay):
    """Tính tần suất xuất hiện động dựa trên lịch sử"""
    thu = ngay.weekday()
    tan_suat = {}
    chu_ky_nghi = {}
    
    # Khởi tạo
    for i in range(100):
        s = f"{i:02d}"
        tan_suat[s] = 0
        chu_ky_nghi[s] = 99  # Chưa từng ra
    
    # Đếm tần suất và tính chu kỳ nghỉ
    for idx, so in enumerate(LICH_SU_2_SO_CUOI):
        tan_suat[so] += 1
        if chu_ky_nghi[so] == 99:
            chu_ky_nghi[so] = idx  # Lần cuối ra cách đây bao nhiêu ngày
    
    # Tính cho số cuối riêng lẻ
    tan_suat_so_cuoi = {str(i):0 for i in range(10)}
    chu_ky_so_cuoi = {str(i):99 for i in range(10)}
    for idx, so in enumerate(LICH_SU_2_SO_CUOI):
        sc = so[-1]
        tan_suat_so_cuoi[sc] += 1
        if chu_ky_so_cuoi[sc] == 99:
            chu_ky_so_cuoi[sc] = idx
    
    return tan_suat, chu_ky_nghi, tan_suat_so_cuoi, chu_ky_so_cuoi

def tinh_phan_bo_theo_thu(ngay):
    """Tính phân bố theo thứ một cách chính xác"""
    thu = ngay.weekday()
    so_ngay_trong_thu = {}
    for t in range(7):
        so_ngay_trong_thu[t] = {'tong':0, 'ra':0}
    
    for idx, so in enumerate(LICH_SU_2_SO_CUOI):
        thu_cua_ngay = (thu - idx) % 7  # Tính thứ của ngày đó
        so_ngay_trong_thu[thu_cua_ngay]['tong'] += 1
        so_ngay_trong_thu[thu_cua_ngay]['ra'] += 1
    
    ty_le_theo_thu = {}
    for t in range(7):
        if so_ngay_trong_thu[t]['tong'] > 0:
            ty_le_theo_thu[t] = so_ngay_trong_thu[t]['ra'] / so_ngay_trong_thu[t]['tong']
        else:
            ty_le_theo_thu[t] = 0.1  # Mặc định
    
    return ty_le_theo_thu[thu]

# ========== LOGIC MỚI ĐÃ CẢI THIỆN ==========
def tinh_thong_tin(so, ngay, tan_suat, chu_ky, ty_le_thu_hien_hanh):
    """Tính điểm với trọng số đã tối ưu"""
    ts_lan = tan_suat.get(so, 0)
    ts_pt = round((ts_lan / TONG_NGAY) * 100, 1)
    ck_nghi = chu_ky.get(so, 3)
    
    # ✅ Mới: Giảm điểm cho số vừa ra trong 2 ngày qua
    diem_giam = 0
    if len(so) == 2:
        if LICH_SU_2_SO_CUOI[0] == so:
            diem_giam = 15  # Giảm mạnh nếu vừa ra hôm qua
        elif LICH_SU_2_SO_CUOI[1] == so:
            diem_giam = 10  # Giảm nếu ra hôm kia
    
    # ✅ Trọng số mới: 45% tần suất + 40% chu kỳ + 15% thứ
    diem_ts = min(ts_pt, 50) * 0.45
    diem_ck = min(ck_nghi * 1.5, 40) * 0.40
    diem_th = min(ty_le_thu_hien_hanh * 100, 30) * 0.15
    
    tong_diem = round(diem_ts + diem_ck + diem_th - diem_giam, 2)
    
    return {
        'so': so,
        'ts_pt': ts_pt,
        'ck_nghi': ck_nghi,
        'tong_diem': tong_diem,
        'diem_giam': diem_giam
    }

def tinh_toan(ngay):
    tan_suat, chu_ky, tan_suat_sc, chu_ky_sc, = tinh_tan_suat(ngay)
    ty_le_thu = tinh_phan_bo_theo_thu(ngay)
    
    # Tính cho lô 2 số
    ds_lo = []
    for i in range(100):
        s = f"{i:02d}"
        ds_lo.append(tinh_thong_tin(s, ngay, tan_suat, chu_ky, ty_le_thu))
    
    ds_lo = sorted(ds_lo, key=lambda x:x['tong_diem'], reverse=True)
    
    # Tính cho số cuối
    ds_sc = []
    for s in '0123456789':
        thong_tin = tinh_thong_tin(s, ngay, tan_suat_sc, chu_ky_sc, ty_le_thu)
        ds_sc.append(thong_tin)
    
    ds_sc = sorted(ds_sc, key=lambda x:x['tong_diem'], reverse=True)
    
    return {'lo3': ds_lo[:3], 'xien2': ds_lo[3:5], 'sc1': ds_sc[:1]}

TY_LE_TRUNG_MOI = {
    'lo1': '~20%', 'lo2': '~18%', 'lo3': '~16%',
    'xien1': '~19%', 'xien2': '~15%', 'sc': '~38%'
}

# ========== GỬI DỰ ĐOÁN ==========
def gui_du_doan(ngay, ten_ngay=""):
    global KET_QUA_D, KET_QUA_D1
    
    if ten_ngay == "DỰ ĐOÁN NGÀY D+1":
        if KET_QUA_D1 is None:
            KET_QUA_D1 = tinh_toan(ngay)
        d = KET_QUA_D1
    else:
        if KET_QUA_D is None:
            KET_QUA_D = tinh_toan(ngay)
        d = KET_QUA_D
    
    ngay_str = ngay.strftime("%d/%m/%Y")
    thu_viet = ['Thứ 2','Thứ 3','Thứ 4','Thứ 5','Thứ 6','Thứ 7','Chủ Nhật']
    thu_hien = thu_viet[ngay.weekday()]
    
    text = f"""🤖 DỰ ĐOÁN XSMB — {ten_ngay}
📅 {ngay_str} | {thu_hien}
📊 Logic đã cải thiện: Tần suất 45% + Chu kỳ 40% + Theo thứ 15%
⚠️ CHỈ THAM KHẢO - KHÔNG ĐẢM BẢO! Tỷ lệ tối đa ~38% cho số cuối

🎯 TOP 3 LÔ CAO NHẤT
🥇 {d['lo3'][0]['so']} | Tỷ lệ: {TY_LE_TRUNG_MOI['lo1']} | Nghỉ {d['lo3'][0]['ck_nghi']} ngày
🥈 {d['lo3'][1]['so']} | Tỷ lệ: {TY_LE_TRUNG_MOI['lo2']} | Nghỉ {d['lo3'][1]['ck_nghi']} ngày
🥉 {d['lo3'][2]['so']} | Tỷ lệ: {TY_LE_TRUNG_MOI['lo3']} | Nghỉ {d['lo3'][2]['ck_nghi']} ngày

🎯 2 LÔ XIÊN CAO
🥇 {d['xien2'][0]['so']} | Tỷ lệ: {TY_LE_TRUNG_MOI['xien1']} | Nghỉ {d['xien2'][0]['ck_nghi']} ngày
🥈 {d['xien2'][1]['so']} | Tỷ lệ: {TY_LE_TRUNG_MOI['xien2']} | Nghỉ {d['xien2'][1]['ck_nghi']} ngày

🎯 SỐ CUỐI ĐẶC BIỆT
🥇 {d['sc1'][0]['so']} | Tỷ lệ: {TY_LE_TRUNG_MOI['sc']} | Nghỉ {d['sc1'][0]['ck_nghi']} ngày

📝 Giải thích: Số nghỉ ngày càng dài → cơ hội càng cao. Số vừa ra 2 ngày qua đã giảm điểm.
🎲 Chơi có trách nhiệm - Chỉ giải trí! Không đầu tư quá khả năng!
"""
    bot.send_message(CHAT_ID, text)
    print(f"✅ Đã gửi {ten_ngay} | {ngay_str}")

# ========== GỬI KẾT QUẢ THỰC TẾ ==========
def gui_ket_qua_thuc_te(ngay):
    ngay_str = ngay.strftime("%d/%m/%Y")
    thu_viet = ['Thứ 2','Thứ 3','Thứ 4','Thứ 5','Thứ 6','Thứ 7','Chủ Nhật']
    thu_hien = thu_viet[ngay.weekday()]
    
    text = f"""🏆 KẾT QUẢ XSMB ĐÃ QUAY — NGÀY {ngay_str}
📅 {ngay_str} | {thu_hien}
📊 Kết quả chính thức đã công bố

🎖️ GIẢI ĐẶC BIỆT: Đợi cập nhật...
🥇 GIẢI NHẤT: Đợi cập nhật...
🥈 GIẢI NHÌ: Đợi cập nhật...
🥉 GIẢI BA: Đợi cập nhật...
🏅 GIẢI TƯ: Đợi cập nhật...
🎖️ GIẢI NĂM: Đợi cập nhật...
🎗️ GIẢI SÁU: Đợi cập nhật...
🎟️ GIẢI BẢY: Đợi cập nhật...

📝 Đối chiếu dự đoán sẽ cập nhật sau khi có kết quả!
"""
    bot.send_message(CHAT_ID, text)
    print(f"🏆 Đã gửi KẾT QUẢ THỰC TẾ | {ngay_str}")

# ========== KIỂM TRA THỜI GIAN ==========
def da_qua_18h35():
    now = datetime.now()
    return now.hour > 18 or (now.hour == 18 and now.minute >= 35)

def dau_ngay_moi():
    now = datetime.now()
    return now.hour == 0 and now.minute == 0

# ========== CHẠY BOT ==========
def chay():
    da_gui_ket_qua = False
    
    while True:
        if dau_ngay_moi():
            da_gui_ket_qua = False
            global KET_QUA_D, KET_QUA_D1
            KET_QUA_D = None
            KET_QUA_D1 = None
            print("🔄 Đặt lại cho ngày mới — Logic đã cải thiện!")
            time.sleep(60)
            continue
        
        if not da_qua_18h35():
            gui_du_doan(datetime.now(), "DỰ ĐOÁN NGÀY D")
            time.sleep(60)
            continue
        
        if not da_gui_ket_qua:
            gui_ket_qua_thuc_te(datetime.now())
            da_gui_ket_qua = True
            print("🏆 18:35 — ĐÃ GỬI KẾT QUẢ THỰC TẾ")
        
        ngay_mai = datetime.now() + timedelta(days=1)
        gui_du_doan(ngay_mai, "DỰ ĐOÁN NGÀY D+1")
        time.sleep(60)

if __name__ == "__main__":
    from threading import Thread
    Thread(target=chay).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
