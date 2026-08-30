# ==========================================================
# BOT XSMB — V6.4 | /DUDOAN LUÔN TRẢ VỀ KẾT QUẢ
# Token: 8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w
# Bot: @Thongkeso999_bot
# ==========================================================

import telebot
import re
import time
import json
import os
import requests
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from collections import Counter
from bs4 import BeautifulSoup

# ====================== 🔧 CẤU HÌNH ======================
TELEGRAM_TOKEN = "8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w"
CHAT_ID = "1030583610"
CHANNEL_ID = "-1001030583610"
PORT = int(os.environ.get("PORT", 10000))
DATA_FILE = "xsmb_data.json"

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
}

# ====================== 🌐 TRANG CHỦ ======================
@app.route('/')
def home():
    return "✅ Bot XSMB V6.4 — /dudoan luôn trả về kết quả"

# ====================== 💾 DỮ LIỆU ======================
def load_all_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Lỗi đọc dữ liệu: {e}")
        return {}

def save_data(date_str, result):
    data = load_all_data()
    data[date_str] = result
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Đã lưu: {date_str}")
    except Exception as e:
        print(f"⚠️ Lỗi lưu dữ liệu: {e}")

# ====================== 📡 LẤY KẾT QUẢ ======================
def fetch_result(date_str):
    d, m, y = date_str.split("/")
    # Nguồn chính: XOSODAIPHAT
    try:
        url = f"https://xosodaiphat.com/xsmb-{d}-{m}-{y}.html"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        all_5digit = re.findall(r"\b\d{5}\b", soup.get_text())
        if len(all_5digit) < 8:
            return None
        dac_biet = all_5digit[-1]
        giai_nhat = all_5digit[-2]
        loto_set = set(num[-2:] for num in all_5digit)
        return {
            "source": "XOSODAIPHAT",
            "special": dac_biet,
            "g1": giai_nhat,
            "loto": sorted(list(loto_set))[:27]
        }
    except Exception as e:
        print(f"❌ Lỗi lấy kết quả: {e}")
        return None

# ====================== 🧠 DỰ ĐOÁN — ĐƠN GIẢN, CHẮC CHẮN ======================
def get_history(days=60):
    data = load_all_data()
    if not data:
        return [], [], {}
    sorted_dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    limit = min(days, len(sorted_dates))
    lotos = []
    first_digits = []
    history = {}
    for dt in sorted_dates[:limit]:
        res = data[dt]
        history[dt] = res
        if res.get("loto"):
            lotos.extend(res["loto"])
        if res.get("special") and len(res["special"]) == 5:
            first_digits.append(res["special"][0])
            lotos.append(res["special"][-2:])
    return lotos, first_digits, history

def gen_prediction(days=60, target_date=None):
    """LUÔN TRẢ VỀ KẾT QUẢ — KHÔNG ĐỂ TRỐNG"""
    try:
        lotos, first_digits, history = get_history(days)
        
        # Tính top 3 lô
        if lotos:
            freq = Counter(lotos)
            total = len(lotos)
            top3 = freq.most_common(3)
            top3_list = []
            for num, count in top3:
                rate = round(count / total * 100, 1)
                top3_list.append({"num": num, "count": count, "rate": rate})
        else:
            top3_list = [
                {"num": "07", "count": 0, "rate": 0.0},
                {"num": "29", "count": 0, "rate": 0.0},
                {"num": "56", "count": 0, "rate": 0.0}
            ]
        
        # Lô xiên
        xien = [top3_list[0]["num"], top3_list[1]["num"]] if len(top3_list) >= 2 else ["00", "00"]
        
        # Đầu số đề
        if first_digits:
            fc = Counter(first_digits)
            fd, fcnt = fc.most_common(1)[0]
            frate = round(fcnt / len(first_digits) * 100, 1)
        else:
            fd, fcnt, frate = "8", 0, 0.0
        
        target_info = f" — Ngày {target_date}" if target_date else " — Ngày mai"
        lines = [
            f"📊 **DỰ ĐOÁN KẾT QUẢ{target_info}**",
            f"📅 Dựa trên {days} ngày gần nhất",
            "________________________________________",
            "",
            "🎯 **3 CON LÔ TỶ LỆ CAO NHẤT:**"
        ]
        for i, item in enumerate(top3_list, 1):
            lines.append(f"   {i}. `{item['num']}` – {item['count']} lần | {item['rate']}%")
        lines.extend([
            "",
            "🔀 **1 CẶP LÔ XIÊN:**",
            f"   → `{xien[0]} – {xien[1]}`",
            "",
            "🔢 **DỰ KIẾN ĐẦU SỐ ĐỀ:**",
            f"   → Đầu số `{fd}` – {fcnt} lần → {frate}%",
            "",
            "⚠️ *Chỉ tham khảo – Chơi có trách nhiệm!*"
        ])
        return "\n".join(lines)
    
    except Exception as e:
        print(f"❌ Lỗi tính dự đoán: {e}")
        return """📊 **DỰ ĐOÁN KẾT QUẢ — Ngày mai**
________________________________________

🎯 **3 CON LÔ TỶ LỆ CAO NHẤT:**
   1. `07` – 0 lần | 0.0%
   2. `29` – 0 lần | 0.0%
   3. `56` – 0 lần | 0.0%

🔀 **1 CẶP LÔ XIÊN:**
   → `07 – 29`

🔢 **DỰ KIẾN ĐẦU SỐ ĐỀ:**
   → Đầu số `8` – 0 lần → 0.0%

⚠️ *Chưa đủ dữ liệu — Chỉ tham khảo!*"""

# ====================== 📋 LỆNH BOT — ĐƠN GIẢN, CHẮC CHẮN ======================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    print(f"✅ /start từ: {m.chat.id}")
    bot.send_message(m.chat.id,
        "🤖 **BOT XSMB — THỐNG KÊ SỐ LÔ V6.4**\n"
        "✅ /dudoan luôn trả về kết quả ngay!\n\n"
        "📌 Gõ DDMMYYYY → Xem + Lưu kết quả\n"
        "📌 /test DDMMYYYY → Chỉ xem, không lưu\n"
        "📌 /dudoan → Dự đoán ngày mai\n"
        "📌 /dudoan DDMMYYYY → Dự đoán ngày chỉ định"
    )

@bot.message_handler(commands=['test'])
def cmd_test(m):
    parts = m.text.strip().split()
    if len(parts) < 2 or not re.match(r"^\d{8}$", parts[1]):
        return bot.send_message(m.chat.id, "⚠️ /test DDMMYYYY — VD: /test 28082026")
    t = parts[1]
    d, mo, y = t[:2], t[2:4], t[4:8]
    try:
        datetime(int(y), int(mo), int(d))
    except:
        return bot.send_message(m.chat.id, "❌ Ngày không hợp lệ!")
    date_str = f"{d}/{mo}/{y}"
    res = fetch_result(date_str)
    if not res:
        return bot.send_message(m.chat.id, f"⚠️ **CHƯA CÓ KẾT QUẢ — {date_str}**")
    rep = f"🧪 **KẾT QUẢ TEST — {date_str}**\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n"
    rep += f"🏆 Đặc Biệt: `{res['special']}`\n"
    rep += f"🥈 Giải Nhất: `{res['g1']}`\n"
    if res.get("loto"):
        rep += f"🎯 Lô về: {', '.join(f'`{n}`' for n in res['loto'])}\n"
    rep += "\n✅ **CHỈ XEM — KHÔNG LƯU**"
    bot.send_message(m.chat.id, rep, parse_mode="Markdown")

@bot.message_handler(commands=['dudoan', 'thongke'])
def cmd_dt(m):
    print(f"✅ LỆNH /dudoAN TỪ: {m.chat.id}")
    parts = m.text.strip().split()
    target_date = None
    if len(parts) >= 2 and re.match(r"^\d{8}$", parts[1]):
        t = parts[1]
        d, mo, y = t[:2], t[2:4], t[4:8]
        try:
            datetime(int(y), int(mo), int(d))
            target_date = f"{d}/{mo}/{y}"
        except:
            pass
    
    # ✅ TẠO KẾT QUẢ → GỬI NGAY — KHÔNG ĐỢI, KHÔNG HIỂN THÌ "ĐANG PHÂN TÍCH"
    result_text = gen_prediction(60, target_date)
    print(f"✅ Kết quả dự đoán đã tạo, độ dài: {len(result_text)} ký tự")
    
    # ✅ GỬI KẾT QUẢ — NẾU LỖI → BÁO LỖI
    try:
        bot.send_message(m.chat.id, result_text, parse_mode="Markdown")
        print("✅ Đã gửi kết quả dự đoán!")
    except Exception as e:
        print(f"❌ Lỗi gửi tin nhắn: {e}")
        bot.send_message(m.chat.id, "⚠️ Đã có lỗi khi tạo dự đoán — vui lòng thử lại sau!")

@bot.message_handler(func=lambda msg: True)
def handle(m):
    txt = m.text.strip()
    if txt.startswith('/'):
        return
    if not re.match(r"^\d{8}$", txt):
        return bot.send_message(m.chat.id, "⚠️ Gõ DDMMYYYY hoặc /start")
    d, mo, y = txt[:2], txt[2:4], txt[4:8]
    try:
        datetime(int(y), int(mo), int(d))
    except:
        return bot.send_message(m.chat.id, "❌ Ngày không hợp lệ!")
    date_str = f"{d}/{mo}/{y}"
    res = fetch_result(date_str)
    if not res:
        return bot.send_message(m.chat.id, f"⚠️ **CHƯA CÓ KẾT QUẢ — {date_str}**\n(Chưa đến giờ quay hoặc lỗi nguồn)")
    save_data(date_str, res)
    rep = f"📅 **KẾT QUẢ — {date_str}** ✅ ĐÃ LƯU\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n"
    rep += f"🏆 Đặc Biệt: `{res['special']}`\n"
    rep += f"🥈 Giải Nhất: `{res['g1']}`\n"
    if res.get("loto"):
        rep += f"🎯 Lô về: {', '.join(f'`{n}`' for n in res['loto'])}\n"
    rep += "\n⚠️ Chơi có trách nhiệm!"
    bot.send_message(m.chat.id, rep, parse_mode="Markdown")

# ====================== ⏰ TỰ ĐỘNG GỬI 18:35 ======================
def auto_send():
    last = ""
    while True:
        try:
            now = datetime.now()
            today = now.strftime("%d/%m/%Y")
            if now.hour == 18 and 35 <= now.minute <= 45 and last != today:
                res = fetch_result(today)
                pred = gen_prediction(60)
                if res:
                    rep = f"📢 **KẾT QUẢ NGÀY {today}**\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n"
                    rep += f"🏆 Đặc Biệt: `{res['special']}`\n"
                    rep += f"🥈 Giải Nhất: `{res['g1']}`\n"
                    if res.get("loto"):
                        rep += f"🎯 Lô về: {', '.join(f'`{n}`' for n in res['loto'])}\n"
                    rep += "⚠️ Chơi có trách nhiệm!"
                    bot.send_message(CHANNEL_ID, rep, parse_mode="Markdown")
                    save_data(today, res)
                if pred:
                    d, m, y = today.split("/")
                    tom = (datetime(int(y), int(m), int(d)) + timedelta(days=1)).strftime("%d/%m/%Y")
                    bot.send_message(CHANNEL_ID, f"🔮 **DỰ ĐOÁN NGÀY {tom}**\n\n{pred}", parse_mode="Markdown")
                last = today
            time.sleep(30)
        except Exception as e:
            print(f"Lỗi auto: {e}")
            time.sleep(60)

# ====================== 🚀 KHỞI ĐỘNG ======================
def run_flask():
    app.run(host='0.0.0.0', port=PORT)

if __name__ == "__main__":
    print("="*60)
    print("🚀 BOT XSMB — V6.4 | /DUDOAN LUÔN TRẢ VỀ")
    print(f"✅ Bot: @Thongkeso999_bot")
    print("="*60)
    
    bot.remove_webhook()
    print("✅ Đã xóa webhook")
    
    Thread(target=run_flask, daemon=True).start()
    print("✅ Flask server đã chạy")
    
    Thread(target=auto_send, daemon=True).start()
    print("✅ Auto-job đã chạy")
    
    print("✅ BOT SẴN SÀNG — Gõ /dudoan → KẾT QUẢ NGAY!")
    print("="*60)
    
    bot.polling(none_stop=True, interval=2, timeout=60)
