import os
import time
import telebot
import requests
from datetime import datetime, timedelta
from flask import Flask
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get('BOT2_TOKEN')
CHAT_ID = os.environ.get('CHANNEL_ID')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Trang web để UptimeRobot gọi
@app.route('/')
def home():
    return "✅ BOT XSMB ĐANG CHẠY - Hoạt động bình thường!"

@app.route('/health')
def health():
    return "ok"

# ==============================================
# 🧠 LẤY DỮ LIỆU KẾT QUẢ XSMB THỰC TẾ
# ==============================================
def lay_du_lieu_xsmb(ngay_ve=90):
    """
    Lấy kết quả XSMB trong N ngày gần nhất từ nguồn dữ liệu
    Trả về danh sách kết quả: date, dac_biet, giai_nhat, ...
    """
    du_lieu = []
    today = datetime.now()
    
    for i in range(ngay_ve):
        ngay = today - timedelta(days=i)
        ngay_str = ngay.strftime("%d-%m-%Y")
        
        try:
            # Nguồn dữ liệu: có thể thay bằng API khác nếu cần
            url = f"https://xsmb.vn/ngay/{ngay_str}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # ==== PHÂN TÍCH DỮ LIỆU (cần điều chỉnh theo cấu trúc trang) ====
                # Giải đặc biệt - 5 số
                db_tag = soup.find('td', class_='giai-dacbiet')
                dac_biet = db_tag.get_text(strip=True) if db_tag else "00000"
                
                # Giải nhất - 4 số
                gn_tag = soup.find('td', class_='giai-nhat')
                giai_nhat = gn_tag.get_text(strip=True) if gn_tag else "0000"
                
                du_lieu.append({
                    'date': ngay_str,
                    'dac_biet': dac_biet,
                    'giai_nhat': giai_nhat
                })
            print(f"📥 Đã lấy dữ liệu ngày {ngay_str}")
        except Exception as e:
            print(f"⚠️ Lỗi lấy dữ liệu ngày {ngay_str}: {e}")
            continue
    
    return du_lieu

# ==============================================
# 📊 TÍNH TỶ LỆ TỪ DỮ LIỆU LỊCH SỬ
# ==============================================
def tinh_tan_suat(du_lieu):
    """
    Đếm số lần xuất hiện và tính tỷ lệ %
    """
    lo_2so_cuoi = {}    # Lô 2 số cuối giải đặc biệt
    so_cuoi_db = {}     # Số cuối giải đặc biệt
    lo_xien = {}        # Lô xiên 2 số liên tiếp
    
    tong_ngay = len(du_lieu)
    if tong_ngay == 0:
        return None
    
    for item in du_lieu:
        db = item['dac_biet']
        if len(db) >= 5:
            hai_so_cuoi = db[-2:]
            so_cuoi = db[-1]
            
            # Đếm lô 2 số cuối
            lo_2so_cuoi[hai_so_cuoi] = lo_2so_cuoi.get(hai_so_cuoi, 0) + 1
            
            # Đếm số cuối giải đặc biệt
            so_cuoi_db[so_cuoi] = so_cuoi_db.get(so_cuoi, 0) + 1
            
            # Đếm lô xiên (cặp số liên tiếp)
            for j in range(len(db) - 1):
                cap = db[j:j+2]
                if cap.isdigit():
                    lo_xien[cap] = lo_xien.get(cap, 0) + 1
    
    # Tính tỷ lệ phần trăm và sắp xếp
    def sap_xep(data_dict):
        ds = []
        for so, dem in data_dict.items():
            ty_le = round((dem / tong_ngay) * 100, 2)
            ds.append({'so': so, 'dem': dem, 'ty_le': ty_le})
        return sorted(ds, key=lambda x: x['ty_le'], reverse=True)
    
    return {
        'top_lo': sap_xep(lo_2so_cuoi)[:5],
        'top_lo_xien': sap_xep(lo_xien)[:5],
        'top_so_cuoi': sap_xep(so_cuoi_db)[:5],
        'tong_ngay': tong_ngay
    }

# ==============================================
# 📩 GỬI TIN NHẮN TELEGRAM
# ==============================================
def gui_tin_nhan():
    try:
        now = datetime.now()
        ngay = now.strftime("%d/%m/%Y")
        gio = now.strftime("%H:%M:%S")
        
        # Lấy dữ liệu & tính toán
        print(f"🔄 [{gio}] Đang lấy dữ liệu & tính toán...")
        du_lieu = lay_du_lieu_xsmb(90)  # Lấy 90 ngày gần nhất
        data = tinh_tan_suat(du_lieu)
        
        if not data or len(data['top_lo']) < 3:
            text = f"""🤖 BOT DỰ ĐOÁN XỔ SỐ MIỀN BẮC
📅 Ngày: {ngay} ⏰ {gio}
⚠️ Đang cập nhật dữ liệu, thử lại sau!
"""
        else:
            text = f"""🤖 BOT DỰ ĐOÁN XỔ SỐ MIỀN BẮC
📅 Ngày nhập dữ liệu: {ngay}
📆 Dự đoán cho ngày: {ngay}
📊 Dữ liệu phân tích: {data['tong_ngay']} ngày gần nhất
⚠️ CHỈ THAM KHẢO - KHÔNG ĐẢM BẢO CHẮC CHẮN!
🎲 Xổ số hoàn toàn ngẫu nhiên, kết quả quá khứ không dự đoán tương lai. Chơi có trách nhiệm!

🎯 TOP 3 CẶP LÔ TỶ LỆ CAO NHẤT
🥇 {data['top_lo'][0]['so']} - {data['top_lo'][0]['ty_le']}% ({data['top_lo'][0]['dem']} lần)
🥈 {data['top_lo'][1]['so']} - {data['top_lo'][1]['ty_le']}% ({data['top_lo'][1]['dem']} lần)
🥉 {data['top_lo'][2]['so']} - {data['top_lo'][2]['ty_le']}% ({data['top_lo'][2]['dem']} lần)

🎯 2 CẶP LÔ XIÊN TỶ LỆ CAO
🥇 {data['top_lo_xien'][0]['so']} - {data['top_lo_xien'][0]['ty_le']}% ({data['top_lo_xien'][0]['dem']} lần)
🥈 {data['top_lo_xien'][1]['so']} - {data['top_lo_xien'][1]['ty_le']}% ({data['top_lo_xien'][1]['dem']} lần)

🎯 ĐẦU SỐ 2 SỐ CUỐI GIẢI ĐẶC BIỆT TỶ LỆ CAO NHẤT
🥇 {data['top_so_cuoi'][0]['so']} - {data['top_so_cuoi'][0]['ty_le']}% ({data['top_so_cuoi'][0]['dem']} lần)

🎲 Chơi có trách nhiệm - Chỉ giải trí!
"""
        
        bot.send_message(CHAT_ID, text)
        print(f"✅ [{gio}] Đã gửi tin nhắn có tính toán tỷ lệ!")
    except Exception as e:
        print(f"❌ Lỗi gửi: {e}")

# ==============================================
# 🚀 CHẠY BOT
# ==============================================
def chay_bot():
    print("⏰ Bắt đầu vòng lặp - Gửi mỗi 1 PHÚT...")
    gui_tin_nhan()  # Gửi lần đầu ngay khi khởi động
    while True:
        time.sleep(60)  # 60 GIÂY = 1 PHÚT - TEST NHANH
        gui_tin_nhan()

if __name__ == "__main__":
    print("🚀 BOT XSMB CÓ LOGIC DỮ LIỆU ĐANG KHỞI ĐỘNG...")
    print(f"📌 Chat ID: {CHAT_ID}")
    
    # Khởi động luồng gửi tin nhắn
    from threading import Thread
    Thread(target=chay_bot).start()
    
    # Chạy web server để UptimeRobot giữ sống
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
