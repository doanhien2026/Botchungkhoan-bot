import os
import time
import telebot
from datetime import datetime, timedelta
from flask import Flask

BOT_TOKEN = os.environ.get('BOT2_TOKEN')
CHAT_ID = os.environ.get('CHANNEL_ID')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

KET_QUA = None
TONG_NGAY = 60

# ========== DỮ LIỆU THỐNG KÊ ==========
TAN_SUAT_LAN = {
    '03':14,'25':12,'00':11,'73':10,'56':9,'12':9,'48':8,'89':8,
    '37':7,'61':7,'15':6,'28':6,'42':5,'59':5,'83':5,'07':4,'19':4,
    '31':4,'68':4,'94':4,'02':3,'17':3,'29':3,'45':3,'76':3,'05':2,
    '14':2,'39':2,'53':2,'81':2,'8':16,'3':14,'5':12,'0':11,'7':10,
    '2':10,'1':9,'6':9,'9':8,'4':7
}
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

TY_LE_TRUNG = {
    'lo1': '18%', 'lo2': '15%', 'lo3': '13%',
    'xien1': '17%', 'xien2': '12%', 'sc': '35%'
}

# ========== TÍNH THÔNG TIN ==========
def tinh_thong_tin(so, thu_hien_tai):
    ts_lan = TAN_SUAT_LAN.get(so, 0)
    ts_pt = round((ts_lan / TONG_NGAY) * 100, 1)
    ck_nghi = CHU_KY_NGHI.get(so, 3)
    
    diem_th = 5
    if so in PHAN_BO_THU:
        ds_thu = PHAN_BO_THU[so]
        tong_thu = sum(ds_thu)
        if tong_thu > 0:
            ty_le_thu = ds_thu[thu_hien_tai] / tong_thu
            diem_th = round(min(ty_le_thu * 20, 10), 1)
    
    tong_diem = round((ts_pt * 0.6) + (min(ck_nghi * 2, 30) * 0.3) + (diem_th * 0.1), 2)
    return {'so': so, 'ts_pt': ts_pt, 'ck_nghi': ck_nghi, 'tong_diem': tong_diem}

def tinh_toan():
    thu = datetime.now().weekday()
    ds_lo = sorted([tinh_thong_tin(s, thu) for s in list(TAN_SUAT_LAN.keys())[:30]],
                   key=lambda x:x['tong_diem'], reverse=True)
    ds_sc = sorted([tinh_thong_tin(s, thu) for s in '0123456789'],
                   key=lambda x:x['tong_diem'], reverse=True)
    return {'lo3': ds_lo[:3], 'xien2': ds_lo[3:5], 'sc1': ds_sc[:1]}

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
⚠️ CHỈ THAM KHẢO - KHÔNG ĐẢM BẢO!
🎲 Xổ số ngẫu nhiên - Chơi có trách nhiệm!

🎯 TOP 3 LÔ CAO NHẤT
🥇 {d['lo3'][0]['so']} | Tỷ lệ trúng: {TY_LE_TRUNG['lo1']}
🥈 {d['lo3'][1]['so']} | Tỷ lệ trúng: {TY_LE_TRUNG['lo2']}
🥉 {d['lo3'][2]['so']} | Tỷ lệ trúng: {TY_LE_TRUNG['lo3']}

🎯 2 LÔ XIÊN CAO
🥇 {d['xien2'][0]['so']} | Tỷ lệ trúng: {TY_LE_TRUNG['xien1']}
🥈 {d['xien2'][1]['so']} | Tỷ lệ trúng: {TY_LE_TRUNG['xien2']}

🎯 SỐ CUỐI ĐẶC BIỆT
🥇 {d['sc1'][0]['so']} | Tỷ lệ trúng: {TY_LE_TRUNG['sc']}

🎲 Chơi có trách nhiệm - Chỉ giải trí!
"""
    bot.send_message(CHAT_ID, text)
    print(f"✅ Đã gửi | {ngay} {thu_hien}")

# ========== TÍNH THỜI GIAN GỬI ==========
def lay_gui_luc():
    bây_giờ = datetime.now()
    gui_luc = bây_giờ.replace(hour=18, minute=35, second=0, microsecond=0)
    # Nếu đã qua 18:35 thì gửi ngay hôm nay, nếu chưa thì đợi đến 18:35
    if bây_giờ >= gui_luc:
        return bây_giờ  # Gửi ngay!
    return gui_luc

# ========== CHẠY BOT ==========
def chay():
    while True:
        lan_gui_tiep = lay_gui_luc()
        doi = (lan_gui_tiep - datetime.now()).total_seconds()
        if doi > 0:
            print(f"⏰ Đợi {int(doi)} giây đến {lan_gui_tiep.strftime('%H:%M')}")
            time.sleep(doi)
        gui()
        # Đặt lịch cho ngày mai
        ngày_mai = datetime.now() + timedelta(days=1)
        gui_luc_mai = ngày_mai.replace(hour=18, minute=35, second=0, microsecond=0)
        doi_mai = (gui_luc_mai - datetime.now()).total_seconds()
        print(f"📅 Lịch gửi ngày mai: {gui_luc_mai.strftime('%d/%m %H:%M')} | Đợi {int(doi_mai/3600)} giờ")
        time.sleep(doi_mai)

if __name__ == "__main__":
    from threading import Thread
    Thread(target=chay).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
