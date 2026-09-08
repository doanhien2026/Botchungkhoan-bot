# ==========================================================
# xsmb_bot2.py — V37.2 | ✅ DỰ ĐOÁN NGÀY MAI (D+1) + SỬA LỖI TỶ LỆ
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
MIN_DAYS_FOR_PREDICT = 30  # Yêu cầu ít nhất 30 ngày dữ liệu mới dự đoán
SEND_RESULT_TIME = "18:40"   # Gửi kết quả ngày D
SEND_PREDICT_TIME = "18:41"  # Gửi dự đoán ngày D+1

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
}

BOT_LOCK = threading.Lock()
POLLING_STARTED = False

# ====================== 📅 HÀM LẤY NGÀY DỰ ĐOÁN ======================
def get_ngay_du_doan():
    """Trả về ngày D+1 — ngày dự đoán (ngày mai)"""
    return (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")

def get_ngay_hom_nay():
    """Trả về ngày D — hôm nay (ngày có kết quả)"""
    return datetime.now().strftime("%d/%m/%Y")

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

def luu_ket_qua(ngay_str, special, g1, loto, source="api", verified=False):
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", ngay_str): return False
    if not special or len(special)!=5 or not special.isdigit(): return False
    if not g1 or len(g1)!=5 or not g1.isdigit(): return False
    if not loto or len(loto) < 5: return False
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

# ====================== 📡 LẤY DỮ LIỆU — 2 NGUỒN ======================
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

    # Nguồn 1
    kq_1 = None
    try:
        url = f"https://xoso.com.vn/xsmb/{ymd_short}.html"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            db = re.search(r'Đặc biệt.*?(\d{5})', resp.text)
            g1 = re.search(r'Giải nhất.*?(\d{5})', resp.text)
            if db and g1:
                all_5digit = re.findall(r'\b\d{5}\b', resp.text)
                loto = sorted(list(set([n[-2:] for n in all_5digit if len(n)==5])))
                if len(loto)>=5:
                    kq_1 = {"special":db.group(1),"g1":g1.group(1),"loto":loto,"source":"xoso.com.vn"}
    except: pass

    # Nguồn 2
    kq_2 = None
    try:
        url = f"https://kqxs.vn/xsmb/ngay-{ymd}"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            db = re.search(r'Đặc biệt.*?(\d{5})', resp.text)
            g1 = re.search(r'Giải nhất.*?(\d{5})', resp.text)
            if db and g1:
                all_5digit = re.findall(r'\b\d{5}\b', resp.text)
                loto = sorted(list(set([n[-2:] for n in all_5digit if len(n)==5])))
                if len(loto)>=5:
                    kq_2 = {"special":db.group(1),"g1":g1.group(1),"loto":loto,"source":"kqxs.vn"}
    except: pass

    if kq_1 and kq_2:
        if kq_1["special"] == kq_2["special"] and kq_1["g1"] == kq_2["g1"]:
            return {**kq_1, "verified": True}
        return None
    return kq_1 or kq_2 or None

# ====================== 📊 DỰ ĐOÁN — NGÀY MAI (D+1) ======================
def tinh_du_doan():
    data = load_data()
    tong = len(data)
    ngay_du_doan = get_ngay_du_doan()  # ✅ LẤY NGÀY MAI

    # Yêu cầu đủ dữ liệu
    if tong < MIN_DAYS_FOR_PREDICT:
        return f"""⚠️ CHƯA ĐỦ DỮ LIỆU ĐỂ DỰ ĐOÁN NGÀY {ngay_du_doan}!
👉 Hiện có: {tong} ngày | Yêu cầu ít nhất: {MIN_DAYS_FOR_PREDICT} ngày
👉 Gõ /lay90 để lấy đủ dữ liệu thật từ nguồn chính xác!
❌ KHÔNG dự đoán khi dữ liệu chưa đủ — tránh kết quả sai lệch!"""

    PHAN_TICH_NGAY = min(ANALYSIS_DAYS, tong)
    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    ds = sap_xep[:PHAN_TICH_NGAY]

    ds_xac_minh = [ng for ng in ds if data[ng].get("verified",False)]
    if len(ds_xac_minh) >= MIN_DAYS_FOR_PREDICT:
        ds, so_ngay = ds_xac_minh, len(ds_xac_minh)
        nguon_thong_bao = f" (chỉ dùng {so_ngay} ngày đã xác minh 2 nguồn)"
    else:
        so_ngay = len(ds)
        nguon_thong_bao = f" (cảnh báo: {len(ds_xac_minh)}/{so_ngay} ngày đã xác minh)"

    # === Đếm tần suất lô ===
    dem_lo = {}
    tat_ca_dau_de = []
    for ngay in ds:
        kq = data[ngay]
        for lo in kq.get("loto", []):
            if len(lo) == 2 and lo.isdigit():
                if lo not in dem_lo: dem_lo[lo] = []
                dem_lo[lo].append(ngay)
        db = kq.get("special", "")
        if len(db) == 5 and db.isdigit():
            tat_ca_dau_de.append(db[0])
            lo_de = db[-2:]
            if lo_de not in dem_lo: dem_lo[lo_de] = []
            dem_lo[lo_de].append(ngay)

    if not dem_lo:
        return "⚠️ Dữ liệu lô trống. Gõ /lay90 trước!"

    # === TÍNH THÔNG TIN + SỬA LỖI TỶ LỆ ===
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

    # SẮP XẾP: ÍT lần nhất → nghỉ dài nhất
    ds_thong_tin.sort(key=lambda x: (x["lan"], -x["nghi"]))

    # Kiểm tra nếu tất cả con có tần suất giống nhau → chưa đủ dữ liệu
    if len(ds_thong_tin) >= 5:
        ty_le_cung = all(abs(x["ty_le"] - ds_thong_tin[0]["ty_le"]) < 0.5 for x in ds_thong_tin[:5])
        if ty_le_cung:
            return f"""⚠️ DỮ LIỆU CHƯA ĐỦ ĐỂ PHÂN TÍCH CHÍNH XÁC!
👉 Tất cả các con lô đều có tần suất gần như giống nhau → chưa đủ ngày để phân biệt
👉 Hiện có {so_ngay} ngày — cần thêm dữ liệu mới có thể phân tích "con ít ra nhất"
👉 Tiếp tục gõ /lay90 để lấy đủ dữ liệu!"""

    pool = ds_thong_tin[:15]  # Top 15 con ít ra nhất

    # === 🎲 NGẪU NHIÊN CÓ TRỌNG SỐ ===
    tong_trong_so = sum((x["nghi"] + 1) ** 2 / (x["lan"] + 1) for x in pool)
    xac_suat = [(x, (x["nghi"] + 1) ** 2 / (x["lan"] + 1) / tong_trong_so) for x in pool]

    da_chon = []
    while len(da_chon) < 3 and xac_suat:
        r = random.random()
        tich = 0
        for i, (item, p) in enumerate(xac_suat):
            tich += p
            if r <= tich:
                da_chon.append(item)
                xac_suat.pop(i)
                if xac_suat:
                    tong_moi = sum(pp for _, pp in xac_suat)
                    xac_suat = [(it, pp / tong_moi) for it, pp in xac_suat]
                break

    while len(da_chon) < 3:
        for x in ds_thong_tin:
            if x not in da_chon:
                da_chon.append(x)
                break

    top3 = da_chon[:3]
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3) >= 2 else ["00", "01"]

    # === Đầu số đề — ít xuất hiện nhất ===
    dau_de, ty_le_dau, dau_count = "9", 20.0, 1
    if tat_ca_dau_de:
        cnt = Counter(tat_ca_dau_de)
        # Lấy 5 đầu số ít ra nhất → chọn ngẫu nhiên có trọng số
        pool_dau = sorted(cnt.items(), key=lambda x: x[1])[:5]
        tong_ts = sum(1/(c+0.5) for _, c in pool_dau)
        r = random.random()
        tich = 0
        for d, c in pool_dau:
            tich += (1/(c+0.5)) / tong_ts
            if r <= tich:
                dau_de = d
                dau_count = c
                ty_le_dau = round(c / len(tat_ca_dau_de) * 100, 1)
                break

    # ==========================================================
    # ✅ GHI RÕ NGÀY DỰ ĐOÁN LÀ NGÀY MAI (D+1)
    # ==========================================================
    return f"""
🎲 **DỰ ĐOÁN KẾT QUẢ NGÀY — {ngay_du_doan} (NGÀY MAI / D+1)**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Phân tích dựa trên {so_ngay} ngày dữ liệu thật{nguon_thong_bao}

🎯 **3 CON LÔ ÍT XUẤT HIỆN NHẤT (sắp ra):**
   (Sắp xếp theo: tần suất thấp nhất → nghỉ dài nhất)
   1. `{top3[0]['so']}` – {top3[0]['lan']}/{so_ngay} ngày → tỷ lệ {top3[0]['ty_le']}%
      → Gần nhất: {top3[0]['ngay_gan_nhat']} | Đã nghỉ {top3[0]['nghi']} ngày
   2. `{top3[1]['so']}` – {top3[1]['lan']}/{so_ngay} ngày → tỷ lệ {top3[1]['ty_le']}%
      → Gần nhất: {top3[1]['ngay_gan_nhat']} | Đã nghỉ {top3[1]['nghi']} ngày
   3. `{top3[2]['so']}` – {top3[2]['lan']}/{so_ngay} ngày → tỷ lệ {top3[2]['ty_le']}%
      → Gần nhất: {top3[2]['ngay_gan_nhat']} | Đã nghỉ {top3[2]['nghi']} ngày

🔄 **1 CẶP LÔ XIÊN:**
   → Kết hợp 2 con ít ra nhất: `{xien[0]} - {xien[1]}`

🔢 **DỰ KIẾN ĐẦU SỐ ĐỀ:**
   → Đầu số `{dau_de}` – xuất hiện {dau_count} lần / {len(tat_ca_dau_de)} ngày → {ty_le_dau}%

🧠 **Logic:** {so_ngay} ngày dữ liệu thật → lọc con ít ra + nghỉ dài → ngẫu nhiên có trọng số
⚠️ *Dự đoán cho ngày {ngay_du_doan} — Chỉ tham khảo, chơi có trách nhiệm!*
"""

# ====================== 🤖 LỆNH BOT ======================
@app.route('/')
def home():
    tong, tu, den, verified = get_stats()
    return f"✅ V37.2 — Dự đoán ngày mai (D+1) | {tong} ngày | {verified} ngày xác minh | ≥{MIN_DAYS_FOR_PREDICT} ngày để dự đoán!"

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
    tong, _, _, verified = get_stats()
    gui_anh_ten(m.chat.id,
        f"🤖 *BOT XSMB — V37.2 | ✅ DỰ ĐOÁN NGÀY MAI (D+1)*\n"
        f"📊 Tổng: *{tong} ngày* | Đã xác minh: *{verified} ngày*\n"
        f"⚠️ Cần ít nhất *{MIN_DAYS_FOR_PREDICT} ngày* để dự đoán chính xác!\n\n"
        f"/dudoan = Dự đoán ngày mai (D+1)\n"
        f"/lay90 = Lấy 90 ngày dữ liệu thật\n"
        f"/status = Xem trạng thái dữ liệu\n"
        f"VD: 08092026 → Xem kết quả lịch sử",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    tong, tu, den, verified = get_stats()
    gui_anh_ten(m.chat.id,
        f"📊 *TRẠNG THÁI DỮ LIỆU*\n"
        f"• Tổng ngày: *{tong} ngày* (Cần ≥{MIN_DAYS_FOR_PREDICT} để dự đoán)\n"
        f"• Đã xác minh 2 nguồn: *{verified} ngày*\n"
        f"• Phạm vi: {tu} → {den}\n"
        f"✅ Dự đoán tự động cho NGÀY MAI (D+1) — KHÔNG tạo số giả!",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['lay90'])
def cmd_lay90(m):
    gui_anh_ten(m.chat.id,
        f"🚀 *ĐANG LẤY DỮ LIỆU THẬT TỪ 2 NGUỒN...*\n"
        f"✅ Mục tiêu: lấy đủ {ANALYSIS_DAYS} ngày\n"
        f"⚠️ Cần ít nhất {MIN_DAYS_FOR_PREDICT} ngày để dự đoán ngày mai chính xác!\n⏰ Khoảng 3-5 phút...",
        parse_mode="Markdown"
    )
    def lay_async():
        today = datetime.now()
        data_hien = load_data()
        lay_moi = da_co = that_bai = da_xac_minh = 0

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
                    if kq.get("verified", False): da_xac_minh += 1
                    data_hien = load_data()
                else: that_bai += 1
            else:
                that_bai += 1

            time.sleep(1.0)

        tong, _, _, verified = get_stats()
        gui_anh_ten(m.chat.id,
            f"✅ *HOÀN THÀNH LẤY DỮ LIỆU!* 🎉\n"
            f"📊 Tổng: *{tong} ngày* | Đã xác minh: *{verified} ngày*\n"
            f"• Đã có sẵn: {da_co} | Lấy mới: {lay_moi} | Xác minh: {da_xac_minh}\n"
            f"⚠️ {'✅ ĐỦ dữ liệu → Gõ /dudoan xem dự đoán NGÀY MAI!' if tong >= MIN_DAYS_FOR_PREDICT else f'⚠️ CHƯA ĐỦ — Cần thêm {MIN_DAYS_FOR_PREDICT - tong} ngày nữa!'}",
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
            tt = "✅ ĐÃ XÁC MINH 2 NGUỒN" if kq.get("verified", False) else "📝 Đã lưu từ 1 nguồn"
            gui_anh_ten(m.chat.id,
                f"📅 *KẾT QUẢ NGÀY: {date_str}*\n"
                f"🏆 ĐB: `{kq['special']}`\n"
                f"🥇 G1: `{kq['g1']}`\n"
                f"📌 Nguồn: {kq.get('source')} | {tt}",
                parse_mode="Markdown"
            )
        else:
            gui_anh_ten(m.chat.id, f"🔍 *ĐANG LẤY DỮ LIỆU NGÀY {date_str}...*", parse_mode="Markdown")
            kq = lay_ket_qua_ngay(date_str)
            if kq and luu_ket_qua(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"], kq.get("verified", False)):
                tt = "✅ ĐÃ XÁC MINH" if kq.get("verified", False) else "📝 Đã lưu từ 1 nguồn"
                gui_anh_ten(m.chat.id,
                    f"✅ *ĐÃ LẤY DỮ LIỆU THẬT!* 🎉\n📅 {date_str}\n🏆 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n📌 {tt}",
                    parse_mode="Markdown"
                )
            else:
                gui_anh_ten(m.chat.id,
                    f"⚠️ *KHÔNG LẤY ĐƯỢC DỮ LIỆU NGÀY {date_str}*\n❌ Bot KHÔNG tạo số giả!",
                    parse_mode="Markdown"
                )
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

            # 18:40 → Gửi kết quả ngày hôm nay (D)
            if gio == SEND_RESULT_TIME and hom_nay not in da_gui_kq:
                kq = lay_ket_qua_ngay(hom_nay)
                if kq and luu_ket_qua(hom_nay, kq["special"], kq["g1"], kq["loto"], kq["source"], kq.get("verified", False)):
                    tt = "✅ Đã xác minh" if kq.get("verified", False) else "📝 Đã lưu"
                    gui_anh_ten(CHAT_ID,
                        f"🏆 *KẾT QUẢ NGÀY HÔM NAY — {hom_nay} (D)*\n"
                        f"🎯 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n📌 {tt}",
                        parse_mode="Markdown"
                    )
                da_gui_kq.add(hom_nay)

            # 18:41 → Gửi dự đoán NGÀY MAI (D+1)
            if gio == SEND_PREDICT_TIME and hom_nay not in da_gui_dd:
                gui_anh_ten(CHAT_ID,
                    f"🔮 *TỰ ĐỘNG DỰ ĐOÁN — NGÀY MAI {ngay_mai} (D+1)*\n" + tinh_du_doan(),
                    parse_mode="Markdown"
                )
                da_gui_dd.add(hom_nay)

            time.sleep(30)
        except Exception as e:
            print(f"⚠️ Lỗi tự động gửi: {e}"); time.sleep(10)

# ====================== 🚀 CHẠY BOT ======================
def run_bot():
    global POLLING_STARTED
    if POLLING_STARTED: return
    POLLING_STARTED = True
    print("="*60)
    print("✅ V37.2 — DỰ ĐOÁN NGÀY MAI (D+1) | SỬA LỖI TỶ LỆ!")
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
