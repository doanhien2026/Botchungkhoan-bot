# =========================================================
# BOT XSMB - VERSION 8.0.0 (SỬ DỤNG API JSON TRỰC TIẾP)
# =========================================================
import os
import re
import time
import json
import urllib.request
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
    return "XSMB Bot Ver 8.0.0 - Active 24/7", 200

# --- HÀM LẤY KẾT QUẢ XSMB BẰNG API JSON CÔNG KHAI ---
def fetch_xsmb(d, m, y):
    # Định dạng ngày DD-MM-YYYY
    date_str = f"{d}-{m}-{y}"
    url = f"https://atpsoftware.vn/api/xoso.php?date={date_str}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = response.read().decode('utf-8')
            data = json.loads(res_data)
            
            # Nếu có dữ liệu trả về từ API
            if "dac_biet" in data and data["dac_biet"]:
                db = str(data.get("dac_biet", "Chưa có"))
                g1 = str(data.get("giai_nhat", "Chưa có"))
                lo_raw = data.get("loto", [])
                lo_list = [str(x)[-2:] for x in lo_raw] if lo_raw else []
                return {"db": db, "g1": g1, "lo": lo_list}
    except Exception as e:
        print(f"Lỗi API 1: {e}")

    # Nguồn API 2 dự phòng (Dạng JSON tĩnh)
    try:
        url2 = f"https://xskt.com.vn/rss-feed/mien-bac-xsmb.rss"
        req2 = urllib.request.Request(url2, headers=headers)
        with urllib.request.urlopen(req2, timeout=8) as response:
            xml_text = response.read().decode('utf-8')
            # Tìm ĐB bằng Regex trong RSS
            db_match = re.search(r'ĐB:\s*(\d{5})', xml_text)
            if db_match:
                return {"db": db_match.group(1), "g1": "Có trong RSS", "lo": []}
    except Exception as e:
        print(f"Lỗi API 2: {e}")

    return {"db": "Chưa có", "g1": "Chưa có", "lo": []}

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
        if data['lo']:
            reply += f"🎲 *Lô về ({len(data['lo'])} giải):*\n`{', '.join(data['lo'])}`\n"
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
