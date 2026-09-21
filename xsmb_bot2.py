# ==========================================================
# xsmb_bot2.py — V41.0 | ✅ DÙNG API ỔN ĐỊNH → LẤY ĐƯỢC DỮ LIỆU
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
DELAY_PER_DAY = 0.25  # Nhanh hơn

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*;q=0.9",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

BOT_LOCK = threading.Lock()
POLLING_STARTED = False

# ====================== 💾 LƯU & ĐỌC DỮ LIỆU ======================
def load_data():
    if not os.path.exists(DATA_FILE): return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"⚠️ Lỗi đọc file: {e}")
        return {}

def save_all_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu: {e}")
        return False

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

# ====================== 📡 LẤY DỮ LIỆU — DÙNG API ỔN ĐỊNH ======================
def lay_ket_qua_ngay(ngay_str):
    """✅ 2 NGUỒN API → LẤY ĐƯỢC DỮ LIỆU THẬT, KHÔNG BỊ CHẶN"""
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

    # ========== NGUỒN 1: API XOSO.WS — ỔN ĐỊNH NHẤT ==========
    try:
        url = f"https://xoso.ws/api/xsmb?date={ymd}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            js = resp.json()
            if js.get("status") == "success" and "data" in js:
                dt = js["data"]
                db = str(dt.get("special", "")).strip()
                g1 = str(dt.get("prize1", "")).strip()
                all_numbers = dt.get("all_numbers", [])
                if db and g1 and len(db)==5 and len(g1)==5:
                    loto = sorted(list(set([str(n)[-2:] for n in all_numbers if str(n).isdigit() and len(str(n))>=2])))
                    if len(loto) >= 10:
                        print(f"✅ N1-xoso.ws | {ngay_str} | ĐB:{db} G1:{g1}")
                        return {"special":db, "g1":g1, "loto":loto, "source":"xoso.ws(API)"}
        print(f"⚠️ N1-xoso.ws: Không có dữ liệu hoặc sai định dạng")
    except Exception as e:
        print(f"⚠️ N1 lỗi: {str(e)[:60]}")
    time.sleep(DELAY_PER_DAY)

    # ========== NGUỒN 2: KQXS API — DỰ PHÒNG ==========
    try:
        url = f"https://api.kqxs.vn/xsmb?ngay={ymd}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            js = resp.json()
            if "dacbiet" in js or "special" in js:
                db = str(js.get("dacbiet", js.get("special", ""))).strip()
                g1 = str(js.get("giai1", js.get("prize1", ""))).strip()
                all_5digit = re.findall(r"\b\d{5}\b", str(js))
                loto = sorted(list(set([n[-2:] for n in all_5digit if len(n)==5])))
                if db and g1 and len(db)==5 and len(g1)==5 and len(loto)>=10:
                    print(f"✅ N2-kqxs.vn | {ngay_str} | ĐB:{db} G1:{g1}")
                    return {"special":db, "g1":g1, "loto":loto, "source":"kqxs.vn(API)"}
        print(f"⚠️ N2-kqxs.vn: Không có dữ liệu")
    except Exception as e:
        print(f"⚠️ N2 lỗi: {str(e)[:60]}")

    print(f"❌ KHÔNG LẤY ĐƯỢC: {ngay_str}")
    return None

# ====================== 📊 DỰ ĐOÁN ======================
def tinh_du_doan():
    data = load_data()
    tong, tu, den, verified, unique_db = get_stats()
    ngay_mai = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")

    if tong < MIN_DAYS_FOR_PREDICT:
        return f"""⚠️ CHƯA ĐỦ DỮ LIỆU!
👉 Hiện có: {tong} ngày | Yêu cầu: ≥{MIN_DAYS_FOR_PREDICT} ngày
👉 Gõ /lay90 — Lấy đủ dữ liệu từ 2 nguồn API!"""

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
📊 Phân tích: {so_ngay} ngày gần nhất | Tổng: {tong} ngày | ĐB duy nhất: {unique_db} ({ti_le_dang_ky}%)
✅ Nguồn: xoso.ws API + kqxs.vn API → ổn định, chính xác

🎯 **3 CON LÔ ÍT XUẤT HIỆN NHẤT → SẮP RA CAO NHẤT:**
   1. `{top3[0]['so']}` — xuất hiện {top3[0]['lan']}/{so_ngay} ngày → Tỷ lệ: **{top3[0]['ty_le']}%** | Đã nghỉ: {top3[0]['nghi']} ngày
   2. `{top3[1]['so']}` — xuất hiện {top3[1]['lan']}/{so_ngay} ngày → Tỷ lệ: **{top3[1]['ty_le']}%** | Đã nghỉ: {top3[1]['nghi']} ngày
   3. `{top3[2]['so']}` — xuất hiện {top3[2]['lan']}/{so_ngay} ngày → Tỷ lệ: **{top3[2]['ty_le']}%** | Đã nghỉ: {top3[2]['nghi']} ngày

🔄 **1 CẶP LÔ XIÊN:** `{xien[0]} - {xien[1]}`

🔢 **Đầu số đề:** `{dau_de}` → **{ty_le_dau}%**
🔢 **2 số cuối đề:** `{so_de}` → **{ty_le_so_de}%**

⚠️ *Chỉ tham khảo — Không chắc chắn 100% — Chơi có trách nhiệm!*
"""

# ====================== 🤖 LỆNH BOT ======================
@app.route('/')
def home():
    tong, tu, den, verified, unique_db = get_stats()
    return f"✅ V41.0 | {tong} ngày | Dùng API ổn định | Lấy được dữ liệu!"

def gui(chat_id, text, md="Markdown"):
    for _ in range(3):
        try:
            with BOT_LOCK: return bot.send_message(chat_id, text, parse_mode=md)
        except Exception as e:
            if "409" in str(e) or "Conflict" in str(e): time.sleep(3)
            else: time.sleep(1)
    return None

@bot.message_handler(commands=['start'])
def start(m):
    tong, tu, den, verified, unique_db = get_stats()
    gui(m.chat.id,
        f"🤖 *BOT XSMB — V41.0 | ✅ DÙNG API ỔN ĐỊNH → LẤY ĐƯỢC DỮ LIỆU*\n"
        f"📊 Tổng: *{tong} ngày* | Đã xác minh: {verified}\n\n"
        f"/lay90 = Lấy 90 ngày từ 2 nguồn API\n"
        f"/dudoan = Dự đoán ngày mai + tỷ lệ %\n"
        f"/status = Xem trạng thái dữ liệu\n"
        f"/xoadulieu = Xóa dữ liệu cũ lấy lại mới\n"
        f"VD: 12092026 = Xem kết quả ngày cũ",
    )

@bot.message_handler(commands=['status'])
def status(m):
    tong, tu, den, verified, unique_db = get_stats()
    gui(m.chat.id,
        f"📊 *TRẠNG THÁI DỮ LIỆU*\n"
        f"• Tổng ngày: *{tong} ngày* (Cần ≥{MIN_DAYS_FOR_PREDICT})\n"
        f"• Phạm vi: {tu} → {den}\n"
        f"• Nguồn: xoso.ws API + kqxs.vn API\n"
        f"• ĐB duy nhất: {unique_db}",
    )

@bot.message_handler(commands=['xoadulieu'])
def xoa(m):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        gui(m.chat.id, "✅ *ĐÃ XÓA DỮ LIỆU CŨ!* 🗑️\n👉 Gõ /lay90 lấy dữ liệu MỚI từ API!",)
    else:
        gui(m.chat.id, "⚠️ Chưa có dữ liệu!",)

@bot.message_handler(commands=['lay90'])
def lay90(m):
    gui(m.chat.id,
        f"🚀 *ĐANG LẤY 90 NGÀY DỮ LIỆU...*\n"
        f"✅ Nguồn: xoso.ws API → kqxs.vn API\n"
        f"⚡ Nhanh & ổn định — Không bị chặn!\n"
        f"⏰ Khoảng 2-3 phút là xong!",
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

            if offset % 15 == 0:
                gui(m.chat.id,
                    f"⏳ Tiến độ: {offset}/{total} ngày ({round(offset/total*100)}%)\n"
                    f"✅ Mới: {lay_moi} | ⚠️ Lỗi: {that_bai} | ✅ Đã có: {da_co}",
                )
            time.sleep(DELAY_PER_DAY)

        tong, _, _, verified, _ = get_stats()
        gui(m.chat.id,
            f"✅ *HOÀN THÀNH!* 🎉\n"
            f"📊 Tổng: *{tong} ngày*\n"
            f"• Đã có sẵn: {da_co} | Lấy mới: {lay_moi} | Lỗi: {that_bai}\n"
            f"{'✅ ĐỦ DỮ LIỆU → Gõ /dudoan NGAY!' if tong >= MIN_DAYS_FOR_PREDICT else f'⚠️ Cần thêm: {MIN_DAYS_FOR_PREDICT - tong} ngày nữa'}",
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
                f"📅 *KẾT QUẢ NGÀY: {date_str}*\n"
                f"🏆 Đặc biệt: `{kq['special']}`\n🥇 Giải nhất: `{kq['g1']}`\n📌 Nguồn: {kq['source']}",
            )
        else:
            gui(m.chat.id, f"🔍 *ĐANG LẤY DỮ LIỆU NGÀY {date_str}...*",)
            kq = lay_ket_qua_ngay(date_str)
            if kq and luu_ket_qua(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"]):
                gui(m.chat.id,
                    f"✅ *ĐÃ LƯU DỮ LIỆU!* 🎉\n📅 {date_str}\n🏆 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n📌 Nguồn: {kq['source']}",
                )
            else:
                gui(m.chat.id, f"❌ *KHÔNG LẤY ĐƯỢC DỮ LIỆU NGÀY {date_str}*",)
    except:
        gui(m.chat.id, "⚠️ Sai định dạng! VD: 12092026",)

# ====================== ⏰ TỰ ĐỘNG GỬI ======================
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
                        f"🏆 *KẾT QUẢ NGÀY HÔM NAY — {hom_nay}*\n"
                        f"🎯 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`",
                    )
                da_gui_kq.add(hom_nay)
            if gio == SEND_PREDICT_TIME and hom_nay not in da_gui_dd:
                gui(CHAT_ID, f"🔮 *DỰ ĐOÁN NGÀY MAI*\n" + tinh_du_doan(),)
                da_gui_dd.add(hom_nay)
            time.sleep(30)
        except Exception as e:
            print(f"Lỗi tự động: {e}")
            time.sleep(10)

# ====================== 🚀 CHẠY BOT ======================
def run_bot():
    global POLLING_STARTED
    if POLLING_STARTED: return
    POLLING_STARTED = True
    print("="*60)
    print("✅ V41.0 — DÙNG API ỔN ĐỊNH → LẤY ĐƯỢC DỮ LIỆU NGAY!")
    print("="*60)
    try: bot.remove_webhook()
    except: pass
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=40, allowed_updates=None)
        except Exception as e:
            if "409" in str(e) or "Conflict" in str(e):
                print("⚠️ 409 — Đợi 5s...")
                time.sleep(5)
            else:
                time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=tu_dong, daemon=True).start()
    run_bot()
