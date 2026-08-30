# ==========================================================
# BOT XSMB — V6.6 | SỬA LỖI ĐỌC DỮ LIỆU | KHÔNG LƯU TRÙNG
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
ANALYSIS_DAYS = 90

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
}

# ====================== 🌐 TRANG CHỦ ======================
@app.route('/')
def home():
    return "✅ Bot XSMB V6.6 — Đọc dữ liệu đúng | Không lưu trùng"

# ====================== 💾 DỮ LIỆU — SỬA LỖI ĐỌC/GHI ======================
def load_all_data():
    """Đọc dữ liệu — SỬA LỖI: đảm bảo trả về dict rỗng thay vì None"""
    if not os.path.exists(DATA_FILE):
        print(f"ℹ️ File {DATA_FILE} chưa tồn tại → Trả về {}")
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                print(f"⚠️ File {DATA_FILE} rỗng → Trả về {}")
                return {}
            data = json.loads(content)
            if not isinstance(data, dict):
                print(f"⚠️ Dữ liệu không phải dict → Trả về {}")
                return {}
            print(f"✅ Đọc được {len(data)} ngày từ {DATA_FILE}")
            return data
    except json.JSONDecodeError as e:
        print(f"❌ Lỗi định dạng JSON: {e} → Tạo mới")
        return {}
    except Exception as e:
        print(f"❌ Lỗi đọc dữ liệu: {e} → Trả về {}")
        return {}

def save_data(date_str, result):
    """Lưu dữ liệu — KIỂM TRA TRÙNG NGÀY TRƯỚC KHI LƯU"""
    data = load_all_data()
    
    # ✅ Kiểm tra đã có chưa → tránh lưu trùng
    if date_str in data:
        print(f"⚠️ Ngày {date_str} ĐÃ CÓ — Bỏ qua, không lưu trùng")
        return False  # Đã tồn tại → không lưu lại
    
    data[date_str] = result
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ ĐÃ LƯU MỚI: {date_str} — Tổng: {len(data)} ngày")
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu dữ liệu: {e}")
        return False

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

# ====================== 🧠 LOGIC DỰ ĐOÁN — ĐỌC ĐÚNG DỮ LIỆU ======================
def get_history_data(days=ANALYSIS_DAYS):
    """Đọc & phân tích lịch sử — SỬA: đảm bảo duyệt đúng dữ liệu"""
    data = load_all_data()
    
    # ✅ In log để kiểm tra
    print(f"📊 Tổng dữ liệu có: {len(data)} ngày")
    if len(data) == 0:
        return [], [], {}, 0
    
    # Sắp xếp ngày giảm dần
    try:
        sorted_dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    except Exception as e:
        print(f"❌ Lỗi sắp xếp ngày: {e}")
        return [], [], {}, 0
    
    limit = min(days, len(sorted_dates))
    print(f"📊 Phân tích {limit} ngày gần nhất")
    
    all_loto_nums = []
    first_digits = []
    last_appear = {}
    
    for idx, dt in enumerate(sorted_dates[:limit]):
        res = data[dt]
        day_lotos = set()
        
        # Lấy số lô
        if res.get("loto") and isinstance(res["loto"], list):
            for n in res["loto"]:
                if isinstance(n, str) and len(n) == 2:
                    day_lotos.add(n)
        
        # Lấy 2 số cuối giải đặc biệt
        special = res.get("special", "")
        if isinstance(special, str) and len(special) == 5:
            day_lotos.add(special[-2:])
            first_digits.append(special[0])
        
        # Cập nhật lần cuối xuất hiện
        for num in day_lotos:
            if num not in last_appear:
                last_appear[num] = idx
        
        all_loto_nums.extend(day_lotos)
    
    print(f"📊 Tổng số lô thu thập: {len(all_loto_nums)}")
    return all_loto_nums, first_digits, last_appear, limit

def calculate_prediction(days=ANALYSIS_DAYS):
    """Tính toán dự đoán — SỬA: xử lý đúng khi có dữ liệu"""
    all_loto_nums, first_digits, last_appear, total_days = get_history_data(days)
    
    # Chưa có đủ dữ liệu
    if total_days < 1:
        return {
            "ready": False,
            "note": "⚠️ Chưa có dữ liệu — Vui lòng nhập kết quả DDMMYYYY trước!",
            "top3": [
                {"num": "07", "count": 0, "rate": 0.0, "sleep": 0, "score": 0},
                {"num": "29", "count": 0, "rate": 0.0, "sleep": 0, "score": 0},
                {"num": "56", "count": 0, "rate": 0.0, "sleep": 0, "score": 0}
            ],
            "xien": ["07", "29"],
            "first_digit": {"digit": "8", "count": 0, "rate": 0.0},
            "total_days": 0
        }
    
    # ✅ Có dữ liệu → Tính toán
    freq = Counter(all_loto_nums)
    total_loto = len(all_loto_nums)
    print(f"📊 Tính toán: {total_loto} số lô duy nhất = {len(freq)} loại")
    
    scored = []
    for num, count in freq.items():
        rate = round(count / total_loto * 100, 2) if total_loto > 0 else 0.0
        sleep_days = last_appear.get(num, 999)
        score = round(count * (1 + 1 / (sleep_days + 1)), 2)
        scored.append({
            "num": num,
            "count": count,
            "rate": rate,
            "sleep": sleep_days,
            "score": score
        })
    
    # Xếp hạng
    scored.sort(key=lambda x: -x["score"])
    top3 = scored[:3] if len(scored) >= 3 else scored
    
    # Điền đủ 3 nếu thiếu
    while len(top3) < 3:
        top3.append({"num": "--", "count": 0, "rate": 0.0, "sleep": 0, "score": 0})
    
    # Lô xiên
    xien = [top3[0]["num"], top3[1]["num"]] if top3[0]["num"] != "--" and top3[1]["num"] != "--" else ["00", "00"]
    
    # Đầu số đề
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
    pred = calculate_prediction(days)
    target_info = f" — Ngày {target_date}" if target_date else " — Ngày mai"
    
    lines = [
        f"📊 **DỰ ĐOÁN KẾT QUẢ{target_info}**",
        f"📅 Phân tích {pred['total_days']} ngày gần nhất",
        "________________________________________",
        "",
        "🎯 **3 CON LÔ TỶ LỆ CAO NHẤT:**"
    ]
    
    for i, item in enumerate(pred["top3"], 1):
        if item["num"] == "--":
            lines.append(f"   {i}. Chưa đủ dữ liệu")
        else:
            lines.append(
                f"   {i}. `{item['num']}` – {item['count']} lần | {item['rate']}% | "
                f"Ngủ {item['sleep']} ngày"
            )
    
    lines.extend([
        "",
        "🔀 **1 CẶP LÔ XIÊN:**",
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
        "🤖 **BOT XSMB — THỐNG KÊ SỐ LÔ V6.6**\n"
        f"✅ Phân tích {ANALYSIS_DAYS} ngày lịch sử\n"
        "✅ Sửa lỗi đọc dữ liệu + Không lưu trùng\n\n"
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
    
    result_text = gen_prediction_text(ANALYSIS_DAYS, target_date)
    bot.send_message(m.chat.id, result_text, parse_mode="Markdown")

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
    
    # ✅ Lưu với kiểm tra trùng
    saved = save_data(date_str, res)
    if not saved:
        rep = f"⚠️ **NGÀY {date_str} ĐÃ TỒN TẠI — KHÔNG LƯU LẠI**\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n"
    else:
        rep = f"📅 **KẾT QUẢ — {date_str}** ✅ ĐÃ LƯU MỚI\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n"
    
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
    print("🚀 BOT XSMB — V6.6 | SỬA LỖI ĐỌC DỮ LIỆU")
    print(f"✅ Phân tích {ANALYSIS_DAYS} ngày | Không lưu trùng")
    print("="*60)
    
    bot.remove_webhook()
    print("✅ Đã xóa webhook")
    
    Thread(target=run_flask, daemon=True).start()
    print("✅ Flask server đã chạy")
    
    Thread(target=auto_send, daemon=True).start()
    print("✅ Auto-job đã chạy")
    
    print("✅ BOT SẴN SÀNG — Gõ /dudoan → Đọc dữ liệu đúng!")
    print("="*60)
    
    bot.polling(none_stop=True, interval=2, timeout=60)
