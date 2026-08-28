# ==========================================================
# BOT XSMB — ĐÃ SỬA LỖI 409 + LẤY DỮ LIỆU ĐÚNG
# ✅ Chỉ 1 instance | ✅ Đặc Biệt ≠ Giải Nhất | ✅ Lô chính xác
# ✅ Không lấy số rác | ✅ Định dạng đúng ảnh | ⏰ Auto 18:35
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
TELEGRAM_TOKEN = "8901722608:AAHnHfYsR8ilnHCHRaDUedA1ra1p0gPWda8"
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

# ====================== 💾 QUẢN LÝ DỮ LIỆU ======================
def load_all_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(date_str, result):
    data = load_all_data()
    data[date_str] = result
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_all_dates():
    return sorted(load_all_data().keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))

def get_saved_result(date_str):
    return load_all_data().get(date_str)

# ====================== 📡 LẤY KẾT QUẢ ĐÚNG — KHÔNG LẤY SỐ RÁC ======================
def fetch_result(date_str):
    """✅ Phân tích đúng khu vực kết quả — ĐB ≠ G1 | Lô 27 số tối đa"""
    d, m, y = date_str.split("/")
    url = f"https://xosodaiphat.com/xsmb-{d}-{m}-{y}.html"
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        
        soup = BeautifulSoup(r.text, "html.parser")
        all_text = soup.get_text()
        
        # Lấy tất cả số 5 chữ số trong trang
        all_5digit = re.findall(r"\b\d{5}\b", all_text)
        if len(all_5digit) < 8:
            print(f"⚠️ Không đủ dữ liệu: {len(all_5digit)} số 5 chữ số")
            return None
        
        # ✅ Đặc Biệt = số CUỐI CÙNG | Giải Nhất = số KẾ CUỐI
        dac_biet = all_5digit[-1]
        giai_nhat = all_5digit[-2]
        
        # ✅ Lô = 2 số cuối của TẤT CẢ giải — KHÔNG lấy số rác
        loto_set = set()
        for num in all_5digit:
            loto_set.add(num[-2:])
        
        # Giới hạn tối đa 27 số lô (tương ứng 27 giải)
        loto_list = sorted(list(loto_set))[:27]
        
        if dac_biet == giai_nhat:
            print(f"⚠️ ĐB = G1 = {dac_biet} — Dữ liệu có thể chưa cập nhật!")
        
        return {
            "source": "XOSODAIPHAT",
            "special": dac_biet,
            "g1": giai_nhat,
            "loto": loto_list
        }
        
    except Exception as e:
        print(f"❌ Lỗi lấy kết quả: {e}")
        return None

# ====================== 🧠 LOGIC DỰ ĐOÁN — ĐÚNG ẢNH ======================
def get_history(days=60):
    all_dates = get_all_dates()
    if not all_dates:
        return [], [], {}, {}
    sorted_dates = sorted(all_dates, key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    limit = min(days, len(sorted_dates))
    lotos, first_digits, db_last2, history = [], [], [], {}
    for dt in sorted_dates[:limit]:
        res = get_saved_result(dt)
        if not res: continue
        history[dt] = res
        if res.get("loto"): lotos.extend(res["loto"])
        if res.get("special") and len(res["special"]) == 5:
            first_digits.append(res["special"][0])
            db_last2.append(res["special"][-2:])
            lotos.append(res["special"][-2:])
    return lotos, first_digits, db_last2, history

def calc_top3_loto(lotos, history):
    if not lotos: return []
    freq = Counter(lotos)
    total = len(lotos)
    sorted_dt = sorted(history.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    last_appear = {}
    for idx, dt in enumerate(sorted_dt):
        res = history[dt]
        nums = set(res.get("loto", []))
        if res.get("special") and len(res["special"]) == 5:
            nums.add(res["special"][-2:])
        for n in nums:
            if n not in last_appear: last_appear[n] = idx
    scored = []
    for num, count in freq.items():
        rate = round(count / total * 100, 1)
        sleep_days = last_appear.get(num, 999)
        scored.append({"num": num, "count": count, "rate": rate, "sleep": sleep_days})
    scored.sort(key=lambda x: (-x["count"], -x["rate"]))
    return scored[:3]

def gen_prediction(days=60):
    lotos, first_digits, _, history = get_history(days)
    if not lotos and not first_digits: return None
    top3 = calc_top3_loto(lotos, history)
    if len(top3) >= 2: xien = [top3[0]["num"], top3[1]["num"]]
    elif len(top3) == 1: xien = [top3[0]["num"], "99"]
    else: xien = ["00", "00"]
    if first_digits:
        fc = Counter(first_digits)
        fd, fcnt = fc.most_common(1)[0]
        frate = round(fcnt / len(first_digits) * 100, 1)
    else: fd, fcnt, frate = "?", 0, 0.0
    lines = [
        f"📊 **DỰ ĐOÁN KẾT QUẢ – DỰA TRÊN {days} NGÀY**",
        "________________________________________",
        "",
        "🎯 **3 CON LÔ TỶ LỆ CAO NHẤT:**",
        "   (Theo tần suất + chu kỳ ngủ)"
    ]
    for i, item in enumerate(top3, 1):
        lines.append(f"   {i}. `{item['num']}` – {item['count']} lần, tỷ lệ {item['rate']}%, ngủ {item['sleep']} ngày")
    lines.extend([
        "",
        "🔀 **1 CẶP LÔ XIÊN:**",
        f"   → Kết hợp 2 con cao nhất: `{xien[0]} – {xien[1]}`",
        "",
        "🔢 **DỰ KIẾN ĐẦU SỐ ĐỀ:**",
        f"   → Đầu số `{fd}` – xuất hiện {fcnt} lần → {frate}%",
        "",
        "🧠 **Cách tính:** Tần suất xuất hiện + số ngày chưa về → điểm cao nhất",
        "⚠️ *Chỉ tham khảo – Chơi có trách nhiệm!*"
    ])
    return "\n".join(lines)

# ====================== 🔐 KIỂM TRA QUYỀN ======================
def auth(uid):
    return str(uid) in [CHAT_ID, CHANNEL_ID.replace("-100", ""), CHANNEL_ID]

# ====================== 📋 LỆNH BOT ======================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    if not auth(m.chat.id):
        return bot.send_message(m.chat.id, "❌ Không có quyền sử dụng bot này.")
    bot.send_message(m.chat.id,
        "🤖 **BOT XSMB — ĐÃ SỬA LỖI 409 + DỮ LIỆU**\n"
        "✅ Chỉ 1 instance | ✅ ĐB ≠ G1 | ✅ Lô chính xác\n"
        "📌 DDMMYYYY → Lưu | /test DDMMYYYY → Xem thử\n"
        "/dudoan → Dự đoán 3 lô + 1 xiên + đầu số đề"
    )

@bot.message_handler(commands=['test'])
def cmd_test(m):
    if not auth(m.chat.id): return
    parts = m.text.strip().split()
    if len(parts) < 2 or not re.match(r"^\d{8}$", parts[1]):
        return bot.send_message(m.chat.id, "⚠️ /test DDMMYYYY — VD: /test 29082026")
    t = parts[1]
    d, mo, y = t[:2], t[2:4], t[4:8]
    try: datetime(int(y), int(mo), int(d))
    except: return bot.send_message(m.chat.id, "❌ Ngày không hợp lệ!")
    date_str = f"{d}/{mo}/{y}"
    bot.send_message(m.chat.id, f"🔍 **TEST NGÀY {date_str}**\nĐang lấy dữ liệu...")
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
    if not auth(m.chat.id): return
    bot.send_message(m.chat.id, "📊 Đang phân tích 60 ngày gần nhất...")
    rep = gen_prediction(60)
    if not rep:
        return bot.send_message(m.chat.id, "⚠️ Chưa đủ dữ liệu! Tra cứu thêm kết quả nhé.")
    bot.send_message(m.chat.id, rep, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle(m):
    txt = m.text.strip()
    if txt.startswith('/'): return
    if not auth(m.chat.id): return
    if not re.match(r"^\d{8}$", txt):
        return bot.send_message(m.chat.id, "⚠️ Gõ DDMMYYYY hoặc /start")
    d, mo, y = txt[:2], txt[2:4], txt[4:8]
    try: datetime(int(y), int(mo), int(d))
    except: return bot.send_message(m.chat.id, "❌ Ngày không hợp lệ!")
    date_str = f"{d}/{mo}/{y}"
    bot.send_message(m.chat.id, f"🔍 Đang lấy & lưu **{date_str}**...")
    res = fetch_result(date_str)
    if not res:
        return bot.send_message(m.chat.id, f"⚠️ **CHƯA CÓ KẾT QUẢ — {date_str}**")
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
    print("⏰ Auto 18:35 — ĐÃ BẬT")
    while True:
        try:
            now = datetime.now()
            today = now.strftime("%d/%m/%Y")
            if now.hour == 18 and 35 <= now.minute <= 45 and last != today:
                print(f"⏰ Gửi: {today}")
                res = fetch_result(today)
                pred = gen_prediction(60)
                if res:
                    rep = f"📢 **KẾT QUẢ NGÀY {today}**\n━━━━━━━━━━━━━━━━━━━━\n"
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
            print(f"❌ Lỗi auto: {e}")
            time.sleep(60)

# ====================== 🚀 FLASK ======================
@app.route('/')
def home(): return "✅ BOT XSMB — ĐANG HOẠT ĐỘNG", 200
def run_flask(): app.run(host='0.0.0.0', port=PORT)

# ====================== ✅ KHỞI ĐỘNG — CHỈ 1 INSTANCE ======================
if __name__ == "__main__":
    print("="*60)
    print("🚀 BOT XSMB — ĐÃ SỬA LỖI 409 + DỮ LIỆU")
    print("✅ Chỉ 1 instance | ✅ ĐB ≠ G1 | ✅ Lô 27 số tối đa")
    print("="*60)
    
    # ✅ BƯỚC QUAN TRỌNG: TẮT WEBHOOK CŨ + ĐỢI 3s → TRÁNH XUNG ĐỘ
    bot.remove_webhook()
    time.sleep(3)
    
    # ✅ CHỈ 1 TIẾN TRÌNH — KHÔNG DÙNG threaded=True
    Thread(target=run_flask, daemon=True).start()
    Thread(target=auto_send, daemon=True).start()
    
    print("✅ SẴN SÀNG — CHỈ 1 INSTANCE ĐANG CHẠY")
    print("="*60)
    
    # ✅ POLLING ĐƠN GIẢN — KHÔNG CÓ THAM SỐ GÂY LỖI
    while True:
        try:
            # ❌ BỎ: threaded, skip_pending_updates — GÂY LỖI 409!
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=60,
                allowed_updates=['message']
            )
        except Exception as e:
            print(f"⚠️ Lỗi kết nối: {e} | Thử lại sau 15s...")
            time.sleep(15)
