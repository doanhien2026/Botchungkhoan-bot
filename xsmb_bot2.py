# =========================================================
# BOT XSMB - VERSION 10.1.0 (ĐA NGUỒN TỰ ĐỘNG FALLBACK)
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
    return "XSMB Bot Ver 10.1.0 - Multi-Source Active 24/7", 200

# --- HÀM LẤY KẾT QUẢ VỚI CƠ CHẾ ĐA NGUỒN TỰ ĐỘNG ---
def fetch_xsmb(d, m, y):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    d_int = int(d)
    m_int = int(m)
    date_formatted = f"{d.zfill(2)}-{m.zfill(2)}-{y}"

    # --- NGUỒN 1: XOSODAIPHAT ---
    try:
        url1 = f"https://xosodaiphat.com/xsmb-{date_formatted}.html"
        res1 = requests.get(url1, headers=headers, timeout=6)
        if res1.status_code == 200:
            html = res1.text
            db_m = re.search(r'id="mb_giai_dacbiet"[^>]*>[\s\S]*?(\d{5})[\s\S]*?</td>', html) or \
                   re.search(r'class="v-gdb"[^>]*>[\s\S]*?(\d{5})[\s\S]*?</td>', html)
            g1_m = re.search(r'id="mb_giai_nhat"[^>]*>[\s\S]*?(\d{5})[\s\S]*?</td>', html) or \
                   re.search(r'class="v-g1"[^>]*>[\s\S]*?(\d{5})[\s\S]*?</td>', html)
            
            db = db_m.group(1) if db_m else "Chưa có"
            g1 = g1_m.group(1) if g1_m else "Chưa có"
            
            if db != "Chưa có":
                print("Lấy thành công từ Nguồn 1 (Xosodaiphat)")
                return {"db": db, "g1": g1}
    except Exception as e:
        print(f"Nguồn 1 lỗi: {e}")

    # --- NGUỒN 2: XSKT (KHI NGUỒN 1 THẤT BẠI) ---
    try:
        url2 = f"https://xskt.com.vn/xsmb/ngay-{d_int}-{m_int}-{y}"
        res2 = requests.get(url2, headers=headers, timeout=6)
        if res2.status_code == 200:
            html = res2.text
            db_m = re.search(r'class="v-gdb[^"]*"[^>]*>(\d{5})<', html) or \
                   re.search(r'v-gdb[^>]*>[\s\S]*?(\d{5})', html)
            g1_m = re.search(r'class="v-g1[^"]*"[^>]*>(\d{5})<', html) or \
                   re.search(r'v-g1[^>]*>[\s\S]*?(\d{5})', html)
            
            db = db_m.group(1) if db_m else "Chưa có"
            g1 = g1_m.group(1) if g1_m else "Chưa có"
            
            if db != "Chưa có":
                print("Lấy thành công từ Nguồn 2 (XSKT)")
                return {"db": db, "g1": g1}
    except Exception as e:
        print(f"Nguồn 2 lỗi: {e}")

    # --- NGUỒN 3: XOSO.COM.VN (DỰ PHÒNG CUỐI CÙNG) ---
    try:
        url3 = f"https://xoso.com.vn/xsmb-{d.zfill(2)}-{m.zfill(2)}-{y}.html"
        res3 = requests.get(url3, headers=headers, timeout=6)
        if res3.status_code == 200:
            html = res3.text
            db_m = re.search(r'class="cls_giai_dac_biet"[^>]*>[\s\S]*?(\d{5})[\s\S]*?<', html) or \
                   re.search(r'class="special-code"[^>]*>(\d{5})<', html)
            g1_m = re.search(r'class="cls_giai_nhat"[^>]*>[\s\S]*?(\d{5})[\s\S]*?<', html)
            
            db = db_m.group(1) if db_m else "Chưa có"
            g1 = g1_m.group(1) if g1_m else "Chưa có"
            
            if db != "Chưa có":
                print("Lấy thành công từ Nguồn 3 (Xoso.com.vn)")
                return {"db": db, "g1": g1}
    except Exception as e:
        print(f"Nguồn 3 lỗi: {e}")

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
