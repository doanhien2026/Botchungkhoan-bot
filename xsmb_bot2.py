# ==========================================================
# BOT XSMB — V8.2 | NGUỒN API KHÁC + LOG CHI TIẾT + TỰ LƯU
# ✅ Gõ DDMMYYYY → Tự lấy + Tự lưu
# ✅ 3 Nguồn API khác nhau — tăng khả năng thành công
# ✅ Ghi log chi tiết vào Render Log → dễ kiểm tra lỗi
# ✅ Bỏ nhập tay — chỉ lấy tự động
# Token: 8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w
# Chat ID: 1030583610 | Channel ID: -1001030583610
# ==========================================================

import telebot
import re
import time
import json
import os
import sys
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
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ====================== 📝 HÀM GHI LOG ======================
def log(msg):
    t = datetime.now().strftime("%H:%M:%S")
    line = f"[{t}] {msg}"
    print(line)
    sys.stdout.flush()  # Ghi ngay ra log Render, không đệm

# ====================== 🌐 TRANG CHỦ ======================
@app.route('/')
def home():
    return "✅ Bot XSMB V8.2 — API đa nguồn + Log chi tiết"

# ====================== 💾 QUẢN LÝ DỮ LIỆU ======================
def load_all_data():
    if not os.path.exists(DATA_FILE):
        log(f"File {DATA_FILE} chưa tồn tại")
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            log(f"Đọc được {len(data)} ngày từ {DATA_FILE}")
            return data if isinstance(data, dict) else {}
    except Exception as e:
        log(f"Lỗi đọc file: {e}")
        return {}

def save_data(date_str, result):
    data = load_all_data()
    if date_str in data:
        log(f"Ngày {date_str} đã có, bỏ qua lưu")
        return False
    data[date_str] = result
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log(f"✅ ĐÃ LƯU: {date_str} — Tổng: {len(data)} ngày")
        return True
    except Exception as e:
        log(f"Lỗi lưu: {e}")
        return False

# ====================== 📡 3 NGUỒN API KHÁC NHAU ======================
def validate_result(special, g1, loto):
    ok = (special and len(special)==5 and special.isdigit() and
          g1 and len(g1)==5 and g1.isdigit() and
          loto and len(loto)>=15)
    if not ok:
        log(f"Dữ liệu không hợp lệ — ĐB:{special} G1:{g1} Lô:{len(loto)}")
    return ok

# NGUỒN 1 — API XOSO.ME đơn giản
def fetch_1(date_str):
    d, m, y = date_str.split("/")
    try:
        url = f"https://xoso.me/api/xsmb?date={d}-{m}-{y}"
        log(f"[N1] Gọi: {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        log(f"[N1] Mã: {r.status_code}")
        if r.status_code != 200: return None
        j = r.json()
        special = str(j.get("special", "")).strip()
        g1 = str(j.get("prize1", "")).strip()
        loto = []
        for k in ["prize1","prize2","prize3","prize4","prize5","prize6","prize7","special"]:
            v = j.get(k, "")
            if isinstance(v, str) and len(v)==5 and v.isdigit(): loto.append(v[-2:])
            elif isinstance(v, list):
                for x in v:
                    s = str(x).strip()
                    if len(s)==5 and s.isdigit(): loto.append(s[-2:])
        loto = sorted(list(set(loto)))
        if validate_result(special, g1, loto):
            log(f"[N1] THÀNH CÔNG — ĐB:{special} G1:{g1} Lô:{len(loto)}")
            return {"source":"XOSO.ME API", "special":special, "g1":g1, "loto":loto}
    except Exception as e:
        log(f"[N1] LỖI: {e}")
    return None

# NGUỒN 2 — API KQXS.NET
def fetch_2(date_str):
    d, m, y = date_str.split("/")
    try:
        url = f"https://api.kqxs.net/xsmb?date={d}/{m}/{y}"
        log(f"[N2] Gọi: {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        log(f"[N2] Mã: {r.status_code}")
        if r.status_code != 200: return None
        j = r.json()
        if j.get("status") != "success": return None
        data = j.get("data", {})
        special = str(data.get("special", "")).strip()
        g1 = str(data.get("prize1", "")).strip()
        loto = []
        for k in ["prize1","prize2","prize3","prize4","prize5","prize6","prize7","special"]:
            v = data.get(k, "")
            if isinstance(v, str) and len(v)==5 and v.isdigit(): loto.append(v[-2:])
            elif isinstance(v, list):
                for x in v:
                    s = str(x).strip()
                    if len(s)==5 and s.isdigit(): loto.append(s[-2:])
        loto = sorted(list(set(loto)))
        if validate_result(special, g1, loto):
            log(f"[N2] THÀNH CÔNG — ĐB:{special} G1:{g1} Lô:{len(loto)}")
            return {"source":"KQXS.NET", "special":special, "g1":g1, "loto":loto}
    except Exception as e:
        log(f"[N2] LỖI: {e}")
    return None

# NGUỒN 3 — API XOSO-API (dự phòng cuối)
def fetch_3(date_str):
    d, m, y = date_str.split("/")
    try:
        url = f"https://xoso-api.onrender.com/api/xsmb?day={d}&month={m}&year={y}"
        log(f"[N3] Gọi: {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        log(f"[N3] Mã: {r.status_code}")
        if r.status_code != 200: return None
        j = r.json()
        if j.get("status") != "success": return None
        res = j.get("result", {})
        special = str(res.get("special_prize", "")).strip()
        g1 = str(res.get("prize_1", "")).strip()
        loto = []
        prizes = res.get("prizes", {})
        for plist in prizes.values():
            if isinstance(plist, list):
                for x in plist:
                    s = str(x).strip()
                    if len(s)==5 and s.isdigit(): loto.append(s[-2:])
        loto = sorted(list(set(loto)))
        if validate_result(special, g1, loto):
            log(f"[N3] THÀNH CÔNG — ĐB:{special} G1:{g1} Lô:{len(loto)}")
            return {"source":"XOSO-API", "special":special, "g1":g1, "loto":loto}
    except Exception as e:
        log(f"[N3] LỖI: {e}")
    return None

# HÀM CHÍNH — THỬ 3 NGUỒN LIÊN TIẾP
def fetch_result(date_str):
    log(f"===== LẤY KẾT QUẢ: {date_str} =====")
    r = fetch_1(date_str)
    if r: return r
    log("Nguồn 1 thất bại → thử Nguồn 2")
    r = fetch_2(date_str)
    if r: return r
    log("Nguồn 2 thất bại → thử Nguồn 3")
    r = fetch_3(date_str)
    if r: return r
    log("❌ TẤT CẢ 3 NGUỒN ĐỀU THẤT BẠI")
    return None

# ====================== 🤖 TỰ QUÉT NGÀY CŨ ======================
def auto_fetch_old_days(max_days=AUTO_FETCH_DAYS):
    log(f"===== BẮT ĐẦU TỰ QUÉT {max_days} NGÀY =====")
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
        time.sleep(1.5)
    log(f"===== HOÀN THÀNH — Lấy mới {count} ngày =====")

# ====================== 🧠 TÍNH TOÁN DỰ ĐOÁN ======================
def calculate_prediction():
    data = load_all_data()
    total = len(data)
    if total < 3:
        return {"ready":False, "note":f"⚠️ Chưa đủ dữ liệu — mới có {total} ngày.\nGõ ngày (VD: 29082026) để tích lũy!"}
    try:
        sorted_dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    except:
        return {"ready":False, "note":"⚠️ Lỗi đọc dữ liệu"}
    limit = min(ANALYSIS_DAYS, total)
    all_loto, first_digits, last_appear = [], [], {}
    for idx, dt in enumerate(sorted_dates[:limit]):
        res = data[dt]
        day_loto = set(res.get("loto", []))
        special = res.get("special", "")
        if len(special)==5:
            day_loto.add(special[-2:])
            first_digits.append(special[0])
        for num in day_loto:
            if num not in last_appear: last_appear[num] = idx
        all_loto.extend(day_loto)
    freq = Counter(all_loto)
    scored = []
    for num, cnt in freq.items():
        scored.append({"num":num, "count":cnt, "rate":round(cnt/limit*100,1), "sleep":last_appear.get(num,999)})
    scored.sort(key=lambda x: -x["rate"])
    top3 = scored[:3]
    xien = [top3[0]["num"], top3[1]["num"]] if len(top3)>=2 else ["--","--"]
    fd = Counter(first_digits).most_common(1)
    fd_digit, fd_rate = (fd[0][0], round(fd[0][1]/len(first_digits)*100,1)) if fd else ("--",0)
    return {"ready":True, "total_days":limit, "top3":top3, "xien":xien, "fd_digit":fd_digit, "fd_rate":fd_rate}

# ====================== 📋 LỆNH BOT ======================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id,
        "🤖 **BOT XSMB — V8.2 | 3 NGUỒN API + LOG CHI TIẾT**\n"
        "✅ Gõ DDMMYYYY → Tự lấy + Tự lưu\n"
        "✅ 3 Nguồn: XOSO.ME | KQXS.NET | XOSO-API\n"
        "✅ Bỏ nhập tay — chỉ lấy tự động\n"
        "✅ Gõ /status → xem tổng ngày đã lưu\n"
        "✅ Gõ /dudoan → dự đoán ngày mai\n\n"
        "📌 Gõ: 29082026 → Xem & lưu kết quả ngay!",
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

@bot.message_handler(commands=['dudoan'])
def cmd_dudoan(m):
    pred = calculate_prediction()
    tom = (datetime.now()+timedelta(days=1)).strftime("%d/%m/%Y")
    if not pred["ready"]:
        return bot.send_message(m.chat.id, f"📅 DỰ ĐOÁN NGÀY MAI: {tom}\n{pred['note']}", parse_mode="Markdown")
    bot.send_message(m.chat.id,
        f"📅 **DỰ ĐOÁN NGÀY MAI: {tom}**\n📊 Phân tích: {pred['total_days']} ngày\n━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎯 3 CON LÔ TỶ LỆ CAO NHẤT:\n" +
        "\n".join([f"  {i+1}. `{x['num']}` — {x['count']} lần | Tỷ lệ: {x['rate']}% | Ngủ: {x['sleep']} ngày" for i,x in enumerate(pred['top3'])]) +
        f"\n\n🔀 LÔ XIÊN: `{pred['xien'][0]}` + `{pred['xien'][1]}`\n"
        f"🔢 ĐẦU SỐ ĐỀ: `{pred['fd_digit']}` — Tỷ lệ: {pred['fd_rate']}%\n\n⚠️ Chỉ tham khảo — Chơi có trách nhiệm!",
        parse_mode="Markdown"
    )

# ✅ Gõ DDMMYYYY → TỰ LẤY + TỰ LƯU
@bot.message_handler(func=lambda msg: not msg.text.startswith('/') and re.match(r"^\d{8}$", msg.text.strip()))
def handle_date(m):
    t = m.text.strip()
    date_str = f"{t[:2]}/{t[2:4]}/{t[4:8]}"
    try: datetime(int(t[4:8]), int(t[2:4]), int(t[:2]))
    except: return bot.send_message(m.chat.id, "❌ Ngày không hợp lệ! VD: 29082026")
    res = fetch_result(date_str)
    if not res:
        return bot.send_message(m.chat.id, f"⚠️ **KHÔNG LẤY ĐƯỢC KẾT QUẢ — {date_str}**\n👉 Vào Render Log xem chi tiết lỗi!", parse_mode="Markdown")
    saved = save_data(date_str, res)
    bot.send_message(m.chat.id,
        f"📅 **KẾT QUẢ — {date_str}** {'✅ ĐÃ LƯU' if saved else '⚠️ ĐÃ CÓ DỮ LIỆU'}\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 Đặc Biệt: `{res['special']}`\n🥇 Giải Nhất: `{res['g1']}`\n"
        f"🎯 Lô về: {', '.join(f'`{n}`' for n in res['loto'])}\n\n⚠️ Chỉ tham khảo — Chơi có trách nhiệm!",
        parse_mode="Markdown"
    )

# ====================== 🚀 KHỞI ĐỘNG ======================
if __name__ == "__main__":
    log("===== BOT XSMB V8.2 KHỞI ĐỘNG =====")
    log(f"Token: {TELEGRAM_TOKEN[:20]}... | ChatID: {CHAT_ID}")
    bot.remove_webhook()
    from threading import Thread
    Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False), daemon=True).start()
    Thread(target=lambda: (time.sleep(10), auto_fetch_old_days()), daemon=True).start()
    log("✅ BOT SẴN SÀNG — Gõ ngày để thử!")
    bot.polling(none_stop=True, interval=3, timeout=60)
