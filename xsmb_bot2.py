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

@app.route('/')
def home():
    return "✅ BOT XSMB ĐANG CHẠY - Dữ liệu từ xstd.mobi"

@app.route('/health')
def health():
    return "ok"

# ==============================================
# 🧠 LẤY DỮ LIỆU KẾT QUẢ XSMB THỰC TỪ xstd.mobi
# ==============================================
def lay_du_lieu_xsmb(ngay_ve=30):
    """
    Lấy kết quả XSMB từ xstd.mobi - nguồn dữ liệu đáng tin cậy
    Trả về danh sách: date, dac_biet (5 số)
    """
    du_lieu = []
    today = datetime.now()
    
    for i in range(ngay_ve):
        ngay = today - timedelta(days=i)
        ngay_str = ngay.strftime("%d/%m/%Y")
        ngay_url = ngay.strftime("%d-%m-%Y")
        
        try:
            url = f"https://xstd.mobi/xsmb-ngay-{ngay_url}.html"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Tìm giải đặc biệt - cấu trúc thực tế của xstd.mobi
                db_tag = soup.find('strong', class_='giai-dacbiet') or soup.find('span', class_='db')
                
                if db_tag:
                    dac_biet = db_tag.get_text(strip=True).replace(' ', '').zfill(5)
                    if dac_biet.isdigit() and len(dac_biet) == 5:
                        du_lieu.append({
                            'date': ngay_str,
                            'dac_biet': dac_biet
                        })
                        print(f"✅ Đã lấy: {ngay_str} | Đặc biệt: {dac_biet}")
            
            time.sleep(1)  # Tránh bị chặn quá nhiều yêu cầu
            
        except Exception as e:
            print(f"⚠️ Lỗi {ngay_str}: {e}")
            continue
    
    return du_lieu

# ==============================================
# 📊 TÍNH TỶ LỆ TỪ DỮ LIỆU THỰC
# ==============================================
def tinh_tan_suat(du_lieu):
    lo_2so_cuoi = {}
    so_cuoi_db = {}
    lo_xien = {}
    
    tong_ngay = len(du_lieu)
    if tong_ngay == 0:
        return None
    
    for item in du_lieu:
        db = item['dac_biet']
        if len(db) == 5 and db.isdigit():
            hai_so_cuoi = db[-2:]
            so_cuoi = db[-1]
            
            # Đếm lô 2 số cuối
            lo_2so_cuoi[hai_so_cuoi] = lo_2so_cuoi.get(hai_so_cuoi, 0) + 1
            
            # Đếm số cuối
            so_cuoi_db[so_cuoi] = so_cuoi_db.get(so_cuoi, 0) + 1
            
            # Đếm lô xiên
            for j in range(4):
                cap = db[j:j+2]
                lo_xien[cap] = lo_xien.get(cap, 0) + 1
    
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
# 📩 GỬI TIN NHẮN
# ==============================================
def gui_tin_nhan():
    try:
        now = datetime.now()
        ngay = now.strftime("%d/%m/%Y")
        gio = now.strftime("%H:%M:%S")
        
        print(f"\n🔄 [{gio}] Đang lấy dữ liệu & tính toán...")
        du_lieu = lay_du_lieu_xsmb(30)  # Lấy 30 ngày gần nhất
        data = tinh_tan_suat(du_lieu)
        
        if not data or data['tong_ngay'] < 10:
            text = f"""🤖 BOT DỰ ĐOÁN XỔ SỐ MIỀN BẮC
📅 Ngày: {ngay} ⏰ {gio}
⚠️ Đang thu thập đủ dữ liệu ({data['tong_ngay'] if data else 0}/30 ngày)...
🔄 Sẽ tính toán chính xác khi có đủ dữ liệu!
"""
        else:
            text = f"""🤖 BOT DỰ ĐOÁN XỔ SỐ MIỀN BẮC
📅 Ngày nhập dữ liệu: {ngay}
📆 Dự đoán cho ngày: {ngay}
📊 Dữ liệu phân tích: {data['tong_ngay']} ngày gần nhất (từ xstd.mobi)
⚠️ CHỈ THAM KHẢO - KHÔNG ĐẢM BẢO CHẮC CHẮN!
🎲 Xổ số hoàn toàn ngẫu nhiên, kết quả quá khứ không dự đoán tương lai. Chơi có trách nhiệm!

🎯 TOP 3 CẶP LÔ TỶ LỆ CAO NHẤT
🥇 {data['top_lo'][0]['so']} - {data['top_lo'][0]['ty_le']}% ({data['top_lo'][0]['dem']} lần)
🥈 {data['top_lo'][1]['so']} - {data['top_lo'][1]['ty_le']}% ({data['top_lo'][1]['dem']} lần)
🥉 {data['top_lo'][2]['so']} - {data['top_lo'][2]['ty_le']}% ({data['top_lo'][2]['dem']} lần)

🎯 2 CẶP LÔ XIÊN TỶ LỆ CAO
🥇 {data['top_lo_xien'][0]['so']} - {data['top_lo_xien'][0]['ty_le']}% ({data['top_lo_xien'][0]['dem']} lần)
🥈 {data['top_lo_xien'][1]['so']} - {data['top_lo_xien'][1]['ty_le']}% ({data['top_lo_xien'][1]['dem']} lần)

🎯 SỐ CUỐI GIẢI ĐẶC BIỆT TỶ LỆ CAO NHẤT
🥇 {data['top_so_cuoi'][0]['so']} - {data['top_so_cuoi'][0]['ty_le']}% ({data['top_so_cuoi'][0]['dem']} lần)

🎲 Chơi có trách nhiệm - Chỉ giải trí!
"""
        
        bot.send_message(CHAT_ID, text)
        print(f"✅ [{gio}] Đã gửi! Dữ liệu: {data['tong_ngay'] if data else 0} ngày")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

# ==============================================
# 🚀 CHẠY BOT
# ==============================================
def chay_bot():
    print("⏰ Bắt đầu vòng lặp - Gửi mỗi 1 PHÚT...")
    gui_tin_nhan()
    while True:
        time.sleep(60)  # 60 GIÂY = 1 PHÚT - TEST NHANH
        gui_tin_nhan()

if __name__ == "__main__":
    print("🚀 BOT XSMB - DỮ LIỆU THỰC TỪ xstd.mobi")
    print(f"📌 Chat ID: {CHAT_ID}")
    
    from threading import Thread
    Thread(target=chay_bot).start()
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
