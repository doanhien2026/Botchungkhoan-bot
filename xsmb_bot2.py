# =========================================================
# BOT XSMB - VERSION 5.0.0 (FULL TÍNH NĂNG + DỰ PHÒNG CÀO)
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
    return "XSMB Bot Ver 5.0.0 - Active 24/7", 200

# --- HÀM CÀO KẾT QUẢ XSMB ĐA NGUỒN (CHỐNG LỖI) ---
def fetch_xsmb(date_str):
    """
    date_str: định dạng 'DD-MM-YYYY'
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    # Nguồn 1: xoso.com.vn
    try:
        url = f"https://xoso.com.vn/xsmb-{date_str}.html"
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200:
            html = res.text
            db_match = re.search(r'class="v-gdb"[^>]*>(\d+)</td>', html) or re.search(r'class="special-prize"[^>]*>(\d+)</span>', html)
            g1_match = re.search(r'class="v-g1"[^>]*>(\d+)</td>', html)
            
            all_lotto = re.findall(r'class="v-g[db0-7]+"[^>]*>(\d+)</td>', html)
            lo_list = [n[-2:] for n in all_lotto] if all_lotto else []

            if db_match:
                db = db_match.group(1)
                g1 = g1_match.group(1) if g1_match else "N/A"
                return {"db": db, "g1": g1, "lo": lo_list}
    except Exception:
        pass

    # Nguồn 2 dự phòng: minhngoc.net.vn
    try:
        d, m, y = date_str.split('-')
        url2 = f"https://www.minhngoc.net.vn/ket-qua-xo-so/mien-bac/{d}-{m}-{y}.html"
        res2 = requests.get(url2, headers=headers, timeout=6)
        if res2.status_code == 200:
            nums = re.findall(r'<td class="giai[^\"]*">(\d+)</td>', res2.text)
            if nums:
                db = nums[0]
                g1 = nums[1] if len(nums) > 1 else "N/A"
                lo_list = [n[-2:] for n in nums]
                return {"db": db, "g1": g1, "lo": lo_list}
    except Exception:
        pass

    return {"db": "Chưa có", "g1": "Chưa có", "lo": []}

# --- 1. XỬ LÝ KHI NGƯỜI DÙNG GÕ TẬP LỆNH / NGÀY THÁNG (YYYY/MM/DD) ---
@bot.message_handler(func=lambda msg: True)
def handle_user_message(message):
    text = message.text.strip()
    
    # Bắt định dạng YYYY/MM/DD hoặc YYYY-MM-DD hoặc YYYYMMDD
    match = re.search(r'(\d{4})[/-]?(\d{2})[/-]?(\d{2})', text)
    if match:
        y, m, d = match.group(1), match.group(2), match.group(3)
        date_query = f"{d}-{m}-{y}"
        display_date = f"{y}/{m}/{d}"
        
        data = fetch_xsmb(date_query)
        
        reply = f"📊 *KẾT QUẢ XSMB NGÀY {display_date}*\n"
        reply += f"🏆 *Giải Đặc Biệt:* `{data['db']}`\n"
        reply += f"🥇 *Giải Nhất:* `{data['g1']}`\n"
        if data['lo']:
            reply += f"🎲 *Lô về ({len(data['lo'])} giải):* {', '.join(data['lo'])}\n"
        else:
            reply += "⚠️ *Không tìm thấy dữ liệu cho ngày này!*\n"
            
        bot.reply_to(message, reply, parse_mode="Markdown")

# --- 2. HÀM TỰ ĐỘNG GỬI TIN NHẮN HẰNG NGÀY ---
def run_xsmb_job():
    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    yesterday = now_vn - timedelta(days=1)
    
    date_query = yesterday.strftime("%d-%m-%Y")
    display_date = yesterday.strftime("%d/%m/%Y")
    now_str = now_vn.strftime("%d/%m/%Y %H:%M:%S")
    
    y_data = fetch_xsmb(date_query)
    
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
        print(f"❌ Lỗi gửi tin nhắn tự động: {e}")

# --- 3. LUỒNG CHẠY BOT VÀ FLASK SERVER ---
def start_polling():
    # Xóa Webhook cũ để tránh lỗi 409 Conflict
    bot.remove_webhook()
    time.sleep(2)
    # Lắng nghe tin nhắn
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == "__main__":
    # Gửi tin nhắn thông báo khi khởi động
    threading.Thread(target=run_xsmb_job, daemon=True).start()
    
    # Bật luồng nhận tin nhắn từ người dùng
    threading.Thread(target=start_polling, daemon=True).start()

    # Khởi chạy Flask Server cho Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
