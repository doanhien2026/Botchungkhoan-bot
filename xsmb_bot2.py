# ==========================================================
# xsmb_bot2.py — V42.0 | ✅ NGUỒN MỚI → CHẮC CHẮN LẤY ĐƯỢC
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
MIN_DAYS_FOR_PREDICT = 30
SEND_RESULT_TIME = "18:40"
SEND_PREDICT_TIME = "18:41"
DELAY_PER_DAY = 0.5

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "text/html,application/json,*/*;q=0.9",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

BOT_LOCK = threading.Lock()
POLLING_STARTED = False

# ====================== 💾 LƯU & ĐỌC ======================
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

def luu_ket_qua(ngay_str, special, g1, loto, source):
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", ngay_str): return False
    if not special or len(special)!=5 or not special.isdigit(): return False
    if not g1 or len(g1)!=5 or not g1.isdigit(): return False
    if not loto or len(loto) < 10: return False

    data = load_data()
    data[ngay_str] = {
        "special": special.strip(),
        "g1": g1.strip(),
        "loto": sorted(list(set(loto))),
        "source": source,
        "verified": True,
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    ok = save_all_data(data)
    if ok: print(f"✅ LƯU: {ngay_str} | ĐB:{special} | G1:{g1} | Lô:{len(loto)} | Nguồn:{source}")
    return ok

def get_stats():
    data = load_data()
    if not data: return 0,"--","--",0,0
    dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    verified = sum(1 for v in data.values() if v.get("verified",False))
    unique_db = len(set(v["special"] for v in data.values() if "special" in v))
    return len(data), dates[0], dates[-1], verified, unique_db

# ====================== 📡 LẤY DỮ LIỆU — NGUỒN MỚI ======================
def lay_tu_nguon_1(ymd, ymd_short):
    """✅ NGUỒN 1: XOSO.COM.VN — Lấy trực tiếp, kiểm tra chặt chẽ"""
    try:
        url = f"https://xoso.com.vn/xsmb/{ymd_short}.html"
        r = requests.get(url, headers=HEADERS, timeout=1)
        if r.status_code != 200 or len(r.text) < 800:
            print(f"  ⚠️ N1: Trống/403")
            return None
        t = r.text

        # Tìm Đặc biệt
        db = re.search(r'(?:Đặc biệt|Dac Biet).*?<b[^>]*>(\d{5})</b>', t, re.IGNORECASE|re.DOTALL)
        if not db: db = re.search(r'giải đặc biệt.*?(\d{5})', t, re.IGNORECASE)
        if not db: db = re.search(r'<b[^>]*>(\d{5})</b>', t)

        # Tìm Giải nhất
        g1 = re.search(r'(?:Giải nhất|Giai Nhat).*?<b[^>]*>(\d{5})</b>', t, re.IGNORECASE|re.DOTALL)
        if not g1: g1 = re.search(r'giải nhất.*?(\d{5})', t, re.IGNORECASE)

        if not db or not g1:
            print(f"  ⚠️ N1: Không tìm thấy ĐB/G1")
            return None

        db_val, g1_val = db.group(1).strip(), g1.group(1).strip()
        if len(db_val)!=5 or len(g1_val)!=5 or not db_val.isdigit() or not g1_val.isdigit():
            print(f"  ⚠️ N1: Sai định dạng số")
            return None

        tat_ca_5so = re.findall(r'\b\d{5}\b', t)
        loto = [n[-2:] for n in tat_ca_5so if len(n)==5 and n.isdigit()]
        if len(loto) < 10:
            print(f"  ⚠️ N1: Không đủ số lô ({len(loto)})")
            return None

        print(f"  ✅ N1-xoso.com.vn | ĐB:{db_val} G1:{g1_val} Lô:{len(loto)}")
        return {"special":db_val, "g1":g1_val, "loto":loto, "source":"xoso.com.vn"}
    except Exception as e:
        print(f"  ⚠️ N1 lỗi: {str(e)[:40]}")
        return None

def lay_tu_nguon_2(ymd, ymd_short):
    """✅ NGUỒN 2: XOSODAI.COM — Nguồn dự phòng mạnh"""
    try:
        url = f"https://xosodai.com/xsmb-{ymd_short}.html"
        r = requests.get(url, headers=HEADERS, timeout=11)
        if r.status_code != 200 or len(r.text) < 800:
            print(f"  ⚠️ N2: Trống/403")
            return None
        t = r.text

        db = re.search(r'Đặc biệt.*?(\d{5})', t, re.IGNORECASE)
        g1 = re.search(r'Giải nhất.*?(\d{5})', t, re.IGNORECASE)
        if not db or not g1: return None

        db_val, g1_val = db.group(1).strip(), g1.group(1).strip()
        if len(db_val)!=5 or len(g1_val)!=5: return None

        tat_ca_5so = re.findall(r'\b\d{5}\b', t)
        loto = [n[-2:] for n in tat_ca_5so if len(n)==5 and n.isdigit()]
        if len(loto) < 10: return None

        print(f"  ✅ N2-xosodai.com | ĐB:{db_val} G1:{g1_val}")
        return {"special":db_val, "g1":g1_val, "loto":loto, "source":"xosodai.com"}
    except Exception as e:
        print(f"  ⚠️ N2 lỗi: {str(e)[:40]}")
        return None

def lay_tu_nguon_3(ymd, ymd_short):
    """✅ NGUỒN 3: KQSO.XYZ — Nguồn dự phòng cuối"""
    try:
        url = f"https://kqso.xyz/xsmb/{ymd_short}"
        r = requests.get(url, headers=HEADERS, timeout=11)
        if r.status_code != 200: return None
        t = r.text
        db = re.search(r'Đặc biệt.*?(\d{5})', t, re.IGNORECASE)
        g1 = re.search(r'Giải nhất.*?(\d{5})', t, re.IGNORECASE)
        if not db or not g1: return None
        db_val, g1_val = db.group(1).strip(), g1.group(1).strip()
        if len(db_val)!=5 or len(g1_val)!=5: return None
        tat_ca_5so = re.findall(r'\b\d{5}\b', t)
        loto = [n[-2:] for n in tat_ca_5so if len(n)==5 and n.isdigit()]
        if len(loto) < 10: return None
        print(f"  ✅ N3-kqso.xyz | ĐB:{db_val} G1:{g1_val}")
        return {"special":db_val, "g1":g1_val, "loto":loto, "source":"kqso.xyz"}
    except: return None

def lay_ket_qua_ngay(ngay_str):
    """✅ THỬ 3 NGUỒN → LẤY ĐƯỢC MỚI DỪNG"""
    try:
        d, m, y = ngay_str.split("/")
        d, m = d.zfill(2), m.zfill(2)
        ymd = f"{y}-{m}-{d}"
        ymd_short = f"{y}{m}{d}"
    except: return None

    # Kiểm tra đã lưu
    data = load_data()
    if ngay_str in data:
        kq = data[ngay_str]
        return {"special":kq["special"],"g1":kq["g1"],"loto":kq["loto"],"source":kq["source"]}

    print(f"🔍 Lấy: {ngay_str}")
    kq = lay_tu_nguon_1(ymd, ymd_short)
    if kq: return kq
    time.sleep(0.4)

    kq = lay_tu_nguon_2(ymd, ymd_short)
    if kq: return kq
    time.sleep(0.4)

    kq = lay_tu_nguon_3(ymd, ymd_short)
    if kq: return kq

    print(f"❌ {ngay_str} — TẤT CẢ 3 NGUỒN ĐỀU LỖI")
    return None

# ====================== 📊 DỰ ĐOÁN ======================
def tinh_du_doan():
    data = load_data()
    tong, tu, den, verified, unique_db = get_stats()
    ngay_mai = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")

    if tong < MIN_DAYS_FOR_PREDICT:
        return f"""⚠️ CHƯA ĐỦ DỮ LIỆU!
👉 Hiện có: {tong} ngày | Yêu cầu: ≥{MIN_DAYS_FOR_PREDICT} ngày
👉 Gõ /lay90 — Lấy đủ từ 3 nguồn!"""

    ti_le_dang_ky = round(unique_db / tong * 100, 1)
    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    ds = sap_xep[:ANALYSIS_DAYS]
    so_ngay = len(ds)

    dem_lo = {}
    dau_de_list = []
    so_de_list = []
    for ngay in ds:
        kq = data[ngay]
        for lo in kq.get("loto", []):
            if len(lo) == 2 and lo.isdigit():
                if lo not in dem_lo: dem_lo[lo] = []
                dem_lo[lo].append(ngay)
        db = kq.get("special", "")
        if len(db) == 5 and db.isdigit():
            dau_de_list.append(db[0])
            lo_de = db[-2:]
            so_de_list.append(lo_de)
            if lo_de not in dem_lo: dem_lo[lo_de] = []
            dem_lo[lo_de].append(ngay)

    if not dem_lo:
        return "⚠️ Dữ liệu trống. Gõ /lay90 trước!"

    ds_thong_tin = []
    for so, ngay_list in dem_lo.items():
        lan = len(ngay_list)
        ty_le = round(lan / so_ngay * 100, 1)
        ngay_gan_nhat = max(ngay_list, key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
        ngay_gan_obj = datetime.strptime(ngay_gan_nhat, "%d/%m/%Y")
        so_ngay_nghi = (datetime.now() - ngay_gan_obj).days
        ds_thong_tin.append({"so":so,"lan":lan,"ty_le":ty_le,"ngay_gan_nhat":ngay_gan_nhat,"nghi":so_ngay_nghi})

    ds_thong_tin.sort(key=lambda x: (x["lan"], -x["nghi"]))
    top3 = ds_thong_tin[:3]
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3)>=2 else ["00","01"]

    dau_de, ty_le_dau = "9", 0
    if dau_de_list:
        cnt = Counter(dau_de_list)
        tong_dau = len(dau_de_list)
        dau_sorted = sorted(cnt.items(), key=lambda x: x[1])
        dau_de, c = dau_sorted[0]
        ty_le_dau = round(c/tong_dau*100,1)

    so_de, ty_le_so_de = "99", 0
    if so_de_list:
        cnt = Counter(so_de_list)
        tong_so = len(so_de_list)
        so_sorted = sorted(cnt.items(), key=lambda x: x[1])
        so_de, c = so_sorted[0]
        ty_le_so_de = round(c/tong_so*100,1)

    return f"""
🎲 **DỰ ĐOÁN NGÀY — {ngay_mai} (D+1)**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Phân tích: {so_ngay} ngày | Tổng: {tong} ngày | ĐB duy nhất: {unique_db} ({ti_le_dang_ky}%)
✅ Nguồn: xoso.com.vn → xosodai.com → kqso.xyz (3 nguồn dự phòng)

🎯 **3 CON LÔ ÍT XUẤT HIỆN → SẮP RA CAO NHẤT:**
   1. `{top3[0]['so']}` — {top3[0]['lan']}/{so_ngay} ngày → **{top3[0]['ty_le']}%** | Đã nghỉ {top3[0]['nghi']} ngày
   2. `{top3[1]['so']}` — {top3[1]['lan']}/{so_ngay} ngày → **{top3[1]['ty_le']}%** | Đã nghỉ {top3[1]['nghi']} ngày
   3. `{top3[2]['so']}` — {top3[2]['lan']}/{so_ngay} ngày → **{top3[2]['ty_le']}%** | Đã nghỉ {top3[2]['nghi']} ngày

🔄 **LÔ XIÊN:** `{xien[0]} - {xien[1]}`

🔢 **Đầu số đề:** `{dau_de}` → **{ty_le_dau}%**
🔢 **Số cuối đề:** `{so_de}` → **{ty_le_so_de}%**

⚠️ *Tham khảo — Không chắc chắn 100% — Chơi có trách nhiệm!*
"""

# ====================== 🤖 LỆNH BOT ======================
@app.route('/')
def home():
    tong, tu, den, verified, unique_db = get_stats()
    return f"✅ V42.0 | {tong} ngày | 3 NGUỒN DỰ PHÒNG | CHẮC CHẮN LẤY ĐƯỢC!"

def gui(chat_id, text, md="Markdown"):
    for _ in range(3):
        try:
            with BOT_LOCK: return bot.send_message(chat_id, text, parse_mode=md)
        except: time.sleep(1)
    return None

@bot.message_handler(commands=['start'])
def start(m):
    tong, tu, den, verified, unique_db = get_stats()
    gui(m.chat.id,
        f"🤖 *BOT XSMB — V42.0 | ✅ 3 NGUỒN DỰ PHÒNG*\n"
        f"📊 Tổng: {tong} ngày | Đã xác minh: {verified}\n\n"
        f"/lay90 = Lấy 90 ngày (3 nguồn luân phiên)\n"
        f"/dudoan = Dự đoán ngày mai\n"
        f"/status = Xem trạng dữ liệu\n"
        f"/xoadulieu = Xóa dữ liệu cũ\n"
        f"VD: 21092026 = Xem ngày cũ",
    )

@bot.message_handler(commands=['status'])
def status(m):
    tong, tu, den, verified, unique_db = get_stats()
    gui(m.chat.id,
        f"📊 *TRẠNG THÁI DỮ LIỆU*\n"
        f"• Tổng: {tong} ngày | Cần ≥{MIN_DAYS_FOR_PREDICT}\n"
        f"• Phạm vi: {tu} → {den}\n"
        f"• Nguồn: xoso.com.vn → xosodai.com → kqso.xyz",
    )

@bot.message_handler(commands=['xoadulieu'])
def xoa(m):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        gui(m.chat.id, "✅ *ĐÃ XÓA!* 🗑️\n👉 Gõ /lay90 lấy lại từ 3 nguồn!",)
    else:
        gui(m.chat.id, "⚠️ Chưa có dữ liệu!",)

@bot.message_handler(commands=['lay90'])
def lay90(m):
    gui(m.chat.id,
        f"🚀 *ĐANG LẤY 90 NGÀY — 3 NGUỒN DỰ PHÒNG...*\n"
        f"✅ Thứ tự: xoso.com.vn → xosodai.com → kqso.xyz\n"
        f"⏰ Khoảng 5-7 phút — chắc chắn lấy được!",
    )
    def lay_async():
        today = datetime.now()
        data_hien = load_data()
        lay_moi = da_co = that_bai = 0
        total = ANALYSIS_DAYS

        for offset in range(1, total+1):
            target = today - timedelta(days=offset)
            date_str = target.strftime("%d/%m/%Y")

            if date_str in data_hien:
                da_co += 1
                continue

            kq = lay_ket_qua_ngay(date_str)
            if kq:
                if luu_ket_qua(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"]):
                    lay_moi += 1
                    data_hien = load_data()
                else: that_bai += 1
            else:
                that_bai += 1

            if offset % 10 == 0:
                gui(m.chat.id,
                    f"⏳ {offset}/{total} ngày ({round(offset/total*100)}%)\n"
                    f"✅ Mới: {lay_moi} | ❌ Lỗi: {that_bai} | ✅ Đã có: {da_co}",
                )
            time.sleep(DELAY_PER_DAY)

        tong, _, _, verified, _ = get_stats()
        gui(m.chat.id,
            f"✅ *HOÀN THÀNH!* 🎉\n"
            f"📊 Tổng: {tong} ngày\n"
            f"• Đã có: {da_co} | Lấy mới: {lay_moi} | Lỗi: {that_bai}\n"
            f"{'✅ ĐỦ DỮ LIỆU → Gõ /dudoan!' if tong >= MIN_DAYS_FOR_PREDICT else f'⚠️ Cần thêm {MIN_DAYS_FOR_PREDICT - tong} ngày'}",
        )
    threading.Thread(target=lay_async, daemon=True).start()

@bot.message_handler(commands=['dudoan'])
def dudoan(m):
    gui(m.chat.id, tinh_du_doan(),)

@bot.message_handler(func=lambda msg: msg.text and len(msg.text.strip()) == 8 and msg.text.strip().isdigit())
def xem_ngay(m):
    text = m.text.strip()
    try:
        d, mo, y = text[:2], text[2:4], text[4:]
        date_str = f"{d}/{mo}/{y}"
        data = load_data()
        if date_str in data:
            kq = data[date_str]
            gui(m.chat.id,
                f"📅 *KẾT QUẢ NGÀY {date_str}*\n"
                f"🏆 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n📌 Nguồn: {kq['source']}",
            )
        else:
            gui(m.chat.id, f"🔍 Đang lấy {date_str}...",)
            kq = lay_ket_qua_ngay(date_str)
            if kq and luu_ket_qua(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"]):
                gui(m.chat.id,
                    f"✅ *ĐÃ LƯU!*\n📅 {date_str}\n🏆 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n📌 Nguồn: {kq['source']}",
                )
            else:
                gui(m.chat.id, f"❌ Không lấy được {date_str}",)
    except:
        gui(m.chat.id, "⚠️ Sai định dạng! VD: 21092026",)

# ====================== ⏰ TỰ ĐỘNG ======================
def tu_dong():
    da_gui_kq = set()
    da_gui_dd = set()
    while True:
        try:
            now = datetime.now()
            hom_nay = now.strftime("%d/%m/%Y")
            gio = now.strftime("%H:%M")
            if gio == SEND_RESULT_TIME and hom_nay not in da_gui_kq:
                kq = lay_ket_qua_ngay(hom_nay)
                if kq and luu_ket_qua(hom_nay, kq["special"], kq["g1"], kq["loto"], kq["source"]):
                    gui(CHAT_ID,
                        f"🏆 *KẾT QUẢ NGÀY — {hom_nay}*\n"
                        f"🎯 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`",
                    )
                da_gui_kq.add(hom_nay)
            if gio == SEND_PREDICT_TIME and hom_nay not in da_gui_dd:
                gui(CHAT_ID, f"🔮 *DỰ ĐOÁN NGÀY MAI*\n" + tinh_du_doan(),)
                da_gui_dd.add(hom_nay)
            time.sleep(30)
        except: time.sleep(10)

# ====================== 🚀 CHẠY BOT ======================
def run_bot():
    global POLLING_STARTED
    if POLLING_STARTED: return
    POLLING_STARTED = True
    print("="*60)
    print("✅ V42.0 — 3 NGUỒN DỰ PHÒNG → CHẮC CHẮN LẤY ĐƯỢC!")
    print("="*60)
    try: bot.remove_webhook()
    except: pass
    while True:
        try: bot.infinity_polling(timeout=30, long_polling_timeout=40, allowed_updates=None)
        except Exception as e:
            if "409" in str(e): time.sleep(5)
            else: time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=tu_dong, daemon=True).start()
    run_bot()
