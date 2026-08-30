# ==========================================================
# BOT XSMB — V6.5 | DỰ ĐOÁN 90 NGÀY | LOGIC CHẶT CHẼ
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
ANALYSIS_DAYS = 90  # ✅ PHÂN TÍCH 90 NGÀY

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
}

# ====================== 🌐 TRANG CHỦ ======================
@app.route('/')
def home():
    return "✅ Bot XSMB V6.5 — Dự đoán 90 ngày | Logic chặt chẽ"

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

# ====================== 🧠 LOGIC DỰ ĐOÁN 90 NGÀY — CHẶT CHẼ ======================
def get_history_data(days=ANALYSIS_DAYS):
    """Lấy dữ liệu lịch sử + tính toán đầy đủ cho logic dự đoán"""
    data = load_all_data()
    if not data:
        return None, None, None, 0
    
    # Sắp xếp ngày giảm dần
    sorted_dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    limit = min(days, len(sorted_dates))
    
    all_loto_nums = []       # Tất cả số lô 2 chữ số
    first_digits = []        # Đầu số giải đặc biệt
    history_detail = {}      # Chi tiết từng ngày
    last_appear = {}         # Lần cuối xuất hiện của mỗi số
    
    for idx, dt in enumerate(sorted_dates[:limit]):
        res = data[dt]
        history_detail[dt] = res
        
        # Lấy tất cả số lô
        day_lotos = set()
        if res.get("loto"):
            for n in res["loto"]:
                day_lotos.add(n)
        if res.get("special") and len(res["special"]) == 5:
            day_lotos.add(res["special"][-2:])
            first_digits.append(res["special"][0])
        
        # Cập nhật lần cuối xuất hiện
        for num in day_lotos:
            if num not in last_appear:
                last_appear[num] = idx
        
        all_loto_nums.extend(day_lotos)
    
    total_records = len(sorted_dates[:limit])
    return all_loto_nums, first_digits, last_appear, total_records

def calculate_prediction(days=ANALYSIS_DAYS):
    """Tính toán dự đoán đầy đủ — trả về dữ liệu có cấu trúc"""
    all_loto_nums, first_digits, last_appear, total_days = get_history_data(days)
    
    # Chưa có đủ dữ liệu
    if not all_loto_nums or len(all_loto_nums) < 10:
        return {
            "ready": False,
            "note": "Chưa có đủ dữ liệu lịch sử — cần nhập kết quả ít nhất 10 ngày",
            "top3": [
                {"num": "07", "count": 0, "rate": 0.0, "sleep": 0, "score": 0},
                {"num": "29", "count": 0, "rate": 0.0, "sleep": 0, "score": 0},
                {"num": "56", "count": 0, "rate": 0.0, "sleep": 0, "score": 0}
            ],
            "xien": ["07", "29"],
            "first_digit": {"digit": "8", "count": 0, "rate": 0.0},
            "total_days": total_days
        }
    
    # 1. Tính tần suất lô
    freq = Counter(all_loto_nums)
    total_loto = len(all_loto_nums)
    
    # 2. Tính điểm xếp hạng: tần suất cao + chu kỳ ngủ hợp lý
    scored = []
    for num, count in freq.items():
        rate = round(count / total_loto * 100, 2)
        sleep_days = last_appear.get(num, 999)
        # Điểm = tần suất * (1 + 1/(ngủ+1)) — ưu tiên số thường ra + vừa ra gần đây
        score = round(count * (1 + 1 / (sleep_days + 1)), 2)
        scored.append({
            "num": num,
            "count": count,
            "rate": rate,
            "sleep": sleep_days,
            "score": score
        })
    
    # 3. Xếp hạng theo điểm → lấy top 3
    scored.sort(key=lambda x: -x["score"])
    top3 = scored[:3]
    
    # 4. Lô xiên = 2 con có điểm cao nhất
    xien = [top3[0]["num"], top3[1]["num"]] if len(top3) >= 2 else ["00", "00"]
    
    # 5. Đầu số đề
    fd_result = {"digit": "8", "count": 0, "rate": 0.0}
    if first_digits:
        fd_freq = Counter(first_digits)
        fd_digit, fd_count = fd_freq.most_common(1)[0]
        fd_rate = round(fd_count / len(first_digits) * 100, 2)
        fd_result = {"digit": fd_digit, "count": fd_count, "rate": fd_rate}
    
    return {
        "ready": True,
        "note": f"✅ Dữ liệu {total_days} ngày — {total_loto} số lô phân tích",
        "top3": top3,
        "xien": xien,
        "first_digit": fd_result,
        "total_days": total_days
    }

def gen_prediction_text(days=ANALYSIS_DAYS, target_date=None):
    """Tạo nội dung tin nhắn dự đoán"""
    pred = calculate_prediction(days)
    target_info = f" — Ngày {target_date}" if target_date else " — Ngày mai"
    
    lines = [
        f"📊 **DỰ ĐOÁN KẾT QUẢ{target_info}**",
        f"📅 Phân tích {pred['total_days']} ngày gần nhất | Logic: Tần suất + Chu kỳ ngủ",
        "________________________________________",
        "",
        "🎯 **3 CON LÔ TỶ LỆ CAO NHẤT:**",
        "   (Điểm = Tần suất × Hệ số chu kỳ ngủ)"
    ]
    
    for i, item in enumerate(pred["top3"], 1):
        lines.append(
            f"   {i}. `{item['num']}` – {item['count']} lần | {item['rate']}% | "
            f"Ngủ {item['sleep']} ngày | Điểm: {item['score']}"
        )
    
    lines.extend([
        "",
        "🔀 **1 CẶP LÔ XIÊN (Kết hợp 2 cao nhất):**",
        f"   → `{pred['xien'][0]} – {pred['xien'][1]}`",
        "",
        "🔢 **DỰ KIẾN ĐẦU SỐ ĐỀ:**",
        f"   → Đầu số `{pred['first_digit']['digit']}` – "
        f"{pred['first_digit']['count']} lần → {pred['first_digit']['rate']}%",
        "",
        f"ℹ️ {pred['note']}",
        "⚠️ *Chỉ tham khảo — Chơi có trách nhiệm!*"
    ])
    
    return "\n".join(lines)

# ====================== 📋 LỆNH BOT ======================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    print(f"✅ /start từ: {m.chat.id}")
    bot.send_message(m.chat.id,
        "🤖 **BOT XSMB — THỐNG KÊ SỐ LÔ V6.5**\n"
        f"✅ Phân tích {ANALYSIS_DAYS} ngày lịch sử\n"
        "✅ Logic: Tần suất + Chu kỳ ngủ + Điểm tổng hợp\n\n"
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
    print(f"✅ LỆNH /dudoan TỪ: {m.chat.id}")
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
    
    # ✅ Tính toán & gửi kết quả NGAY
    result_text = gen_prediction_text(ANALYSIS_DAYS, target_date)
    print(f"✅ Đã tạo dự đoán — {ANALYSIS_DAYS} ngày")
    
    try:
        bot.send_message(m.chat.id, result_text, parse_mode="Markdown")
        print("✅ Đã gửi kết quả dự đoán!")
    except Exception as e:
        print(f"❌ Lỗi gửi: {e}")
        bot.send_message(m.chat.id, "⚠️ Đã có lỗi — vui lòng thử lại!")

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
                pred = gen_prediction_text(ANALYSIS_DAYS)
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
    print(f"🚀 BOT XSMB — V6.5 | PHÂN TÍCH {ANALYSIS_DAYS} NGÀY")
    print(f"✅ Bot: @Thongkeso999_bot")
    print("✅ Logic: Tần suất + Chu kỳ ngủ + Điểm tổng hợp")
    print("="*60)
    
    bot.remove_webhook()
    print("✅ Đã xóa webhook")
    
    Thread(target=run_flask, daemon=True).start()
    print("✅ Flask server đã chạy")
    
    Thread(target=auto_send, daemon=True).start()
    print("✅ Auto-job đã chạy")
    
    print(f"✅ BOT SẴN SÀNG — Gõ /dudoan → Phân tích {ANALYSIS_DAYS} ngày!")
    print("="*60)
    
    bot.polling(none_stop=True, interval=2, timeout=60)
