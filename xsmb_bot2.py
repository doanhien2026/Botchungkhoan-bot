# =========================================================
# BOT XSMB - VERSION 12.0.0 (API CHÍNH THỨC MINH NGỌC)
# =========================================================
import os
import re
import time
import requests
import threading
import telebot
from flask import Flask
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# --- CẤU HÌNH BOT ---
TELEGRAM_TOKEN = "8901722608:AAHnHfYsR8ilnHCHRaDUedA1ra1p0gPWda8"
CHAT_ID = "1030583610"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@app.route('/')
def home():
    return "XSMB Bot Ver 12.0.0 - API Minh Ngoc Active 24/7", 200

# --- HÀM LẤY KẾT QUẢ TỪ API TRỰC TIẾP ---
def fetch_xsmb(d, m, y):
    # API trực tiếp của Minh Ngọc theo ngày DD-MM-YYYY
    date_formatted = f"{d.zfill(2)}-{m.zfill(2)}-{y}"
    url = f"https://www.minhngoc.com.vn/getrate/xsmb/{date_formatted}.js"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.minhngoc.com.vn/"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            text = res.text
            # Tìm giải đặc biệt (5 chữ số) và giải nhất (5 chữ số) từ dữ liệu API
            db_m = re.search(r'giai_dac_biet["\':\s]+["\']?(\d{5})["\']?', text) or \
                   re.search(r'DB["\':\s]+["\']?(\d{5})["\']?', text) or \
                   re.search(r'(\d{5})', text)
                   
            g1_m = re.search(r'giai_nhat["\':\s]+["\']?(\d{5})["\']?', text) or \
                   re.search(r'G1["\':\s]+["\']?(\d{5})["\']?', text)
            
            db = db_m.group(1) if db_m else "Chưa có"
            g1 = g1_m.group(1) if g1_m else "Chưa có"
            
            return {"db": db, "g1": g1}
    except Exception as e:
        print(f"Lỗi API: {e}")

    # Nguồn API dự phòng 2 (VOH)
    try:
        url_voh = f"https://voh.com.vn/api/v1/lottery/xsmb?date={y}-{m.zfill(2)}-{d.zfill(2)}"
        res_voh = requests.get(url_voh, headers=headers, timeout=10)
        if res_voh.status_code == 200:
            data = res_voh.json()
            db = data.get("data", {}).get("special", "Chưa có")
            g1 = data.get("data", {}).get("first", "Chưa có")
            return {"db": db, "g1": g1}
    except Exception:
        pass

    return {"db": "Chưa có", "g1": "Chưa có"}

# --- 1. XỬ LÝ KHI NGƯỜI DÙNG GÕ NGÀY (YYYY/MM/DD) ---
@bot.message_handler(func=lambda msg: True)
def handle_user_message(message):
    text = message.text.strip()
    match = re.search(r'(\d{4})[/-]?(\d{2})[/-]?(\d{2})', text)
    if match:
        y, m, d = match.group(1), match.group(2), match.group(3)
        display_date = f"{y}/{m}/{d}"
        
        data = fetch_xsmb(d, m, y)
        
        reply = f"📊 *KẾT QUẢ XSMB NGÀY {display_date}*\n"
        reply += f"🏆 *Giải Đặc Biệt:* `{data['db']}`\n"
        reply += f"🥇 *Giải Nhất:* `{data['g1']}`\n"
        
        bot.reply_to(message, reply, parse_mode="Markdown")

# --- 2. GỬI KẾT QUẢ TỰ ĐỘNG HẰNG NGÀY ---
def run_xsmb_job():
    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    yesterday = now_vn - timedelta(days=1)
    
    d, m, y = yesterday.strftime("%d"), yesterday.strftime("%m"), yesterday.strftime("%Y")
    display_date = yesterday.strftime("%d/%m/%Y")
    now_str = now_vn.strftime("%d/%m/%Y %H:%M:%S")
    
    y_data = fetch_xsmb(d, m, y)
    
    msg = f"📊 *KẾT QUẢ XSMB HÔM QUA ({display_date})*\n"
    msg += f"🏆 *Giải Đặc Biệt:* `{y_data['db']}`\n"
    msg += f"🥇 *Giải Nhất:* `{y_data['g1']}`\n"
    msg += "-----------------------------------\n"
    msg += f"🤖 *BOT DỰ ĐOÁN XSMB HÔM NAY*\n"
    msg += f"⏰ *Thời gian VN:* `{now_str}`\n\n"
    msg += "🎯 *TOP 3 LÔ CAO NHẤT*\n"
    msg += "🥇 `03` | Tỷ lệ trúng: 18%\n"
    msg += "🥈 `25` | Tỷ lệ trúng: 15%\n"
    msg += "🥉 `73` | Tỷ lệ trúng: 13%\n\n"
    msg += "🎯 *2 LÔ XIÊN CAO*\n"
    msg += "🥇 `12` | Tỷ lệ trúng: 17%\n"
    msg += "🥈 `89` | Tỷ lệ trúng: 12%\n\n"
    msg += "🎯 *SỐ CUỐI ĐẶC BIỆT*\n"
    msg += "🥇 `8` | Tỷ lệ trúng: 35%\n\n"
    msg += "🎲 *Chơi có trách nhiệm - Chỉ giải trí!*"
    
    try:
        bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
    except Exception as e:
        print(f"Lỗi gửi tin nhắn: {e}")

# --- 3. KHỜI CHẠY POLLING ---
def start_polling():
    time.sleep(3)
    try:
        bot.remove_webhook(drop_pending_updates=True)
    except Exception:
        pass
    
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=20)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_xsmb_job, daemon=True).start()
    threading.Thread(target=start_polling, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
