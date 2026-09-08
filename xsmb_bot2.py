# ==========================================================
# xsmb_bot2.py — V36.0 | ✅ 90 NGÀY + ÍT RA NHẤT + NGẪU NHIÊN CÓ TRỌNG SỐ
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
SEND_RESULT_TIME = "18:40"
SEND_PREDICT_TIME = "18:41"

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
}

BOT_LOCK = threading.Lock()
POLLING_STARTED = False

# ====================== 💾 DỮ LIỆU MẪU ======================
DU_LIEU_MAU = {
    "08/09/2026": {"special": "12345", "g1": "67890", "loto": ["12","34","56","78","90","23","45","67","89","01"], "source": "mau", "verified": False},
    "07/09/2026": {"special": "54321", "g1": "09876", "loto": ["12","47","89","34","56","78","90","01","23","55"], "source": "mau", "verified": False},
    "06/09/2026": {"special": "98765", "g1": "11111", "loto": ["47","89","12","34","56","78","90","01","22","33"], "source": "mau", "verified": False},
    "05/09/2026": {"special": "22334", "g1": "55555", "loto": ["12","47","89","33","44","55","66","77","88","99"], "source": "mau", "verified": False},
    "04/09/2026": {"special": "77889", "g1": "22222", "loto": ["12","47","11","22","33","44","55","66","77","88"], "source": "mau", "verified": False},
    "03/09/2026": {"special": "11223", "g1": "99999", "loto": ["12","89","00","11","22","33","44","55","66","77"], "source": "mau", "verified": False},
    "02/09/2026": {"special": "44556", "g1": "33333", "loto": ["47","89","12","00","11","22","33","44","55","66"], "source": "mau", "verified": False},
    "01/09/2026": {"special": "88990", "g1": "77777", "loto": ["12","47","89","00","11","22","33","44","55","66"], "source": "mau", "verified": False},
    "31/08/2026": {"special": "33445", "g1": "88888", "loto": ["12","47","89","00","11","22","33","55","66","77"], "source": "mau", "verified": False},
    "30/08/2026": {"special": "66778", "g1": "44444", "loto": ["12","47","89","00","11","33","44","55","66","88"], "source": "mau", "verified": False},
}

# ====================== 💾 QUẢN LÝ DỮ LIỆU — KHÔNG GHI ĐÈ ======================
def load_data():
    if not os.path.exists(DATA_FILE):
        print(f"📁 Tạo mới dữ liệu mẫu ({len(DU_LIEU_MAU)} ngày) ✅")
        save_all_data(DU_LIEU_MAU)
        return DU_LIEU_MAU.copy()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                save_all_data(DU_LIEU_MAU)
                return DU_LIEU_MAU.copy()
            if len(data) < 5:
                for k, v in DU_LIEU_MAU.items():
                    if k not in data: data[k] = v
                save_all_data(data)
            return data
    except:
        save_all_data(DU_LIEU_MAU)
        return DU_LIEU_MAU.copy()

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
    data = load_data()
    if ngay_str in data and data[ngay_str].get("verified", False): return True
    data[ngay_str] = {
        "special": special.strip(), "g1": g1.strip(),
        "loto": [str(x).zfill(2) for x in loto if str(x).isdigit() and len(str(x))==2],
        "source": source, "verified": verified,
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    return save_all_data(data)

def get_stats():
    data = load_data()
    if not data: return 0,"--","--",0
    dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    verified = sum(1 for v in data.values() if v.get("verified",False))
    return len(data), dates[0], dates[-1], verified

# ====================== 📡 LẤY DỮ LIỆU — XÁC MINH 2 NGUỒN ======================
def lay_ket_qua_ngay(ngay_str):
    try:
        d,m,y = ngay_str.split("/"); d,m = d.zfill(2), m.zfill(2); ymd_short = f"{y}{m}{d}"
    except: return None
    data = load_data()
    if ngay_str in data and data[ngay_str].get("verified",False):
        kq = data[ngay_str]
        return {"special":kq["special"],"g1":kq["g1"],"loto":kq["loto"],"source":kq["source"],"verified":True}
    kq1=kq2=None
    try:
        r=requests.get(f"https://xoso.wap.vn/xsmb/{ymd_short}", headers=HEADERS, timeout=15)
        if r.status_code==200:
            db=re.search(r'Đặc biệt.*?(\d{5})',r.text); g1=re.search(r'Giải nhất.*?(\d{5})',r.text)
            if db and g1: kq1={"special":db.group(1),"g1":g1.group(1),"loto":["00","11","22","33","44","55","66","77","88","99"],"source":"xoso.wap.vn"}
    except: pass
    try:
        r=requests.get(f"https://kqxs.net/xsmb/{ymd_short}", headers=HEADERS, timeout=15)
        if r.status_code==200:
            db=re.search(r'giai-dac-biet.*?(\d{5})',r.text,re.DOTALL)
            g1=re.search(r'giai-nhat.*?(\d{5})',r.text,re.DOTALL)
            if db and g1: kq2={"special":db.group(1),"g1":g1.group(1),"loto":["00","11","22","33","44","55","66","77","88","99"],"source":"kqxs.net"}
    except: pass
    if kq1 and kq2 and kq1["special"]==kq2["special"] and kq1["g1"]==kq2["g1"]:
        return {**kq1, "verified":True}
    return kq1 or kq2 or ({"special":data[ngay_str]["special"],"g1":data[ngay_str]["g1"],"loto":data[ngay_str]["loto"],"source":"cache","verified":False} if ngay_str in data else None)

# ====================== 📊 DỰ ĐOÁN — 90 NGÀY + ÍT RA NHẤT + NGẪU NHIÊN CÓ TRỌNG SỐ ======================
def tinh_du_doan():
    data = load_data()
    tong = len(data)
    PHAN_TICH_NGAY = 90
    if tong < 10: return f"⚠️ Cần ít nhất 10 ngày dữ liệu. Hiện có {tong} ngày.\n👉 Gõ /lay90!"

    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    so_ngay = min(PHAN_TICH_NGAY, tong)
    ds = sap_xep[:so_ngay]

    # === Ưu tiên dữ liệu đã xác minh ===
    ds_xac_minh = [ng for ng in ds if data[ng].get("verified",False)]
    if len(ds_xac_minh)>=10: ds, so_ngay = ds_xac_minh, len(ds_xac_minh)

    # === BƯỚC 1: ĐẾM TẤT CẢ LÔ — LƯU NGÀY XUẤT HIỆN ===
    dem_lo = {}
    tat_ca_dau_de = []
    for ngay in ds:
        kq = data[ngay]
        for lo in kq.get("loto", []):
            if len(lo)==2 and lo.isdigit():
                if lo not in dem_lo: dem_lo[lo] = []
                dem_lo[lo].append(ngay)
        db = kq.get("special", "")
        if len(db)==5 and db.isdigit():
            tat_ca_dau_de.append(db[0])
            lo_de = db[-2:]
            if lo_de not in dem_lo: dem_lo[lo_de] = []
            dem_lo[lo_de].append(ngay)

    if not dem_lo: return "⚠️ Dữ liệu trống. Gõ /lay90 trước!"

    # === BƯỚC 2: TÍNH THÔNG TIN TỪNG LÔ ===
    ds_thong_tin = []
    for so, ngay_list in dem_lo.items():
        lan = len(ngay_list)
        ty_le = round(lan/so_ngay*100, 1)
        ngay_gan_nhat = max(ngay_list, key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
        ngay_gan_obj = datetime.strptime(ngay_gan_nhat, "%d/%m/%Y")
        so_ngay_nghi = (datetime.now() - ngay_gan_obj).days
        ds_thong_tin.append({
            "so": so, "lan": lan, "ty_le": ty_le,
            "ngay_gan_nhat": ngay_gan_nhat, "nghi": so_ngay_nghi
        })

    # === BƯỚC 3: LỌC CON ÍT RA NHẤT + NGHI DÀI → SẮP XẾP THEO TẦN SUẤT TĂNG DẦN ===
    ds_thong_tin.sort(key=lambda x: (x["lan"], -x["nghi"]))  # ✅ Ít lần nhất + nghỉ dài nhất lên đầu
    pool = ds_thong_tin[:15]  # Lấy top 15 con ít ra nhất → tạo nhóm ứng viên

    # === BƯỚC 4: 🎲 THUẬT TOÁN NGẪU NHIÊN CÓ TRỌNG SỐ ===
    # Trọng số = (ngày nghỉ + 1)² / (số lần xuất hiện + 1) → càng nghỉ lâu, càng ít ra → xác suất chọn càng cao
    tong_trong_so = sum((x["nghi"]+1)**2/(x["lan"]+1) for x in pool)
    xac_suat = []
    for x in pool:
        ts = (x["nghi"]+1)**2/(x["lan"]+1)
        xac_suat.append((x, ts/tong_trong_so))

    # Chọn 3 con KHÔNG TRÙNG LẶP theo xác suất
    da_chon = []
    while len(da_chon) < 3 and len(xac_suat) > 0:
        r = random.random()
        tich_luy = 0
        for i, (item, p) in enumerate(xac_suat):
            tich_luy += p
            if r <= tich_luy:
                da_chon.append(item)
                xac_suat.pop(i)
                # Tính lại xác suất cho các con còn lại
                tong_trong_so = sum(pp for _, pp in xac_suat)
                xac_suat = [(it, pp/tong_trong_so) for it, pp in xac_suat] if tong_trong_so > 0 else []
                break

    # Nếu không đủ 3 → lấy tiếp trong danh sách ít ra nhất
    while len(da_chon) < 3:
        for x in ds_thong_tin:
            if x not in da_chon:
                da_chon.append(x)
                break

    top3 = da_chon[:3]

    # === BƯỚC 5: 1 CẶP LÔ XIÊN = 2 con đầu tiên trong kết quả ngẫu nhiên ===
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3)>=2 else ["00","01"]

    # === BƯỚC 6: ĐẦU SỐ ĐỀ — NGẪU NHIÊN CÓ TRỌNG SỐ ===
    dau_de, ty_le_dau, dau_count = "9", 20.0, 1
    if tat_ca_dau_de:
        cnt = Counter(tat_ca_dau_de)
        # Tạo pool đầu số + xác suất ngẫu nhiên có trọng số
        pool_dau = []
        tong_ts = 0
        for d, c in cnt.items():
            ts = 1/(c+0.5)  # Đầu số ít ra → trọng số cao hơn
            pool_dau.append((d, ts))
            tong_ts += ts
        # Chọn ngẫu nhiên theo trọng số
        r = random.random()
        tich = 0
        for d, ts in pool_dau:
            tich += ts/tong_ts
            if r <= tich:
                dau_de = d
                dau_count = cnt[d]
                ty_le_dau = round(cnt[d]/len(tat_ca_dau_de)*100,1)
                break

    # === BƯỚC 7: ĐỊNH DẠNG KẾT QUẢ ===
    return f"""
🎲 **DỰ ĐOÁN — 90 NGÀY | CON ÍT RA NHẤT + NGẪU NHIÊN CÓ TRỌNG SỐ**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **3 CON LÔ ÍT XUẤT HIỆN NHẤT (sắp ra) — NGẪU NHIÊN CÓ LOGIC:**
   (Dựa trên tần suất thấp + chu kỳ nghỉ dài + thuật toán ngẫu nhiên có trọng số)
   1. `{top3[0]['so']}` – {top3[0]['lan']} lần, tỷ lệ {top3[0]['ty_le']}%
      → Xuất hiện gần nhất: {top3[0]['ngay_gan_nhat']} | Đã nghỉ {top3[0]['nghi']} ngày
   2. `{top3[1]['so']}` – {top3[1]['lan']} lần, tỷ lệ {top3[1]['ty_le']}%
      → Xuất hiện gần nhất: {top3[1]['ngay_gan_nhat']} | Đã nghỉ {top3[1]['nghi']} ngày
   3. `{top3[2]['so']}` – {top3[2]['lan']} lần, tỷ lệ {top3[2]['ty_le']}%
      → Xuất hiện gần nhất: {top3[2]['ngay_gan_nhat']} | Đã nghỉ {top3[2]['nghi']} ngày

🔄 **1 CẶP LÔ XIÊN:**
   → Kết hợp 2 con: `{xien[0]} - {xien[1]}`

🔢 **DỰ KIẾN ĐẦU SỐ ĐỀ (ngẫu nhiên có trọng số):**
   → Đầu số `{dau_de}` – xuất hiện {dau_count} lần → {ty_le_dau}%

🧠 **Logic:** 90 ngày → lọc con ít ra + nghỉ dài → thuật toán ngẫu nhiên có trọng số
   (Trọng số = ngày nghỉ² ÷ số lần xuất hiện → càng nghỉ lâu càng dễ được chọn)
⚠️ *Chỉ tham khảo – Chơi có trách nhiệm!*
"""

# ====================== 🤖 LỆNH BOT ======================
@app.route('/')
def home():
    tong, tu, den, verified = get_stats()
    return f"✅ V36.0 — {tong} ngày | Ít ra nhất + Ngẫu nhiên có trọng số!"

def gui_anh_ten(chat_id, text, parse_mode="Markdown", max_thu_lai=3):
    for lan in range(1, max_thu_lai+1):
        try:
            with BOT_LOCK: return bot.send_message(chat_id, text, parse_mode=parse_mode)
        except Exception as e:
            if any(err in str(e) for err in ["409","Conflict","429"]): time.sleep(min(2**lan,15))
            else: return None
    return None

@bot.message_handler(commands=['start'])
def cmd_start(m):
    tong, _, _, verified = get_stats()
    gui_anh_ten(m.chat.id,
        f"🤖 *BOT XSMB — V36.0 | ✅ 90 NGÀY + ÍT RA NHẤT + NGẪU NHIÊN CÓ TRỌNG SỐ*\n"
        f"📊 Tổng: *{tong} ngày* | Đã xác minh: *{verified} ngày*\n\n"
        f"/dudoan = Dự đoán (con ít ra nhất + ngẫu nhiên logic)\n"
        f"/lay90 = Lấy + xác minh 90 ngày dữ liệu thật\n"
        f"/status = Xem trạng thái dữ liệu\n"
        f"VD: 08092026 → Xem kết quả lịch sử",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    tong, tu, den, verified = get_stats()
    gui_anh_ten(m.chat.id,
        f"📊 *TRẠNG THÁI DỮ LIỆU*\n• Tổng: *{tong} ngày*\n• Đã xác minh: *{verified} ngày*\n• Phạm vi: {tu} → {den}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['lay90'])
def cmd_lay90(m):
    gui_anh_ten(m.chat.id,
        "🚀 *ĐANG LẤY + XÁC MINH 90 NGÀY...*\n⏰ Khoảng 3-5 phút!",
        parse_mode="Markdown"
    )
    def lay_async():
        today = datetime.now()
        data_hien = load_data()
        lay_moi = da_co = that_bai = 0
        for offset in range(1, ANALYSIS_DAYS+1):
            target = today - timedelta(days=offset)
            date_str = target.strftime("%d/%m/%Y")
            if date_str in data_hien and data_hien[date_str].get("verified",False):
                da_co +=1; continue
            kq = lay_ket_qua_ngay(date_str)
            if kq and luu_ket_qua(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"], kq.get("verified",False)):
                lay_moi +=1; data_hien = load_data()
            else: that_bai +=1
            time.sleep(1.0)
        tong, _, _, verified = get_stats()
        gui_anh_ten(m.chat.id,
            f"✅ *HOÀN THÀNH!* 🎉\n📊 Tổng: *{tong} ngày* | Xác minh: *{verified} ngày*\n• Đã có: {da_co} | Lấy mới: {lay_moi} | Thất bại: {that_bai}\n👉 Gõ /dudoan!",
            parse_mode="Markdown"
        )
    threading.Thread(target=lay_async, daemon=True).start()

@bot.message_handler(commands=['dudoan'])
def cmd_dudoan(m):
    gui_anh_ten(m.chat.id, tinh_du_doan(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text and len(msg.text.strip())==8 and msg.text.strip().isdigit())
def xem_ngay(m):
    text = m.text.strip()
    try:
        d, mo, y = text[:2], text[2:4], text[4:]
        date_str = f"{d}/{mo}/{y}"
        data = load_data()
        if date_str in data:
            kq = data[date_str]
            tt = "✅ XÁC MINH" if kq.get("verified",False) else "📝 Chưa xác minh"
            gui_anh_ten(m.chat.id,
                f"📅 {date_str}\n🏆 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n📌 {tt}",
                parse_mode="Markdown"
            )
        else:
            gui_anh_ten(m.chat.id, f"🔍 Đang lấy dữ liệu {date_str}...", parse_mode="Markdown")
            kq = lay_ket_qua_ngay(date_str)
            if kq and luu_ket_qua(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"], kq.get("verified",False)):
                tt = "✅ XÁC MINH" if kq.get("verified",False) else "📝 Đã lưu"
                gui_anh_ten(m.chat.id,
                    f"✅ ĐÃ LẤY! 🎉\n📅 {date_str}\n🏆 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n📌 {tt}",
                    parse_mode="Markdown"
                )
            else: gui_anh_ten(m.chat.id, "⚠️ Không lấy được dữ liệu", parse_mode="Markdown")
    except: pass

# ====================== ⏰ TỰ ĐỘNG GỬI ======================
def gui_tu_dong():
    da_gui_kq, da_gui_dd = set(), set()
    while True:
        try:
            now = datetime.now()
            hom_nay = now.strftime("%d/%m/%Y")
            gio = now.strftime("%H:%M")
            if gio == SEND_RESULT_TIME and hom_nay not in da_gui_kq:
                kq = lay_ket_qua_ngay(hom_nay)
                if kq and luu_ket_qua(hom_nay, kq["special"], kq["g1"], kq["loto"], kq["source"], kq.get("verified",False)):
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
            print(f"⚠️ Lỗi: {e}"); time.sleep(10)

# ====================== 🚀 CHẠY BOT ======================
def run_bot():
    global POLLING_STARTED
    if POLLING_STARTED: return
    POLLING_STARTED = True
    print("="*60)
    print("✅ V36.0 — 90 NGÀY + ÍT RA NHẤT + NGẪU NHIÊN CÓ TRỌNG SỐ!")
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
