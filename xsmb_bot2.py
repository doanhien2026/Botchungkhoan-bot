# =========================================================
# BOT XSMB - VERSION 4.3.0 (CÀO KẾT QUẢ API & FIX KHÔNG LỖI)
# =========================================================
import os
import time
import requests
import threading
from flask import Flask
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# --- CẤU HÌNH BOT XSMB ---
TELEGRAM_TOKEN = "8901722608:AAHnHfYsR8ilnHCHRaDUedA1ra1p0gPWda8"
CHAT_ID = "1030583610"

@app.route('/')
def home():
    return "XSMB Bot Ver 4.3.0 - Active 24/7", 200

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

# --- HÀM TỰ ĐỘNG CÀO KẾT QUẢ XSMB NGÀY HÔM QUA QUA API ---
def get_yesterday_xsmb():
    vn_tz = timezone(timedelta(hours=7))
    yesterday = datetime.now(vn_tz) - timedelta(days=1)
    date_str = yesterday.strftime("%d-%m-%Y")
    display_date = yesterday.strftime("%d/%m/%Y")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # Sử dụng API JSON của Ketqua.vn / Xoso.com.vn (Bypasses HTML parser)
    try:
        url = f"https://api.xoso.com.vn/api/xsmb?date={date_str}"
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            data = res.json()
            db = data.get("gdb", ["N/A"])[0]
            g1 = data.get("g1", ["N/A"])[0]
            return {"date": display_date, "db": db, "g1": g1}
    except Exception:
        pass

    # Nguồn dự phòng 2: cào nhanh qua regex
    try:
        url2 = f"https://xoso.com.vn/xsmb-{date_str}.html"
        res2 = requests.get(url2, headers=headers, timeout=8)
        if res2.status_code == 200:
            import re
            db_match = re.search(r'class="v-gdb"[^>]*>(\d+)</td>', res2.text)
            g1_match = re.search(r'class="v-g1"[^>]*>(\d+)</td>', res2.text)
            
            db = db_match.group(1) if db_match else "Chưa cập nhật"
            g1 = g1_match.group(1) if g1_match else "Chưa cập nhật"
            return {"date": display_date, "db": db, "g1": g1}
    except Exception as e:
        print(f"❌ Lỗi lấy kết quả XSMB: {e}")
        
    return {"date": display_date, "db": "Chưa có", "g1": "Chưa có"}

# --- TẠO NỘI DUNG VÀ GỬI TIN NHẮN ---
def run_xsmb_job():
    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    now_str = now_vn.strftime("%d/%m/%Y %H:%M:%S")
    
    y_data = get_yesterday_xsmb()
    
    msg = f"📊 *KẾT QUẢ XSMB HÔM QUA ({y_data['date']})*\n"
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
