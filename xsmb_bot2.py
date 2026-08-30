# ==========================================================
# BOT XSMB — V7.0 | NGUỒN CHÍNH XÁC + ĐỌC DỮ LIỆU ĐÚNG
# ✅ Ưu tiên XOSO.COM.VN | ✅ Không còn số mặc định | ✅ Hiển thị ngày + tỷ lệ rõ
# Token: 8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w
# Chat/Channel ID: 1030583610 | -1001030583610
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
    return "✅ Bot XSMB V7.0 — Nguồn chính xác + Dữ liệu đúng"

# ====================== 💾 QUẢN LÝ DỮ LIỆU ======================
def load_all_data():
    if not os.path.exists(DATA_FILE):
        print(f"ℹ️ File {DATA_FILE} chưa tồn tại → Trả về trống")
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                print(f"⚠️ File {DATA_FILE} rỗng")
                return {}
            data = json.loads(content)
            if not isinstance(data, dict):
                print(f"⚠️ Dữ liệu không phải dạng từ điển")
                return {}
            print(f"✅ Đọc được {len(data)} ngày từ {DATA_FILE}")
            return data
    except json.JSONDecodeError as e:
        print(f"❌ Lỗi định dạng JSON: {e}")
        return {}
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")
        return {}

def save_data(date_str, result):
    data = load_all_data()
    if date_str in data:
        print(f"⚠️ Ngày {date_str} ĐÃ CÓ — Bỏ qua lưu")
        return False
    data[date_str] = result
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ ĐÃ LƯU: {date_str} — Nguồn: {result.get('source','UNKNOWN')} — Tổng: {len(data)} ngày")
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu: {e}")
        return False

# ====================== 📡 LẤY KẾT QUẢ — NGUỒN CHÍNH XÁC ======================
def validate_result(special, g1, loto):
    if not special or len(special) != 5 or not special.isdigit():
        return False
    if not g1 or len(g1) != 5 or not g1.isdigit():
        return False
    if not loto or len(loto) < 15:
        return False
    return True

def fetch_from_xoso(date_str):
    """✅ NGUỒN 1: XOSO.COM.VN — Nguồn chính thức, ưu tiên nhất"""
    d, m, y = date_str.split("/")
    try:
        url = f"https://xoso.com.vn/xsmb/ngay/{d}-{m}-{y}.html"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"⚠️ xoso.com.vn lỗi mã: {r.status_code}")
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        
        db_elem = soup.find("td", class_="giaidb")
        g1_elem = soup.find("td", class_="giai1")
        if not db_elem or not g1_elem:
            print("⚠️ Không tìm thấy Giải Đặc Biệt / Giải Nhất")
            return None
        
        special = db_elem.get_text(strip=True).replace(" ", "")
        g1 = g1_elem.get_text(strip=True).replace(" ", "")
        
        loto_set = set()
        all_cells = soup.find_all("td", class_=re.compile(r"giai\d+|giaidb"))
        for cell in all_cells:
            text = cell.get_text(strip=True).replace(" ", "")
            if len(text) == 5 and text.isdigit():
                loto_set.add(text[-2:])
        
        loto = sorted(list(loto_set))
        if validate_result(special, g1, loto):
            print(f"✅ LẤY TỪ XOSO.COM.VN — ĐB: {special}, G1: {g1}, Lô: {len(loto)} số")
            return {"source": "XOSO.COM.VN", "special": special, "g1": g1, "loto": loto}
        print(f"❌ Dữ liệu không hợp lệ — ĐB: {special}, G1: {g1}, Lô: {len(loto)}")
    except Exception as e:
        print(f"❌ Lỗi XOSO.COM.VN: {e}")
    return None

def fetch_from_xosodaiphat(date_str):
    """⚠️ NGUỒN 2: DỰ PHÒNG — Chỉ dùng khi nguồn chính thức lỗi"""
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
        special = all_5digit[-1]
        g1 = all_5digit[-2]
        loto_set = set(num[-2:] for num in all_5digit)
        loto = sorted(list(loto_set))
        if validate_result(special, g1, loto):
            print(f"⚠️ DÙNG NGUỒN DỰ PHÒNG XOSODAIPHAT — ĐB: {special}, G1: {g1}")
            return {"source": "XOSODAIPHAT", "special": special, "g1": g1, "loto": loto}
    except Exception as e:
        print(f"❌ Lỗi XOSODAIPHAT: {e}")
    return None

def fetch_result(date_str):
    """✅ Ưu tiên nguồn chính thức trước, dự phòng sau"""
    print(f"🔍 Đang lấy kết quả: {date_str}")
    result = fetch_from_xoso(date_str)
    if result:
        return result
    print("⚠️ Nguồn chính thức thất bại → thử nguồn dự phòng...")
    result = fetch_from_xosodaiphat(date_str)
    if result:
        return result
    print("❌ TẤT CẢ NGUỒN ĐỀU THẤT BẠI")
    return None

# ====================== 🧠 LOGIC TÍNH TOÁN DỰ ĐOÁN ======================
def get_history_data(days=ANALYSIS_DAYS):
    data = load_all_data()
    if not data or len(data) == 0:
        print("⚠️ KHÔNG CÓ DỮ LIỆU LỊCH SỬ")
        return [], [], {}, 0
    
    try:
        sorted_dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    except Exception as e:
        print(f"❌ Lỗi sắp xếp ngày: {e}")
        return [], [], {}, 0
    
    limit = min(days, len(sorted_dates))
    print(f"📊 Phân tích {limit} ngày gần nhất: {sorted_dates[:5]}...")
    
    all_loto_nums = []
    first_digits = []
    last_appear = {}
    
    for idx, dt in enumerate(sorted_dates[:limit]):
        res = data[dt]
        day_lotos = set()
        
        if res.get("loto") and isinstance(res["loto"], list):
            for n in res["loto"]:
                if isinstance(n, str) and len(n) == 2:
                    day_lotos.add(n)
        
        special = res.get("special", "")
        if isinstance(special, str) and len(special) == 5:
            day_lotos.add(special[-2:])
            first_digits.append(special[0])
        
        for num in day_lotos:
            if num not in last_appear:
                last_appear[num] = idx
        
        all_loto_nums.extend(day_lotos)
    
    print(f"📊 Tổng lô: {len(all_loto_nums)} lần, {len(set(all_loto_nums))} loại")
    return all_loto_nums, first_digits, last_appear, limit

def calculate_prediction(days=ANALYSIS_DAYS):
    all_loto_nums, first_digits, last_appear, total_days = get_history_data(days)
    
    if total_days < 1:
        return {
            "ready": False,
            "note": "⚠️ Chưa có dữ liệu! Vui lòng nhập kết quả DDMMYYYY trước (VD: 29082026)",
            "top3": [],
            "xien": ["--", "--"],
            "first_digit": {"digit": "--", "count": 0, "rate": 0.0},
            "total_days": 0
        }
    
    freq = Counter(all_loto_nums)
    total_loto = len(all_loto_nums)
    unique_count = len(freq)
    
    scored = []
    for num, count in freq.items():
        rate = round(count / total_days * 100, 2)
        sleep_days = last_appear.get(num, 999)
        score = round(count * (1 + 1 / (sleep_days + 1)), 2)
        scored.append({
            "num": num,
            "count": count,
            "rate": rate,
            "sleep": sleep_days,
            "score": score
        })
    
    scored.sort(key=lambda x: -x["score"])
    top3 = scored[:3]
    
    xien = [top3[0]["num"], top3[1]["num"]] if len(top3) >= 2 else ["--", "--"]
    
    fd_result = {"digit": "--", "count": 0, "rate": 0.0}
    if first_digits:
        fd_freq = Counter(first_digits)
        fd_digit, fd_count = fd_freq.most_common(1)[0]
        fd_rate = round(fd_count / len(first_digits) * 100, 2)
        fd_result = {"digit": fd_digit, "count": fd_count, "rate": fd_rate}
    
    return {
        "ready": True,
        "note": f"✅ Dữ liệu {total_days} ngày | {total_loto} lần xuất hiện | {unique_count} loại số lô",
        "top3": top3,
        "xien": xien,
        "first_digit": fd_result,
        "total_days": total_days
    }

def gen_prediction_text(days=ANALYSIS_DAYS, target_date=None):
    pred = calculate_prediction(days)
    
    if target_date:
        target_info = f"📅 DỰ ĐOÁN NGÀY: {target_date}"
    else:
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
        target_info = f"📅 DỰ ĐOÁN NGÀY MAI: {tomorrow}"
    
    if not pred["ready"]:
        return f"""{target_info}
📈 Phân tích: 0 ngày gần nhất
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ {pred['note']}

💡 Hướng dẫn: Nhập kết quả các ngày trước đó:
   29082026
   28082026
   27082026
   ...
   Nhập ít nhất 5-7 ngày → dự đoán chính xác hơn!

⚠️ Chỉ tham khảo — Chơi có trách nhiệm!"""
    
    lines = [
        f"📊 {target_info}",
        f"📈 Phân tích: {pred['total_days']} ngày gần nhất",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "🎯 3 CON LÔ CÓ TỶ LỆ XUẤT HIỆN CAO NHẤT:",
        "   (Tỷ lệ = Số lần xuất hiện ÷ Tổng ngày × 100%)"
    ]
    
    for i, item in enumerate(pred["top3"], 1):
        lines.append(
            f"   {i} • `{item['num']}`  →  {item['count']} lần  |  Tỷ lệ: {item['rate']}%  |  "
            f"Ngủ: {item['sleep']} ngày trước khi ra gần nhất"
        )
    
    lines.extend([
        "",
        "🔀 1 CẶP LÔ XIÊN (Kết hợp 2 con cao nhất):",
        f"   → `{pred['xien'][0]}` + `{pred['xien'][1]}`",
        "",
        "🔢 DỰ KIẾN ĐẦU SỐ GIẢI ĐẶC BIỆT:",
        f"   → Đầu số `{pred['first_digit']['digit']}`  |  Xuất hiện: {pred['first_digit']['count']} lần  |  Tỷ lệ: {pred['first_digit']['rate']}%",
        "",
        f"ℹ️ {pred['note']}",
        "",
        "💡 GIẢI THÍCH TỶ LỆ:",
        "   • Tỷ lệ % = Số lần xuất hiện trong quá khứ ÷ Tổng ngày phân tích × 100%",
        "   • Ngủ = Số ngày liên tục chưa xuất hiện tính đến ngày gần nhất",
        "   • Ưu tiên số có tỷ lệ cao + vừa ra gần đây",
        "",
        "⚠️ Chỉ tham khảo — Chơi có trách nhiệm!"
    ])
    
    return "\n".join(lines)

# ====================== 📋 LỆNH BOT ======================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id,
        "🤖 **BOT XSMB — THỐNG KÊ SỐ LÔ V7.0**\n"
        "✅ Nguồn chính thức XOSO.COM.VN\n"
        "✅ Hiển thị ngày dự đoán + Tỷ lệ rõ ràng\n"
        "✅ Không còn số mặc định giả lập\n"
        f"✅ Phân tích {ANALYSIS_DAYS} ngày lịch sử\n\n"
        "📌 Gõ DDMMYYYY → Lưu kết quả ngày đó (VD: 29082026)\n"
        "📌 /test DDMMYYYY → Xem kết quả, không lưu\n"
        "📌 /dudoan → Dự đoán ngày mai\n"
        "📌 /dudoan 30082026 → Dự đoán ngày chỉ định\n"
        "📌 Nhập ít nhất 5-7 ngày kết quả → dự đoán chính xác hơn!",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['test'])
def cmd_test(m):
    parts = m.text.strip().split()
    if len(parts) < 2 or not re.match(r"^\d{8}$", parts[1]):
        return bot.send_message(m.chat.id, "⚠️ /test DDMMYYYY — VD: /test 29082026")
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
    rep += f"🥇 Giải Nhất: `{res['g1']}`\n"
    if res.get("loto"):
        rep += f"🎯 Lô về: {', '.join(f'`{n}`' for n in res['loto'])}\n"
    rep += "\n✅ **CHỈ XEM — KHÔNG LƯU**"
    bot.send_message(m.chat.id, rep, parse_mode="Markdown")

@bot.message_handler(commands=['dudoan', 'thongke'])
def cmd_dt(m):
    print(f"✅ LỆNH /dudoan TỪ: {m.chat.id} — Nội dung: {m.text}")
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
        return bot.send_message(m.chat.id, "⚠️ Gõ DDMMYYYY để lưu kết quả (VD: 29082026) hoặc /start để xem hướng dẫn")
    d, mo, y = txt[:2], txt[2:4], txt[4:8]
    try:
        datetime(int(y), int(mo), int(d))
    except:
        return bot.send_message(m.chat.id, "❌ Ngày không hợp lệ! VD đúng: 29082026")
    date_str = f"{d}/{mo}/{y}"
    res = fetch_result(date_str)
    if not res:
        return bot.send_message(m.chat.id, f"⚠️ **KHÔNG LẤY ĐƯỢC KẾT QUẢ — {date_str}**\nKiểm tra lại hoặc thử lại sau!")
    saved = save_data(date_str, res)
    if not saved:
        rep = f"⚠️ **NGÀY {date_str} ĐÃ TỒN TẠI — KHÔNG LƯU LẠI**\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n"
    else:
        rep = f"📅 **KẾT QUẢ — {date_str}** ✅ ĐÃ LƯU\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n"
    rep += f"🏆 Đặc Biệt: `{res['special']}`\n"
    rep += f"🥇 Giải Nhất: `{res['g1']}`\n"
    if res.get("loto"):
        rep += f"🎯 Lô về: {', '.join(f'`{n}`' for n in res['loto'])}\n"
    rep += "\n⚠️ Chỉ tham khảo — Chơi có trách nhiệm!"
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
                if res:
                    rep = f"📢 **KẾT QUẢ NGÀY {today}**\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n"
                    rep += f"🏆 Đặc Biệt: `{res['special']}`\n"
                    rep += f"🥇 Giải Nhất: `{res['g1']}`\n"
                    if res.get("loto"):
                        rep += f"🎯 Lô về: {', '.join(f'`{n}`' for n in res['loto'])}\n"
                    rep += "⚠️ Chỉ tham khảo — Chơi có trách nhiệm!"
                    bot.send_message(CHANNEL_ID, rep, parse_mode="Markdown")
                    save_data(today, res)
                
                d, m, y = today.split("/")
                tom = (datetime(int(y), int(m), int(d)) + timedelta(days=1)).strftime("%d/%m/%Y")
                pred_text = gen_prediction_text(ANALYSIS_DAYS, tom)
                bot.send_message(CHANNEL_ID, f"🔮 {pred_text}", parse_mode="Markdown")
                last = today
            time.sleep(30)
        except Exception as e:
            print(f"❌ Lỗi auto_send: {e}")
            time.sleep(60)

# ====================== 🚀 KHỞI ĐỘNG ======================
if __name__ == "__main__":
    print("="*60)
    print("🚀 BOT XSMB — V7.0 | NGUỒN CHÍNH XÁC + DỮ LIỆU ĐÚNG")
    print("✅ Ưu tiên XOSO.COM.VN | ✅ Không số mặc định | ✅ Hiển thị ngày + tỷ lệ")
    print("="*60)
    
    bot.remove_webhook()
    print("✅ Đã xóa webhook")
    
    from threading import Thread
    def run_flask():
        app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
    Thread(target=run_flask, daemon=True).start()
    print("✅ Flask server đã chạy")
    
    Thread(target=auto_send, daemon=True).start()
    print("✅ Auto-job đã chạy")
    
    print("✅ BOT SẴN SÀNG — Gõ /start để bắt đầu!")
    print("="*60)
    
    bot.polling(none_stop=True, interval=3, timeout=60)
