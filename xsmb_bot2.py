# =========================================================
# BOT XSMB - VERSION 4.2.0 (CÀO KẾT QUẢ & FIX LỖI 409)
# =========================================================
import os
import time
import requests
import threading
from bs4 import BeautifulSoup
from flask import Flask
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# --- CẤU HÌNH BOT XSMB ---
TELEGRAM_TOKEN = "8901722608:AAHnHfYsR8ilnHCHRaDUedA1ra1p0gPWda8"
CHAT_ID = "1030583610"

@app.route('/')
def home():
    return "XSMB Bot Ver 4.2.0 - Active 24/7", 200

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, json=payload, timeout=12)
        return res.status_code == 200
    except Exception as e:
        print(f"❌ Lỗi gửi Telegram: {e}")
        return False

# --- CÀO KẾT QUẢ XSMB NGÀY HÔM QUA ---
def get_yesterday_xsmb():
    vn_tz = timezone(timedelta(hours=7))
    yesterday = datetime.now(vn_tz) - timedelta(days=1)
    date_str = yesterday.strftime("%d-%m-%Y")
    display_date = yesterday.strftime("%d/%m/%Y")
    
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://xoso.com.vn/xsmb-{date_str}.html"
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            db_el = soup.find("span", class_="special-prize") or soup.find("td", class_="v-gdb")
            db = db_el.text.strip() if db_el else "N/A"
            
            g1_el = soup.find("td", class_="v-g1")
            g1 = g1_el.text.strip() if g1_el else "N/A"
            
            return {"date": display_date, "db": db, "g1": g1}
    except Exception as e:
        print(f"❌ Lỗi cào dữ liệu: {e}")
        
    return {"date": display_date, "db": "Chưa có", "g1": "Chưa có"}

def run_xsmb_job():
    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    now_str = now_vn.strftime("%d/%m/%Y %H:%M:%S")
    
    y_data = get_yesterday_xsmb()
    
    msg = f"📊 *KẾT QUẢ XSMB HÔM QUA ({y_data['date']})*\n"
    msg += f"🏆 *Đặc biệt:* `{y_data['db']}`\n"
    msg += f"🥇 *Giải nhất:* `{y_data['g1']}`\n"
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
    
    send_telegram(msg)

def start_bot_thread():
    time.sleep(5)
    run_xsmb_job()

if __name__ == "__main__":
    t = threading.Thread(target=start_bot_thread)
    t.daemon = True
    t.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
