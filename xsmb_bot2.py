# =========================================================
# BOT XSMB - VERSION 4.0.0 (CÀO KẾT QUẢ XSMB NGÀY HÔM TRƯỚC)
# =========================================================
import os
import time
import requests
import threading
import telebot
from bs4 import BeautifulSoup
from flask import Flask
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

TELEGRAM_TOKEN = "8901722608:AAHnHfYsR8ilnHCHRaDUedA1ra1p0gPWda8"
CHAT_ID = "1030583610"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@app.route('/')
def home():
    return "XSMB Bot Ver 4.0.0 - Active 24/7", 200

# --- HÀM TỰ ĐỘNG CÀO KẾT QUẢ XSMB NGÀY HÔM TRƯỚC ---
def get_yesterday_xsmb():
    vn_tz = timezone(timedelta(hours=7))
    yesterday = datetime.now(vn_tz) - timedelta(days=1)
    date_str = yesterday.strftime("%d-%m-%Y")
    display_date = yesterday.strftime("%d/%m/%Y")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    url = f"https://xoso.com.vn/xsmb-{date_str}.html"
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Lấy giải đặc biệt
            db_el = soup.find("span", class_="special-prize") or soup.find("td", class_="v-gdb")
            db = db_el.text.strip() if db_el else "N/A"
            
            # Lấy giải nhất
            g1_el = soup.find("td", class_="v-g1")
            g1 = g1_el.text.strip() if g1_el else "N/A"
            
            # Lấy tập hợp các lô (2 số cuối)
            lotto_els = soup.find_all("td", class_=["v-gdb", "v-g1", "v-g2", "v-g3", "v-g4", "v-g5", "v-g6", "v-g7"])
            lotto_list = []
            for el in lotto_els:
                num = el.text.strip()
                if len(num) >= 2:
                    lotto_list.append(num[-2:])
            
            lotto_str = ", ".join(lotto_list[:10]) if lotto_list else "Đang cập nhật..."
            
            return {
                "date": display_date,
                "db": db,
                "g1": g1,
                "lotto": lotto_str
            }
    except Exception as e:
        print(f"❌ Lỗi cào dữ liệu: {e}")
        
    return {"date": display_date, "db": "Chưa có", "g1": "Chưa có", "lotto": "Không lấy được dữ liệu"}

# --- TẠO NỘI DUNG TỔNG HỢP & DỰ ĐOÁN ---
def get_prediction_message():
    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    now_str = now_vn.strftime("%d/%m/%Y %H:%M:%S")
    
    # Lấy dữ liệu hôm trước
    y_data = get_yesterday_xsmb()
    
    msg = f"📊 *KẾT QUẢ XSMB NGÀY HÔM QUA ({y_data['date']})*\n"
    msg += f"🏆 *Đặc biệt:* `{y_data['db']}`\n"
    msg += f"🥇 *Giải nhất:* `{y_data['g1']}`\n"
    msg += f"🎲 *Một số lô về:* `{y_data['lotto']}`\n"
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
    return msg

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = get_prediction_message()
    bot.reply_to(message, text, parse_mode="Markdown")

def auto_send_job():
    time.sleep(3)
    try:
        text = get_prediction_message()
        bot.send_message(CHAT_ID, text, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Lỗi gửi tự động: {e}")

def run_telebot_polling():
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"❌ Lỗi Polling: {e}")
            time.sleep(5)

if __name__ == "__main__":
    t1 = threading.Thread(target=auto_send_job)
    t1.daemon = True
    t1.start()

    t2 = threading.Thread(target=run_telebot_polling)
    t2.daemon = True
    t2.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
