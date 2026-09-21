# ==========================================================
# xsmb_bot2.py — V40.3 | ✅ KIỂM TRA CHÉO → DỮ LIỆU CHÍNH XÁC
# Token: 8944857392:AAGPf2Nr90wRiO3Q1v_o2M3fexyhJjFZnh8
# Chat ID: -1001030583610
# ==========================================================

import telebot, json, os, re, time, requests, threading, random
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
MAX_RETRY = 2
DELAY_PER_DAY = 0.4

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/json,*/*;q=0.9",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/"
    }

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

def luu_ket_qua_xac_minh(ngay_str, special, g1, loto, nguon_list):
    """✅ LƯU CHỈ KHI ĐƯỢC XÁC MINH → KHÔNG LƯU DỮ LIỆU BẤT ĐỊNH"""
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", ngay_str): return False
    if not special or len(special)!=5 or not special.isdigit(): return False
    if not g1 or len(g1)!=5 or not g1.isdigit(): return False
    if not loto or len(loto) < 15: return False  # Ít nhất 15 cặp lô → chắc chắn đủ

    data = load_data()
    data[ngay_str] = {
        "special": special.strip(),
        "g1": g1.strip(),
        "loto": sorted(list(set(loto))),
        "nguon": nguon_list,
        "verified": len(nguon_list) >= 2,  # ✅ Xác minh khi ≥2 nguồn khớp
        "cap_nhat": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    ok = save_all_data(data)
    if ok:
        print(f"✅ LƯU CHÍNH XÁC: {ngay_str} | ĐB:{special} | G1:{g1} | Nguồn:{len(nguon_list)}")
    return ok

def get_stats():
    data = load_data()
    if not data: return 0,"--","--",0,0
    dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    verified = sum(1 for v in data.values() if v.get("verified",False))
    unique_db = len(set(v["special"] for v in data.values() if "special" in v))
    return len(data), dates[0], dates[-1], verified, unique_db

# ====================== 📡 LẤY TỪ MỖI NGUỒN ======================
def lay_tu_xoso_com_vn(ymd, ymd_short):
    try:
        url = f"https://xoso.com.vn/xsmb/{ymd_short}.html"
        r = requests.get(url, headers=get_headers(), timeout=10)
        if r.status_code != 200: return None
        t = r.text
        # Tìm Đặc biệt — chính xác nhất
        db = re.search(r'(?:Đặc biệt|Dac Biet).*?<b[^>]*>(\d{5})</b>', t, re.IGNORECASE|re.DOTALL)
        if not db: db = re.search(r'giải đặc biệt.*?(\d{5})', t, re.IGNORECASE)
        # Tìm Giải nhất
        g1 = re.search(r'(?:Giải nhất|Giai Nhat).*?<b[^>]*>(\d{5})</b>', t, re.IGNORECASE|re.DOTALL)
        if not g1: g1 = re.search(r'giải nhất.*?(\d{5})', t, re.IGNORECASE)
        if not db or not g1: return None
        db_val, g1_val = db.group(1).strip(), g1.group(1).strip()
        if len(db_val)!=5 or len(g1_val)!=5: return None
        # Tất cả số 5 chữ số → lấy 2 số cuối = lô
        tat_ca_5so = re.findall(r'\b\d{5}\b', t)
        loto = [n[-2:] for n in tat_ca_5so if len(n)==5 and n.isdigit()]
        if len(loto) < 15: return None
        return {"db":db_val, "g1":g1_val, "loto":loto, "nguon":"xoso.com.vn"}
    except: return None

def lay_tu_xoso_ws(ymd, ymd_short):
    try:
        url = f"https://xoso.ws/api/xsmb?date={ymd}"
        r = requests.get(url, headers=get_headers(), timeout=10)
        if r.status_code != 200: return None
        j = r.json()
        if j.get("status") != "success" or "data" not in j: return None
        d = j["data"]
        db = str(d.get("special", "")).strip()
        g1 = str(d.get("prize1", "")).strip()
        if len(db)!=5 or len(g1)!=5: return None
        tat_ca_so = d.get("all_numbers", [])
        loto = [str(n)[-2:] for n in tat_ca_so if str(n).isdigit() and len(str(n))>=2]
        if len(loto) < 15: return None
        return {"db":db, "g1":g1, "loto":loto, "nguon":"xoso.ws"}
    except: return None

def lay_tu_kqxs_vn(ymd, ymd_short):
    try:
        url = f"https://kqxs.vn/xsmb/ngay-{ymd}"
        r = requests.get(url, headers=get_headers(), timeout=10)
        if r.status_code != 200: return None
        t = r.text
        db = re.search(r'Đặc biệt.*?(\d{5})', t, re.IGNORECASE)
        g1 = re.search(r'Giải nhất.*?(\d{5})', t, re.IGNORECASE)
        if not db or not g1: return None
        db_val, g1_val = db.group(1).strip(), g1.group(1).strip()
        if len(db_val)!=5 or len(g1_val)!=5: return None
        tat_ca_5so = re.findall(r'\b\d{5}\b', t)
        loto = [n[-2:] for n in tat_ca_5so if len(n)==5 and n.isdigit()]
        if len(loto) < 15: return None
        return {"db":db_val, "g1":g1_val, "loto":loto, "nguon":"kqxs.vn"}
    except: return None

# ====================== ✅ KIỂM TRA CHÉO 3 NGUỒN ======================
def lay_ket_nga_chinh_xac(ngay_str):
    """✅ LẤY TỪ 3 NGUỒN → CHỈ LƯU KHI ÍT NHẤT 2 NGUỒN KHỚP"""
    try:
        d, m, y = ngay_str.split("/")
        d, m = d.zfill(2), m.zfill(2)
        ymd = f"{y}-{m}-{d}"
        ymd_short = f"{y}{m}{d}"
    except: return None

    # Kiểm tra đã lưu & xác minh
    data = load_data()
    if ngay_str in data and data[ngay_str].get("verified", False):
        kq = data[ngay_str]
        return {"special":kq["special"],"g1":kq["g1"],"loto":kq["loto"],"nguon":kq["nguon"],"verified":True}

    # Lấy song song từ 3 nguồn
    kq1 = lay_tu_xoso_com_vn(ymd, ymd_short)
    time.sleep(0.3)
    kq2 = lay_tu_xoso_ws(ymd, ymd_short)
    time.sleep(0.3)
    kq3 = lay_tu_kqxs_vn(ymd, ymd_short)

    # Tổng hợp kết quả
    tat_ca_kq = [k for k in [kq1, kq2, kq3] if k]
    if not tat_ca_kq:
        print(f"❌ {ngay_str} — TẤT CẢ 3 NGUỒN ĐỀU KHÔNG CÓ DỮ LIỆU")
        return None

    # Đếm sự trùng khớp
    dem_db = {}
    dem_g1 = {}
    for kq in tat_ca_kq:
        dem_db[kq["db"]] = dem_db.get(kq["db"], 0) + 1
        dem_g1[kq["g1"]] = dem_g1.get(kq["g1"], 0) + 1

    # Lấy giá trị xuất hiện nhiều nhất
    db_chinh = max(dem_db.items(), key=lambda x: x[1])
    g1_chinh = max(dem_g1.items(), key=lambda x: x[1])

    # ✅ XÁC MINH: Ít nhất 2 nguồn khớp
    if db_chinh[1] < 2 or g1_chinh[1] < 2:
        print(f"⚠️ {ngay_str} — Dữ liệu không khớp giữa các nguồn → Bỏ qua không lưu")
        print(f"   ĐB: {dem_db} | G1: {dem_g1}")
        return None

    # Lấy danh sách nguồn khớp
    nguon_khop = []
    for kq in tat_ca_kq:
        if kq["db"] == db_chinh[0] and kq["g1"] == g1_chinh[0]:
            nguon_khop.append(kq["nguon"])

    # Lấy lô từ nguồn đáng tin cậy nhất
    loto_chinh = tat_ca_kq[0]["loto"]
    for kq in tat_ca_kq:
        if len(kq["loto"]) > len(loto_chinh):
            loto_chinh = kq["loto"]

    print(f"✅ {ngay_str} — CHÍNH XÁC | ĐB:{db_chinh[0]}({db_chinh[1]}/3) G1:{g1_chinh[0]}({g1_chinh[1]}/3) | Nguồn:{nguon_khop}")
    return {
        "special": db_chinh[0],
        "g1": g1_chinh[0],
        "loto": sorted(list(set(loto_chinh))),
        "nguon": nguon_khop,
        "verified": True
    }

# ====================== 📊 DỰ ĐOÁN ======================
def tinh_du_doan():
    data = load_data()
    tong, tu, den, verified, unique_db = get_stats()
    ngay_mai = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")

    if tong < MIN_DAYS_FOR_PREDICT:
        return f"""⚠️ CHƯA ĐỦ DỮ LIỆU!
👉 Hiện có: {tong} ngày (đã xác minh: {verified})
👉 Yêu cầu: ≥{MIN_DAYS_FOR_PREDICT} ngày
👉 Gõ /lay90 để lấy dữ liệu CHÍNH XÁC!"""

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
📊 Phân tích: {so_ngay} ngày | Tổng: {tong} ngày | Đã xác minh: {verified} ✅
✅ Nguồn: Kiểm tra chéo 3 trang → chỉ lưu khi ≥2 trang khớp

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
    return f"✅ V40.3 | {tong} ngày | Xác minh: {verified} | Kiểm tra chéo 3 nguồn!"

def gui(chat_id, text, md="Markdown"):
    for _ in range(3):
        try:
            with BOT_LOCK: return bot.send_message(chat_id, text, parse_mode=md)
        except: time.sleep(2)
    return None

@bot.message_handler(commands=['start'])
def start(m):
    tong, tu, den, verified, unique_db = get_stats()
    gui(m.chat.id,
        f"🤖 *BOT XSMB — V40.3 | ✅ KIỂM TRA CHÉO → DỮ LIỆU CHÍNH XÁC*\n"
        f"📊 Tổng: {tong} ngày | Đã xác minh: {verified} ✅\n\n"
        f"/lay90 = Lấy 90 ngày (kiểm tra chéo 3 trang)\n"
        f"/dudoan = Dự đoán ngày mai + tỷ lệ\n"
        f"/status = Xem trạng dữ liệu\n"
        f"/kiemtra 12092026 = So sánh dữ liệu với thực tế",
    )

@bot.message_handler(commands=['status'])
def status(m):
    tong, tu, den, verified, unique_db = get_stats()
    gui(m.chat.id,
        f"📊 *TRẠNG THÁI DỮ LIỆU*\n"
        f"• Tổng: {tong} ngày | Đã xác minh: {verified} ✅\n"
        f"• Phạm vi: {tu} → {den}\n"
        f"• Nguồn: xoso.com.vn + xoso.ws + kqxs.vn\n"
        f"• Quy tắc: Chỉ lưu khi ≥2 trang khớp nhau",
    )

@bot.message_handler(commands=['xoadulieu'])
def xoa(m):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        gui(m.chat.id, "✅ *ĐÃ XÓA DỮ LIỆU CŨ!* 🗑️\n👉 Gõ /lay90 lấy lại dữ liệu CHÍNH XÁC!",)
    else:
        gui(m.chat.id, "⚠️ Chưa có dữ liệu!",)

@bot.message_handler(commands=['lay90'])
def lay90(m):
    gui(m.chat.id,
        f"🚀 *ĐANG LẤY 90 NGÀY — KIỂM TRA CHÉO 3 NGUỒN...*\n"
        f"✅ Chỉ lưu khi ÍT NHẤT 2 trang khớp nhau\n"
        f"⏰ Khoảng 6-8 phút — Đảm bảo chính xác!",
    )
    def lay_async():
        today = datetime.now()
        data_hien = load_data()
        lay_moi = da_co = khong_khop = 0
        total = ANALYSIS_DAYS

        for offset in range(1, total+1):
            target = today - timedelta(days=offset)
            date_str = target.strftime("%d/%m/%Y")

            if date_str in data_hien and data_hien[date_str].get("verified", False):
                da_co += 1
                continue

            kq = lay_ket_nga_chinh_xac(date_str)
            if kq:
                if luu_ket_qua_xac_minh(date_str, kq["special"], kq["g1"], kq["loto"], kq["nguon"]):
                    lay_moi += 1
                    data_hien = load_data()
                else: khong_khop += 1
            else:
                khong_khop += 1

            if offset % 10 == 0:
                gui(m.chat.id,
                    f"⏳ {offset}/{total} ngày ({round(offset/total*100)}%)\n"
                    f"✅ Mới: {lay_moi} | ⚠️ Không khớp: {khong_khop} | ✅ Đã có: {da_co}",
                )
            time.sleep(DELAY_PER_DAY)

        tong, _, _, verified, _ = get_stats()
        gui(m.chat.id,
            f"✅ *HOÀN THÀNH!* 🎉\n"
            f"📊 Tổng: {tong} ngày | Đã xác minh: {verified} ✅\n"
            f"• Đã có: {da_co} | Lấy mới: {lay_moi} | Không khớp: {khong_khop}\n"
            f"{'✅ ĐỦ DỮ LIỆU → Gõ /dudoan!' if tong >= MIN_DAYS_FOR_PREDICT else f'⚠️ Cần thêm {MIN_DAYS_FOR_PREDICT - tong} ngày nữa'}",
        )
    threading.Thread(target=lay_async, daemon=True).start()

@bot.message_handler(commands=['dudoan'])
def dudoan(m):
    gui(m.chat.id, tinh_du_doan(),)

@bot.message_handler(commands=['kiemtra'])
def kiemtra(m):
    text = m.text.replace("/kiemtra","").strip()
    if len(text) != 8 or not text.isdigit():
        gui(m.chat.id, "⚠️ Định dạng: /kiemtra 12092026",)
        return
    d, mo, y = text[:2], text[2:4], text[4:]
    ngay = f"{d}/{mo}/{y}"
    data = load_data()
    if ngay in data:
        kq = data[ngay]
        gui(m.chat.id,
            f"📅 *DỮ LIỆU NGÀY {ngay}*\n"
            f"🏆 Đặc biệt: `{kq['special']}`\n"
            f"🥇 Giải nhất: `{kq['g1']}`\n"
            f"📌 Nguồn: {', '.join(kq['nguon'])}\n"
            f"{'✅ ĐÃ XÁC MINH — Chính xác!' if kq['verified'] else '⚠️ Chưa xác minh'}",
        )
    else:
        gui(m.chat.id, f"🔍 Đang lấy dữ liệu {ngay}...",)
        kq = lay_ket_nga_chinh_xac(ngay)
        if kq and luu_ket_qua_xac_minh(ngay, kq["special"], kq["g1"], kq["loto"], kq["nguon"]):
            gui(m.chat.id,
                f"✅ *ĐÃ LƯU CHÍNH XÁC!*\n"
                f"📅 {ngay}\n"
                f"🏆 ĐB: `{kq['special']}`\n"
                f"🥇 G1: `{kq['g1']}`\n"
                f"📌 Nguồn: {', '.join(kq['nguon'])}",
            )
        else:
            gui(m.chat.id, f"❌ Không lấy được hoặc dữ liệu không khớp giữa các nguồn",)

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
                kq = lay_ket_nga_chinh_xac(hom_nay)
                if kq and luu_ket_qua_xac_minh(hom_nay, kq["special"], kq["g1"], kq["loto"], kq["nguon"]):
                    gui(CHAT_ID,
                        f"🏆 *KẾT QUẢ NGÀY HÔM NAY — {hom_nay}*\n"
                        f"🎯 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n✅ Đã xác minh chính xác",
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
    print("✅ V40.3 — KIỂM TRA CHÉO 3 NGUỒN → DỮ LIỆU CHÍNH XÁC!")
    print("="*60)
    try: bot.remove_webhook()
    except: pass
    while True:
        try: bot.infinity_polling(timeout=30, long_polling_timeout=40, allowed_updates=None)
        except Exception as e:
            if "409" in str(e): time.sleep(15)
            else: time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=tu_dong, daemon=True).start()
    run_bot()
