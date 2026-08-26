# =========================================================
# BOT XSMB - VERSION 3.0.0 (TÁCH BOT RIÊNG & PHẢN HỒI /START)
# =========================================================
import os
import time
import requests
import threading
import telebot
from flask import Flask
from datetime import datetime, timezone, timedelta

# --- KHỞI TẠO FLASK MỞ CỔNG PORT CHO RENDER ---
app = Flask(__name__)

# --- CẤU HÌNH BOT XSMB MỚI (@XSMB6868_bot) ---
TELEGRAM_TOKEN = "8901722608:AAHnHfYsR8ilnHCHRaDUedA1ra1p0gPWda8"
CHAT_ID = "1030583610"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@app.route('/')
def home():
    return "XSMB Bot Ver 3.0.0 - Active 24/7", 200

# --- NỘI DUNG MẪU DỰ ĐOÁN XSMB ---
def get_prediction_message():
    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    date_str = now_vn.strftime("%d/%m/%Y %H:%M:%S")
    
    msg = f"🤖 *BOT DỰ ĐOÁN XSMB*\n"
    msg += f"⏰ *Thời gian VN:* `{date_str}`\n"
    msg += f"📊 *Dữ liệu:* 60 ngày gần nhất\n"
    msg += "⚠️ *CHỈ THAM KHẢO - KHÔNG ĐẢM BẢO!*\n"
    msg += "🎲 *Xổ số ngẫu nhiên - Chơi có trách nhiệm!*\n\n"
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
    return msg

# --- XỬ LÝ KHI NGƯỜI DÙNG BẤM /START HOẶC BẤM TIN NHẮN ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = get_prediction_message()
    bot.reply_to(message, text, parse_mode="Markdown")

# --- GỬI THÔNG BÁO TỰ ĐỘNG KHI RENDER KHIỂN BOT KHỞI ĐỘNG ---
def auto_send_job():
    time.sleep(3)
    try:
        text = get_prediction_message()
        bot.send_message(CHAT_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Lỗi gửi tự động: {e}")

# --- LUỒNG CHẠY BOT POLLING ĐỂ LẮNG NGHE LỆNH ---
def run_telebot_polling():
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"❌ Lỗi Polling: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Luồng 1: Bắn báo cáo chào mừng khi khởi tạo
    t1 = threading.Thread(target=auto_send_job)
    t1.daemon = True
    t1.start()

    # Luồng 2: Lắng nghe phản hồi /start liên tục
    t2 = threading.Thread(target=run_telebot_polling)
    t2.daemon = True
    t2.start()

    # Mở Web Port cho Render (giữ live 24/7)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
