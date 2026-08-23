import os
import time
import telebot
import random
from datetime import datetime, timedelta

BOT_TOKEN = os.environ.get('BOT2_TOKEN')
CHAT_ID = os.environ.get('CHANNEL_ID')

if not BOT_TOKEN or not CHAT_ID:
    print("❌ Thiếu biến môi trường!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# ==============================================
# 🧠 LOGIC TÍNH TOÁN TỶ LỆ DỰA TRÊN DỮ LIỆU LỊCH SỬ
# ==============================================

def get_xsmb_history():
    """
    Lấy dữ liệu kết quả XSMB 90 ngày gần nhất
    Ở đây mình tạo dữ liệu mẫu mô phỏng kết quả thực tế
    Khi có API/nguồn dữ liệu thật thì thay vào đây!
    """
    history_data = []
    today = datetime.now()
    
    # Tạo dữ liệu 90 ngày gần nhất (mô phỏng)
    for i in range(90):
        date = today - timedelta(days=i)
        date_str = date.strftime("%d/%m/%Y")
        
        # Tạo kết quả XSMB ngẫu nhiên nhưng có tính phân bố
        dac_biet = f"{random.randint(0,99999):05d}"
        giai_nhat = f"{random.randint(0,9999):04d}"
        giai_nhi = [f"{random.randint(0,9999):04d}" for _ in range(2)]
        giai_ba = [f"{random.randint(0,999):03d}" for _ in range(6)]
        giai_tu = [f"{random.randint(0,99):02d}" for _ in range(4)]
        giai_nam = [f"{random.randint(0,9999):04d}" for _ in range(6)]
        giai_sau = [f"{random.randint(0,99):02d}" for _ in range(3)]
        giai_bay = [f"{random.randint(0,9):01d}" for _ in range(4)]
        
        history_data.append({
            'date': date_str,
            'dac_biet': dac_biet,
            'giai_nhat': giai_nhat,
            'giai_nhi': giai_nhi,
            'giai_ba': giai_ba,
            'giai_tu': giai_tu,
            'giai_nam': giai_nam,
            'giai_sau': giai_sau,
            'giai_bay': giai_bay
        })
    return history_data

def calculate_frequency(history_data):
    """
    Tính tần suất và tỷ lệ xuất hiện của các số
    """
    # Đếm tần suất lô 2 số cuối giải đặc biệt
    lo_2so_cuoi = {}
    dau_2so = {}
    cuoi_2so = {}
    lo_nhi = {}  # lô xiên 2 số
    
    total_days = len(history_data)
    
    for record in history_data:
        db = record['dac_biet']
        if len(db) == 5:
            hai_so_cuoi = db[-2:]
            hai_so_dau = db[:2]
            so_dau = db[0]
            so_cuoi = db[-1]
            
            # Đếm lô 2 số cuối
            lo_2so_cuoi[hai_so_cuoi] = lo_2so_cuoi.get(hai_so_cuoi, 0) + 1
            
            # Đếm đầu 2 số
            dau_2so[hai_so_dau] = dau_2so.get(hai_so_dau, 0) + 1
            
            # Đếm số đầu và số cuối riêng lẻ
            cuoi_2so[so_cuoi] = cuoi_2so.get(so_cuoi, 0) + 1
            
            # Tạo lô xiên (cặp số liên tiếp)
            for i in range(len(db)-1):
                cap = db[i:i+2]
                if cap.isdigit():
                    lo_nhi[cap] = lo_nhi.get(cap, 0) + 1
    
    # Tính tỷ lệ phần trăm
    def calc_percent(data_dict):
        result = []
        for num, count in data_dict.items():
            percent = round((count / total_days) * 100, 2)
            result.append({'number': num, 'count': count, 'percent': percent})
        return sorted(result, key=lambda x: x['percent'], reverse=True)
    
    top_lo = calc_percent(lo_2so_cuoi)
    top_lo_xien = calc_percent(lo_nhi)
    top_dau_2so = calc_percent(dau_2so)
    top_so_cuoi = calc_percent(cuoi_2so)
    
    return {
        'top_lo': top_lo[:5],           # TOP 5 lô 2 số cuối
        'top_lo_xien': top_lo_xien[:5], # TOP 5 lô xiên
        'top_dau_2so': top_dau_2so[:3], # TOP 3 đầu 2 số
        'top_so_cuoi': top_so_cuoi[:3], # TOP 3 số cuối giải đặc biệt
        'total_days': total_days
    }

def send_message():
    try:
        now = datetime.now()
        date_now = now.strftime("%d/%m/%Y")
        time_now = now.strftime("%H:%M:%S")
        
        # Lấy dữ liệu & tính toán
        history = get_xsmb_history()
        data = calculate_frequency(history)
        
        # Tạo nội dung tin nhắn
        text = f"""🤖 BOT DỰ ĐOÁN XỔ SỐ MIỀN BẮC
📅 Ngày nhập dữ liệu: {date_now}
📆 Dự đoán cho ngày: {date_now}
📊 Dữ liệu phân tích: {data['total_days']} ngày gần nhất
⚠️ CHỈ THAM KHẢO - KHÔNG ĐẢM BẢO CHẮC CHẮN!
🎲 Xổ số hoàn toàn ngẫu nhiên, kết quả quá khứ không dự đoán tương lai. Chơi có trách nhiệm!

🎯 TOP 3 CẶP LÔ TỶ LỆ CAO NHẤT
🥇 {data['top_lo'][0]['number']} - {data['top_lo'][0]['percent']}% ({data['top_lo'][0]['count']} lần)
🥈 {data['top_lo'][1]['number']} - {data['top_lo'][1]['percent']}% ({data['top_lo'][1]['count']} lần)
🥉 {data['top_lo'][2]['number']} - {data['top_lo'][2]['percent']}% ({data['top_lo'][2]['count']} lần)

🎯 2 CẶP LÔ XIÊN TỶ LỆ CAO
🥇 {data['top_lo_xien'][0]['number']} - {data['top_lo_xien'][0]['percent']}% ({data['top_lo_xien'][0]['count']} lần)
🥈 {data['top_lo_xien'][1]['number']} - {data['top_lo_xien'][1]['percent']}% ({data['top_lo_xien'][1]['count']} lần)

🎯 ĐẦU SỐ 2 SỐ CUỐI GIẢI ĐẶC BIỆT TỶ LỆ CAO NHẤT
🥇 {data['top_so_cuoi'][0]['number']} - {data['top_so_cuoi'][0]['percent']}% ({data['top_so_cuoi'][0]['count']} lần)

🎲 Chơi có trách nhiệm - Chỉ giải trí!
"""
        bot.send_message(CHAT_ID, text)
        print(f"✅ [{time_now}] Đã gửi tin nhắn có tính toán tỷ lệ!")
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi: {e}")
        return False

if __name__ == "__main__":
    print("🚀 BOT CÓ LOGIC TÍNH TỶ LỆ ĐANG KHỞI ĐỘNG...")
    print(f"📌 Chat ID: {CHAT_ID}")
    
    send_message()
    
    # VÒNG LẶP - Test mỗi 1 phút
    print("⏰ Bắt đầu vòng lặp - Gửi mỗi 1 phút...")
    while True:
        try:
            time.sleep(60)  # 60 giây = 1 phút
            send_message()
        except Exception as e:
            print(f"🔄 Lỗi vòng lặp: {e} - Thử lại sau 60s...")
            time.sleep(60)
