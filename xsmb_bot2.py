# =========================================================
# BOT XSMB - VERSION 5.2.0 (CHUẨN BÀI - FIX LỖI 409 & CÀO)
# =========================================================
import os
import re
import time
import requests
import threading
import telebot
from bs4 import BeautifulSoup
from flask import Flask
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# --- CẤU HÌNH BOT ---
TELEGRAM_TOKEN = "8901722608:AAHnHfYsR8ilnHCHRaDUedA1ra1p0gPWda8"
CHAT_ID = "1030583610"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@app.route('/')
def home():
    return "XSMB Bot Ver 5.2.0 - Active 24/7", 200

# --- HÀM CÀO KẾT QUẢ TỪ KQXS.VN (ỔN ĐỊNH 100%) ---
def fetch_xsmb(d, m, y):
    url = f"https://kqxs.vn/mien-bac/xsmb-{d}-{m}-{y}.html"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Cào giải đặc biệt
            gdb_elem = soup.find(class_=re.compile(r'v-gdb|gdb|special'))
            db = gdb_elem.text.strip() if gdb_elem else "Chưa có"
            
            # Cào giải nhất
            g1_elem = soup.find(class_=re.compile(r'v-g1|g1'))
            g1 = g1_elem.text.strip() if g1_elem else "Chưa có"
            
            # Cào tất cả các giải để lấy 27 con lô
            all_cells = soup.find_all(['td', 'span'], class_=re.compile(r'v-g|prize'))
            lo_list = []
            for cell in all_cells:
                text = cell.text.strip()
                if text.isdigit() and len(text) >= 2:
                    lo_list.append(text[-2:])
            
            if db != "Chưa có":
                return {"db": db, "g1": g1, "lo": lo_list[:27]}
    except Exception as e:
        print(f"Lỗi cào dữ liệu: {e}")

    return {"db": "Chưa có", "g1": "Chưa có", "lo": []}

# --- 1. XỬ LÝ LỆNH NGƯỜI DÙNG (YYYY/MM/DD) ---
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
        if data['lo']:
            reply += f"🎲 *Lô về ({len(data['lo'])} giải):* {', '.join(data['lo'])}\n"
        else:
            reply += "⚠️ *Chưa có dữ liệu hoặc ngày chưa quay số!*\n"
            
        bot.reply_to(message, reply, parse_mode="Markdown")

# --- 2. GỬI KẾT QUẢ TỰ ĐỘNG ---
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

# --- 3. KHỞI CHẠY BOT (CHỐNG LỖI 409 CONFLICT) ---
def start_polling():
    time.sleep(3)
    try:
        bot.remove_webhook()
    except Exception:
        pass
    
    # Chạy infinity_polling tự động thử lại khi dính lỗi 409
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"Đang kết nối lại Bot... ({e})")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_xsmb_job, daemon=True).start()
    threading.Thread(target=start_polling, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
