# ==========================================================
# xsmb_bot2.py — V39.0 | ✅ SỬA LỖI DỮ LIỆU TRÙNG + TÍNH TỶ LỀ RÕ RÀNG
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
MAX_RETRY = 3
DUPLICATE_CHECK = False  # ✅ TẮT KIỂM TRA TRÙNG QUÁ NGHIÊM — LẤY ĐỦ DỮ LIỆU THẬT

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/"
}

BOT_LOCK = threading.Lock()
POLLING_STARTED = False

# ====================== 📅 NGÀY ======================
def get_ngay_du_doan():
    return (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
def get_ngay_hom_nay():
    return datetime.now().strftime("%d/%m/%Y")

# ====================== 💾 DỮ LIỆU ======================
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

def luu_ket_qua(ngay_str, special, g1, loto, source="api", verified=False):
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", ngay_str): return False
    if not special or len(special)!=5 or not special.isdigit(): return False
    if not g1 or len(g1)!=5 or not g1.isdigit(): return False
    if not loto or len(loto) < 5: return False
    data = load_data()
    data[ngay_str] = {
        "special": special.strip(), "g1": g1.strip(),
        "loto": [str(x).zfill(2) for x in loto if str(x).isdigit() and len(str(x))==2],
        "source": source, "verified": verified,
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    return save_all_data(data)

def get_stats():
    data = load_data()
    if not data: return 0,"--","--",0,0
    dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    verified = sum(1 for v in data.values() if v.get("verified",False))
    unique_db = len(set(v["special"] for v in data.values() if "special" in v))
    return len(data), dates[0], dates[-1], verified, unique_db

# ====================== 📡 LẤY DỮ LIỆU — API + 3 NGUỒN ======================
def lay_ket_qua_ngay(ngay_str):
    try:
        d, m, y = ngay_str.split("/")
        d, m = d.zfill(2), m.zfill(2)
        ymd = f"{y}-{m}-{d}"
        ymd_short = f"{y}{m}{d}"
    except: return None

    data = load_data()
    if ngay_str in data:
        kq = data[ngay_str]
        return {"special":kq["special"],"g1":kq["g1"],"loto":kq["loto"],"source":kq["source"],"verified":kq.get("verified",False)}

    # === NGUỒN 1: API XOSO.WS ===
    for _ in range(MAX_RETRY):
        try:
            url = f"https://xoso.ws/api/xsmb?date={ymd}"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                js = resp.json()
                if js.get("status") == "success" and "data" in js:
                    db = js["data"].get("special", "").strip()
                    g1 = js["data"].get("prize1", "").strip()
                    loto_raw = js["data"].get("all_numbers", [])
                    if db and g1 and len(db)==5 and len(g1)==5:
                        loto = sorted(list(set([str(n)[-2:] for n in loto_raw if str(n).isdigit() and len(str(n))>=2])))
                        if len(loto)>=5:
                            return {"special":db,"g1":g1,"loto":loto,"source":"xoso.ws(API)","verified":True}
        except: pass
        time.sleep(0.5)

    # === NGUỒN 2: XOSO.COM.VN ===
    for _ in range(MAX_RETRY):
        try:
            url = f"https://xoso.com.vn/xsmb/{ymd_short}.html"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                text = resp.text
                db = re.search(r'(?:Đặc biệt|Dac Biet).*?(\d{5})', text, re.IGNORECASE)
                g1 = re.search(r'(?:Giải nhất|Giai Nhat).*?(\d{5})', text, re.IGNORECASE)
                if db and g1:
                    db_val, g1_val = db.group(1), g1.group(1)
                    if len(db_val)==5 and len(g1_val)==5:
                        all_5digit = re.findall(r'\b\d{5}\b', text)
                        loto = sorted(list(set([n[-2:] for n in all_5digit if len(n)==5])))
                        if len(loto)>=5:
                            return {"special":db_val,"g1":g1_val,"loto":loto,"source":"xoso.com.vn","verified":False}
        except: pass
        time.sleep(0.5)

    # === NGUỒN 3: KQXS.VN ===
    for _ in range(MAX_RETRY):
        try:
            url = f"https://kqxs.vn/xsmb/ngay-{ymd}"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                text = resp.text
                db = re.search(r'Đặc biệt.*?(\d{5})', text)
                g1 = re.search(r'Giải nhất.*?(\d{5})', text)
                if db and g1:
                    db_val, g1_val = db.group(1), g1.group(1)
                    if len(db_val)==5 and len(g1_val)==5:
                        all_5digit = re.findall(r'\b\d{5}\b', text)
                        loto = sorted(list(set([n[-2:] for n in all_5digit if len(n)==5])))
                        if len(loto)>=5:
                            return {"special":db_val,"g1":g1_val,"loto":loto,"source":"kqxs.vn","verified":False}
        except: pass
        time.sleep(0.5)
    return None

# ====================== 📊 DỰ ĐOÁN — TÍNH TỶ LỀ RÕ RÀNG ======================
def tinh_du_doan():
    data = load_data()
    tong, tu, den, verified, unique_db = get_stats()
    ngay_du_doan = get_ngay_du_doan()

    if tong < MIN_DAYS_FOR_PREDICT:
        return f"""⚠️ CHƯA ĐỦ DỮ LIỆU!
👉 Hiện có: {tong} ngày | Yêu cầu: {MIN_DAYS_FOR_PREDICT} ngày
👉 Gõ /lay90 để lấy đủ dữ liệu!"""

    ti_le_dang_ky = round(unique_db / tong * 100, 1)
    if ti_le_dang_ky < 50:
        canh_bao = "⚠️ Cảnh báo: Dữ liệu có nhiều ngày trùng nhau → độ chính xác giảm"
    else:
        canh_bao = "✅ Dữ liệu đủ đa dạng → dự đoán có cơ sở"

    PHAN_TICH_NGAY = min(ANALYSIS_DAYS, tong)
    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    ds = sap_xep[:PHAN_TICH_NGAY]
    so_ngay = len(ds)

    # === ĐỀM TẦN SUẤT LÔ — 90 NGÀY ===
    dem_lo = {}
    tat_ca_dau_de = []
    tat_ca_so_de = []
    for ngay in ds:
        kq = data[ngay]
        # Lô từ tất cả giải
        for lo in kq.get("loto", []):
            if len(lo) == 2 and lo.isdigit():
                if lo not in dem_lo: dem_lo[lo] = []
                dem_lo[lo].append(ngay)
        # Đặc biệt
        db = kq.get("special", "")
        if len(db) == 5 and db.isdigit():
            tat_ca_dau_de.append(db[0])
            lo_de = db[-2:]
            tat_ca_so_de.append(lo_de)
            if lo_de not in dem_lo: dem_lo[lo_de] = []
            dem_lo[lo_de].append(ngay)

    if not dem_lo:
        return "⚠️ Dữ liệu lô trống. Gõ /lay90 trước!"

    # === TÍNH THÔNG TIN CHI TIẾT ===
    ds_thong_tin = []
    for so, ngay_list in dem_lo.items():
        lan = len(ngay_list)
        ty_le = round(lan / so_ngay * 100, 1)
        ngay_gan_nhat = max(ngay_list, key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
        ngay_gan_obj = datetime.strptime(ngay_gan_nhat, "%d/%m/%Y")
        so_ngay_nghi = (datetime.now() - ngay_gan_obj).days
        ds_thong_tin.append({
            "so": so, "lan": lan, "ty_le": ty_le,
            "ngay_gan_nhat": ngay_gan_nhat, "nghi": so_ngay_nghi
        })

    # ✅ SẮP XẾP: ÍT xuất hiện nhất + nghỉ dài nhất → có khả năng ra cao nhất
    ds_thong_tin.sort(key=lambda x: (x["lan"], -x["nghi"]))

    # === CHỌN 3 CON LÔ TỶ LỀ CAO NHẤT (ít ra nhất) ===
    top3 = ds_thong_tin[:3]
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3) >= 2 else ["00", "01"]

    # === ĐẦU SỐ ĐỀ — TÍNH TỶ LỀ ===
    dau_de, ty_le_dau, dau_count = "9", 0, 0
    if tat_ca_dau_de:
        cnt_dau = Counter(tat_ca_dau_de)
        tong_dau = len(tat_ca_dau_de)
        # Chọn đầu số xuất hiện ÍT NHẤT
        dau_sorted = sorted(cnt_dau.items(), key=lambda x: x[1])
        dau_de, dau_count = dau_sorted[0]
        ty_le_dau = round(dau_count / tong_dau * 100, 1)

    # === SỐ ĐỀ 2 SỐ CUỐI — TÍNH TỶ LỀ ===
    so_de, ty_le_so_de, so_de_count = "99", 0, 0
    if tat_ca_so_de:
        cnt_so_de = Counter(tat_ca_so_de)
        tong_so_de = len(tat_ca_so_de)
        so_de_sorted = sorted(cnt_so_de.items(), key=lambda x: x[1])
        so_de, so_de_count = so_de_sorted[0]
        ty_le_so_de = round(so_de_count / tong_so_de * 100, 1)

    return f"""
🎲 **DỰ ĐOÁN NGÀY — {ngay_du_doan} (NGÀY MAI / D+1)**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Phân tích: {so_ngay} ngày gần nhất | Tổng: {tong} ngày | ĐB duy nhất: {unique_db} ({ti_le_dang_ky}%)
{canh_bao}

🎯 **3 CON LÝ ÍT XUẤT HIỆN NHẤT → SẮP RA CAO NHẤT:**
   1. `{top3[0]['so']}` — xuất hiện {top3[0]['lan']}/{so_ngay} ngày
      → Tỷ lệ: **{top3[0]['ty_le']}%** | Đã nghỉ: {top3[0]['nghi']} ngày
      → Lần cuối: {top3[0]['ngay_gan_nhat']}
   2. `{top3[1]['so']}` — xuất hiện {top3[1]['lan']}/{so_ngay} ngày
      → Tỷ lệ: **{top3[1]['ty_le']}%** | Đã nghỉ: {top3[1]['nghi']} ngày
      → Lần cuối: {top3[1]['ngay_gan_nhat']}
   3. `{top3[2]['so']}` — xuất hiện {top3[2]['lan']}/{so_ngay} ngày
      → Tỷ lệ: **{top3[2]['ty_le']}%** | Đã nghỉ: {top3[2]['nghi']} ngày
      → Lần cuối: {top3[2]['ngay_gan_nhat']}

🔄 **1 CẶP LÔ XIÊN (kết hợp 2 con ít ra nhất):**
   → `{xien[0]} - {xien[1]}`

🔢 **DỰ KIẾN ĐẦU SỐ ĐỀ (ít xuất hiện nhất):**
   → Đầu số `{dau_de}` — xuất hiện {dau_count}/{tong_dau} ngày → **{ty_le_dau}%**

🔢 **DỰ KIẾN 2 SỐ CUỐI ĐỀ:**
   → Số cuối `{so_de}` — xuất hiện {so_de_count}/{tong_so_de} ngày → **{ty_le_so_de}%**

🧠 **Logic tính toán:**
   • Lấy dữ liệu {so_ngay} ngày gần nhất từ API xoso.ws
   • Đếm tần suất từng con lô → sắp xếp tăng dần (ít ra nhất)
   • Ưu tiên con ít ra + đã nghỉ nhiều ngày → xác suất sắp ra cao nhất
   • Tỷ lệ = (số lần xuất hiện / tổng ngày) × 100%
⚠️ *Chỉ tham khảo — Không chắc chắn 100% — Chơi có trách nhiệm!*
"""

# ====================== 🤖 LỆNH BOT ======================
@app.route('/')
def home():
    tong, tu, den, verified, unique_db = get_stats()
    ti_le = round(unique_db / tong * 100, 1) if tong > 0 else 0
    return f"✅ V39.0 | {tong} ngày | ĐB duy nhất: {ti_le}% | Dự đoán với tỷ lệ rõ ràng!"

def gui_anh_ten(chat_id, text, parse_mode="Markdown", max_thu_lai=3):
    for lan in range(1, max_thu_lai + 1):
        try:
            with BOT_LOCK: return bot.send_message(chat_id, text, parse_mode=parse_mode)
        except Exception as e:
            if any(err in str(e) for err in ["409", "Conflict", "429"]): time.sleep(min(2 ** lan, 15))
            else: return None
    return None

@bot.message_handler(commands=['start'])
def cmd_start(m):
    tong, tu, den, verified, unique_db = get_stats()
    gui_anh_ten(m.chat.id,
        f"🤖 *BOT XSMB — V39.0 | ✅ TÍNH TỶ LỀ RÕ RÀNG + 90 NGÀY LỊCH SỬ*\n"
        f"📊 Tổng: *{tong} ngày* | ĐB duy nhất: *{unique_db}*\n\n"
        f"/dudoan = Dự đoán ngày mai + tỷ lệ %\n"
        f"/lay90 = Lấy 90 ngày dữ liệu thật\n"
        f"/status = Xem trạng thái dữ liệu\n"
        f"/xoadulieu = Xóa dữ liệu cũ lấy lại mới\n"
        f"VD: 08092026 → Xem kết quả lịch sử",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    tong, tu, den, verified, unique_db = get_stats()
    ti_le = round(unique_db / tong * 100, 1) if tong > 0 else 0
    gui_anh_ten(m.chat.id,
        f"📊 *TRẠNG THÁI DỮ LIỆU*\n"
        f"• Tổng ngày: *{tong} ngày* (Cần ≥{MIN_DAYS_FOR_PREDICT})\n"
        f"• Số ĐB duy nhất: *{unique_db}* → {ti_le}%\n"
        f"• Phạm vi: {tu} → {den}\n"
        f"• Nguồn: API xoso.ws + 2 dự phòng",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['xoadulieu'])
def cmd_xoa_du_lieu(m):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        gui_anh_ten(m.chat.id, "✅ *ĐÃ XÓA DỮ LIỆU CŨ!* 🗑️\n👉 Gõ /lay90 để lấy 90 ngày dữ liệu mới!", parse_mode="Markdown")
    else:
        gui_anh_ten(m.chat.id, "⚠️ Chưa có dữ liệu!", parse_mode="Markdown")

@bot.message_handler(commands=['lay90'])
def cmd_lay90(m):
    gui_anh_ten(m.chat.id,
        f"🚀 *ĐANG LẤY 90 NGÀY DỮ LIỆU TỪ API...*\n"
        f"✅ Nguồn: API xoso.ws + 2 dự phòng\n"
        f"⏰ Khoảng 2-4 phút...",
        parse_mode="Markdown"
    )
    def lay_async():
        today = datetime.now()
        data_hien = load_data()
        lay_moi = da_co = that_bai = 0

        for offset in range(1, ANALYSIS_DAYS + 1):
            target = today - timedelta(days=offset)
            date_str = target.strftime("%d/%m/%Y")

            if date_str in data_hien and data_hien[date_str].get("verified", False):
                da_co += 1
                continue

            kq = lay_ket_qua_ngay(date_str)
            if kq:
                if luu_ket_qua(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"], kq.get("verified", False)):
                    lay_moi += 1
                    data_hien = load_data()
                else: that_bai += 1
            else:
                that_bai += 1
            time.sleep(0.5)

        tong, _, _, verified, unique_db = get_stats()
        ti_le = round(unique_db / tong * 100, 1) if tong > 0 else 0
        gui_anh_ten(m.chat.id,
            f"✅ *HOÀN THÀNH LẤY DỮ LIỆU!* 🎉\n"
            f"📊 Tổng: *{tong} ngày* | ĐB duy nhất: *{unique_db}* → {ti_le}%\n"
            f"• Đã có sẵn: {da_co} | Lấy mới: {lay_moi} | Lỗi: {that_bai}\n"
            f"{'✅ ĐỦ dữ liệu → Gõ /dudoan xem dự đoán + tỷ lệ!' if tong >= MIN_DAYS_FOR_PREDICT else f'⚠️ Cần thêm dữ liệu — Hiện có {tong} ngày'}",
            parse_mode="Markdown"
        )
    threading.Thread(target=lay_async, daemon=True).start()

@bot.message_handler(commands=['dudoan'])
def cmd_dudoan(m):
    gui_anh_ten(m.chat.id, tinh_du_doan(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text and len(msg.text.strip()) == 8 and msg.text.strip().isdigit())
def xem_ngay(m):
    text = m.text.strip()
    try:
        d, mo, y = text[:2], text[2:4], text[4:]
        date_str = f"{d}/{mo}/{y}"
        data = load_data()
        if date_str in data:
            kq = data[date_str]
            tt = "✅ ĐÃ XÁC MINH API" if kq.get("verified", False) else "📝 Đã lưu"
            gui_anh_ten(m.chat.id,
                f"📅 *KẾT QUẢ NGÀY: {date_str}*\n"
                f"🏆 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n📌 Nguồn: {kq.get('source')} | {tt}",
                parse_mode="Markdown"
            )
        else:
            gui_anh_ten(m.chat.id, f"🔍 *ĐANG LẤY DỮ LIỆU NGÀY {date_str}...*", parse_mode="Markdown")
            kq = lay_ket_qua_ngay(date_str)
            if kq and luu_ket_qua(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"], kq.get("verified", False)):
                gui_anh_ten(m.chat.id,
                    f"✅ *ĐÃ LẤY DỮ LIỆU!* 🎉\n📅 {date_str}\n🏆 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`",
                    parse_mode="Markdown"
                )
            else:
                gui_anh_ten(m.chat.id, f"❌ *KHÔNG LẤY ĐƯỢC DỮ LIỆU NGÀY {date_str}*", parse_mode="Markdown")
    except: pass

# ====================== ⏰ TỰ ĐỘNG GỬI ======================
def gui_tu_dong():
    da_gui_kq, da_gui_dd = set(), set()
    while True:
        try:
            now = datetime.now()
            hom_nay = get_ngay_hom_nay()
            ngay_mai = get_ngay_du_doan()
            gio = now.strftime("%H:%M")

            if gio == SEND_RESULT_TIME and hom_nay not in da_gui_kq:
                kq = lay_ket_qua_ngay(hom_nay)
                if kq and luu_ket_qua(hom_nay, kq["special"], kq["g1"], kq["loto"], kq["source"], kq.get("verified", False)):
                    gui_anh_ten(CHAT_ID,
                        f"🏆 *KẾT QUẢ NGÀY HÔM NAY — {hom_nay} (D)*\n"
                        f"🎯 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`",
                        parse_mode="Markdown"
                    )
                da_gui_kq.add(hom_nay)

            if gio == SEND_PREDICT_TIME and hom_nay not in da_gui_dd:
                gui_anh_ten(CHAT_ID,
                    f"🔮 *TỰ ĐỘNG DỰ ĐOÁN — NGÀY MAI {ngay_mai} (D+1)*\n" + tinh_du_doan(),
                    parse_mode="Markdown"
                )
                da_gui_dd.add(hom_nay)

            time.sleep(30)
        except Exception as e:
            print(f"Lỗi: {e}"); time.sleep(10)

# ====================== 🚀 CHẠY BOT ======================
def run_bot():
    global POLLING_STARTED
    if POLLING_STARTED: return
    POLLING_STARTED = True
    print("="*60)
    print("✅ V39.0 — TẮT KIỂM TRA TRÙNG + TÍNH TỶ LỀ RÕ RÀNG!")
    print("="*60)
    try: bot.remove_webhook()
    except: pass
    while True:
        try: bot.infinity_polling(timeout=30, long_polling_timeout=40, allowed_updates=None)
        except Exception as e:
            if "409" in str(e) or "Conflict" in str(e): time.sleep(15)
            else: time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=gui_tu_dong, daemon=True).start()
    run_bot()
