# ==========================================================
# xsmb_bot2.py — V47.0 | � TỰ LẤY 90 NGÀY KHÔNG NHẬP TAY
# Token: 8944857392:AAGPf2Nr90wRiO3Q1v_o2M3fexyhJjFZnh8
# Chat ID: -1001030583610
# ==========================================================

import telebot, json, os, re, time, requests, threading
from datetime import datetime, timedelta
from flask import Flask
from collections import Counter

# ====================== 🔧 CẤU HÌNH ======================
TELEGRAM_TOKEN = "8944857392:AAGPf2Nr90wRiO3Q1v_o2M3fexyhJjFZnh8"
CHAT_ID = "-1001030583610"
DATA_FILE = "xsmb_data.json"
PORT = int(os.environ.get("PORT", 10000))
ANALYSIS_DAYS = 90
MIN_DAYS = 30

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

BOT_LOCK = threading.Lock()
POLLING_STARTED = False
IS_FETCHING = False

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

def luu_ket_qua(ngay_str, db, g1, loto, nguon):
    data = load_data()
    data[ngay_str] = {
        "special": db.strip(),
        "g1": g1.strip(),
        "loto": sorted(list(set(loto))),
        "source": nguon,
        "updated": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    return save_all_data(data)

def get_stats():
    data = load_data()
    if not data: return 0,"--","--"
    dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    return len(data), dates[0], dates[-1]

# ====================== 📡 TỰ ĐỘNG LẤY TỪ NGUỒN ======================
def lay_ngay_tu_nguon(ngay_str):
    """Lấy kết quả 1 ngày từ nguồn xoso.com.vn"""
    try:
        d, m, y = ngay_str.split("/")
        ymd = f"{y}{m}{d}"
    except: return None

    data = load_data()
    if ngay_str in data: return data[ngay_str]

    # Nguồn: xoso.com.vn
    try:
        url = f"https://xoso.com.vn/xsmb/{ymd}.html"
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200 or len(r.text) < 500:
            return None
        
        t = r.text
        # Tìm Giải Đặc biệt
        db_match = re.search(r'Đặc biệt.*?<b[^>]*>(\d{5})</b>', t, re.IGNORECASE|re.DOTALL)
        if not db_match:
            db_match = re.search(r'<td[^>]*>Đặc biệt</td>.*?<b[^>]*>(\d{5})</b>', t, re.DOTALL)
        if not db_match:
            db_match = re.search(r'>(\d{5})<', t)
            if db_match and len(db_match.group(1))==5:
                pass
            else:
                return None
        db = db_match.group(1).strip()

        # Tìm Giải nhất
        g1_match = re.search(r'Giải nhất.*?(\d{5})', t, re.IGNORECASE|re.DOTALL)
        if not g1_match:
            return None
        g1 = g1_match.group(1).strip()

        # Lấy tất cả số 5 chữ số → trích lô 2 số cuối
        tat_ca_so = re.findall(r'\b(\d{5})\b', t)
        if len(tat_ca_so) < 5:
            return None
        loto = sorted(list(set([n[-2:] for n in tat_ca_so if len(n)==5])))

        if len(db)==5 and len(g1)==5 and len(loto)>=10:
            luu_ket_qua(ngay_str, db, g1, loto, f"xoso.com.vn/{ymd}")
            print(f"✅ LẤY: {ngay_str} | ĐB:{db} G1:{g1} | Lô:{len(loto)}")
            return {"special":db, "g1":g1, "loto":loto, "source":"xoso.com.vn"}
    except Exception as e:
        print(f"⚠️ Lỗi {ngay_str}: {str(e)[:40]}")
    return None

def lay_90_ngay():
    """Tự động lấy 90 ngày gần nhất"""
    global IS_FETCHING
    if IS_FETCHING: return "⚠️ Đang lấy dữ liệu, vui lòng chờ..."
    IS_FETCHING = True

    data = load_data()
    da_lay = len(data)
    gap = ANALYSIS_DAYS - da_lay
    if gap <= 0:
        IS_FETCHING = False
        return f"✅ Đã có đủ {ANALYSIS_DAYS} ngày rồi!"

    thanh_cong = 0
    that_bai = 0
    ngay_hien = datetime.now()

    for i in range(gap):
        ngay_lay = ngay_hien - timedelta(days=i)
        ngay_str = ngay_lay.strftime("%d/%m/%Y")
        if ngay_str in data: continue
        if lay_ngay_tu_nguon(ngay_str):
            thanh_cong += 1
        else:
            that_bai += 1
        time.sleep(0.8)  # Không gọi quá nhanh

    IS_FETCHING = False
    tong, tu, den = get_stats()
    return f"""✅ HOÀN THÀNH LẤY DỮ LIỆU!
📊 Mới lấy: {thanh_cong} ngày thành công | {that_bai} ngày lỗi
📈 Tổng hiện có: {tong} ngày
📋 Từ {tu} đến {den}
{f'✅ Đủ {MIN_DAYS} ngày → Gõ /dudoan ngay!' if tong >= MIN_DAYS else f'⏳ Cần thêm {MIN_DAYS - tong} ngày nữa'}"""

# ====================== 📊 TÍNH DỰ ĐOÁN ======================
def tinh_tu_du_lieu(du_lieu):
    dem_lo = {}
    dau_de = []
    cuoi_de = []
    ten_ngay = sorted(du_lieu.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    
    for ngay in ten_ngay:
        kq = du_lieu[ngay]
        db = kq["special"]
        dau_de.append(db[0])
        cuoi_de.append(db[-2:])
        for lo in kq["loto"]:
            if lo not in dem_lo: dem_lo[lo] = []
            dem_lo[lo].append(ngay)

    tong = len(ten_ngay)
    if tong < 5: return None, None, None, None, 0

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
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3)>=2 else ["--", "--"]

    cnt_dau = Counter(dau_de)
    it_dau = sorted(cnt_dau.items(), key=lambda x: x[1])[0]
    cnt_cuoi = Counter(cuoi_de)
    it_cuoi = sorted(cnt_cuoi.items(), key=lambda x: x[1])[0]

    return top3, xien, it_dau, it_cuoi, tong

# ====================== 🧪 TEST NGÀY CŨ ======================
def test_ngay_cu(ngay_str):
    data = load_data()
    if ngay_str not in data:
        return f"⚠️ Chưa có dữ liệu {ngay_str}"
    
    ngay_muc_tieu = datetime.strptime(ngay_str, "%d/%m/%Y")
    du_lieu_truoc = {n:data[n] for n in data if datetime.strptime(n, "%d/%m/%Y") < ngay_muc_tieu}
    
    if len(du_lieu_truoc) < 10:
        return f"⚠️ Chưa đủ dữ liệu trước {ngay_str} (cần ≥10 ngày)"
    
    top3, xien, it_dau, it_cuoi, tong = tinh_tu_du_lieu(du_lieu_truoc)
    if not top3: return "⚠️ Không tính được"

    db_thuc = data[ngay_str]["special"]
    cuoi_thuc = db_thuc[-2:]
    dau_thuc = db_thuc[0]
    lo_thuc = data[ngay_str]["loto"]

    kiem_tra = []
    for con in top3:
        trung = "✅ TRÚNG" if con["so"] in lo_thuc else "❌ KHÔNG"
        kiem_tra.append(f"  {con['so']} — {con['lan']} lần | {con['ty_le']}% → {trung}")

    return f"""🧪 TEST DỰ ĐOÁN NGÀY: {ngay_str}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Dữ liệu phân tích: {tong} ngày trước đó

🔮 DỰ ĐOÁN:
🎯 3 CON LÔ ÍT XUẤT HIỆN:
{chr(10).join(kiem_tra)}

🔄 XIÊN 2: {xien[0]} - {xien[1]}
  → {'✅ TRÚNG' if xien[0] in lo_thuc and xien[1] in lo_thuc else '❌ KHÔNG'}

🔢 Đầu số đề: {it_dau[0]} → {'✅ TRÚNG' if it_dau[0]==dau_thuc else '❌ KHÔNG'}
🔢 2 số cuối đề: {it_cuoi[0]} → {'✅ TRÚNG' if it_cuoi[0]==cuoi_thuc else '❌ KHÔNG'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 KẾT QUẢ THỰC TẾ:
🏆 Đặc biệt: {db_thuc}
  → Đầu: {dau_thuc} | Cuối: {cuoi_thuc}
🥇 Giải nhất: {data[ngay_str]['g1']}
"""

# ====================== 🤖 LỆNH BOT ======================
def gui(chat_id, text):
    for _ in range(3):
        try:
            with BOT_LOCK: return bot.send_message(chat_id, text, parse_mode="Markdown")
        except: time.sleep(1)

@bot.message_handler(commands=['start'])
def start(m):
    tong, tu, den = get_stats()
    gui(m.chat.id, f"""🤖 BOT XSMB — V47.0
📊 Đã có: {tong}/{ANALYSIS_DAYS} ngày

✅ LỆNH SỬ DỤNG:
/lay90 → 🤖 TỰ ĐỘNG lấy 90 ngày từ nguồn ✅
/dudoan → Dự đoán ngày mai
/test 21092026 → Kiểm tra dự đoán ngày cũ
21092026 → Xem kết quả ngày này
/status → Xem trạng dữ liệu
/xoa → Xóa dữ liệu lấy lại
""")

@bot.message_handler(commands=['lay90'])
def lay90_cmd(m):
    gui(m.chat.id, "🚀 ĐANG LẤY DỮ LIỆU TỪ NGUỒN...\nVui lòng chờ khoảng 1-2 phút ⏳")
    def chay_lay():
        ket_qua = lay_90_ngay()
        gui(m.chat.id, ket_qua)
    threading.Thread(target=chay_lay, daemon=True).start()

@bot.message_handler(commands=['status'])
def status(m):
    tong, tu, den = get_stats()
    gui(m.chat.id, f"""📊 TRẠNG THÁI DỮ LIỆU
Tổng: {tong}/{ANALYSIS_DAYS} ngày
Phạm vi: {tu} → {den}
Nguồn: Tự động lấy từ xoso.com.vn ✅
{f'✅ Đủ dữ liệu!' if tong >= MIN_DAYS else f'⏳ Cần thêm {MIN_DAYS - tong} ngày → gõ /lay90'}""")

@bot.message_handler(commands=['dudoan'])
def dudoan(m):
    data = load_data()
    tong, tu, den = get_stats()
    ngay_mai = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")

    if tong < MIN_DAYS:
        gui(m.chat.id, f"""⚠️ Chưa đủ {MIN_DAYS} ngày
👉 Đã có: {tong} ngày
👉 Gõ /lay90 để tự động lấy thêm!""")
        return

    top3, xien, it_dau, it_cuoi, _ = tinh_tu_du_lieu(data)
    if not top3:
        gui(m.chat.id, "⚠️ Dữ liệu chưa đủ tính toán")
        return

    gui(m.chat.id, f"""🎲 DỰ ĐOÁN — NGÀY {ngay_mai}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Phân tích: {tong} ngày thật từ nguồn

🎯 3 CON LÔ ÍT XUẤT HIỆN NHẤT:
  1. {top3[0]['so']} — {top3[0]['lan']} lần | {top3[0]['ty_le']}% | nghỉ {top3[0]['nghi']} ngày
  2. {top3[1]['so']} — {top3[1]['lan']} lần | {top3[1]['ty_le']}% | nghỉ {top3[1]['nghi']} ngày
  3. {top3[2]['so']} — {top3[2]['lan']} lần | {top3[2]['ty_le']}% | nghỉ {top3[2]['nghi']} ngày

🔄 XIÊN 2: {xien[0]} - {xien[1]}

🔢 Đầu số đề: {it_dau[0]} — {round(it_dau[1]/tong*100,1)}%
🔢 2 số cuối đề: {it_cuoi[0]} — {round(it_cuoi[1]/tong*100,1)}%

⚠️ Dựa trên dữ liệu thực tế — Tham khảo!
""")

@bot.message_handler(commands=['test'])
def test_cmd(m):
    parts = m.text.strip().split()
    if len(parts) != 2:
        gui(m.chat.id, "⚠️ Đúng: /test 21092026")
        return
    try:
        _, ngay_raw = parts
        d, mo, y = ngay_raw[:2], ngay_raw[2:4], ngay_raw[4:]
        ngay_str = f"{d}/{mo}/{y}"
    except:
        gui(m.chat.id, "⚠️ Ngày 8 số: 21092026")
        return
    gui(m.chat.id, test_ngay_cu(ngay_str))

@bot.message_handler(commands=['xoa'])
def xoa(m):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        gui(m.chat.id, "✅ ĐÃ XÓA! Gõ /lay90 để lấy lại tự động từ nguồn")
    else:
        gui(m.chat.id, "Chưa có dữ liệu")

# Gõ 8 số → xem kết quả ngày
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
👉 Gõ /test {ngay_raw} để kiểm tra dự đoán ngày này!""")
    else:
        gui(m.chat.id, f"""⚠️ Chưa có {ngay_str}
👉 Gõ /lay90 để tự động lấy tất cả dữ liệu!""")

# ====================== 🚀 CHẠY BOT ======================
def run_bot():
    global POLLING_STARTED
    if POLLING_STARTED: return
    POLLING_STARTED = True
    print("✅ V47.0 — TỰ LẤY 90 NGÀY TỪ NGUỒN, KHÔNG NHẬP TAY!")
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
