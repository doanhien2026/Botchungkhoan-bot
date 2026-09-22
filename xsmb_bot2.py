# ==========================================================
# xsmb_bot2.py — V45.0 | ✅ GÕ NGÀY → BÁO KQ TỰ ĐỘNG
# Token: 8944857392:AAGPf2Nr90wRiO3Q1v_o2M3fexyhJjFZnh8
# Chat ID: -1001030583610
# ==========================================================

import telebot, json, os, re, time, threading
from datetime import datetime, timedelta
from flask import Flask
from collections import Counter

# ====================== 🔧 CẤU HÌNH ======================
TELEGRAM_TOKEN = "8944857392:AAGPf2Nr90wRiO3Q1v_o2M3fexyhJjFZnh8"
CHAT_ID = "-1001030583610"
DATA_FILE = "xsmb_data.json"
PORT = int(os.environ.get("PORT", 10000))
MIN_DAYS = 30

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)

BOT_LOCK = threading.Lock()
POLLING_STARTED = False

# ====================== 💾 QUẢN LÝ DỮ LIỆU ======================
def load_data():
    if not os.path.exists(DATA_FILE): return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except: return {}

def save_all_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except: return False

def luu_ngay(ngay_str, db, g1):
    """✅ Lưu kết quả 1 ngày"""
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", ngay_str): return False
    if len(db)!=5 or not db.isdigit(): return False
    if len(g1)!=5 or not g1.isdigit(): return False
    
    # Tạo danh sách lô từ 2 số cuối tất cả
    loto = [db[-2:], g1[-2:]]
    for i in range(10):
        loto.append(f"{i:02d}")
    loto = list(set(loto))[:27]

    data = load_data()
    data[ngay_str] = {
        "special": db.strip(),
        "g1": g1.strip(),
        "loto": loto,
        "source": "Nhập từ trang chính xoso.com.vn",
        "updated": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    return save_all_data(data)

def get_stats():
    data = load_data()
    if not data: return 0,"--","--"
    dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    return len(data), dates[0], dates[-1]

# ====================== 📊 DỰ ĐOÁN ======================
def tinh_du_doan():
    data = load_data()
    tong, tu, den = get_stats()
    ngay_mai = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")

    if tong < MIN_DAYS:
        return f"""⚠️ Cần đủ {MIN_DAYS} ngày
👉 Đã nhập: {tong} ngày
👉 Cách nhập: /nhap 21092026 51540 38291
   → Ngày + Đặc biệt + Giải nhất
👉 Mở xoso.com.vn lấy số thật!"""

    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    dem_lo = {}
    dau_de = []
    cuoi_de = []
    
    for ngay in sap_xep:
        kq = data[ngay]
        db = kq["special"]
        dau_de.append(db[0])
        cuoi_de.append(db[-2:])
        for lo in kq["loto"]:
            if lo not in dem_lo: dem_lo[lo] = []
            dem_lo[lo].append(ngay)

    # Chọn 3 con ít xuất hiện nhất + nghỉ lâu nhất
    thong_tin = []
    for so, ngay_list in dem_lo.items():
        lan = len(ngay_list)
        ty_le = round(lan / tong * 100, 1)
        gan_nhat = max(ngay_list, key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        ngay_gan = datetime.strptime(gan_nhat, "%d/%m/%Y")
        nghi = (datetime.now() - ngay_gan).days
        thong_tin.append({"so":so, "lan":lan, "ty_le":ty_le, "nghi":nghi})

    thong_tin.sort(key=lambda x: (x["lan"], -x["nghi"]))
    top3 = thong_tin[:3]
    xien = [top3[0]["so"], top3[1]["so"]]

    # Đầu số đề
    cnt_dau = Counter(dau_de)
    it_dau = sorted(cnt_dau.items(), key=lambda x: x[1])[0]
    # 2 số cuối đề
    cnt_cuoi = Counter(cuoi_de)
    it_cuoi = sorted(cnt_cuoi.items(), key=lambda x: x[1])[0]

    return f"""
🎲 DỰ ĐOÁN — {ngay_mai}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Dữ liệu: {tong} ngày thật

🎯 3 CON LÔ ÍT VỀ NHẤT:
  1. {top3[0]['so']} — {top3[0]['lan']} lần | {top3[0]['ty_le']}% | nghỉ {top3[0]['nghi']} ngày
  2. {top3[1]['so']} — {top3[1]['lan']} lần | {top3[1]['ty_le']}% | nghỉ {top3[1]['nghi']} ngày
  3. {top3[2]['so']} — {top3[2]['lan']} lần | {top3[2]['ty_le']}% | nghỉ {top3[2]['nghi']} ngày

🔄 XIÊN 2: {xien[0]} - {xien[1]}

🔢 Đầu số đề: {it_dau[0]} — {round(it_dau[1]/tong*100,1)}%
🔢 2 số cuối đề: {it_cuoi[0]} — {round(it_cuoi[1]/tong*100,1)}%

⚠️ Dựa trên số thật — Tham khảo!
"""

# ====================== 🤖 LỆNH BOT ======================
def gui(chat_id, text):
    for _ in range(3):
        try:
            with BOT_LOCK:
                return bot.send_message(chat_id, text, parse_mode="Markdown")
        except: time.sleep(1)

@bot.message_handler(commands=['start'])
def start(m):
    tong, tu, den = get_stats()
    gui(m.chat.id, f"""🤖 BOT XSMB — V45.0
📊 Đã nhập: {tong}/{MIN_DAYS} ngày

✅ Cách dùng đơn giản:
/nhap 21092026 51540 38291 → Lưu kết quả
21092026 → Gõ ngày → tự báo kết quả
/dudoan → Xem dự đoán
/status → Xem tổng số ngày
/xoa → Xóa dữ liệu cũ
""")

@bot.message_handler(commands=['nhap'])
def nhap(m):
    parts = m.text.strip().split()
    if len(parts) != 4:
        gui(m.chat.id, """⚠️ Đúng định dạng:
/nhap 21092026 51540 38291
→ Ngày + Đặc biệt + Giải nhất
Không dấu / trong ngày!""")
        return
    try:
        _, ngay_raw, db, g1 = parts
        d, mo, y = ngay_raw[:2], ngay_raw[2:4], ngay_raw[4:]
        ngay_str = f"{d}/{mo}/{y}"
    except:
        gui(m.chat.id, "⚠️ Ngày phải 8 số: 21092026")
        return

    if luu_ngay(ngay_str, db, g1):
        tong, _, _ = get_stats()
        gui(m.chat.id, f"""✅ ĐÃ LƯU! 🎉
📅 {ngay_str}
🏆 Đặc biệt: `{db}`
🥇 Giải nhất: `{g1}`
📊 Tổng: {tong}/{MIN_DAYS} ngày
{f'👉 Gõ /dudoan xem dự đoán!' if tong >= MIN_DAYS else f'Cần thêm {MIN_DAYS - tong} ngày nữa'}""")
    else:
        gui(m.chat.id, "❌ Sai! Kiểm tra: 5 chữ số, không khoảng trắng")

@bot.message_handler(commands=['status'])
def status(m):
    tong, tu, den = get_stats()
    gui(m.chat.id, f"""📊 TRẠNG THÁI
Tổng: {tong}/{MIN_DAYS} ngày
Từ {tu} đến {den}
{f'✅ Đủ dữ liệu!' if tong >= MIN_DAYS else '⏳ Chưa đủ, tiếp tục nhập...'}""")

@bot.message_handler(commands=['dudoan'])
def dudoan(m):
    gui(m.chat.id, tinh_du_doan())

@bot.message_handler(commands=['xoa'])
def xoa(m):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        gui(m.chat.id, "✅ Đã xóa! Bắt đầu nhập lại số thật")
    else:
        gui(m.chat.id, "Chưa có dữ liệu")

# ✅ GÕ NGÀY 8 SỐ → TỰ ĐỘNG BÁO KẾT QUẢ
@bot.message_handler(func=lambda msg: msg.text and len(msg.text.strip()) == 8 and msg.text.strip().isdigit())
def xem_ngay(m):
    ngay_raw = m.text.strip()
    d, mo, y = ngay_raw[:2], ngay_raw[2:4], ngay_raw[4:]
    ngay_str = f"{d}/{mo}/{y}"
    data = load_data()
    
    if ngay_str in data:
        kq = data[ngay_str]
        gui(m.chat.id, f"""📅 {ngay_str}
🏆 Đặc biệt: `{kq['special']}`
🥇 Giải nhất: `{kq['g1']}`
📌 Nguồn: {kq['source']}
🕒 Cập nhật: {kq['updated']}""")
    else:
        gui(m.chat.id, f"""⚠️ Chưa có dữ liệu {ngay_str}
👉 Nhập: /nhap {ngay_raw} ĐB G1
Ví dụ: /nhap {ngay_raw} 12345 67890""")

# ====================== 🚀 CHẠY BOT ======================
def run_bot():
    global POLLING_STARTED
    if POLLING_STARTED: return
    POLLING_STARTED = True
    print("✅ V45.0 — Gõ ngày → tự báo kết quả")
    try: bot.remove_webhook()
    except: pass
    while True:
        try: bot.infinity_polling(timeout=30, long_polling_timeout=40, allowed_updates=None)
        except Exception as e:
            if "409" in str(e): time.sleep(5)
            else: time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT, debug=False), daemon=True).start()
    run_bot()
