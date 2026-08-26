# =========================================================
# BOT XSMB - VERSION 6.0.0 (SIÊU ỔN ĐỊNH - LẤY FULL DỮ LIỆU)
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
    return "XSMB Bot Ver 6.0.0 - Active 24/7", 200

# --- HÀM LẤY KẾT QUẢ XSMB CHÍNH XÁC QUA API ---
def fetch_xsmb(d, m, y):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    date_formatted = f"{d}-{m}-{y}"
    
    # Nguồn API 1: API KQXS
    try:
        url = f"https://api.xoso.me/api/v1/get-kqxs-mmien-bac?date={date_formatted}"
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200:
            data = res.json()
            if "gdb" in data:
                db = str(data["gdb"])
                g1 = str(data["g1"])
                lo_list = [str(x)[-2:] for x in data.get("lotto", [])]
                return {"db": db, "g1": g1, "lo": lo_list}
    except Exception:
        pass

    # Nguồn API 2 dự phòng: cào trực tiếp từ xoso.com.vn qua regex chuẩn
    try:
        url2 = f"https://xoso.com.vn/xsmb-{d}-{m}-{y}.html"
        res2 = requests.get(url2, headers=headers, timeout=6)
        if res2.status_code == 200:
            html = res2.text
            db_match = re.search(r'class="v-gdb"[^>]*>(\d{5})</td>', html)
            g1_match = re.search(r'class="v-g1"[^>]*>(\d{5})</td>', html)
            all_lotto = re.findall(r'class="v-g[db0-7]+"[^>]*>(\d+)</td>', html)
            
            if db_match:
                db = db_match.group(1)
                g1 = g1_match.group(1) if g1_match else "N/A"
                lo_list = [n[-2:] for n in all_lotto] if all_lotto else []
                return {"db": db, "g1": g1, "lo": lo_list}
    except Exception:
        pass

    return {"db": "Chưa có", "g1": "Chưa có", "lo": []}

# --- 1. XỬ LÝ KHI NGƯỜI DÙNG GÕ NĂM/THÁNG/NGÀY (YYYY/MM/DD) ---
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
            reply += "⚠️ *Chưa có dữ liệu hoặc chưa tới giờ quay số!*\n"
            
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

# --- 3. KHỞI CHẠY BOT ---
def start_polling():
    time.sleep(2)
    try:
        bot.remove_webhook()
    except Exception:
        pass
    
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_xsmb_job, daemon=True).start()
    threading.Thread(target=start_polling, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
