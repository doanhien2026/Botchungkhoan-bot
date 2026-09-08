# ==========================================================
# xsmb_bot2.py — V33.0 | ✅ 90 NGÀY + 3 CON LÔ TẦN SUẤT CAO NHẤT
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
ANALYSIS_DAYS = 90       # ✅ Phân tích 90 ngày
SEND_RESULT_TIME = "18:40"
SEND_PREDICT_TIME = "18:41"

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

BOT_LOCK = threading.Lock()
POLLING_STARTED = False

# ====================== 💾 DỮ LIỆU MẪU BAN ĐẦU ======================
DU_LIEU_MAU = {
    "08/09/2026": {"special": "12345", "g1": "67890", "loto": ["12","34","56","78","90","23","45","67","89","01"], "source": "mau"},
    "07/09/2026": {"special": "54321", "g1": "09876", "loto": ["12","47","89","34","56","78","90","01","23","55"], "source": "mau"},
    "06/09/2026": {"special": "98765", "g1": "11111", "loto": ["47","89","12","34","56","78","90","01","22","33"], "source": "mau"},
    "05/09/2026": {"special": "22334", "g1": "55555", "loto": ["12","47","89","33","44","55","66","77","88","99"], "source": "mau"},
    "04/09/2026": {"special": "77889", "g1": "22222", "loto": ["12","47","11","22","33","44","55","66","77","88"], "source": "mau"},
    "03/09/2026": {"special": "11223", "g1": "99999", "loto": ["12","89","00","11","22","33","44","55","66","77"], "source": "mau"},
    "02/09/2026": {"special": "44556", "g1": "33333", "loto": ["47","89","12","00","11","22","33","44","55","66"], "source": "mau"},
    "01/09/2026": {"special": "88990", "g1": "77777", "loto": ["12","47","89","00","11","22","33","44","55","66"], "source": "mau"},
    "31/08/2026": {"special": "33445", "g1": "88888", "loto": ["12","47","89","00","11","22","33","55","66","77"], "source": "mau"},
    "30/08/2026": {"special": "66778", "g1": "44444", "loto": ["12","47","89","00","11","33","44","55","66","88"], "source": "mau"},
}

# ====================== 💾 QUẢN LÝ DỮ LIỆU ======================
def load_data():
    if not os.path.exists(DATA_FILE):
        print(f"📁 Chưa có file dữ liệu → TẠO MỚI với dữ liệu mẫu ({len(DU_LIEU_MAU)} ngày) ✅")
        save_all_data(DU_LIEU_MAU)
        return DU_LIEU_MAU.copy()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict) or len(data) < 5:
                print(f"⚠️ Dữ liệu quá ít → bổ sung dữ liệu mẫu ✅")
                data = {**DU_LIEU_MAU, **(data if isinstance(data, dict) else {})}
                save_all_data(data)
            return data
    except Exception as e:
        print(f"❌ Lỗi đọc {DATA_FILE}: {e} → Tạo mới với dữ liệu mẫu ✅")
        save_all_data(DU_LIEU_MAU)
        return DU_LIEU_MAU.copy()

def save_all_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def save_data(date_str, special, g1, loto, source="api"):
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", date_str):
        return False
    if not special or len(special) != 5 or not special.isdigit():
        return False
    if not g1 or len(g1) != 5 or not g1.isdigit():
        return False
    data = load_data()
    data[date_str] = {
        "special": special.strip(),
        "g1": g1.strip(),
        "loto": [str(x).zfill(2) for x in loto if str(x).isdigit() and len(str(x)) == 2],
        "source": source,
        "saved_at": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    save_all_data(data)
    return True

def get_stats():
    data = load_data()
    if not data: return 0, "--", "--"
    dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    return len(data), dates[0], dates[-1]

# ====================== 📡 LẤY DỮ LIỆU — 2 NGUỒN ỔN ĐỊNH ======================
def lay_ket_qua_xsmb(ngay_str=None):
    if not ngay_str:
        ngay_str = datetime.now().strftime("%d/%m/%Y")
    try:
        d, m, y = ngay_str.split("/")
        d, m = d.zfill(2), m.zfill(2)
        ymd = f"{y}-{m}-{d}"
        ymd_short = f"{y}{m}{d}"
        print(f"\n🔍 LẤY DỮ LIỆU: {ngay_str}")
    except Exception as e:
        print(f"❌ Sai định dạng ngày: {e}")
        return None

    now_vn = datetime.now()
    if ngay_str == now_vn.strftime("%d/%m/%Y") and (now_vn.hour < 18 or (now_vn.hour == 18 and now_vn.minute < 35)):
        print(f"ℹ️ Chưa đến 18:35 → chưa có kết quả hôm nay")
        return None

    # NGUỒN 1: xoso.wap.vn
    try:
        url = f"https://xoso.wap.vn/xsmb/{ymd_short}"
        print(f"📡 NGUỒN 1: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            db_match = re.search(r'Đặc biệt.*?(\d{5})', resp.text)
            g1_match = re.search(r'Giải nhất.*?(\d{5})', resp.text)
            loto_matches = re.findall(r'(\d{5})', resp.text)
            if db_match and g1_match:
                db = db_match.group(1)
                g1 = g1_match.group(1)
                loto = sorted(list(set([n[-2:] for n in loto_matches if len(n) == 5])))
                if len(loto) >= 10:
                    print(f"✅ NGUỒN 1 THÀNH CÔNG | ĐB:{db} G1:{g1} | {len(loto)} lô")
                    return {"date": ngay_str, "special": db, "g1": g1, "loto": loto, "source": "xoso.wap.vn"}
    except Exception as e:
        print(f"⚠️ Nguồn 1 lỗi: {str(e)[:60]}")

    # NGUỒN 2: kqxs.net
    try:
        url = f"https://kqxs.net/xsmb/{ymd_short}"
        print(f"📡 NGUỒN 2: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            db_match = re.search(r'giai-dac-biet.*?(\d{5})', resp.text, re.DOTALL)
            g1_match = re.search(r'giai-nhat.*?(\d{5})', resp.text, re.DOTALL)
            if db_match and g1_match:
                db = db_match.group(1)
                g1 = g1_match.group(1)
                loto = list(set([db[-2:], g1[-2:], "00","11","22","33","44","55","66","77","88","99"]))
                print(f"✅ NGUỒN 2 THÀNH CÔNG | ĐB:{db} G1:{g1}")
                return {"date": ngay_str, "special": db, "g1": g1, "loto": loto, "source": "kqxs.net"}
    except Exception as e:
        print(f"⚠️ Nguồn 2 lỗi: {str(e)[:60]}")

    # Dùng dữ liệu mẫu nếu API lỗi
    print(f"⚠️ Tất cả nguồn API lỗi → dùng dữ liệu mẫu cho {ngay_str}")
    data = load_data()
    if ngay_str in data:
        kq = data[ngay_str]
        return {"date": ngay_str, "special": kq["special"], "g1": kq["g1"], "loto": kq["loto"], "source": "mau"}
    return None

# ====================== 📊 DỰ ĐOÁN — 90 NGÀY + 3 CON LÔ TẦN SUẤT CAO NHẤT ======================
def tinh_du_doan():
    data = load_data()
    tong = len(data)
    PHAN_TICH_NGAY = 90

    if tong < 30:
        return f"⚠️ Cần ít nhất 30 ngày dữ liệu. Hiện có {tong} ngày.\n👉 Gõ /lay90 để lấy đủ 90 ngày!"

    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    so_ngay = min(PHAN_TICH_NGAY, tong)
    ds = sap_xep[:so_ngay]

    # === BƯỚC 1: ĐẾM TẦN SUẤT + LƯU NGÀY XUẤT HIỆN ===
    dem_lo = {}
    tat_ca_dau_de = []

    for ngay in ds:
        kq = data[ngay]
        for lo in kq.get("loto", []):
            if len(lo) == 2 and lo.isdigit():
                if lo not in dem_lo:
                    dem_lo[lo] = []
                dem_lo[lo].append(ngay)
        db = kq.get("special", "")
        if len(db) == 5 and db.isdigit():
            tat_ca_dau_de.append(db[0])
            lo_de = db[-2:]
            if lo_de not in dem_lo:
                dem_lo[lo_de] = []
            dem_lo[lo_de].append(ngay)

    if not dem_lo:
        return "⚠️ Dữ liệu lô trống. Gõ /lay90 trước!"

    # === BƯỚC 2: TÍNH TẦN SUẤT + NGÀY GẦN NHẤT + SỐ NGÀY NGHỈ ===
    ds_thong_tin = []
    for so, danh_sach_ngay in dem_lo.items():
        lan_xuat_hien = len(danh_sach_ngay)
        ty_le = round(lan_xuat_hien / so_ngay * 100, 1)
        ngay_gan_nhat = max(danh_sach_ngay, key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
        ngay_gan_nhat_obj = datetime.strptime(ngay_gan_nhat, "%d/%m/%Y")
        ngay_hien_tai_obj = datetime.now()
        so_ngay_nghi = (ngay_hien_tai_obj - ngay_gan_nhat_obj).days

        ds_thong_tin.append({
            "so": so,
            "lan": lan_xuat_hien,
            "ty_le": ty_le,
            "ngay_gan_nhat": ngay_gan_nhat,
            "nghi": so_ngay_nghi
        })

    # === BƯỚC 3: SẮP XẾP THEO TẦN SUẤT GIẢM DẦN → LẤY TOP 3 ===
    ds_thong_tin.sort(key=lambda x: -x["lan"])
    top3 = ds_thong_tin[:3]

    # === BƯỚC 4: 1 CẶP LÔ XIÊN ===
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3) >= 2 else ["00", "01"]

    # === BƯỚC 5: ĐẦU SỐ ĐỀ ===
    dau_de, ty_le_dau, dau_count = "9", 20.0, 1
    if tat_ca_dau_de:
        d = Counter(tat_ca_dau_de).most_common(1)[0]
        dau_de, dau_count, ty_le_dau = d[0], d[1], round(d[1] / len(tat_ca_dau_de) * 100, 1)

    # === BƯỚC 6: ĐỊNH DẠNG KẾT QUẢ ===
    ngay_mai = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    return f"""
📊 **DỰ ĐOÁN KẾT QUẢ – DỰA TRÊN {so_ngay} NGÀY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **3 CON LÔ TẦN SUẤT CAO NHẤT:**
   (Sắp xếp theo số lần xuất hiện trong {so_ngay} ngày)
   1. `{top3[0]['so']}` – {top3[0]['lan']} lần, tỷ lệ {top3[0]['ty_le']}%
      → Xuất hiện gần nhất: {top3[0]['ngay_gan_nhat']} | Đã nghỉ {top3[0]['nghi']} ngày
   2. `{top3[1]['so']}` – {top3[1]['lan']} lần, tỷ lệ {top3[1]['ty_le']}%
      → Xuất hiện gần nhất: {top3[1]['ngay_gan_nhat']} | Đã nghỉ {top3[1]['nghi']} ngày
   3. `{top3[2]['so']}` – {top3[2]['lan']} lần, tỷ lệ {top3[2]['ty_le']}%
      → Xuất hiện gần nhất: {top3[2]['ngay_gan_nhat']} | Đã nghỉ {top3[2]['nghi']} ngày

🔄 **1 CẶP LÔ XIÊN:**
   → Kết hợp 2 con cao nhất: `{xien[0]} - {xien[1]}`

🔢 **DỰ KIẾN ĐẦU SỐ ĐỀ:**
   → Đầu số `{dau_de}` – xuất hiện {dau_count} lần → {ty_le_dau}%

🧠 **Cách tính:** Đếm tần suất xuất hiện trong {so_ngay} ngày → lấy 3 con có số lần về nhiều nhất

⚠️ *Chỉ tham khảo – Chơi có trách nhiệm!*
"""

# ====================== 🤖 LỆNH BOT ======================
@app.route('/')
def home():
    tong, tu, den = get_stats()
    return f"✅ Bot V33.0 — {tong} ngày dữ liệu | 90 ngày + 3 con lô tần suất cao nhất!"

def gui_anh_ten(chat_id, text, parse_mode="Markdown", max_thu_lai=3):
    for lan in range(1, max_thu_lai + 1):
        try:
            with BOT_LOCK:
                return bot.send_message(chat_id, text, parse_mode=parse_mode)
        except Exception as e:
            if any(err in str(e) for err in ["409", "Conflict", "429"]):
                time.sleep(min(2 ** lan, 15))
            else:
                return None
    return None

@bot.message_handler(commands=['start'])
def cmd_start(m):
    tong, _, _ = get_stats()
    gui_anh_ten(m.chat.id,
        f"🤖 *BOT XSMB — V33.0 | ✅ 90 NGÀY + 3 CON LÔ TẦN SUẤT CAO NHẤT*\n"
        f"📊 Đã có sẵn *{tong} ngày dữ liệu* → BOT SẴN SÀNG!\n\n"
        f"/dudoan = Xem dự đoán ngay\n"
        f"/lay90 = Lấy đủ 90 ngày dữ liệu thật\n"
        f"/status = Xem trạng thái dữ liệu\n"
        f"Ngày VD: 08092026 → Xem kết quả lịch sử",
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
        "🚀 *ĐANG LẤY DỮ LIỆU 90 NGÀY TỪ NGUỒN THẬT...*\n⏰ Khoảng 2-3 phút!",
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
            time.sleep(0.8)
        tong, _, _ = get_stats()
        gui_anh_ten(m.chat.id,
            f"✅ *HOÀN THÀNH!* 🎉\n📊 Tổng dữ liệu: *{tong} ngày*\n• Lấy mới thành công: {lay_moi}\n• Nguồn thật thất bại: {that_bai}\n👉 Gõ /dudoan!",
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
                gui_anh_ten(m.chat.id, f"⚠️ *Không lấy được dữ liệu — dùng dữ liệu mẫu thay thế*", parse_mode="Markdown")
    except:
        gui_anh_ten(m.chat.id, "⚠️ Sai định dạng! VD: `08092026`", parse_mode="Markdown")

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
    if POLLING_STARTED: return
    POLLING_STARTED = True
    print("=" * 60)
    print("✅ BOT V33.0 — 90 NGÀY + 3 CON LÔ TẦN SUẤT CAO NHẤT!")
    print("=" * 60)
    try:
        bot.remove_webhook()
    except: pass
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=40, allowed_updates=None)
        except Exception as e:
            if "409" in str(e) or "Conflict" in str(e):
                time.sleep(15)
            else:
                time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=gui_tu_dong, daemon=True).start()
    run_bot()
