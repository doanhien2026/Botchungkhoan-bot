# ==========================================================
# xsmb_bot2.py — V37.0 | ✅ DỮ LIỆU CHÍNH XÁC + KHÔNG TẠO SỐ GIẢ
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
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
}

BOT_LOCK = threading.Lock()
POLLING_STARTED = False

# ====================== 💾 QUẢN LÝ DỮ LIỆU — KHÔNG TẠO SỐ GIẢ ======================
def load_data():
    if not os.path.exists(DATA_FILE):
        print(f"📁 Chưa có file dữ liệu → TẠO TRỐNG, KHÔNG DÙNG SỐ GIẢ!")
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                print(f"⚠️ File dữ liệu sai định dạng → Tạo trống mới")
                return {}
            return data
    except Exception as e:
        print(f"❌ Lỗi đọc {DATA_FILE}: {e} → Tạo trống mới")
        return {}

def save_all_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu file: {e}")
        return False

def luu_ket_qua(ngay_str, special, g1, loto, source="api", verified=False):
    """✅ LƯU DỮ LIỆU — CHỈ KHI ĐỦ ĐIỀU KIỆN, KHÔNG TẠO SỐ GIẢ"""
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", ngay_str):
        print(f"❌ Sai định dạng ngày: {ngay_str}")
        return False
    if not special or len(special) != 5 or not special.isdigit():
        print(f"❌ Đặc biệt không hợp lệ: {special}")
        return False
    if not g1 or len(g1) != 5 or not g1.isdigit():
        print(f"❌ Giải nhất không hợp lệ: {g1}")
        return False
    if not loto or len(loto) < 5:
        print(f"❌ Dữ liệu lô quá ít: {len(loto)}")
        return False

    data = load_data()

    # ✅ ĐÃ CÓ DỮ LIỆU XÁC MINH → KHÔNG GHI ĐÈ
    if ngay_str in data and data[ngay_str].get("verified", False):
        print(f"ℹ️ {ngay_str} đã có dữ liệu xác minh → KHÔNG GHI ĐÈ")
        return True

    data[ngay_str] = {
        "special": special.strip(),
        "g1": g1.strip(),
        "loto": [str(x).zfill(2) for x in loto if str(x).isdigit() and len(str(x)) == 2],
        "source": source,
        "verified": verified,
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    ok = save_all_data(data)
    if ok:
        status = "✅ XÁC MINH" if verified else "📝 ĐÃ LƯU"
        print(f"{status}: {ngay_str} | ĐB:{special} G1:{g1} | Tổng: {len(data)} ngày")
    return ok

def get_stats():
    data = load_data()
    if not data: return 0, "--", "--", 0
    dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    verified = sum(1 for v in data.values() if v.get("verified", False))
    return len(data), dates[0], dates[-1], verified

# ====================== 📡 LẤY DỮ LIỆU — NGUỒN CHÍNH XÁC + KIỂM TRA CHẶT CHẼ ======================
def lay_ket_qua_ngay(ngay_str):
    """✅ Lấy kết quả 1 ngày — 2 NGUỒN ĐỘC LẬP + KIỂM TRA TRÙNG KHỚP + TỪ CHỐI DỮ LIỆU SAI"""
    try:
        d, m, y = ngay_str.split("/")
        d, m = d.zfill(2), m.zfill(2)
        ymd = f"{y}-{m}-{d}"
        ymd_short = f"{y}{m}{d}"
    except Exception as e:
        print(f"❌ Sai định dạng ngày {ngay_str}: {e}")
        return None

    # ✅ ĐÃ CÓ DỮ LIỆU → DÙNG DỮ LIỆU ĐÃ LƯU
    data = load_data()
    if ngay_str in data:
        kq = data[ngay_str]
        print(f"ℹ️ {ngay_str} → dùng dữ liệu đã lưu ({kq.get('source')})")
        return {
            "special": kq["special"],
            "g1": kq["g1"],
            "loto": kq["loto"],
            "source": kq["source"],
            "verified": kq.get("verified", False)
        }

    # ========== NGUỒN 1: XOSO.VN (Nguồn đáng tin cậy) ==========
    kq_1 = None
    try:
        url = f"https://xoso.com.vn/xsmb/{ymd_short}.html"
        print(f"📡 NGUỒN 1: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            # Tìm Giải Đặc Biệt
            db_match = re.search(r'giari-dac-biet.*?<span[^>]*>(\d{5})</span>', resp.text, re.DOTALL | re.IGNORECASE)
            if not db_match:
                db_match = re.search(r'Đặc biệt.*?(\d{5})', resp.text)
            # Tìm Giải Nhất
            g1_match = re.search(r'giari-nhat.*?<span[^>]*>(\d{5})</span>', resp.text, re.DOTALL | re.IGNORECASE)
            if not g1_match:
                g1_match = re.search(r'Giải nhất.*?(\d{5})', resp.text)

            if db_match and g1_match:
                db = db_match.group(1)
                g1 = g1_match.group(1)
                # Lấy tất cả số 2 chữ số cuối → tạo danh sách lô
                all_5digit = re.findall(r'\b\d{5}\b', resp.text)
                loto = sorted(list(set([n[-2:] for n in all_5digit if n.isdigit() and len(n) == 5])))

                if len(db) == 5 and len(g1) == 5 and len(loto) >= 5:
                    kq_1 = {"special": db, "g1": g1, "loto": loto, "source": "xoso.com.vn"}
                    print(f"✅ NGUỒN 1 OK | ĐB:{db} G1:{g1} | {len(loto)} lô")
    except Exception as e:
        print(f"⚠️ Nguồn 1 lỗi: {str(e)[:80]}")

    # ========== NGUỒN 2: KQXS.VN ==========
    kq_2 = None
    try:
        url = f"https://kqxs.vn/xsmb/ngay-{ymd}"
        print(f"📡 NGUỒN 2: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            db_match = re.search(r'DacBiet.*?value="(\d{5})"', resp.text)
            if not db_match:
                db_match = re.search(r'Đặc biệt.*?(\d{5})', resp.text)
            g1_match = re.search(r'GiaiNhat.*?value="(\d{5})"', resp.text)
            if not g1_match:
                g1_match = re.search(r'Giải nhất.*?(\d{5})', resp.text)

            if db_match and g1_match:
                db = db_match.group(1)
                g1 = g1_match.group(1)
                all_5digit = re.findall(r'\b\d{5}\b', resp.text)
                loto = sorted(list(set([n[-2:] for n in all_5digit if n.isdigit() and len(n) == 5])))

                if len(db) == 5 and len(g1) == 5 and len(loto) >= 5:
                    kq_2 = {"special": db, "g1": g1, "loto": loto, "source": "kqxs.vn"}
                    print(f"✅ NGUỒN 2 OK | ĐB:{db} G1:{g1} | {len(loto)} lô")
    except Exception as e:
        print(f"⚠️ Nguồn 2 lỗi: {str(e)[:80]}")

    # ========== ✅ XÁC MINH: 2 NGUỒN TRÙNG KHỚP → LƯU ==========
    if kq_1 and kq_2:
        if kq_1["special"] == kq_2["special"] and kq_1["g1"] == kq_2["g1"]:
            print(f"✅✅ XÁC MINH THÀNH CÔNG — 2 NGUỒN TRÙNG KHỚP!")
            return {**kq_1, "verified": True}
        else:
            print(f"⚠️ 2 NGUỒN KHÔNG TRÙNG KHỚP → TỪ CHỐI LƯU, KHÔNG TẠO SỐ GIẢ!")
            return None

    # ========== CHỈ 1 NGUỒN → LƯU NHƯNG CHƯA XÁC MINH ==========
    if kq_1:
        print(f"ℹ️ Chỉ có nguồn 1 → lưu chưa xác minh")
        return {**kq_1, "verified": False}
    if kq_2:
        print(f"ℹ️ Chỉ có nguồn 2 → lưu chưa xác minh")
        return {**kq_2, "verified": False}

    # ❌ KHÔNG CÓ NGUỒN NÀO → KHÔNG TẠO SỐ GIẢ
    print(f"❌ TẤT CẢ NGUỒN THẤT BẠI — KHÔNG TẠO SỐ GIẢ!")
    return None

# ====================== 📊 DỰ ĐOÁN — 90 NGÀY + ÍT RA NHẤT + NGẪU NHIÊN CÓ TRỌNG SỐ ======================
def tinh_du_doan():
    data = load_data()
    tong = len(data)
    PHAN_TICH_NGAY = 90

    if tong < 10:
        return f"⚠️ Chưa có đủ dữ liệu! Hiện có {tong} ngày.\n👉 Gõ /lay90 để lấy dữ liệu thật từ nguồn chính xác!\n⚠️ KHÔNG DÙNG SỐ GIẢ — chỉ tính khi có dữ liệu thật!"

    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    so_ngay = min(PHAN_TICH_NGAY, tong)
    ds = sap_xep[:so_ngay]

    # Ưu tiên dữ liệu đã xác minh
    ds_xac_minh = [ng for ng in ds if data[ng].get("verified", False)]
    if len(ds_xac_minh) >= 10:
        ds, so_ngay = ds_xac_minh, len(ds_xac_minh)
        nguon_thong_bao = " (chỉ dùng dữ liệu đã xác minh 2 nguồn)"
    else:
        nguon_thong_bao = f" (cảnh báo: chỉ có {len(ds_xac_minh)} ngày đã xác minh, độ chính xác hạn chế)"

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

    # === Tính thông tin từng lô ===
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

    # === LỌC CON ÍT RA NHẤT + NGHI DÀI ===
    ds_thong_tin.sort(key=lambda x: (x["lan"], -x["nghi"]))
    pool = ds_thong_tin[:15]

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

    # === Đầu số đề ===
    dau_de, ty_le_dau, dau_count = "9", 20.0, 1
    if tat_ca_dau_de:
        cnt = Counter(tat_ca_dau_de)
        pool_dau = [(d, 1 / (c + 0.5)) for d, c in cnt.items()]
        tong_ts = sum(ts for _, ts in pool_dau)
        r = random.random()
        tich = 0
        for d, ts in pool_dau:
            tich += ts / tong_ts
            if r <= tich:
                dau_de = d
                dau_count = cnt[d]
                ty_le_dau = round(cnt[d] / len(tat_ca_dau_de) * 100, 1)
                break

    return f"""
🎲 **DỰ ĐOÁN — DỰA TRÊN {so_ngay} NGÀY DỮ LIỆU THẬT{nguon_thong_bao}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **3 CON LÔ ÍT XUẤT HIỆN NHẤT (sắp ra) — NGẪU NHIÊN CÓ LOGIC:**
   (Dữ liệu lấy từ nguồn chính xác, KHÔNG tạo số giả)
   1. `{top3[0]['so']}` – {top3[0]['lan']} lần, tỷ lệ {top3[0]['ty_le']}%
      → Xuất hiện gần nhất: {top3[0]['ngay_gan_nhat']} | Đã nghỉ {top3[0]['nghi']} ngày
   2. `{top3[1]['so']}` – {top3[1]['lan']} lần, tỷ lệ {top3[1]['ty_le']}%
      → Xuất hiện gần nhất: {top3[1]['ngay_gan_nhat']} | Đã nghỉ {top3[1]['nghi']} ngày
   3. `{top3[2]['so']}` – {top3[2]['lan']} lần, tỷ lệ {top3[2]['ty_le']}%
      → Xuất hiện gần nhất: {top3[2]['ngay_gan_nhat']} | Đã nghỉ {top3[2]['nghi']} ngày

🔄 **1 CẶP LÔ XIÊN:**
   → Kết hợp 2 con: `{xien[0]} - {xien[1]}`

🔢 **DỰ KIẾN ĐẦU SỐ ĐỀ:**
   → Đầu số `{dau_de}` – xuất hiện {dau_count} lần → {ty_le_dau}%

🧠 **Logic:** 90 ngày dữ liệu thật → lọc con ít ra + nghỉ dài → ngẫu nhiên có trọng số
⚠️ *Chỉ tham khảo – Chơi có trách nhiệm!*
"""

# ====================== 🤖 LỆNH BOT ======================
@app.route('/')
def home():
    tong, tu, den, verified = get_stats()
    return f"✅ V37.0 — {tong} ngày | {verified} ngày xác minh | KHÔNG TẠO SỐ GIẢ!"

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
        f"🤖 *BOT XSMB — V37.0 | ✅ DỮ LIỆU CHÍNH XÁC + KHÔNG TẠO SỐ GIẢ*\n"
        f"📊 Tổng: *{tong} ngày* | Đã xác minh: *{verified} ngày*\n\n"
        f"/dudoan = Dự đoán (dữ liệu thật, không tạo số giả)\n"
        f"/lay90 = Lấy 90 ngày từ 2 nguồn chính xác + xác minh\n"
        f"/status = Xem trạng thái dữ liệu\n"
        f"VD: 08092026 → Xem kết quả lịch sử",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    tong, tu, den, verified = get_stats()
    gui_anh_ten(m.chat.id,
        f"📊 *TRẠNG THÁI DỮ LIỆU*\n"
        f"• Tổng ngày: *{tong} ngày*\n"
        f"• Đã xác minh 2 nguồn: *{verified} ngày*\n"
        f"• Phạm vi: {tu} → {den}\n"
        f"✅ KHÔNG bao giờ tạo số giả hay dữ liệu ảo!",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['lay90'])
def cmd_lay90(m):
    gui_anh_ten(m.chat.id,
        "🚀 *ĐANG LẤY DỮ LIỆU THẬT TỪ 2 NGUỒN CHÍNH XÁC...*\n"
        "✅ Lấy từng ngày + Xác minh 2 nguồn + KHÔNG tạo số giả\n⏰ Khoảng 3-5 phút, vui lòng chờ!",
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
                print(f"⚠️ Bỏ qua {date_str} — không lấy được dữ liệu, KHÔNG tạo số giả!")

            time.sleep(1.2)

        tong, _, _, verified = get_stats()
        gui_anh_ten(m.chat.id,
            f"✅ *HOÀN THÀNH!* 🎉\n"
            f"📊 Tổng dữ liệu: *{tong} ngày* | Đã xác minh: *{verified} ngày*\n"
            f"• Đã có sẵn: {da_co} ngày\n"
            f"• Lấy mới thành công: {lay_moi} ngày (trong đó {da_xac_minh} ngày xác minh 2 nguồn)\n"
            f"• Không lấy được: {that_bai} ngày (KHÔNG tạo số giả thay thế)\n"
            f"👉 Gõ /dudoan để xem dự đoán dựa trên dữ liệu thật!",
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
            gui_anh_ten(m.chat.id, f"🔍 *ĐANG LẤY DỮ LIỆU THẬT NGÀY {date_str}...*", parse_mode="Markdown")
            kq = lay_ket_qua_ngay(date_str)
            if kq and luu_ket_qua(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"], kq.get("verified", False)):
                tt = "✅ ĐÃ XÁC MINH" if kq.get("verified", False) else "📝 Đã lưu từ 1 nguồn"
                gui_anh_ten(m.chat.id,
                    f"✅ *ĐÃ LẤY DỮ LIỆU THẬT!* 🎉\n📅 {date_str}\n🏆 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n📌 {tt}",
                    parse_mode="Markdown"
                )
            else:
                gui_anh_ten(m.chat.id,
                    f"⚠️ *KHÔNG LẤY ĐƯỢC DỮ LIỆU NGÀY {date_str}*\n"
                    f"❌ Bot KHÔNG tạo số giả hay dữ liệu ảo để thay thế.",
                    parse_mode="Markdown"
                )
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
                if kq and luu_ket_qua(hom_nay, kq["special"], kq["g1"], kq["loto"], kq["source"], kq.get("verified", False)):
                    tt = "✅ Đã xác minh" if kq.get("verified", False) else "📝 Đã lưu"
                    gui_anh_ten(CHAT_ID,
                        f"🏆 *KẾT QUẢ NGÀY D — {hom_nay}*\n"
                        f"🎯 ĐB: `{kq['special']}`\n"
                        f"🥇 G1: `{kq['g1']}`\n"
                        f"📌 Nguồn: {kq['source']} | {tt}",
                        parse_mode="Markdown"
                    )
                da_gui_kq.add(hom_nay)
            if gio == SEND_PREDICT_TIME and hom_nay not in da_gui_dd:
                gui_anh_ten(CHAT_ID, tinh_du_doan(), parse_mode="Markdown")
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
    print("✅ V37.0 — DỮ LIỆU CHÍNH XÁC + KHÔNG TẠO SỐ GIẢ!")
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
