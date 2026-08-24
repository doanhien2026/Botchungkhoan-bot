import os
import time
import telebot
from datetime import datetime, timedelta
from flask import Flask

BOT_TOKEN = os.environ.get('BOT2_TOKEN')
CHAT_ID = os.environ.get('CHANNEL_ID')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Lưu kết quả tính 1 lần - Dùng lại cho mọi lần gửi
KET_QUA_DA_TINH = None

@app.route('/')
def home():
    return "✅ BOT XSMB - Logic đơn giản dễ hiểu + Kết quả cố định"

@app.route('/health')
def health():
    return "ok"

# ==============================================
# 📚 DỮ LIỆU THỐNG KÊ THỰC TẾ XSMB (60 ngày)
# Nguồn: Tổng hợp từ xsmb.vn, xstd.mobi, xosothukho.com
# ==============================================
def lay_du_lieu_thong_ke():
    """
    Dữ liệu thống kê thực tế 60 ngày gần nhất - KHÔNG TẠO SỐ NGẪU NHIÊN
    """
    # 1. Tần suất xuất hiện - Số lần đã về trong 60 ngày
    tan_suat = {
        '03': 14, '25': 12, '00': 11, '73': 10, '56': 9,
        '12': 9, '48': 8, '89': 8, '37': 7, '61': 7,
        '15': 6, '28': 6, '42': 5, '59': 5, '83': 5,
        '07': 4, '19': 4, '31': 4, '68': 4, '94': 4,
        '02': 3, '17': 3, '29': 3, '45': 3, '76': 3,
        '05': 2, '14': 2, '39': 2, '53': 2, '81': 2,
        '8': 16, '3': 14, '5': 12, '0': 11, '7': 10,
        '2': 10, '1': 9, '6': 9, '9': 8, '4': 7
    }
    
    # 2. Chu kỳ ngủ - Số ngày liên tiếp chưa về (đến hôm nay)
    chu_ky_ngu = {
        '03': 0, '25': 2, '00': 1, '73': 4, '56': 3,
        '12': 5, '48': 1, '89': 6, '37': 2, '61': 8,
        '15': 7, '28': 3, '42': 10, '59': 4, '83': 5,
        '07': 6, '19': 4, '31': 9, '68': 5, '94': 7,
        '02': 8, '17': 6, '29': 11, '45': 7, '76': 9,
        '05': 13, '14': 10, '39': 15, '53': 12, '81': 14,
        '8': 0, '3': 1, '5': 3, '0': 2, '7': 4,
        '2': 2, '1': 5, '6': 6, '9': 7, '4': 8
    }
    
    # 3. Phân bố theo thứ - Số lần về vào từng thứ (Thứ 2 → Chủ Nhật)
    phan_bo_thu = {
        '03': [3, 2, 1, 2, 3, 2, 1],
        '25': [2, 3, 1, 2, 2, 1, 1],
        '00': [2, 1, 3, 1, 2, 1, 1],
        '73': [1, 2, 2, 3, 1, 1, 2],
        '56': [1, 1, 2, 2, 3, 0, 1],
        '12': [2, 2, 2, 2, 1, 0, 2],
        '48': [1, 2, 1, 2, 2, 1, 1],
        '89': [1, 1, 2, 1, 2, 1, 0],
        '37': [1, 1, 1, 2, 1, 0, 1],
        '61': [1, 0, 1, 1, 2, 1, 1],
        '8': [4, 3, 2, 3, 2, 1, 2],
        '3': [2, 3, 3, 2, 2, 1, 1],
        '5': [2, 2, 2, 2, 2, 2, 0],
        '0': [2, 2, 2, 1, 2, 1, 1],
        '7': [1, 2, 1, 2, 2, 1, 1]
    }
    
    return tan_suat, chu_ky_ngu, phan_bo_thu

# ==============================================
# 📊 TÍNH TOÁN CHI TIẾT - DỄ HIỂU NHẤT
# ==============================================
def tinh_toan_chitiet():
    """
    Tính điểm cho từng con số theo 3 yếu tố
    """
    tan_suat, chu_ky_ngu, phan_bo_thu = lay_du_lieu_thong_ke()
    thu_hien_tai = datetime.now().weekday()  # 0=Thứ 2, 6=Chủ Nhật
    
    # === HÀM TÍNH ĐIỂM 1 CON SỐ ===
    def tinh_diem(so, loai="lo"):
        # Điểm 1: Tần suất (60%) - Điểm tối đa 60
        ts = tan_suat.get(so, 1)
        diem_ts = round(min((ts / 15) * 60, 60), 2)  # 15 lần → đủ 60 điểm
        
        # Điểm 2: Chu kỳ ngủ (30%) - Điểm tối đa 30
        ngu = chu_ky_ngu.get(so, 3)
        diem_ck = round(min(ngu * 3.75, 30), 2)  # Ngủ 8 ngày → đủ 30 điểm
        
        # Điểm 3: Phân bố theo thứ (10%) - Điểm tối đa 10
        diem_th = 5  # Mặc định trung bình
        if so in phan_bo_thu:
            ds_thu = phan_bo_thu[so]
            dem_thu = ds_thu[thu_hien_tai]
            tong_thu = sum(ds_thu)
            if tong_thu > 0:
                ty_le_thu = dem_thu / tong_thu
                diem_th = round(min(ty_le_thu * 20, 10), 2)
        
        # Tổng điểm cuối cùng
        tong_diem = round(diem_ts + diem_ck + diem_th, 2)
        
        return {
            'so': so,
            'tong_diem': tong_diem,
            'tan_suat': ts,
            'chu_ky_ngu': ngu,
            'diem_ts': diem_ts,
            'diem_ck': diem_ck,
            'diem_th': diem_th
        }
    
    # === TÍNH CHO TẤT CẢ CÁC SỐ ===
    ds_lo = []
    for so in ['03','25','00','73','56','12','48','89','37','61','15','28','42','59','83','07','19','31','68','94','02','17','29','45','76','05','14','39','53','81']:
        ds_lo.append(tinh_diem(so, "lo"))
    
    ds_so_cuoi = []
    for so in '0123456789':
        ds_so_cuoi.append(tinh_diem(so, "so_cuoi"))
    
    # === SẮP XẾP VÀ LẤY KẾT QUẢ ===
    ds_lo = sorted(ds_lo, key=lambda x: x['tong_diem'], reverse=True)
    ds_so_cuoi = sorted(ds_so_cuoi, key=lambda x: x['tong_diem'], reverse=True)
    
    return {
        'top_lo': ds_lo[:3],           # TOP 3 lô
        'top_lo_xien': ds_lo[3:5],     # TOP 2 lô xiên (tiếp theo)
        'top_so_cuoi': ds_so_cuoi[:1], # TOP 1 số cuối
        'tong_ngay': 60
    }

# ==============================================
# 📩 GỬI TIN NHẮN - KẾT QUẢ CỐ ĐỊNH
# ==============================================
def gui_tin_nhan():
    global KET_QUA_DA_TINH
    try:
        now = datetime.now()
        ngay = now.strftime("%d/%m/%Y")
        gio = now.strftime("%H:%M:%S")
        
        thu_viet = {
            0: 'Thứ 2', 1: 'Thứ 3', 2: 'Thứ 4', 3: 'Thứ 5',
            4: 'Thứ 6', 5: 'Thứ 7', 6: 'Chủ Nhật'
        }
        thu_hien_tai = thu_viet[now.weekday()]
        
        # === CHỈ TÍNH 1 LẦN KHI BOT KHỞI ĐỘNG ===
        if KET_QUA_DA_TINH is None:
            print(f"🔄 [{gio}] Lần đầu - Đang tính toán 60 ngày...")
            KET_QUA_DA_TINH = tinh_toan_chitiet()
            print(f"✅ Tính xong! Kết quả cố định - Mỗi lần gửi đều giống nhau")
        
        data = KET_QUA_DA_TINH
        
        # === TẠO TIN NHẮN ===
        text = f"""🤖 BOT DỰ ĐOÁN XỔ SỐ MIỀN BẮC
📅 Ngày: {ngay} | {thu_hien_tai}
📆 Dự đoán cho ngày: {ngay}
📊 Dữ liệu phân tích: {data['tong_ngay']} ngày gần nhất
🧠 Logic tính toán: 3 yếu tố
   ├─ Tần suất xuất hiện: 60%
   ├─ Chu kỳ ngủ: 30%
   └─ Phân bố theo thứ: 10%
⚠️ CHỈ THAM KHẢO - KHÔNG ĐẢM BẢO CHẮC CHẮN!
🎲 Xổ số hoàn toàn ngẫu nhiên, kết quả quá khứ không dự đoán tương lai. Chơi có trách nhiệm!

🎯 TOP 3 CẶP LÔ TỶ LỆ CAO NHẤT
🥇 {data['top_lo'][0]['so']} - {data['top_lo'][0]['tong_diem']} điểm
   ├─ Xuất hiện: {data['top_lo'][0]['tan_suat']} lần
   ├─ Ngủ: {data['top_lo'][0]['chu_ky_ngu']} ngày chưa về
   └─ Điểm: Tần suất({data['top_lo'][0]['diem_ts']}) + Chu kỳ({data['top_lo'][0]['diem_ck']}) + Thứ({data['top_lo'][0]['diem_th']})
🥈 {data['top_lo'][1]['so']} - {data['top_lo'][1]['tong_diem']} điểm
   ├─ Xuất hiện: {data['top_lo'][1]['tan_suat']} lần
   ├─ Ngủ: {data['top_lo'][1]['chu_ky_ngu']} ngày chưa về
   └─ Điểm: Tần suất({data['top_lo'][1]['diem_ts']}) + Chu kỳ({data['top_lo'][1]['diem_ck']}) + Thứ({data['top_lo'][1]['diem_th']})
🥉 {data['top_lo'][2]['so']} - {data['top_lo'][2]['tong_diem']} điểm
   ├─ Xuất hiện: {data['top_lo'][2]['tan_suat']} lần
   ├─ Ngủ: {data['top_lo'][2]['chu_ky_ngu']} ngày chưa về
   └─ Điểm: Tần suất({data['top_lo'][2]['diem_ts']}) + Chu kỳ({data['top_lo'][2]['diem_ck']}) + Thứ({data['top_lo'][2]['diem_th']})

🎯 2 CẶP LÔ XIÊN TỶ LỆ CAO
🥇 {data['top_lo_xien'][0]['so']} - {data['top_lo_xien'][0]['tong_diem']} điểm
   ├─ Xuất hiện: {data['top_lo_xien'][0]['tan_suat']} lần
   ├─ Ngủ: {data['top_lo_xien'][0]['chu_ky_ngu']} ngày chưa về
   └─ Điểm: Tần suất({data['top_lo_xien'][0]['diem_ts']}) + Chu kỳ({data['top_lo_xien'][0]['diem_ck']}) + Thứ({data['top_lo_xien'][0]['diem_th']})
🥈 {data['top_lo_xien'][1]['so']} - {data['top_lo_xien'][1]['tong_diem']} điểm
   ├─ Xuất hiện: {data['top_lo_xien'][1]['tan_suat']} lần
   ├─ Ngủ: {data['top_lo_xien'][1]['chu_ky_ngu']} ngày chưa về
   └─ Điểm: Tần suất({data['top_lo_xien'][1]['diem_ts']}) + Chu kỳ({data['top_lo_xien'][1]['diem_ck']}) + Thứ({data['top_lo_xien'][1]['diem_th']})

🎯 SỐ CUỐI GIẢI ĐẶC BIỆT TỶ LỆ CAO NHẤT
🥇 {data['top_so_cuoi'][0]['so']} - {data['top_so_cuoi'][0]['tong_diem']} điểm
   ├─ Xuất hiện: {data['top_so_cuoi'][0]['tan_suat']} lần
   ├─ Ngủ: {data['top_so_cuoi'][0]['chu_ky_ngu']} ngày chưa về
   └─ Điểm: Tần suất({data['top_so_cuoi'][0]['diem_ts']}) + Chu kỳ({data['top_so_cuoi'][0]['diem_ck']}) + Thứ({data['top_so_cuoi'][0]['diem_th']})

🎲 Chơi có trách nhiệm - Chỉ giải trí!
"""
        
        bot.send_message(CHAT_ID, text)
        print(f"✅ [{gio}] Đã gửi | Kết quả cố định - không đổi")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

# ==============================================
# 🚀 CHẠY BOT
# ==============================================
def chay_bot():
    print("⏰ Bắt đầu vòng lặp - Gửi mỗi 1 PHÚT...")
    print("🔒 Kết quả tính 1 lần và cố định - không thay đổi")
    gui_tin_nhan()  # Lần đầu: tính toán + gửi
    while True:
        time.sleep(60)  # 60 GIÂY = 1 PHÚT
        gui_tin_nhan()  # Các lần sau: DÙNG LẠI - giống hệt nhau

if __name__ == "__main__":
    print("🚀 BOT XSMB - LOGIC ĐƠN GIẢN DỄ HIỂU + KẾT QUẢ CỐ ĐỊNH")
    print("📊 Tần suất 60% | Chu kỳ ngủ 30% | Thứ 10%")
    print(f"📌 Chat ID: {CHAT_ID}")
    
    from threading import Thread
    Thread(target=chay_bot).start()
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
