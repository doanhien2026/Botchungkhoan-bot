import telebot
import re
import time
import json
import os
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from collections import Counter

# ====================== 🔧 CẤU HÌNH ======================
TELEGRAM_TOKEN = "8901722608:AAHnHfYsR8ilnHCHRaDUedA1ra1p0gPWda8"
CHAT_ID = "1030583610"
CHANNEL_ID = "-1001030583610"
PORT = 10000
DATA_FILE = "xsmb_data.json"

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

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

# ====================== 📡 LẤY DỮ LIỆU TỪ NGUỒN ======================
import requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
}

def fetch_result(date_str):
    d, m, y = date_str.split("/")
    # Nguồn 1: XOSODAIPHAT
    url = f"https://xosodaiphat.com/xsmb-{d}-{m}-{y}.html"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            nums = re.findall(r"\b\d{5}\b", r.text)
            real = [n for n in nums if n not in {"99999","00000","11111","88888"}]
            if len(real) >= 2:
                db = real[0]
                g1 = real[1]
                lotos = sorted(set(n[-2:] for n in real if n[-2:] != "00"))
                return {"source": "XOSODAIPHAT", "special": db, "g1": g1, "loto": lotos}
    except Exception as e:
        print(f"Nguồn 1 lỗi: {e}")
    # Nguồn 2: XOSO.COM.VN
    url2 = f"https://xoso.com.vn/ket-qua-xo-so-mien-bac-{d}-{m}-{y}.html"
    try:
        r = requests.get(url2, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            nums = re.findall(r"\b\d{5}\b", r.text)
            real = [n for n in nums if n not in {"99999","00000","11111","88888"}]
            if len(real) >= 2:
                db = real[0]
                g1 = real[1]
                lotos = sorted(set(n[-2:] for n in real if n[-2:] != "00"))
                return {"source": "XOSO.COM.VN", "special": db, "g1": g1, "loto": lotos}
    except Exception as e:
        print(f"Nguồn 2 lỗi: {e}")
    return None

# ====================== 🧠 LOGIC DỰ ĐOÁN ======================
def get_history(days=60):
    all_dates = get_all_dates()
    if not all_dates:
        return [], [], [], {}
    sorted_dates = sorted(all_dates, key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    limit = min(days, len(sorted_dates))
    lotos, first_digits, db_last2, history = [], [], [], {}
    for dt in sorted_dates[:limit]:
        res = get_saved_result(dt)
        if not res: continue
        history[dt] = res
        if res.get("loto"): lotos.extend(res["loto"])
        if res.get("special") and len(res["special"])==5:
            first_digits.append(res["special"][0])
            db_last2.append(res["special"][-2:])
            lotos.append(res["special"][-2:])
    return lotos, first_digits, db_last2, history

def calc_top3(lotos, history):
    if not lotos: return []
    freq = Counter(lotos)
    total = len(lotos)
    # Tính chu kỳ ngủ
    sorted_dt = sorted(history.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    last_app = {}
    for idx, dt in enumerate(sorted_dt):
        res = history[dt]
        nums = set(res.get("loto", []))
        if res.get("special") and len(res["special"])==5:
            nums.add(res["special"][-2:])
        for n in nums:
            if n not in last_app: last_app[n] = idx
    # Tính điểm
    scored = []
    for num, cnt in freq.items():
        rate = round(cnt/total*100,1)
        sleep = last_app.get(num, 999)
        score = round(cnt * (1 + min(sleep,30)/30),2)
        scored.append({"num":num,"count":cnt,"rate":rate,"sleep":sleep,"score":score})
    scored.sort(key=lambda x:-x["score"])
    return scored[:3]

def gen_prediction(days=60):
    lotos, first_digits, _, history = get_history(days)
    if not lotos and not first_digits: return None
    top3 = calc_top3(lotos, history)
    if len(top3)>=2: xien = [top3[0]["num"], top3[1]["num"]]
    elif len(top3)==1: xien = [top3[0]["num"], "99"]
    else: xien = ["00","00"]
    # Đầu số đề
    if first_digits:
        fc = Counter(first_digits)
        fd, fcnt = fc.most_common(1)[0]
        frate = round(fcnt/len(first_digits)*100,1)
    else: fd, fcnt, frate = "?",0,0.0
    # Báo cáo
    lines = [
        f"📊 **DỰ ĐOÁN — {days} NGÀY GẦN NHẤT**",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🎯 **3 CON LÔ TỶ LỆ CAO:**",
        "   (Tần suất + chu kỳ ngủ)"
    ]
    for i,item in enumerate(top3,1):
        lines.append(f"   {i}. `{item['num']}` — {item['count']} lần, {item['rate']}%, ngủ {item['sleep']} ngày")
    lines.extend([
        "",
        "🔀 **1 CẶP LÔ XIÊN:**",
        f"   → `{xien[0]} - {xien[1]}`",
        "",
        "🔢 **DỰ KIẾN ĐẦU SỐ ĐỀ:**",
        f"   → `{fd}` — {fcnt} lần → {frate}%",
        "",
        "🧠 Tính: Tần suất × (1 + ngủ/30) → điểm cao nhất",
        "⚠️ Tham khảo — Chơi có trách nhiệm!"
    ])
    return "\n".join(lines)

# ====================== 🔐 KIỂM TRA QUYỀN ======================
def auth(uid):
    return str(uid) in [CHAT_ID, CHANNEL_ID.replace("-100",""), CHANNEL_ID]

# ====================== 📋 LỆNH BOT ======================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    if not auth(m.chat.id): return bot.send_message(m.chat.id, "❌ Không có quyền.")
    bot.send_message(m.chat.id,
        "🤖 **BOT XSMB — HOÀN CHỈNH**\n"
        "✅ Dữ liệu bảo toàn | 📡 2 nguồn dữ liệu\n"
        "⏰ Tự động gửi 18:35 hàng ngày\n\n"
        "📌 **LỆNH:**\n"
        "• DDMMYYYY → Xem + LƯU kết quả\n"
        "• /test DDMMYYYY → Chỉ xem, KHÔNG lưu\n"
        "• /dudoan → Dự đoán 3 lô + xiên + đầu số đề\n"
        "• /thongke → Báo cáo thống kê 60 ngày"
    )

@bot.message_handler(commands=['test'])
def cmd_test(m):
    if not auth(m.chat.id): return
    parts = m.text.strip().split()
    if len(parts)<2 or not re.match(r"^\d{8}$", parts[1]):
        return bot.send_message(m.chat.id, "⚠️ /test DDMMYYYY — VD: /test 25082026")
    t = parts[1]
    d,m,y = t[:2],t[2:4],t[4:8]
    try: datetime(int(y),int(m),int(d))
    except: return bot.send_message(m.chat.id, "❌ Ngày sai!")
    date_str = f"{d}/{m}/{y}"
    bot.send_message(m.chat.id, f"🔍 **TEST NGÀY {date_str}**\nĐang lấy...")
    res = fetch_result(date_str)
    if not res:
        return bot.send_message(m.chat.id,
            f"⚠️ **CHƯA CÓ KẾT QUẢ — {date_str}**\n✅ Dữ liệu cũ: KHÔNG ĐỔI"
        )
    rep = f"🧪 **KẾT QUẢ TEST — {date_str}**\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n🏆 Đặc Biệt: `{res['special']}`\n"
    if res.get("g1"): rep += f"🥈 Giải Nhất: `{res['g1']}`\n"
    if res.get("loto"): rep += f"🎯 Lô về: `{', '.join(res['loto'])}`\n"
    rep += "\n✅ **CHỈ XEM — KHÔNG LƯU DỮ LIỆU**"
    bot.send_message(m.chat.id, rep, parse_mode="Markdown")

@bot.message_handler(commands=['dudoan','thongke'])
def cmd_dt(m):
    if not auth(m.chat.id): return
    bot.send_message(m.chat.id, "📊 Đang phân tích 60 ngày...")
    rep = gen_prediction(60)
    if not rep:
        return bot.send_message(m.chat.id, "⚠️ Chưa đủ dữ liệu! Tra cứu thêm kết quả nhé.")
    bot.send_message(m.chat.id, rep, parse_mode="Markdown")

@bot.message_handler(func=lambda msg:True)
def handle(m):
    txt = m.text.strip()
    if txt.startswith('/'): return
    if not auth(m.chat.id): return
    if not re.match(r"^\d{8}$", txt):
        return bot.send_message(m.chat.id, "⚠️ Gõ DDMMYYYY hoặc dùng lệnh /start /test /dudoan")
    d,mo,y = txt[:2],txt[2:4],txt[4:8]
    try: datetime(int(y),int(mo),int(d))
    except: return bot.send_message(m.chat.id, "❌ Ngày sai!")
    date_str = f"{d}/{mo}/{y}"
    bot.send_message(m.chat.id, f"🔍 Đang lấy & lưu **{date_str}**...")
    res = fetch_result(date_str)
    if not res:
        return bot.send_message(m.chat.id,
            f"⚠️ **CHƯA CÓ KẾT QUẢ — {date_str}**\n✅ Dữ liệu cũ: KHÔNG ĐỔI"
        )
    save_data(date_str, res)
    rep = f"📅 **KẾT QUẢ — {date_str}** ✅ ĐÃ LƯU\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n🏆 Đặc Biệt: `{res['special']}`\n"
    if res.get("g1"): rep += f"🥈 Giải Nhất: `{res['g1']}`\n"
    if res.get("loto"): rep += f"🎯 Lô về: `{', '.join(res['loto'])}`\n"
    rep += "\n⚠️ Tham khảo — Chơi có trách nhiệm!"
    bot.send_message(m.chat.id, rep, parse_mode="Markdown")

# ====================== ⏰ TỰ ĐỘNG GỬI 18:35 ======================
def auto_send():
    last = ""
    print("⏰ Auto 18:35 ĐÃ BẬT")
    while True:
        try:
            now = datetime.now()
            today = now.strftime("%d/%m/%Y")
            if now.hour==18 and 35<=now.minute<=45 and last!=today:
                print(f"⏰ Gửi tự động: {today}")
                res = fetch_result(today)
                pred = gen_prediction(60)
                # Gửi kết quả
                if res:
                    rep = f"📢 **KẾT QUẢ NGÀY {today}**\n🏆 Đặc Biệt: `{res['special']}`\n"
                    if res.get("g1"): rep += f"🥈 Giải Nhất: `{res['g1']}`\n"
                    if res.get("loto"): rep += f"🎯 Lô về: `{', '.join(res['loto'])}`\n"
                    rep += "⚠️ Chơi có trách nhiệm!"
                    bot.send_message(CHANNEL_ID, rep, parse_mode="Markdown")
                    save_data(today, res)
                    print(f"✅ Kết quả đã gửi + lưu")
                # Gửi dự đoán ngày mai
                if pred:
                    d,m,y = today.split("/")
                    tom = (datetime(int(y),int(m),int(d)) + timedelta(days=1)).strftime("%d/%m/%Y")
                    bot.send_message(CHANNEL_ID, f"🔮 **DỰ ĐOÁN NGÀY {tom}**\n\n{pred}", parse_mode="Markdown")
                    print(f"✅ Dự đoán ngày mai đã gửi")
                last = today
            time.sleep(30)
        except Exception as e:
            print(f"❌ Auto lỗi: {e}")
            time.sleep(60)

# ====================== 🚀 KHỞI ĐỘNG ======================
@app.route('/')
def home(): return "✅ Bot XSMB ĐANG HOẠT ĐỘNG",200
def run_flask(): app.run(host='0.0.0.0', port=PORT)

if __name__ == "__main__":
    print("="*60)
    print("🚀 BOT XSMB — HOÀN CHỈNH TRONG 1 FILE")
    print("📡 2 Nguồn | 💾 Tự lưu | ⏰ Auto 18:35")
    print("="*60)
    bot.remove_webhook()
    time.sleep(1)
    Thread(target=run_flask, daemon=True).start()
    Thread(target=auto_send, daemon=True).start()
    print("✅ SẴN SÀNG — TẤT CẢ CHỨC NĂNG ĐÃ SẴN")
    print("="*60)
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60, allowed_updates=['message'])
        except Exception as e:
            print(f"⚠️ Lỗi: {e} | Thử lại 15s...")
            time.sleep(15)
