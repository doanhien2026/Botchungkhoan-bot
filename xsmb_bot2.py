# ==========================================================
# BOT XSMB — V8.0 | NGUỒN API ĐƠN GIẢN + TỰ LƯU + BỎ NHẬP TAY
# ✅ Gõ DDMMYYYY → Tự lấy kết quả + Tự lưu ngay
# ✅ Nguồn: API chính thức, không bị chặn
# ✅ Bỏ hoàn toàn lệnh /nhap — chỉ lấy từ nguồn tự động
# ✅ Tự quét 90 ngày cũ khi khởi động
# Token: 8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w
# Chat ID: 1030583610 | Channel ID: -1001030583610
# ==========================================================

import telebot
import re
import time
import json
import os
import requests
from datetime import datetime, timedelta
from flask import Flask
from collections import Counter

# ====================== 🔧 CẤU HÌNH ======================
TELEGRAM_TOKEN = "8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w"
CHAT_ID = "1030583610"
CHANNEL_ID = "-1001030583610"
PORT = int(os.environ.get("PORT", 10000))
DATA_FILE = "xsmb_data.json"
ANALYSIS_DAYS = 90
AUTO_FETCH_DAYS = 90

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ====================== 🌐 TRANG CHỦ ======================
@app.route('/')
def home():
    return "✅ Bot XSMB V8.0 — API tự động + Tự lưu + Bỏ nhập tay"

# ====================== 💾 QUẢN LÝ DỮ LIỆU ======================
def load_all_data():
    if not os.path.exists(DATA_FILE): return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except: return {}

def save_data(date_str, result):
    data = load_all_data()
    if date_str in data:
        print(f"⚠️ {date_str} đã có, bỏ qua")
        return False
    data[date_str] = result
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ ĐÃ LƯU: {date_str} — Tổng: {len(data)} ngày")
    return True

# ====================== 📡 LẤY KẾT QUẢ — NGUỒN API ĐƠN GIẢN ======================
def fetch_result(date_str):
    """✅ Nguồn API đơn giản — ít bị chặn, trả dữ liệu chuẩn"""
    d, m, y = date_str.split("/")
    date_api = f"{d}/{m}/{y}"
    try:
        # NGUỒN 1: API KQXS — ổn định, dễ lấy
        url = f"https://api.kqxs.net/xsmb?date={date_api}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            j = r.json()
            if j.get("status") == "success" and j.get("data"):
                data = j["data"]
                special = data.get("special", "").strip()
                g1 = data.get("prize1", "").strip()
                loto = []
                for key in [f"prize{i}" for i in range(1, 8)] + ["special"]:
                    val = data.get(key, "")
                    if isinstance(val, str) and len(val) == 5 and val.isdigit():
                        loto.append(val[-2:])
                    elif isinstance(val, list):
                        for v in val:
                            if len(str(v)) == 5 and str(v).isdigit():
                                loto.append(str(v)[-2:])
                loto = sorted(list(set(loto)))
                if len(special) == 5 and len(g1) == 5 and len(loto) >= 15:
                    print(f"✅ API KQXS — {date_str} | ĐB:{special} G1:{g1} Lô:{len(loto)}")
                    return {"source": "API KQXS", "special": special, "g1": g1, "loto": loto}
        # NGUỒN 2: API THỨ HAI — dự phòng
        url2 = f"https://xsmb-api.vercel.app/api?date={y}-{m}-{d}"
        r2 = requests.get(url2, headers=HEADERS, timeout=15)
        if r2.status_code == 200:
            j2 = r2.json()
            if j2.get("special"):
                special = str(j2["special"]).zfill(5)
                g1 = str(j2.get("prize1", "")).zfill(5)
                loto = []
                all_prizes = j2.get("prizes", [])
                for p in all_prizes:
                    if isinstance(p, list):
                        for v in p:
                            if len(str(v)) == 5: loto.append(str(v)[-2:])
                    elif len(str(p)) == 5: loto.append(str(p)[-2:])
                loto = sorted(list(set(loto)))
                if len(special) == 5 and len(g1) == 5 and len(loto) >= 15:
                    print(f"✅ API Vercel — {date_str} | ĐB:{special} G1:{g1} Lô:{len(loto)}")
                    return {"source": "API Vercel", "special": special, "g1": g1, "loto": loto}
        return None
    except Exception as e:
        print(f"❌ Lỗi lấy {date_str}: {e}")
        return None

# ====================== 🤖 TỰ QUÉT NGÀY CŨ ======================
def auto_fetch_old_days(max_days=AUTO_FETCH_DAYS):
    print(f"🔍 TỰ QUÉT {max_days} NGÀY GẦN NHẤT...")
    existing = load_all_data()
    today = datetime.now()
    count = 0
    for offset in range(1, max_days + 1):
        target = today - timedelta(days=offset)
        date_str = target.strftime("%d/%m/%Y")
        if date_str in existing: continue
        res = fetch_result(date_str)
        if res:
            save_data(date_str, res)
            count += 1
        time.sleep(1)
    print(f"✅ HOÀN THÀNH: Lấy mới {count} ngày | Tổng: {len(load_all_data())} ngày")

# ====================== 🧠 TÍNH TOÁN DỰ ĐOÁN ======================
def calculate_prediction():
    data = load_all_data()
    if len(data) < 3:
        return {"ready": False, "note": f"⚠️ Chưa đủ dữ liệu — mới có {len(data)} ngày. Gõ thêm ngày để đủ ≥ 3 ngày!"}
    try:
        sorted_dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    except: return {"ready": False, "note": "⚠️ Lỗi đọc dữ liệu"}
    limit = min(ANALYSIS_DAYS, len(sorted_dates))
    all_loto = []
    first_digits = []
    last_appear = {}
    for idx, dt in enumerate(sorted_dates[:limit]):
        res = data[dt]
        day_loto = set(res.get("loto", []))
        special = res.get("special", "")
        if len(special) == 5:
            day_loto.add(special[-2:])
            first_digits.append(special[0])
        for num in day_loto:
            if num not in last_appear: last_appear[num] = idx
        all_loto.extend(day_loto)
    freq = Counter(all_loto)
    scored = []
    for num, cnt in freq.items():
        rate = round(cnt / limit * 100, 1)
        sleep = last_appear.get(num, 999)
        scored.append({"num": num, "count": cnt, "rate": rate, "sleep": sleep})
    scored.sort(key=lambda x: -x["rate"])
    top3 = scored[:3]
    xien = [top3[0]["num"], top3[1]["num"]] if len(top3) >= 2 else ["--", "--"]
    fd = Counter(first_digits).most_common(1)
    fd_digit, fd_rate = (fd[0][0], round(fd[0][1]/len(first_digits)*100,1)) if fd else ("--", 0)
    return {
        "ready": True,
        "total_days": limit,
        "top3": top3,
        "xien": xien,
        "fd_digit": fd_digit,
        "fd_rate": fd_rate
    }

# ====================== 📋 LỆNH BOT ======================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id,
        "🤖 **BOT XSMB — V8.0 | TỰ ĐỘNG LẤY & LƯU**\n"
        "✅ Gõ DDMMYYYY → Tự lấy kết quả + Tự lưu ngay\n"
        "✅ Tự quét 90 ngày cũ khi khởi động\n"
        "✅ Tính tỷ lệ tự động từ dữ liệu đã lưu\n"
        "✅ Bỏ nhập tay — chỉ lấy từ nguồn tự động\n\n"
        "📌 Gõ: 29082026 → Xem & lưu kết quả\n"
        "📌 /dudoan → Dự đoán ngày mai\n"
        "📌 /status → Xem tổng số ngày đã lưu\n"
        "📌 /test DDMMYYYY → Xem kết quả, không lưu",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    data = load_all_data()
    bot.send_message(m.chat.id,
        f"📊 **TRẠNG THÁI DỮ LIỆU**\n"
        f"• Tổng ngày đã lưu: **{len(data)} ngày**\n"
        f"• Ngày cũ nhất: {min(data.keys()) if data else 'Chưa có'}\n"
        f"• Ngày mới nhất: {max(data.keys()) if data else 'Chưa có'}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['test'])
def cmd_test(m):
    parts = m.text.strip().split()
    if len(parts) < 2 or not re.match(r"^\d{8}$", parts[1]):
        return bot.send_message(m.chat.id, "⚠️ /test DDMMYYYY — VD: /test 29082026")
    t = parts[1]
    date_str = f"{t[:2]}/{t[2:4]}/{t[4:8]}"
    res = fetch_result(date_str)
    if not res:
        return bot.send_message(m.chat.id, f"⚠️ **KHÔNG LẤY ĐƯỢC KẾT QUẢ — {date_str}**")
    bot.send_message(m.chat.id,
        f"🧪 **KẾT QUẢ TEST — {date_str}**\n📡 Nguồn: {res['source']}\n"
        f"🏆 Đặc Biệt: `{res['special']}`\n🥇 Giải Nhất: `{res['g1']}`\n"
        f"🎯 Lô về: {', '.join(f'`{n}`' for n in res['loto'])}\n\n✅ **CHỈ XEM — KHÔNG LƯU**",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['dudoan'])
def cmd_dudoan(m):
    pred = calculate_prediction()
    tom = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    if not pred["ready"]:
        return bot.send_message(m.chat.id,
            f"📅 DỰ ĐOÁN NGÀY MAI: {tom}\n━━━━━━━━━━━━━━━━━━\n{pred['note']}",
            parse_mode="Markdown"
        )
    bot.send_message(m.chat.id,
        f"📅 **DỰ ĐOÁN NGÀY MAI: {tom}**\n📊 Phân tích: {pred['total_days']} ngày\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎯 3 CON LÔ TỶ LỆ CAO NHẤT:\n" +
        "\n".join([f"  {i+1}. `{x['num']}` — {x['count']} lần | Tỷ lệ: {x['rate']}% | Ngủ: {x['sleep']} ngày" for i, x in enumerate(pred['top3'])]) +
        f"\n\n🔀 LÔ XIÊN: `{pred['xien'][0]}` + `{pred['xien'][1]}`\n"
        f"🔢 ĐẦU SỐ ĐỀ: `{pred['fd_digit']}` — Tỷ lệ: {pred['fd_rate']}%\n\n"
        "⚠️ Chỉ tham khảo — Chơi có trách nhiệm!",
        parse_mode="Markdown"
    )

# ✅ Gõ DDMMYYYY → TỰ LẤY + TỰ LƯU NGAY
@bot.message_handler(func=lambda msg: not msg.text.startswith('/') and re.match(r"^\d{8}$", msg.text.strip()))
def handle_date_input(m):
    t = m.text.strip()
    date_str = f"{t[:2]}/{t[2:4]}/{t[4:8]}"
    try:
        datetime(int(t[4:8]), int(t[2:4]), int(t[:2]))
    except:
        return bot.send_message(m.chat.id, "❌ Ngày không hợp lệ! VD: 29082026")
    res = fetch_result(date_str)
    if not res:
        return bot.send_message(m.chat.id, f"⚠️ **KHÔNG LẤY ĐƯỢC KẾT QUẢ — {date_str}**\nKiểm tra lại ngày hoặc thử lại sau!")
    saved = save_data(date_str, res)
    bot.send_message(m.chat.id,
        f"📅 **KẾT QUẢ — {date_str}** {'✅ ĐÃ LƯU' if saved else '⚠️ ĐÃ CÓ DỮ LIỆU'}\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 Đặc Biệt: `{res['special']}`\n🥇 Giải Nhất: `{res['g1']}`\n"
        f"🎯 Lô về: {', '.join(f'`{n}`' for n in res['loto'])}\n\n⚠️ Chỉ tham khảo — Chơi có trách nhiệm!",
        parse_mode="Markdown"
    )

# ====================== ⏰ TỰ ĐỘNG GỬI 18:35 ======================
def auto_send():
    last = ""
    while True:
        try:
            now = datetime.now()
            today = now.strftime("%d/%m/%Y")
            if now.hour == 18 and 35 <= now.minute <= 45 and last != today:
                res = fetch_result(today)
                if res:
                    save_data(today, res)
                    bot.send_message(CHANNEL_ID,
                        f"📢 **KẾT QUẢ NGÀY {today}**\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n"
                        f"🏆 Đặc Biệt: `{res['special']}`\n🥇 Giải Nhất: `{res['g1']}`\n"
                        f"🎯 Lô về: {', '.join(f'`{n}`' for n in res['loto'])}\n\n⚠️ Chơi có trách nhiệm!",
                        parse_mode="Markdown"
                    )
                pred = calculate_prediction()
                tom = (datetime.strptime(today, "%d/%m/%Y") + timedelta(days=1)).strftime("%d/%m/%Y")
                if pred["ready"]:
                    bot.send_message(CHANNEL_ID,
                        f"🔮 **DỰ ĐOÁN NGÀY: {tom}**\n📊 Phân tích: {pred['total_days']} ngày\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "🎯 3 CON LÔ TỶ LỆ CAO NHẤT:\n" +
                        "\n".join([f"  {i+1}. `{x['num']}` — {x['count']} lần | Tỷ lệ: {x['rate']}%" for i, x in enumerate(pred['top3'])]) +
                        f"\n\n🔀 LÔ XIÊN: `{pred['xien'][0]}` + `{pred['xien'][1]}`\n"
                        f"🔢 ĐẦU SỐ ĐỀ: `{pred['fd_digit']}` — {pred['fd_rate']}%\n\n⚠️ Chơi có trách nhiệm!",
                        parse_mode="Markdown"
                    )
                last = today
            time.sleep(30)
        except Exception as e:
            print(f"❌ Lỗi auto_send: {e}")
            time.sleep(60)

# ====================== 🚀 KHỞI ĐỘNG ======================
if __name__ == "__main__":
    print("="*60)
    print("🚀 BOT XSMB — V8.0 | API TỰ ĐỘNG + TỰ LƯU + BỎ NHẬP TAY")
    print("✅ Gõ DDMMYYYY → Tự lấy + Tự lưu ngay")
    print("✅ Bỏ hoàn toàn lệnh nhập tay")
    print("✅ Tự quét 90 ngày cũ khi khởi động")
    print("="*60)
    
    bot.remove_webhook()
    from threading import Thread
    Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False), daemon=True).start()
    Thread(target=auto_send, daemon=True).start()
    Thread(target=lambda: (time.sleep(5), auto_fetch_old_days()), daemon=True).start()
    
    print("✅ BOT SẴN SÀNG — Gõ /start → Gõ ngày → Tự lưu!")
    bot.polling(none_stop=True, interval=3, timeout=60)
