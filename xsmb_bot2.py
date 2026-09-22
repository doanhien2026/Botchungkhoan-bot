# ==========================================================
# xsmb_bot2.py — V46.0 | ✅ TEST DỰ ĐOÁN NGÀY CŨ
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
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", ngay_str): return False
    if len(db)!=5 or not db.isdigit(): return False
    if len(g1)!=5 or not g1.isdigit(): return False
    
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

# ====================== 📊 TÍNH DỰ ĐOÁN ======================
def tinh_du_doan_tu_du_lieu(danh_sach_ngay):
    """Tính dự đoán từ danh sách dữ liệu cho trước"""
    dem_lo = {}
    dau_de = []
    cuoi_de = []
    
    for ngay in danh_sach_ngay:
        kq = danh_sach_ngay[ngay]
        db = kq["special"]
        dau_de.append(db[0])
        cuoi_de.append(db[-2:])
        for lo in kq["loto"]:
            if lo not in dem_lo: dem_lo[lo] = []
            dem_lo[lo].append(ngay)

    tong_ngay = len(danh_sach_ngay)
    if tong_ngay < 5:
        return None, None, None, None, "Ít dữ liệu quá"

    # 3 con lô ít xuất hiện nhất + nghỉ lâu nhất
    thong_tin = []
    for so, ngay_list in dem_lo.items():
        lan = len(ngay_list)
        ty_le = round(lan / tong_ngay * 100, 1)
        gan_nhat = max(ngay_list, key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        ngay_gan = datetime.strptime(gan_nhat, "%d/%m/%Y")
        nghi = (datetime.now() - ngay_gan).days
        thong_tin.append({"so":so, "lan":lan, "ty_le":ty_le, "nghi":nghi})

    thong_tin.sort(key=lambda x: (x["lan"], -x["nghi"]))
    top3 = thong_tin[:3]
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3)>=2 else ["--", "--"]

    # Đầu số đề ít xuất hiện
    cnt_dau = Counter(dau_de)
    it_dau = sorted(cnt_dau.items(), key=lambda x: x[1])[0]
    # 2 số cuối đề ít xuất hiện
    cnt_cuoi = Counter(cuoi_de)
    it_cuoi = sorted(cnt_cuoi.items(), key=lambda x: x[1])[0]

    return top3, xien, it_dau, it_cuoi, tong_ngay

# ====================== 🧪 TEST DỰ ĐOÁN NGÀY CŨ ======================
def test_ngay_cu(ngay_str):
    """Test dự đoán 1 ngày trong quá khứ"""
    data = load_data()
    if ngay_str not in data:
        return None, f"⚠️ Chưa có dữ liệu ngày {ngay_str}"
    
    # Lấy tất cả dữ liệu TRƯỚC ngày cần test
    ngay_muc_tieu = datetime.strptime(ngay_str, "%d/%m/%Y")
    du_lieu_truoc = {}
    for n in data:
        if datetime.strptime(n, "%d/%m/%Y") < ngay_muc_tieu:
            du_lieu_truoc[n] = data[n]
    
    if len(du_lieu_truoc) < 10:
        return None, f"⚠️ Chưa đủ dữ liệu trước ngày {ngay_str} (cần ít nhất 10 ngày)"
    
    # Tính dự đoán
    top3, xien, it_dau, it_cuoi, tong = tinh_du_doan_tu_du_lieu(du_lieu_truoc)
    if not top3:
        return None, "⚠️ Không tính được dự đoán"
    
    # Kết quả thực tế ngày đó
    kq_thuc_te = data[ngay_str]
    db_thuc = kq_thuc_te["special"]
    cuoi_thuc = db_thuc[-2:]
    dau_thuc = db_thuc[0]
    lo_thuc = kq_thuc_te["loto"]

    # Đối chiếu
    kiem_tra_top3 = []
    for con in top3:
        trung = "✅ TRÚNG" if con["so"] in lo_thuc else "❌ KHÔNG"
        kiem_tra_top3.append(f"  {con['so']} — {trung}")
    
    trung_xien = "✅ TRÚNG" if xien[0] in lo_thuc and xien[1] in lo_thuc else "❌ KHÔNG"
    trung_dau = "✅ TRÚNG" if it_dau[0] == dau_thuc else "❌ KHÔNG"
    trung_cuoi = "✅ TRÚNG" if it_cuoi[0] == cuoi_thuc else "❌ KHÔNG"

    ket_qua = f"""
🧪 KIỂM TRA DỰ ĐOÁN NGÀY: {ngay_str}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Dữ liệu phân tích: {tong} ngày trước đó

🔮 DỰ ĐOÁN:
🎯 3 CON LÔ:
{chr(10).join(kiem_tra_top3)}

🔄 XIÊN 2: {xien[0]} - {xien[1]} → {trung_xien}

🔢 Đầu số đề: {it_dau[0]} → {trung_dau}
🔢 2 số cuối đề: {it_cuoi[0]} → {trung_cuoi}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 KẾT QUẢ THỰC TẾ NGÀY {ngay_str}:
🏆 Đặc biệt: {db_thuc}
  → Đầu: {dau_thuc} | Cuối: {cuoi_thuc}
🥇 Giải nhất: {kq_thuc_te['g1']}
"""
    return True, ket_qua

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
    gui(m.chat.id, f"""🤖 BOT XSMB — V46.0
📊 Đã nhập: {tong}/{MIN_DAYS} ngày

✅ LỆNH SỬ DỤNG:
/nhap 21092026 51540 38291 → Lưu kết quả
21092026 → Xem lịch sử ngày này
/test 21092026 → ✅ TEST dự đoán ngày cũ
/dudoan → Dự đoán ngày mai
/status → Xem tổng trạng
/xoa → Xóa dữ liệu cũ
""")

@bot.message_handler(commands=['nhap'])
def nhap(m):
    parts = m.text.strip().split()
    if len(parts) != 4:
        gui(m.chat.id, """⚠️ Đúng định dạng:
/nhap 21092026 51540 38291
→ Ngày + Đặc biệt + Giải nhất""")
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
👉 Gõ /test {ngay_raw} để kiểm tra dự đoán ngày này!""")
    else:
        gui(m.chat.id, "❌ Sai! Kiểm tra: 5 chữ số, không khoảng trắng")

# ✅ LỆNH MỚI: TEST DỰ ĐOÁN NGÀY CŨ
@bot.message_handler(commands=['test'])
def test_ngay(m):
    parts = m.text.strip().split()
    if len(parts) != 2:
        gui(m.chat.id, """⚠️ Đúng định dạng:
/test 21092026
→ Kiểm tra dự đoán ngày 21/09/2026
So sánh dự đoán vs kết quả thực tế!""")
        return
    try:
        _, ngay_raw = parts
        d, mo, y = ngay_raw[:2], ngay_raw[2:4], ngay_raw[4:]
        ngay_str = f"{d}/{mo}/{y}"
    except:
        gui(m.chat.id, "⚠️ Ngày phải 8 số: 21092026")
        return

    ok, ket_qua = test_ngay_cu(ngay_str)
    gui(m.chat.id, ket_qua)

@bot.message_handler(commands=['status'])
def status(m):
    tong, tu, den = get_stats()
    gui(m.chat.id, f"""📊 TRẠNG THÁI
Tổng: {tong}/{MIN_DAYS} ngày
Từ {tu} đến {den}
{f'✅ Đủ dữ liệu!' if tong >= MIN_DAYS else '⏳ Chưa đủ, tiếp tục nhập...'}""")

@bot.message_handler(commands=['dudoan'])
def dudoan(m):
    data = load_data()
    tong, tu, den = get_stats()
    ngay_mai = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    
    if tong < MIN_DAYS:
        gui(m.chat.id, f"""⚠️ Cần đủ {MIN_DAYS} ngày
👉 Đã nhập: {tong} ngày
👉 Tiếp tục nhập thêm {MIN_DAYS - tong} ngày nữa!""")
        return

    top3, xien, it_dau, it_cuoi, _ = tinh_du_doan_tu_du_lieu(data)
    gui(m.chat.id, f"""
🎲 DỰ ĐOÁN — NGÀY {ngay_mai}
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
""")

@bot.message_handler(commands=['xoa'])
def xoa(m):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        gui(m.chat.id, "✅ Đã xóa! Bắt đầu nhập lại số thật")
    else:
        gui(m.chat.id, "Chưa có dữ liệu")

# Gõ 8 số → xem lịch sử
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
🕒 Cập nhật: {kq['updated']}
👉 Gõ /test {ngay_raw} để kiểm tra dự đoán ngày này!""")
    else:
        gui(m.chat.id, f"""⚠️ Chưa có dữ liệu {ngay_str}
👉 Nhập: /nhap {ngay_raw} ĐB G1""")

# ====================== 🚀 CHẠY BOT ======================
def run_bot():
    global POLLING_STARTED
    if POLLING_STARTED: return
    POLLING_STARTED = True
    print("✅ V46.0 — Có lệnh /test kiểm tra dự đoán ngày cũ")
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
