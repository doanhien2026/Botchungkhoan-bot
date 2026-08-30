# ==========================================================
# BOT XSMB — V7.2 | TỰ QUÉT 90 NGÀY CŨ + 3 NGUỒN + TỶ LỆ ĐÚNG
# ✅ Tự động lấy dữ liệu 90 ngày gần nhất khi khởi động
# ✅ XOSO.ME | ✅ KQSXOSO | ✅ XOSODAIPHAT | ✅ /nhap thủ công
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
from bs4 import BeautifulSoup

# ====================== 🔧 CẤU HÌNH ======================
TELEGRAM_TOKEN = "8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w"
CHAT_ID = "1030583610"
CHANNEL_ID = "-1001030583610"
PORT = int(os.environ.get("PORT", 10000))
DATA_FILE = "xsmb_data.json"
ANALYSIS_DAYS = 90
AUTO_FETCH_DAYS = 90  # Tự động quét bao nhiêu ngày cũ khi khởi động

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
}

# ====================== 🌐 TRANG CHỦ ======================
@app.route('/')
def home():
    return "✅ Bot XSMB V7.2 — Tự quét 90 ngày cũ + Tỷ lệ chính xác"

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

# ====================== 📡 LẤY KẾT QUẢ — 3 NGUỒN ======================
def validate_result(special, g1, loto):
    if not special or len(special) != 5 or not special.isdigit():
        return False
    if not g1 or len(g1) != 5 or not g1.isdigit():
        return False
    if not loto or len(loto) < 15:
        return False
    return True

# NGUỒN 1: XOSO.ME
def fetch_from_xosome(date_str):
    d, m, y = date_str.split("/")
    try:
        url = f"https://xoso.me/xsmb/{d}-{m}-{y}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        db_tag = soup.find("div", class_="special-prize")
        g1_tag = soup.find("div", class_="prize-1")
        if not db_tag or not g1_tag:
            return None
        special = db_tag.get_text(strip=True).replace(" ", "")
        g1 = g1_tag.get_text(strip=True).replace(" ", "")
        loto_set = set()
        all_prizes = soup.find_all("div", class_=re.compile(r"prize-\d|special"))
        for tag in all_prizes:
            text = tag.get_text(strip=True).replace(" ", "")
            if len(text) == 5 and text.isdigit():
                loto_set.add(text[-2:])
        loto = sorted(list(loto_set))
        if validate_result(special, g1, loto):
            print(f"✅ [{date_str}] XOSO.ME → ĐB:{special} G1:{g1} Lô:{len(loto)} số")
            return {"source": "XOSO.ME", "special": special, "g1": g1, "loto": loto}
        return None
    except Exception as e:
        print(f"⚠️ [{date_str}] XOSO.ME lỗi: {e}")
        return None

# NGUỒN 2: KQSXOSO
def fetch_from_kqxs(date_str):
    d, m, y = date_str.split("/")
    try:
        url = f"https://kqxsoso.com/xsmb-{d}-{m}-{y}.html"
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
            print(f"✅ [{date_str}] KQSXOSO → ĐB:{special} G1:{g1} Lô:{len(loto)} số")
            return {"source": "KQSXOSO", "special": special, "g1": g1, "loto": loto}
        return None
    except Exception as e:
        print(f"⚠️ [{date_str}] KQSXOSO lỗi: {e}")
        return None

# NGUỒN 3: XOSODAIPHAT
def fetch_from_xosodaiphat(date_str):
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
            print(f"✅ [{date_str}] XOSODAIPHAT → ĐB:{special} G1:{g1} Lô:{len(loto)} số")
            return {"source": "XOSODAIPHAT", "special": special, "g1": g1, "loto": loto}
    except Exception as e:
        print(f"⚠️ [{date_str}] XOSODAIPHAT lỗi: {e}")
    return None

# HÀM CHÍNH — Thử 3 nguồn
def fetch_result(date_str):
    result = fetch_from_xosome(date_str)
    if result:
        return result
    result = fetch_from_kqxs(date_str)
    if result:
        return result
    result = fetch_from_xosodaiphat(date_str)
    if result:
        return result
    return None

# ====================== 🤖 TỰ ĐỘNG QUÉT NGÀY CŨ KHI KHỞI ĐỘNG ======================
def auto_fetch_old_days(max_days=AUTO_FETCH_DAYS):
    """✅ Tự động quét và lưu dữ liệu các ngày cũ khi bot khởi động"""
    print("="*60)
    print(f"🔍 BẮT ĐẦU TỰ QUÉT {max_days} NGÀY GẦN NHẤT...")
    print("="*60)
    
    existing_data = load_all_data()
    today = datetime.now()
    fetched_count = 0
    skipped_count = 0
    failed_dates = []
    
    for day_offset in range(1, max_days + 1):  # Từ hôm qua lùi về
        target_date = today - timedelta(days=day_offset)
        date_str = target_date.strftime("%d/%m/%Y")
        
        # Bỏ qua nếu đã có dữ liệu
        if date_str in existing_data:
            skipped_count += 1
            continue
        
        # Lấy kết quả
        result = fetch_result(date_str)
        if result:
            save_data(date_str, result)
            fetched_count += 1
        else:
            failed_dates.append(date_str)
        
        # Tránh bị chặn quá nhanh → delay 1.5s
        time.sleep(1.5)
    
    print("="*60)
    print(f"✅ HOÀN THÀNH QUÉT DỮ LIỆU:")
    print(f"   • Đã lấy mới: {fetched_count} ngày")
    print(f"   • Đã có sẵn: {skipped_count} ngày")
    print(f"   • Thất bại: {len(failed_dates)} ngày")
    if failed_dates:
        print(f"   • Ngày thất bại: {', '.join(failed_dates[:5])}{'...' if len(failed_dates) > 5 else ''}")
    print(f"   • Tổng dữ liệu hiện có: {len(load_all_data())} ngày")
    print("="*60)
    return fetched_count, skipped_count, failed_dates

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
    print(f"📊 Phân tích {limit} ngày gần nhất")
    
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
    
    if total_days < 3:  # Cần ít nhất 3 ngày để tính tỷ lệ đáng tin cậy
        return {
            "ready": False,
            "note": f"⚠️ Chưa đủ dữ liệu — mới có {total_days} ngày. Cần ít nhất 3-5 ngày để tính tỷ lệ!",
            "top3": [],
            "xien": ["--", "--"],
            "first_digit": {"digit": "--", "count": 0, "rate": 0.0},
            "total_days": total_days
        }
    
    freq = Counter(all_loto_nums)
    total_loto = len(all_loto_nums)
    unique_count = len(freq)
    
    scored = []
    for num, count in freq.items():
        rate = round(count / total_days * 100, 2)  # Tỷ lệ % trên tổng số ngày
        sleep_days = last_appear.get(num, 999)
        score = round(count * (1 + 1 / (sleep_days + 1)), 2)  # Điểm kết hợp tần suất + ngủ
        scored.append({"num": num, "count": count, "rate": rate, "sleep": sleep_days, "score": score})
    
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
📈 Phân tích: {pred['total_days']} ngày gần nhất
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ {pred['note']}

💡 Đang tự động lấy dữ liệu ngày cũ trong nền...
   Vui lòng chờ 1-2 phút rồi gõ /dudoan lại!

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
        "🤖 **BOT XSMB — THỐNG KÊ SỐ LÔ V7.2**\n"
        "✅ TỰ QUÉT 90 NGÀY DỮ LIỆU KHI KHỞI ĐỘNG\n"
        "✅ 3 Nguồn: XOSO.ME | KQSXOSO | XOSODAIPHAT\n"
        "✅ Tỷ lệ tính toán chính xác từ dữ liệu thực tế\n"
        "✅ /nhap — Nhập thủ công khi cần\n\n"
        "📌 Gõ DDMMYYYY → Xem & lưu kết quả ngày đó\n"
        "📌 /dudoan → Dự đoán ngày mai (tự phân tích dữ liệu đã có)\n"
        "📌 /dudoan DDMMYYYY → Dự đoán ngày chỉ định\n"
        "📌 /status → Xem số ngày dữ liệu đã có\n"
        "⏳ Lần đầu chạy → Bot tự quét 90 ngày cũ, vui lòng chờ 1-2 phút!",
        parse_mode="Markdown"
    )

# Xem trạng thái dữ liệu
@bot.message_handler(commands=['status'])
def cmd_status(m):
    data = load_all_data()
    bot.send_message(m.chat.id,
        f"📊 **TRẠNG THÁI DỮ LIỆU**\n"
        f"• Tổng ngày đã lưu: **{len(data)} ngày**\n"
        f"• Nguồn dữ liệu: XOSO.ME + KQSXOSO + XOSODAIPHAT\n"
        f"• Ngày cũ nhất: {min(data.keys()) if data else 'Chưa có'}\n"
        f"• Ngày mới nhất: {max(data.keys()) if data else 'Chưa có'}\n\n"
        f"💡 Với {len(data)} ngày → dự đoán sẽ chính xác hơn!",
        parse_mode="Markdown"
    )

# LỆNH NHẬP THỦ CÔNG
@bot.message_handler(commands=['nhap'])
def cmd_nhap_thu_cong(m):
    parts = m.text.strip().split()
    if len(parts) < 5:
        return bot.send_message(m.chat.id,
            "⚠️ **Cách dùng:** /nhap DDMMYYYY ĐB G1 LÔ1,LÔ2,...\n"
            "💡 VD: /nhap 29082026 90737 47583 01,03,08,19,34,37,41,43,44,48,52,56,61,62,67,77,81,83,88,93,94,96",
            parse_mode="Markdown"
        )
    t, db, g1, loto_str = parts[1], parts[2], parts[3], parts[4]
    if not re.match(r"^\d{8}$", t):
        return bot.send_message(m.chat.id, "❌ Định dạng ngày sai! VD: 29082026")
    if len(db) != 5 or not db.isdigit():
        return bot.send_message(m.chat.id, "❌ Giải Đặc Biệt phải 5 chữ số! VD: 90737")
    if len(g1) != 5 or not g1.isdigit():
        return bot.send_message(m.chat.id, "❌ Giải Nhất phải 5 chữ số! VD: 47583")
    d, mo, y = t[:2], t[2:4], t[4:8]
    try:
        datetime(int(y), int(mo), int(d))
    except:
        return bot.send_message(m.chat.id, "❌ Ngày không hợp lệ!")
    date_str = f"{d}/{mo}/{y}"
    loto = [n.strip() for n in loto_str.split(",") if n.strip() and len(n.strip()) == 2]
    if len(loto) < 15:
        return bot.send_message(m.chat.id, f"⚠️ Cần ít nhất 15 số lô, mới có {len(loto)} — Kiểm tra lại!")
    result = {"source": "NHẬP THỦ CÔNG", "special": db, "g1": g1, "loto": loto}
    saved = save_data(date_str, result)
    if saved:
        rep = f"✅ **ĐÃ LƯU THỦ CÔNG — {date_str}**\n📡 Nguồn: NHẬP THỦ CÔNG\n━━━━━━━━━━━━━━━━━━━━\n"
        rep += f"🏆 Đặc Biệt: `{db}`\n🥇 Giải Nhất: `{g1}`\n🎯 Lô về: {', '.join(f'`{n}`' for n in loto)}\n\n⚠️ Chơi có trách nhiệm!"
        bot.send_message(m.chat.id, rep, parse_mode="Markdown")
    else:
        bot.send_message(m.chat.id, f"⚠️ **NGÀY {date_str} ĐÃ TỒN TẠI — KHÔNG LƯU LẠI**", parse_mode="Markdown")

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
        return bot.send_message(m.chat.id, f"⚠️ **KHÔNG LẤY ĐƯỢC KẾT QUẢ — {date_str}**\nThử lại sau hoặc dùng /nhap!")
    rep = f"🧪 **KẾT QUẢ TEST — {date_str}**\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n"
    rep += f"🏆 Đặc Biệt: `{res['special']}`\n🥇 Giải Nhất: `{res['g1']}`\n"
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
        return bot.send_message(m.chat.id, "⚠️ Gõ DDMMYYYY để lưu kết quả (VD: 29082026)\nGõ /start để xem hướng dẫn!")
    d, mo, y = txt[:2], txt[2:4], txt[4:8]
    try:
        datetime(int(y), int(mo), int(d))
    except:
        return bot.send_message(m.chat.id, "❌ Ngày không hợp lệ! VD đúng: 29082026")
    date_str = f"{d}/{mo}/{y}"
    res = fetch_result(date_str)
    if not res:
        return bot.send_message(m.chat.id,
            f"⚠️ **KHÔNG LẤY ĐƯỢC KẾT QUẢ — {date_str}**\n👉 Dùng: /nhap {txt} ĐB G1 LÔ1,LÔ2,... để nhập thủ công!",
            parse_mode="Markdown"
        )
    saved = save_data(date_str, res)
    if not saved:
        rep = f"⚠️ **NGÀY {date_str} ĐÃ TỒN TẠI — KHÔNG LƯU LẠI**\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n"
    else:
        rep = f"📅 **KẾT QUẢ — {date_str}** ✅ ĐÃ LƯU\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n"
    rep += f"🏆 Đặc Biệt: `{res['special']}`\n🥇 Giải Nhất: `{res['g1']}`\n"
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
                    rep += f"🏆 Đặc Biệt: `{res['special']}`\n🥇 Giải Nhất: `{res['g1']}`\n"
                    if res.get("loto"):
                        rep += f"🎯 Lô về: {', '.join(f'`{n}`' for n in res['loto'])}\n"
                    rep += "⚠️ Chơi có trách nhiệm!"
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
    print("🚀 BOT XSMB — V7.2 | TỰ QUÉT 90 NGÀY CŨ + TỶ LỆ ĐÚNG")
    print("✅ Tự động lấy dữ liệu lịch sử khi khởi động")
    print("✅ 3 Nguồn: XOSO.ME | KQSXOSO | XOSODAIPHAT")
    print("✅ Tỷ lệ tính toán chính xác từ dữ liệu")
    print("="*60)
    
    bot.remove_webhook()
    print("✅ Đã xóa webhook")
    
    # Khởi động Flask
    from threading import Thread
    def run_flask():
        app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
    Thread(target=run_flask, daemon=True).start()
    print("✅ Flask server đã chạy")
    
    # 🤖 TỰ QUÉT DỮ LIỆU NGÀY CŨ — Chạy ngầm khi khởi động
    def background_fetch():
        time.sleep(5)  # Đợi bot khởi động xong
        auto_fetch_old_days(AUTO_FETCH_DAYS)
    Thread(target=background_fetch, daemon=True).start()
    print(f"🔄 Đang tự động quét {AUTO_FETCH_DAYS} ngày cũ... (chạy ngầm)")
    
    # Auto-job gửi 18:35
    Thread(target=auto_send, daemon=True).start()
    print("✅ Auto-job đã chạy")
    
    print("✅ BOT SẴN SÀNG — Gõ /start → /status → /dudoan!")
    print("="*60)
    
    # Bắt đầu polling
    bot.polling(none_stop=True, interval=3, timeout=60)
