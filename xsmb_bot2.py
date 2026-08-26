# =========================================================
# BOT XSMB - VERSION 9.2.0 (FIX TRIỆT ĐỂ LỖI FETCH DATA)
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

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfyeby4DsBh6MLUH-XYdgk6znzDyeNsehSI6CqGiHFgU-XJ4k_WBD0sXasDx55bfW4F-ktGOQ/exec"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@app.route('/')
def home():
    return "XSMB Bot Ver 9.2.0 - Active 24/7", 200

# --- HÀM LẤY KẾT QUẢ QUA GOOGLE PROXY ---
def fetch_xsmb(d, m, y):
    date_formatted = f"{d}-{m}-{y}"
    try:
        # Gửi chuẩn tham số date=DD-MM-YYYY
        params = {"date": date_formatted}
        res = requests.get(GOOGLE_SCRIPT_URL, params=params, timeout=15, allow_redirects=True)
        
        if res.status_code == 200:
            data = res.json()
            db = data.get("db", "Chưa có")
            g1 = data.get("g1", "Chưa có")
            return {"db": db, "g1": g1}
    except Exception as e:
        print(f"Lỗi truy vấn Google Script: {e}")

    return {"db": "Chưa có", "g1": "Chưa có"}

# --- 1. XỬ LÝ KHI NGƯỜI DÙNG GÕ NGÀY (YYYY/MM/DD) ---
@bot.message_handler(func=lambda msg: True)
def handle_user_message(message):
    text = message.text.strip()
    match = re.search(r'(\d{4})[/-]?(\d{2})[/-]?(\d{2})', text)
    if match:
        y, m, d = match.group(1), match.group(2), match.group(3)
        display_date = f"{y}/{m}/{d}"
        
        # Đảm bảo d, m đủ 2 chữ số dạng chuỗi
        d_str = str(int(d)).zfill(2)
        m_str = str(int(m)).zfill(2)
        
        data = fetch_xsmb(d_str, m_str, y)
        
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
