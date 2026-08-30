# ==========================================================
# BOT XSMB — V8.1 | API MIỄN PHÍ + TỰ LƯU + BỎ NHẬP TAY
# ✅ Gõ DDMMYYYY → Tự lấy kết quả + Tự lưu ngay
# ✅ 2 Nguồn API: KQXS.VN + XOSO-API (không bị chặn Render)
# ✅ Bỏ hoàn toàn lệnh /nhap
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
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# ====================== 🌐 TRANG CHỦ ======================
@app.route('/')
def home():
    return "✅ Bot XSMB V8.1 — API miễn phí + Tự lưu + Bỏ nhập tay"

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

# ====================== 📡 LẤY KẾT QUẢ — 2 NGUỒN API MIỄN PHÍ ======================
def validate_result(special, g1, loto):
    if not special or len(special) != 5 or not special.isdigit():
        return False
    if not g1 or len(g1) != 5 or not g1.isdigit():
        return False
    if not loto or len(loto) < 15:
        return False
    return True

# NGUỒN 1: API KQXS — ổn định, không bị chặn
def fetch_from_kqxs_api(date_str):
    d, m, y = date_str.split("/")
    try:
        # Định dạng: DD/MM/YYYY → YYYY-MM-DD
        date_api = f"{y}-{m}-{d}"
        url = f"https://api.kqxs.vn/api/xsmb?date={date_api}"
        print(f"🔍 Đang gọi API KQXS: {url}")
        r = requests.get(url, headers=HEADERS, timeout=20)
        print(f"📡 Mã phản hồi KQXS: {r.status_code}")
        if r.status_code != 200:
            return None
        j = r.json()
        if j.get("error") is False and "data" in j:
            data = j["data"]
            special = str(data.get("special", "")).strip()
            g1 = str(data.get("prize1", "")).strip()
            loto = []
            # Lấy tất cả số 2 chữ số cuối từ các giải
            for key in ["prize1", "prize2", "prize3", "prize4", "prize5", "prize6", "prize7", "special"]:
                val = data.get(key, [])
                if isinstance(val, str):
                    if len(val) == 5 and val.isdigit():
                        loto.append(val[-2:])
                elif isinstance(val, list):
                    for v in val:
                        s = str(v).strip()
                        if len(s) == 5 and s.isdigit():
                            loto.append(s[-2:])
            loto = sorted(list(set(loto)))
            if validate_result(special, g1, loto):
                print(f"✅ API KQXS — {date_str} | ĐB:{special} G1:{g1} Lô:{len(loto)} số")
                return {"source": "API KQXS", "special": special, "g1": g1, "loto": loto}
        return None
    except Exception as e:
        print(f"❌ Lỗi API KQXS: {e}")
        return None

# NGUỒN 2: XOSO-API — dự phòng, miễn phí, không bị chặn
def fetch_from_xoso_api(date_str):
    d, m, y = date_str.split("/")
    try:
        url = f"https://xoso-api.onrender.com/api/xsmb?day={d}&month={m}&year={y}"
        print(f"🔍 Đang gọi API XOSO: {url}")
        r = requests.get(url, headers=HEADERS, timeout=20)
        print(f"📡 Mã phản hồi XOSO: {r.status_code}")
        if r.status_code != 200:
            return None
        j = r.json()
        if j.get("status") == "success" and "result" in j:
            res = j["result"]
            special = str(res.get("special_prize", "")).strip()
            g1 = str(res.get("prize_1", "")).strip()
            loto = []
            prizes = res.get("prizes", {})
            for prize_list in prizes.values():
                if isinstance(prize_list, list):
                    for num in prize_list:
                        s = str(num).strip()
                        if len(s) == 5 and s.isdigit():
                            loto.append(s[-2:])
            loto = sorted(list(set(loto)))
            if validate_result(special, g1, loto):
                print(f"✅ API XOSO — {date_str} | ĐB:{special} G1:{g1} Lô:{len(loto)} số")
                return {"source": "API XOSO", "special": special, "g1": g1, "loto": loto}
        return None
    except Exception as e:
        print(f"❌ Lỗi API XOSO: {e}")
        return None

# HÀM CHÍNH — Thử 2 nguồn liên tiếp
def fetch_result(date_str):
    print(f"🔍 Đang lấy kết quả: {date_str}")
    # Thử nguồn 1
    result = fetch_from_kqxs_api(date_str)
    if result:
        return result
    # Thử nguồn 2
    print("⚠️ Nguồn 1 thất bại → thử Nguồn 2...")
    result = fetch_from_xoso_api(date_str)
    if result:
        return result
    print("❌ TẤT CẢ NGUỒN ĐỀU THẤT BẠI")
    return None

# ====================== 🤖 TỰ QUÉT NGÀY CŨ KHI KHỞI ĐỘNG ======================
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
    
    for day_offset in range(1, max_days + 1):
        target_date = today - timedelta(days=day_offset)
        date_str = target_date.strftime("%d/%m/%Y")
        
        if date_str in existing_data:
            skipped_count += 1
            continue
        
        result = fetch_result(date_str)
        if result:
            save_data(date_str, result)
            fetched_count += 1
        else:
            failed_dates.append(date_str)
        
        time.sleep(2)  # Tránh bị giới hạn tần suất API
    
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

# ====================== 🧠 TÍNH TOÁN DỰ ĐOÁN ======================
def calculate_prediction():
    data = load_all_data()
    total_days = len(data)
    
    if total_days < 3:
        return {
            "ready": False,
            "note": f"⚠️ Chưa đủ dữ liệu — mới có {total_days} ngày.\nGõ thêm ngày (VD: 29082026) để tích lũy!\nCần ít nhất 3-5 ngày → dự đoán chính xác hơn!"
        }
    
    try:
        sorted_dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    except Exception as e:
        print(f"❌ Lỗi sắp xếp ngày: {e}")
        return {"ready": False, "note": "⚠️ Lỗi đọc dữ liệu, vui lòng thử lại!"}
    
    limit = min(ANALYSIS_DAYS, total_days)
    all_loto_nums = []
    first_digits = []
    last_appear = {}
    
    for idx, dt in enumerate(sorted_dates[:limit]):
        res = data[dt]
        day_loto = set(res.get("loto", []))
        special = res.get("special", "")
        if isinstance(special, str) and len(special) == 5:
            day_loto.add(special[-2:])
            first_digits.append(special[0])
        for num in day_loto:
            if num not in last_appear:
                last_appear[num] = idx
        all_loto_nums.extend(day_loto)
    
    freq = Counter(all_loto_nums)
    scored = []
    for num, count in freq.items():
        rate = round(count / limit * 100, 1)
        sleep_days = last_appear.get(num, 999)
        scored.append({
            "num": num,
            "count": count,
            "rate": rate,
            "sleep": sleep_days
        })
    
    scored.sort(key=lambda x: (-x["rate"], x["sleep"]))
    top3 = scored[:3]
    xien = [top3[0]["num"], top3[1]["num"]] if len(top3) >= 2 else ["--", "--"]
    
    fd_result = {"digit": "--", "count": 0, "rate": 0.0}
    if first_digits:
        fd_freq = Counter(first_digits)
        fd_digit, fd_count = fd_freq.most_common(1)[0]
        fd_rate = round(fd_count / len(first_digits) * 100, 1)
        fd_result = {"digit": fd_digit, "count": fd_count, "rate": fd_rate}
    
    return {
        "ready": True,
        "total_days": limit,
        "top3": top3,
        "xien": xien,
        "first_digit": fd_result
    }

# ====================== 📋 LỆNH BOT ======================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id,
        "🤖 **BOT XSMB — V8.1 | API MIỄN PHÍ + TỰ LƯU**\n"
        "✅ Gõ DDMMYYYY → Tự lấy kết quả + Tự lưu ngay\n"
        "✅ 2 Nguồn API: KQXS + XOSO-API (không bị chặn)\n"
        "✅ Bỏ nhập tay — chỉ lấy từ nguồn tự động\n"
        "✅ Tự quét 90 ngày cũ khi khởi động\n\n"
        "📌 Gõ: 29082026 → Xem & lưu kết quả\n"
        "📌 /dudoan → Dự đoán ngày mai\n"
        "📌 /status → Xem tổng số ngày đã lưu\n"
        "📌 /test DDMMYYYY → Xem kết quả, không lưu\n\n"
        "💡 Nhập càng nhiều ngày → dự đoán càng chính xác!",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    data = load_all_data()
    bot.send_message(m.chat.id,
        f"📊 **TRẠNG THÁI DỮ LIỆU**\n"
        f"• Tổng ngày đã lưu: **{len(data)} ngày**\n"
        f"• Ngày cũ nhất: {min(data.keys()) if data else 'Chưa có'}\n"
        f"• Ngày mới nhất: {max(data.keys()) if data else 'Chưa có'}\n\n"
        f"💡 Với {len(data)} ngày → dự đoán sẽ chính xác hơn!",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['test'])
def cmd_test(m):
    parts = m.text.strip().split()
    if len(parts) < 2 or not re.match(r"^\d{8}$", parts[1]):
        return bot.send_message(m.chat.id, "⚠️ /test DDMMYYYY — VD: /test 29082026")
    t = parts[1]
    date_str = f"{t[:2]}/{t[2:4]}/{t[4:8]}"
    try:
        datetime(int(t[4:8]), int(t[2:4]), int(t[:2]))
    except:
        return bot.send_message(m.chat.id, "❌ Ngày không hợp lệ! VD: 29082026")
    res = fetch_result(date_str)
    if not res:
        return bot.send_message(m.chat.id,
            f"⚠️ **KHÔNG LẤY ĐƯỢC KẾT QUẢ — {date_str}**\n"
            "Kiểm tra lại ngày hoặc thử lại sau!",
            parse_mode="Markdown"
        )
    bot.send_message(m.chat.id,
        f"🧪 **KẾT QUẢ TEST — {date_str}**\n📡 Nguồn: {res['source']}\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 Đặc Biệt: `{res['special']}`\n🥇 Giải Nhất: `{res['g1']}`\n"
        f"🎯 Lô về: {', '.join(f'`{n}`' for n in res['loto'])}\n\n✅ **CHỈ XEM — KHÔNG LƯU**",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['dudoan'])
def cmd_dudoan(m):
    pred = calculate_prediction()
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    
    if not pred["ready"]:
        return bot.send_message(m.chat.id,
            f"📅 **DỰ ĐOÁN NGÀY MAI: {tomorrow}**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n{pred['note']}",
            parse_mode="Markdown"
        )
    
    bot.send_message(m.chat.id,
        f"📅 **DỰ ĐOÁN NGÀY MAI: {tomorrow}**\n📊 Phân tích: {pred['total_days']} ngày\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎯 3 CON LÔ CÓ TỶ LỆ XUẤT HIỆN CAO NHẤT:\n"
        "   (Tỷ lệ = Số lần xuất hiện ÷ Tổng ngày × 100%)\n\n" +
        "\n".join([
            f"   {i+1}. `{x['num']}`  →  {x['count']} lần  |  Tỷ lệ: {x['rate']}%  |  Ngủ: {x['sleep']} ngày"
            for i, x in enumerate(pred['top3'])
        ]) +
        f"\n\n🔀 1 CẶP LÔ XIÊN: `{pred['xien'][0]}` + `{pred['xien'][1]}`\n\n"
        f"🔢 DỰ KIẾN ĐẦU SỐ GIẢI ĐẶC BIỆT: `{pred['first_digit']['digit']}`  |  Tỷ lệ: {pred['first_digit']['rate']}%\n\n"
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
        return bot.send_message(m.chat.id, "❌ Ngày không hợp lệ! VD đúng: 29082026")
    
    res = fetch_result(date_str)
    if not res:
        return bot.send_message(m.chat.id,
            f"⚠️ **KHÔNG LẤY ĐƯỢC KẾT QUẢ — {date_str}**\n"
            "Kiểm tra lại ngày hoặc thử lại sau!",
            parse_mode="Markdown"
        )
    
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
                        f"🎯 Lô về: {', '.join(f'`{n}`' for n in res['loto'])}\n\n⚠️ Chỉ tham khảo — Chơi có trách nhiệm!",
                        parse_mode="Markdown"
                    )
                pred = calculate_prediction()
                d, m, y = today.split("/")
                tom = (datetime(int(y), int(m), int(d)) + timedelta(days=1)).strftime("%d/%m/%Y")
                if pred["ready"]:
                    bot.send_message(CHANNEL_ID,
                        f"🔮 **DỰ ĐOÁN NGÀY: {tom}**\n📊 Phân tích: {pred['total_days']} ngày\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "🎯 3 CON LÔ TỶ LỆ CAO NHẤT:\n" +
                        "\n".join([
                            f"   {i+1}. `{x['num']}`  →  {x['count']} lần  |  Tỷ lệ: {x['rate']}%"
                            for i, x in enumerate(pred['top3'])
                        ]) +
                        f"\n\n🔀 LÔ XIÊN: `{pred['xien'][0]}` + `{pred['xien'][1]}`\n"
                        f"🔢 ĐẦU SỐ ĐỀ: `{pred['first_digit']['digit']}` — Tỷ lệ: {pred['first_digit']['rate']}%\n\n⚠️ Chơi có trách nhiệm!",
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
    print("🚀 BOT XSMB — V8.1 | API MIỄN PHÍ + TỰ LƯU + BỎ NHẬP TAY")
    print("✅ 2 Nguồn API: KQXS + XOSO-API (không bị chặn Render)")
    print("✅ Gõ DDMMYYYY → Tự lấy + Tự lưu ngay")
    print("✅ Bỏ hoàn toàn lệnh nhập tay")
    print("✅ Tự quét 90 ngày cũ khi khởi động")
    print("="*60)
    
    bot.remove_webhook()
    print("✅ Đã xóa webhook")
    
    # Khởi động Flask
    from threading import Thread
    def run_flask():
        app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
    Thread(target=run_flask, daemon=True).start()
    print("✅ Flask server đã chạy")
    
    # Tự quét dữ liệu ngày cũ — chạy ngầm
    def background_fetch():
        time.sleep(5)
        auto_fetch_old_days(AUTO_FETCH_DAYS)
    Thread(target=background_fetch, daemon=True).start()
    print(f"🔄 Đang tự động quét {AUTO_FETCH_DAYS} ngày cũ... (chạy ngầm)")
    
    # Auto-job gửi 18:35
    Thread(target=auto_send, daemon=True).start()
    print("✅ Auto-job đã chạy")
    
    print("✅ BOT SẴN SÀNG — Gõ /start → Gõ ngày → Tự lưu!")
    print("="*60)
    
    bot.polling(none_stop=True, interval=3, timeout=60)
