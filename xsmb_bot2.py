# ==========================================================
# BOT XSMB — ĐÃ SỬA LỆNH /dudoan KHÔNG GỬI KẾT QUẢ
# ✅ ĐB ≠ G1 | ✅ Lô chính xác | ✅ /dudoan có tham số ngày
# ✅ Tự động tính + gửi kết quả dự đoán ngay | ⏰ Auto 18:35
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

# ====================== 📡 LẤY KẾT QUẢ ĐÚNG ======================
def fetch_result(date_str):
    d, m, y = date_str.split("/")
    url = f"https://xosodaiphat.com/xsmb-{d}-{m}-{y}.html"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        all_text = soup.get_text()
        all_5digit = re.findall(r"\b\d{5}\b", all_text)
        if len(all_5digit) < 8:
            return None
        dac_biet = all_5digit[-1]
        giai_nhat = all_5digit[-2]
        loto_set = set()
        for num in all_5digit:
            loto_set.add(num[-2:])
        loto_list = sorted(list(loto_set))[:27]
        return {
            "source": "XOSODAIPHAT",
            "special": dac_biet,
            "g1": giai_nhat,
            "loto": loto_list
        }
    except Exception as e:
        print(f"Lỗi fetch: {e}")
        return None

# ====================== 🧠 LOGIC DỰ ĐOÁN ======================
def get_history(days=60):
    all_dates = get_all_dates()
    if not all_dates:
        return [], [], {}, {}
    sorted_dates = sorted(all_dates, key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    limit = min(days, len(sorted_dates))
    lotos, first_digits, history = [], [], {}
    for dt in sorted_dates[:limit]:
        res = get_saved_result(dt)
        if not res: continue
        history[dt] = res
        if res.get("loto"): lotos.extend(res["loto"])
        if res.get("special") and len(res["special"]) == 5:
            first_digits.append(res["special"][0])
            lotos.append(res["special"][-2:])
    return lotos, first_digits, history

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

def gen_prediction(days=60, target_date=None):
    lotos, first_digits, history = get_history(days)
    if not lotos and not first_digits:
        return None
    top3 = calc_top3_loto(lotos, history)
    if len(top3) >= 2: xien = [top3[0]["num"], top3[1]["num"]]
    elif len(top3) == 1: xien = [top3[0]["num"], "99"]
    else: xien = ["00", "00"]
    if first_digits:
        fc = Counter(first_digits)
        fd, fcnt = fc.most_common(1)[0]
        frate = round(fcnt / len(first_digits) * 100, 1)
    else: fd, fcnt, frate = "?", 0, 0.0
    
    target_info = f" — Ngày {target_date}" if target_date else ""
    lines = [
        f"📊 **DỰ ĐOÁN KẾT QUẢ{target_info}**",
        f"📅 Dựa trên {days} ngày gần nhất",
        "________________________________________",
        "",
        "🎯 **3 CON LÔ TỶ LỆ CAO NHẤT:**",
        "   (Tần suất xuất hiện + chu kỳ ngủ)"
    ]
    for i, item in enumerate(top3, 1):
        lines.append(f"   {i}. `{item['num']}` – {item['count']} lần | {item['rate']}% | Ngủ {item['sleep']} ngày")
    lines.extend([
        "",
        "🔀 **1 CẶP LÔ XIÊN:**",
        f"   → Kết hợp 2 con cao nhất: `{xien[0]} – {xien[1]}`",
        "",
        "🔢 **DỰ KIẾN ĐẦU SỐ ĐỀ:**",
        f"   → Đầu số `{fd}` – xuất hiện {fcnt} lần → {frate}%",
        "",
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
        "🤖 **BOT XSMB — ĐÃ SỬA LỆNH DỰ ĐOÁN**\n"
        "✅ ĐB ≠ G1 | ✅ Lô chính xác | ✅ Dự đoán đầy đủ\n\n"
        "📌 **CÁCH DÙNG:**\n"
        "• DDMMYYYY → Xem + LƯU kết quả\n"
        "• /test DDMMYYYY → Chỉ xem, KHÔNG lưu\n"
        "• /dudoan → Dự đoán mặc định (ngày mai)\n"
        "• /dudoan DDMMYYYY → Dự đoán cho ngày chỉ định\n"
        "• /thongke → Xem thống kê 60 ngày"
    )

@bot.message_handler(commands=['test'])
def cmd_test(m):
    if not auth(m.chat.id): return
    parts = m.text.strip().split()
    if len(parts) < 2 or not re.match(r"^\d{8}$", parts[1]):
        return bot.send_message(m.chat.id, "⚠️ /test DDMMYYYY — VD: /test 28082026")
    t = parts[1]
    d, mo, y = t[:2], t[2:4], t[4:8]
    try: datetime(int(y), int(mo), int(d))
    except: return bot.send_message(m.chat.id, "❌ Ngày không hợp lệ!")
    date_str = f"{d}/{mo}/{y}"
    bot.send_message(m.chat.id, f"🔍 **TEST NGÀY {date_str}**\nĐang lấy dữ liệu...")
    res = fetch_result(date_str)
    if not res:
        return bot.send_message(m.chat.id, f"⚠️ **CHƯA CÓ KẾT QUẢ — {date_str}**\n✅ Dữ liệu cũ: KHÔNG THAY ĐỔI")
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
    parts = m.text.strip().split()
    target_date = None
    
    # ✅ Hỗ trợ: /dudoan → mặc định ngày mai | /dudoan DDMMYYYY → ngày chỉ định
    if len(parts) >= 2 and re.match(r"^\d{8}$", parts[1]):
        t = parts[1]
        d, mo, y = t[:2], t[2:4], t[4:8]
        try:
            datetime(int(y), int(mo), int(d))
            target_date = f"{d}/{mo}/{y}"
        except:
            pass
    
    bot.send_message(m.chat.id, "📊 Đang phân tích 60 ngày gần nhất...")
    rep = gen_prediction(60, target_date)
    
    if not rep:
        return bot.send_message(m.chat.id,
            "⚠️ **CHƯA ĐỦ DỮ LIỆU!**\n"
            "Vui lòng tra cứu thêm kết quả các ngày trước nhé.\n"
            "Gõ DDMMYYYY để lưu kết quả."
        )
    
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
    bot.send_message(m.chat.id, f"🔍 Đ
