# ==========================================================
# xsmb_bot2.py — V31.0 | ✅ TOKEN MỚI + ĐỊNH DẠNG THEO ẢNH
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
PORT = 10000
ANALYSIS_DAYS = 60       # ✅ 60 ngày như yêu cầu
SEND_RESULT_TIME = "18:40"
SEND_PREDICT_TIME = "18:41"

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://xsmb.vn/"
}

BOT_LOCK = threading.Lock()
POLLING_STARTED = False

# ====================== 💾 QUẢN LÝ DỮ LIỆU ======================
def load_data():
    if not os.path.exists(DATA_FILE):
        print(f"📁 File {DATA_FILE} chưa tồn tại → trả trống")
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"❌ Lỗi đọc {DATA_FILE}: {e}")
        return {}

def save_data(date_str, special, g1, loto, source="api"):
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", date_str):
        print(f"❌ Sai định dạng ngày: {date_str}")
        return False
    if not special or len(special) != 5 or not special.isdigit():
        print(f"❌ Đặc biệt không hợp lệ: '{special}'")
        return False
    if not g1 or len(g1) != 5 or not g1.isdigit():
        print(f"❌ Giải nhất không hợp lệ: '{g1}'")
        return False

    data = load_data()
    data[date_str] = {
        "special": special.strip(),
        "g1": g1.strip(),
        "loto": [str(x).zfill(2) for x in loto if str(x).isdigit() and len(str(x)) == 2],
        "source": source,
        "saved_at": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 ✅ LƯU THÀNH CÔNG: {date_str} | ĐB:{special} G1:{g1} | {len(data)} ngày TỔNG")
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu dữ liệu: {e}")
        return False

def get_stats():
    data = load_data()
    if not data: return 0, "--", "--"
    dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    return len(data), dates[0], dates[-1]

# ====================== 📡 LẤY DỮ LIỆU — 3 NGUỒN ======================
def lay_ket_qua_xsmb(ngay_str=None):
    if not ngay_str:
        ngay_str = datetime.now().strftime("%d/%m/%Y")
    try:
        d, m, y = ngay_str.split("/")
        d, m = d.zfill(2), m.zfill(2)
        ymd = f"{y}-{m}-{d}"
        ymd_short = f"{y}{m}{d}"
        print(f"\n🔍 === BẮT ĐẦU LẤY: {ngay_str} ===")
    except Exception as e:
        print(f"❌ Sai định dạng ngày '{ngay_str}': {e}")
        return None

    now_vn = datetime.now()
    if ngay_str == now_vn.strftime("%d/%m/%Y") and (now_vn.hour < 18 or (now_vn.hour == 18 and now_vn.minute < 35)):
        print(f"ℹ️ Ngày hôm nay chưa đến 18:35 → chưa có kết quả")
        return None

    # NGUỒN 1
    try:
        url = f"https://api.xosoonline.vn/xsmb?date={ymd}"
        print(f"📡 NGUỒN 1: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            db = str(data.get("dacbiet") or data.get("special") or data.get("db") or "").strip()
            g1 = str(data.get("giai_nhat") or data.get("giai1") or data.get("g1") or "").strip()
            tat_ca_5so = []
            for key in ["dacbiet", "giai_nhat", "giai2", "giai3", "giai4", "giai5", "giai6", "giai7"]:
                val = data.get(key, "")
                if isinstance(val, str) and len(val) == 5 and val.isdigit(): tat_ca_5so.append(val)
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, str) and len(item) == 5 and item.isdigit(): tat_ca_5so.append(item)
            loto = sorted(list(set([n[-2:] for n in tat_ca_5so if len(n) == 5 and n.isdigit()])))
            if len(db) == 5 and db.isdigit() and len(g1) == 5 and g1.isdigit() and len(loto) >= 10:
                print(f"✅ NGUỒN 1 OK | ĐB:{db} G1:{g1} | {len(loto)} lô")
                return {"date": ngay_str, "special": db, "g1": g1, "loto": loto, "source": "api.xosoonline.vn"}
    except Exception as e: print(f"⚠️ Nguồn 1: {str(e)[:80]}")

    # NGUỒN 2
    try:
        url = f"https://kqxs.vn/api/xsmb/{ymd_short}"
        print(f"📡 NGUỒN 2: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            db = str(data.get("special") or data.get("dacbiet") or "").strip()
            g1 = str(data.get("prize1") or data.get("giai_nhat") or "").strip()
            tat_ca_5so = []
            for k, v in data.items():
                if isinstance(v, str) and len(v) == 5 and v.isdigit(): tat_ca_5so.append(v)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, str) and len(item) == 5 and item.isdigit(): tat_ca_5so.append(item)
            loto = sorted(list(set([n[-2:] for n in tat_ca_5so if len(n) == 5 and n.isdigit()])))
            if len(db) == 5 and db.isdigit() and len(g1) == 5 and g1.isdigit() and len(loto) >= 10:
                print(f"✅ NGUỒN 2 OK")
                return {"date": ngay_str, "special": db, "g1": g1, "loto": loto, "source": "kqxs.vn"}
    except Exception as e: print(f"⚠️ Nguồn 2: {str(e)[:80]}")

    # NGUỒN 3
    try:
        url = f"https://xoso.me/api/result?date={ymd}&region=xsmb"
        print(f"📡 NGUỒN 3: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            db = str(data.get("result", {}).get("special", "")).strip()
            g1 = str(data.get("result", {}).get("prize1", "")).strip()
            tat_ca_5so = []
            prizes = data.get("result", {})
            for k, v in prizes.items():
                if isinstance(v, str) and len(v) == 5 and v.isdigit(): tat_ca_5so.append(v)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, str) and len(item) == 5 and item.isdigit(): tat_ca_5so.append(item)
            loto = sorted(list(set([n[-2:] for n in tat_ca_5so if len(n) == 5 and n.isdigit()])))
            if len(db) == 5 and db.isdigit() and len(g1) == 5 and g1.isdigit() and len(loto) >= 10:
                print(f"✅ NGUỒN 3 OK")
                return {"date": ngay_str, "special": db, "g1": g1, "loto": loto, "source": "xoso.me"}
    except Exception as e: print(f"⚠️ Nguồn 3: {str(e)[:80]}")

    print(f"❌ TẤT CẢ NGUỒN THẤT BẠI — {ngay_str}")
    return None

# ====================== 📊 DỰ ĐOÁN — ĐÚNG ĐỊNH DẠNG ẢNH ======================
def tinh_du_doan():
    data = load_data()
    tong = len(data)
    PHAN_TICH_NGAY = 60

    if tong < 30:
        return f"⚠️ Cần ít nhất 30 ngày dữ liệu. Hiện có {tong} ngày.\n👉 Gõ /lay90 để lấy dữ liệu!"

    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    so_ngay = min(PHAN_TICH_NGAY, tong)
    ds = sap_xep[:so_ngay]

    thong_tin_lo = {}
    tat_ca_dau_de = []

    for idx, ngay in enumerate(ds):
        kq = data[ngay]
        for lo in kq.get("loto", []):
            if len(lo) == 2 and lo.isdigit():
                if lo not in thong_tin_lo:
                    thong_tin_lo[lo] = {"lan": 0, "ngay_gan_nhat": idx}
                thong_tin_lo[lo]["lan"] += 1
                thong_tin_lo[lo]["ngay_gan_nhat"] = min(thong_tin_lo[lo]["ngay_gan_nhat"], idx)
        db = kq.get("special", "")
        if len(db) == 5 and db.isdigit():
            tat_ca_dau_de.append(db[0])
            lo_de = db[-2:]
            if lo_de not in thong_tin_lo:
                thong_tin_lo[lo_de] = {"lan": 0, "ngay_gan_nhat": idx}
            thong_tin_lo[lo_de]["lan"] += 1
            thong_tin_lo[lo_de]["ngay_gan_nhat"] = min(thong_tin_lo[lo_de]["ngay_gan_nhat"], idx)

    if not thong_tin_lo:
        return "⚠️ Dữ liệu lô trống. Gõ /lay90 trước!"

    ds_diem = []
    for so, info in thong_tin_lo.items():
        tan_suat = info["lan"]
        ty_le = round(tan_suat / so_ngay * 100, 1)
        chu_ky_ngu = info["ngay_gan_nhat"]
        diem_tong_hop = round(tan_suat * 1.5 + chu_ky_ngu * 2)
        ds_diem.append({
            "so": so,
            "lan": tan_suat,
            "ty_le": ty_le,
            "ngu": chu_ky_ngu,
            "diem": diem_tong_hop
        })

    ds_diem.sort(key=lambda x: -x["diem"])
    top3 = ds_diem[:3]
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3) >= 2 else ["00", "01"]

    dau_de, ty_le_dau, dau_count = "9", 20.0, 1
    if tat_ca_dau_de:
        d = Counter(tat_ca_dau_de).most_common(1)[0]
        dau_de, dau_count, ty_le_dau = d[0], d[1], round(d[1] / len(tat_ca_dau_de) * 100, 1)

    ngay_mai = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    return f"""
📊 **DỰ ĐOÁN KẾT QUẢ – DỰA TRÊN {PHAN_TICH_NGAY} NGÀY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **3 CON LÔ TỶ LỆ CAO NHẤT:**
   (Theo tần suất + chu kỳ nghỉ)
   1. `{top3[0]['so']}` – {top3[0]['lan']} lần, tỷ lệ {top3[0]['ty_le']}%, nghỉ {top3[0]['ngu']} ngày
   2. `{top3[1]['so']}` – {top3[1]['lan']} lần, tỷ lệ {top3[1]['ty_le']}%, nghỉ {top3[1]['ngu']} ngày
   3. `{top3[2]['so']}` – {top3[2]['lan']} lần, tỷ lệ {top3[2]['ty_le']}%, nghỉ {top3[2]['ngu']} ngày

🔄 **1 CẶP LÔ XIÊN:**
   → Kết hợp 2 con cao nhất: `{xien[0]} - {xien[1]}`

🔢 **DỰ KIẾN ĐẦU SỐ ĐỀ:**
   → Đầu số `{dau_de}` – xuất hiện {dau_count} lần → {ty_le_dau}%

🧠 **Cách tính:** Tần suất xuất hiện + số ngày chưa về → điểm tổng hợp cao nhất

⚠️ *Chỉ tham khảo – Chơi có trách nhiệm!*
"""

# ====================== 🤖 LỆNH BOT ======================
@app.route('/')
def home():
    tong, tu, den = get_stats()
    return f"✅ Bot XSMB V31.0 — Token MỚI | Đã lưu {tong} ngày dữ liệu"

def gui_anh_ten(chat_id, text, parse_mode="Markdown", max_thu_lai=3):
    for lan in range(1, max_thu_lai + 1):
        try:
            with BOT_LOCK:
                return bot.send_message(chat_id, text, parse_mode=parse_mode)
        except Exception as e:
            if any(err in str(e) for err in ["409", "Conflict", "429"]):
                tam_nghi = min(2 ** lan, 15)
                print(f"⚠️ Lỗi Telegram (lần {lan}): {e} → chờ {tam_nghi}s...")
                time.sleep(tam_nghi)
            else:
                print(f"❌ Lỗi gửi: {e}")
                return None
    return None

@bot.message_handler(commands=['start'])
def cmd_start(m):
    gui_anh_ten(m.chat.id,
        "🤖 *BOT XSMB — V31.0 | TOKEN MỚI + ĐỊNH DẠNG THEO ẢNH ✅*\n"
        "/lay90 = Lấy 60 ngày dữ liệu thật\n"
        "/dudoan = Xem dự đoán\n"
        "/status = Xem trạng thái dữ liệu\n"
        "Ngày VD: 29082026 → Xem kết quả lịch sử\n\n"
        "📌 Gõ /lay90 → Bắt đầu!",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    tong, tu, den = get_stats()
    gui_anh_ten(m.chat.id,
        f"📊 *TRẠNG THÁI DỮ LIỆU*\n• Tổng ngày: *{tong} ngày*\n• Phạm vi: {tu} → {den}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['lay90'])
def cmd_lay90(m):
    gui_anh_ten(m.chat.id,
        "🚀 *ĐANG LẤY DỮ LIỆU 60 NGÀY...*\n⏰ Khoảng 2-3 phút!",
        parse_mode="Markdown"
    )
    def lay_async():
        today = datetime.now()
        lay_moi = that_bai = 0
        for offset in range(1, ANALYSIS_DAYS + 1):
            target_date = today - timedelta(days=offset)
            date_str = target_date.strftime("%d/%m/%Y")
            if date_str in load_data(): continue
            kq = lay_ket_qua_xsmb(date_str)
            if kq and save_data(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"]):
                lay_moi += 1
            else:
                that_bai += 1
            time.sleep(0.5)
        tong, _, _ = get_stats()
        gui_anh_ten(m.chat.id,
            f"✅ *HOÀN THÀNH!* 🎉\n📊 Tổng: *{tong} ngày*\n• Lấy mới: {lay_moi}\n• Thất bại: {that_bai}\n👉 Gõ /dudoan!",
            parse_mode="Markdown"
        )
    threading.Thread(target=lay_async, daemon=True).start()

@bot.message_handler(commands=['dudoan'])
def cmd_dudoan(m):
    gui_anh_ten(m.chat.id, tinh_du_doan(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text and len(msg.text.strip()) == 8 and msg.text.strip().isdigit())
def xem_ngay_cu(m):
    text = m.text.strip()
    try:
        d, mo, y = text[:2], text[2:4], text[4:]
        date_str = f"{d}/{mo}/{y}"
        data = load_data()
        if date_str in data:
            kq = data[date_str]
            gui_anh_ten(m.chat.id,
                f"📅 *KẾT QUẢ NGÀY: {date_str}*\n🏆 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n📌 Nguồn: {kq.get('source')}",
                parse_mode="Markdown"
            )
        else:
            gui_anh_ten(m.chat.id, f"🔍 *ĐANG LẤY DỮ LIỆU NGÀY {date_str}...*", parse_mode="Markdown")
            kq = lay_ket_qua_xsmb(date_str)
            if kq and save_data(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"]):
                gui_anh_ten(m.chat.id,
                    f"✅ *ĐÃ LẤY!* 🎉\n📅 {date_str}\n🏆 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`",
                    parse_mode="Markdown"
                )
            else:
                gui_anh_ten(m.chat.id, f"⚠️ *Không lấy được dữ liệu ngày {date_str}*", parse_mode="Markdown")
    except:
        gui_anh_ten(m.chat.id, "⚠️ Sai định dạng! VD: `29082026`", parse_mode="Markdown")

# ====================== ⏰ TỰ ĐỘNG GỬI ======================
def gui_tu_dong():
    da_gui_kq, da_gui_dd = set(), set()
    while True:
        try:
            now = datetime.now()
            hom_nay = now.strftime("%d/%m/%Y")
            gio = now.strftime("%H:%M")
            if gio == SEND_RESULT_TIME and hom_nay not in da_gui_kq:
                kq = lay_ket_qua_xsmb(hom_nay)
                if kq and save_data(hom_nay, kq["special"], kq["g1"], kq["loto"], kq["source"]):
                    gui_anh_ten(CHAT_ID,
                        f"🏆 *KẾT QUẢ NGÀY D — {hom_nay}*\n🎯 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n📌 Nguồn: {kq['source']}",
                        parse_mode="Markdown"
                    )
                da_gui_kq.add(hom_nay)
            if gio == SEND_PREDICT_TIME and hom_nay not in da_gui_dd:
                gui_anh_ten(CHAT_ID, tinh_du_doan(), parse_mode="Markdown")
                da_gui_dd.add(hom_nay)
            time.sleep(30)
        except Exception as e:
            print(f"⚠️ Lỗi tự động gửi: {e}")
            time.sleep(10)

# ====================== 🚀 CHẠY BOT ======================
def run_bot():
    global POLLING_STARTED
    if POLLING_STARTED:
        print("⚠️ Polling đã chạy — KHÔNG khởi động lại!")
        return
    POLLING_STARTED = True
    print("=" * 60)
    print("✅ BOT V31.0 — TOKEN MỚI + ĐỊNH DẠNG THEO ẢNH!")
    print("=" * 60)
    try:
        bot.remove_webhook()
        print("✅ Đã TẮT Webhook!")
    except Exception as e:
        print(f"⚠️ Lỗi tắt webhook: {e} — tiếp tục...")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=40, allowed_updates=None)
        except Exception as e:
            if "409" in str(e) or "Conflict" in str(e):
                print("🔴 LỖI 409 → đợi 15s...")
                time.sleep(15)
            else:
                print(f"⚠️ Lỗi polling: {e} → đợi 5s...")
                time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=gui_tu_dong, daemon=True).start()
    run_bot()
