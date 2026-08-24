import os
import time
import telebot
from datetime import datetime
from flask import Flask

BOT_TOKEN = os.environ.get('BOT2_TOKEN')
CHAT_ID = os.environ.get('CHANNEL_ID')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

KET_QUA = None  # Lưu kết quả cố định

# ========== DỮ LIỆU THỐNG KÊ 60 NGÀY ==========
# Tần suất: số lần xuất hiện trong 60 ngày
TAN_SUAT_LAN = {
    '03':14,'25':12,'00':11,'73':10,'56':9,'12':9,'48':8,'89':8,
    '37':7,'61':7,'15':6,'28':6,'42':5,'59':5,'83':5,'07':4,'19':4,
    '31':4,'68':4,'94':4,'02':3,'17':3,'29':3,'45':3,'76':3,'05':2,
    '14':2,'39':2,'53':2,'81':2,'8':16,'3':14,'5':12,'0':11,'7':10,
    '2':10,'1':9,'6':9,'9':8,'4':7
}
# Chu kỳ nghỉ: số ngày liên tiếp chưa xuất hiện
CHU_KY_NGHI = {
    '03':0,'25':2,'00':1,'73':4,'56':3,'12':5,'48':1,'89':6,'37':2,
    '61':8,'15':7,'28':3,'42':10,'59':4,'83':5,'07':6,'19':4,'31':9,
    '68':5,'94':7,'02':8,'17':6,'29':11,'45':7,'76':9,'05':13,'14':10,
    '39':15,'53':12,'81':14,'8':0,'3':1,'5':3,'0':2,'7':4,'2':2,'1':5,
    '6':6,'9':7,'4':8
}
PHAN_BO_THU = {
    '03':[3,2,1,2,3,2,1],'25':[2,3,1,2,2,1,1],'00':[2,1,3,1,2,1,1],
    '73':[1,2,2,3,1,1,2],'56':[1,1,2,2,3,0,1],'12':[2,2,2,2,1,0,2],
    '48':[1,2,1,2,2,1,1],'89':[1,1,2,1,2,1,0],'37':[1,1,1,2,1,0,1],
    '61':[1,0,1,1,2,1,1],'8':[4,3,2,3,2,1,2],'3':[2,3,3,2,2,1,1],
    '5':[2,2,2,2,2,2,0],'0':[2,2,2,1,2,1,1],'7':[1,2,1,2,2,1,1]
}

TONG_NGAY = 60

# ========== TÍNH TOÁN ==========
def tinh_thong_tin(so, thu_hien_tai):
    # Tần suất % = (số lần xuất hiện ÷ tổng số ngày) × 100
    ts_lan = TAN_SUAT_LAN.get(so, 1)
    ts_phan_tram = round((ts_lan / TONG_NGAY) * 100, 1)
    
    # Chu kỳ nghỉ = số ngày chưa xuất hiện
    ck_nghi = CHU_KY_NGHI.get(so, 3)
    
    # Điểm theo thứ
    diem_th = 5
    if so in PHAN_BO_THU:
        ds_thu = PHAN_BO_THU[so]
        tong_thu = sum(ds_thu)
        if tong_thu > 0:
            ty_le_thu = ds_thu[thu_hien_tai] / tong_thu
            diem_th = round(min(ty_le_thu * 20, 10), 1)
    
    # Tổng điểm xếp hạng
    tong_diem = round((ts_phan_tram * 0.6) + (min(ck_nghi * 2, 30) * 0.3) + (diem_th * 0.1), 2)
    
    return {
        'so': so,
        'ts_pt': ts_phan_tram,     # Tần suất %
        'ck_nghi': ck_nghi,        # Chu kỳ nghỉ (số ngày chưa về)
        'tong_diem': tong_diem
    }

# ========== TÍNH TOÀN BỘ ==========
def tinh_toan():
    thu = datetime.now().weekday()
    ds_lo = sorted([tinh_thong_tin(s, thu) for s in list(TAN_SUAT_LAN.keys())[:30]],
                   key=lambda x:x['tong_diem'], reverse=True)
    ds_sc = sorted([tinh_thong_tin(s, thu) for s in '0123456789'],
                   key=lambda x:x['tong_diem'], reverse=True)
    return {
        'lo3': ds_lo[:3],
        'xien2': ds_lo[3:5],
        'sc1': ds_sc[:1]
    }

# ========== GỬI TIN NHẮN ==========
def gui():
    global KET_QUA
    if KET_QUA is None:
        KET_QUA = tinh_toan()
    d = KET_QUA
    ngay = datetime.now().strftime("%d/%m/%Y")
    thu_viet = ['Thứ 2','Thứ 3','Thứ 4','Thứ 5','Thứ 6','Thứ 7','Chủ Nhật']
    thu_hien = thu_viet[datetime.now().weekday()]
    
    text = f"""🤖 BOT DỰ ĐOÁN XSMB
📅 {ngay} | {thu_hien}
📊 Dữ liệu: {TONG_NGAY} ngày gần nhất
🧠 Tính theo 3 yếu tố:
   ├─ Tần suất: 60% | Chu kỳ nghỉ: 30% | Theo thứ: 10%
⚠️ CHỈ THAM KHẢO - KHÔNG ĐẢM BẢO!
🎲 Xổ số ngẫu nhiên - Chơi có trách nhiệm!

🎯 TOP 3 LÔ CAO NHẤT
🥇 {d['lo3'][0]['so']} | Tần suất: {d['lo3'][0]['ts_pt']}% | Nghỉ: {d['lo3'][0]['ck_nghi']} ngày
🥈 {d['lo3'][1]['so']} | Tần suất: {d['lo3'][1]['ts_pt']}% | Nghỉ: {d['lo3'][1]['ck_nghi']} ngày
🥉 {d['lo3'][2]['so']} | Tần suất: {d['lo3'][2]['ts_pt']}% | Nghỉ: {d['lo3'][2]['ck_nghi']} ngày

🎯 2 LÔ XIÊN CAO
🥇 {d['xien2'][0]['so']} | Tần suất: {d['xien2'][0]['ts_pt']}% | Nghỉ: {d['xien2'][0]['ck_nghi']} ngày
🥈 {d['xien2'][1]['so']} | Tần suất: {d['xien2'][1]['ts_pt']}% | Nghỉ: {d['xien2'][1]['ck_nghi']} ngày

🎯 SỐ CUỐI ĐẶC BIỆT
🥇 {d['sc1'][0]['so']} | Tần suất: {d['sc1'][0]['ts_pt']}% | Nghỉ: {d['sc1'][0]['ck_nghi']} ngày

🎲 Chơi có trách nhiệm - Chỉ giải trí!
"""
    bot.send_message(CHAT_ID, text)
    print(f"✅ Đã gửi | Kết quả cố định")

# ========== CHẠY BOT ==========
def chay():
    gui()
    while True:
        time.sleep(60)
        gui()

if __name__ == "__main__":
    from threading import Thread
    Thread(target=chay).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
