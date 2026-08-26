# =========================================================
# BOT XSMB - VERSION 2.3.0 (FIX PORT TIMEOUT & RUNNER)
# =========================================================
import os
import sys
import time
import requests
import threading
from flask import Flask
from datetime import datetime, timezone, timedelta

# --- KHỞI TẠO FLASK ĐỂ MỞ CỔNG PORT CHO RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "XSMB Bot Ver 2.3.0 - Active 24/7", 200

# --- THÔNG SỐ CẤU HÌNH ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1030583610")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=12)
        return res.status_code == 200
    except Exception as e:
        print(f"❌ Lỗi gửi Telegram: {e}")
        return False

def run_xsmb_task():
    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    now_str = now_vn.strftime("%d/%m/%Y %H:%M:%S")
    
    msg = f"🎉 *BÁO CÁO XSMB (VER 2.3.0)*\n"
    msg += f"⏰ *Thời gian VN:* `{now_str}`\n"
    msg += "-----------------------------------\n"
    msg += "Bot XSMB đã kết nối thành công và đang hoạt động!"
    
    send_telegram(msg)

def start_bot_thread():
    time.sleep(3)
    run_xsmb_task()

if __name__ == "__main__":
    # Chạy tác vụ Bot trong luồng riêng
    t = threading.Thread(target=start_bot_thread)
    t.daemon = True
    t.start()
    
    # Lắng nghe đúng Port môi trường do Render cấp
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
