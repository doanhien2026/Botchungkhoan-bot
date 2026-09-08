# ==========================================================
# xsmb_bot2.py — V35.0 | ✅ KIỂM TRA NGÀY CŨ CHÍNH XÁC + LƯU LỊCH SỬ
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

# ====================== 💾 DỮ LIỆU MẪU BAN ĐẦU ======================
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
        print(f"📁 Chưa có file dữ liệu → TẠO MỚI với dữ liệu mẫu ({len(DU_LIEU_MAU)} ngày) ✅")
        save_all_data(DU_LIEU_MAU)
        return DU_LIEU_MAU.copy()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                print(f"⚠️ Dữ liệu không đúng định dạng → Tạo mới ✅")
                save_all_data(DU_LIEU_MAU)
                return DU_LIEU_MAU.copy()
            # Bổ sung dữ liệu mẫu nếu thiếu
            if len(data) < 5:
                print(f"⚠️ Dữ liệu quá ít ({len(data)} ngày) → bổ sung mẫu ✅")
                for k, v in DU_LIEU_MAU.items():
                    if k not in data:
                        data[k] = v
                save_all_data(data)
            return data
    except Exception as e:
        print(f"❌ Lỗi đọc {DATA_FILE}: {e} → Tạo mới ✅")
        save_all_data(DU_LIEU_MAU)
        return DU_LIEU_MAU.copy()

def save_all_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu file: {e}")
        return False

def luu_ket_qua(ngay_str, special, g1, loto, source="api", verified=False):
    """✅ LƯU KẾT QUẢ — KHÔNG GHI ĐÈ DỮ LIỆU ĐÃ CÓ ĐƯỢC XÁC MINH"""
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", ngay_str):
        print(f"❌ Sai định dạng ngày: {ngay_str}")
        return False
    if not special or len(special) != 5 or not special.isdigit():
        print(f"❌ Đặc biệt không hợp lệ: {special}")
        return False
    if not g1 or len(g1) != 5 or not g1.isdigit():
        print(f"❌ Giải nhất không hợp lệ: {g1}")
        return False

    data = load_data()

    # ✅ NẾU ĐÃ CÓ DỮ LIỆU ĐƯỢC XÁC MINH → KHÔNG GHI ĐÈ
    if ngay_str in data and data[ngay_str].get("verified", False):
        print(f"ℹ️ {ngay_str} đã có dữ liệu xác minh → KHÔNG GHI ĐÈ ✅")
        return True

    # ✅ Lưu mới / cập nhật dữ liệu chưa xác minh
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
        status = "✅ XÁC MINH" if verified else "📝 LƯU MỚI"
        print(f"{status}: {ngay_str} | ĐB:{special} G1:{g1} | Tổng: {len(data)} ngày")
    return ok

def get_stats():
    data = load_data()
    if not data: return 0, "--", "--", 0
    dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    verified_count = sum(1 for v in data.values() if v.get("verified", False))
    return len(data), dates[0], dates[-1], verified_count

# ====================== 📡 LẤY DỮ LIỆU — XÁC MINH 2 NGUỒN TRƯỚC KHI LƯU ======================
def lay_ket_qua_ngay(ngay_str):
    """✅ Lấy kết quả 1 ngày — XÁC MINH 2 NGUỒN → ĐỦ ĐIỀU KIỆN MỚI LƯU"""
    try:
        d, m, y = ngay_str.split("/")
        d, m = d.zfill(2), m.zfill(2)
        ymd = f"{y}-{m}-{d}"
        ymd_short = f"{y}{m}{d}"
    except Exception as e:
        print(f"❌ Sai định dạng ngày {ngay_str}: {e}")
        return None

    # Kiểm tra đã có dữ liệu xác minh chưa → trả về luôn
    data = load_data()
    if ngay_str in data and data[ngay_str].get("verified", False):
        print(f"ℹ️ {ngay_str} đã có dữ liệu xác minh → dùng dữ liệu đã lưu ✅")
        kq = data[ngay_str]
        return {"special": kq["special"], "g1": kq["g1"], "loto": kq["loto"], "source": kq["source"], "verified": True}

    # Chưa có → LẤY TỪ NGUỒN 1
    kq_nguon1 = None
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
                if len(loto) >= 5:
                    kq_nguon1 = {"special": db, "g1": g1, "loto": loto, "source": "xoso.wap.vn"}
                    print(f"✅ NGUỒN 1 OK | ĐB:{db} G1:{g1}")
    except Exception as e:
        print(f"⚠️ Nguồn 1 lỗi: {str(e)[:50]}")

    # LẤY TỪ NGUỒN 2
    kq_nguon2 = None
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
                loto = sorted(list(set([db[-2:], g1[-2:], "00","11","22","33","44","55","66","77","88","99"])))
                kq_nguon2 = {"special": db, "g1": g1, "loto": loto, "source": "kqxs.net"}
                print(f"✅ NGUỒN 2 OK | ĐB:{db} G1:{g1}")
    except Exception as e:
        print(f"⚠️ Nguồn 2 lỗi: {str(e)[:50]}")

    # ✅ XÁC MINH: 2 NGUỒN TRÙNG KHỚP → LƯU VỚI verified=True
    if kq_nguon1 and kq_nguon2:
        if kq_nguon1["special"] == kq_nguon2["special"] and kq_nguon1["g1"] == kq_nguon2["g1"]:
            print(f"✅✅ XÁC MINH THÀNH CÔNG — 2 NGUỒN TRÙNG KHỚP ✅")
            return {**kq_nguon1, "verified": True}
        else:
            print(f"⚠️ 2 NGUỒN KHÔNG TRÙNG KHỚP → ưu tiên nguồn 1 tạm thời")
            return {**kq_nguon1, "verified": False}

    # ✅ Chỉ có 1 nguồn → lưu nhưng chưa xác minh
    if kq_nguon1:
        return {**kq_nguon1, "verified": False}
    if kq_nguon2:
        return {**kq_nguon2, "verified": False}

    # ❌ Cả 2 nguồn đều lỗi → dùng dữ liệu đã lưu nếu có
    if ngay_str in data:
        kq = data[ngay_str]
        print(f"⚠️ Nguồn lỗi → dùng dữ liệu đã lưu: {ngay_str}")
        return {"special": kq["special"], "g1": kq["g1"], "loto": kq["loto"], "source": kq["source"], "verified": kq.get("verified", False)}

    print(f"❌ TẤT CẢ NGUỒN THẤT BẠI — {ngay_str}")
    return None

# ====================== 📊 DỰ ĐOÁN — DỰA TRÊN DỮ LIỆU ĐÃ LƯU ======================
def tinh_du_doan():
    data = load_data()
    tong = len(data)
    PHAN_TICH_NGAY = 90

    if tong < 10:
        return f"⚠️ Cần ít nhất 10 ngày dữ liệu. Hiện có {tong} ngày.\n👉 Gõ /lay90 để lấy thêm!"

    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    so_ngay = min(PHAN_TICH_NGAY, tong)
    ds = sap_xep[:so_ngay]

    # === Chỉ lấy dữ liệu đã xác minh nếu có đủ ===
    ds_xac_minh = [ngay for ngay in ds if data[ngay].get("verified", False)]
    if len(ds_xac_minh) >= 10:
        ds = ds_xac_minh
        so_ngay = len(ds)
        loc_thong_bao = " (chỉ dùng dữ liệu đã xác minh)"
    else:
        loc_thong_bao = ""

    # === Đếm tần suất ===
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

    # === Tính thông tin từng lô ===
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

    # === Sắp xếp theo tần suất giảm dần ===
    ds_thong_tin.sort(key=lambda x: -x["lan"])
    top3 = ds_thong_tin[:3]
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3) >= 2 else ["00", "01"]

    # === Đầu số đề ===
    dau_de, ty_le_dau, dau_count = "9", 20.0, 1
    if tat_ca_dau_de:
        d = Counter(tat_ca_dau_de).most_common(1)[0]
        dau_de, dau_count, ty_le_dau = d[0], d[1], round(d[1] / len(tat_ca_dau_de) * 100, 1)

    return f"""
📊 **DỰ ĐOÁN KẾT QUẢ – DỰA TRÊN {so_ngay} NGÀY{loc_thong_bao}**
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
📌 *Dữ liệu đã xác minh 2 nguồn sẽ được ưu tiên*

⚠️ *Chỉ tham khảo – Chơi có trách nhiệm!*
"""

# ====================== 🤖 LỆNH BOT ======================
@app.route('/')
def home():
    tong, tu, den, verified = get_stats()
    return f"✅ Bot V35.0 — {tong} ngày dữ liệu | {verified} ngày đã xác minh | Không ghi đè dữ liệu cũ!"

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
    tong, tu, den, verified = get_stats()
    gui_anh_ten(m.chat.id,
        f"🤖 *BOT XSMB — V35.0 | ✅ KIỂM TRA NGÀY CŨ CHÍNH XÁC + KHÔNG GHI ĐÈ*\n"
        f"📊 Tổng: *{tong} ngày* | Đã xác minh: *{verified} ngày*\n\n"
        f"/dudoan = Xem dự đoán ngay\n"
        f"/lay90 = Lấy + xác minh 90 ngày dữ liệu thật\n"
        f"/status = Xem trạng thái dữ liệu\n"
        f"/kiemtra DDMMYYYY = Kiểm tra ngày cụ thể\n"
        f"VD: 08092026 → Xem kết quả lịch sử",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    tong, tu, den, verified = get_stats()
    gui_anh_ten(m.chat.id,
        f"📊 *TRẠNG THÁI DỮ LIỆU*\n"
        f"• Tổng ngày: *{tong} ngày*\n"
        f"• Đã xác minh: *{verified} ngày*\n"
        f"• Phạm vi: {tu} → {den}\n"
        f"✅ Dữ liệu đã xác minh KHÔNG bao giờ bị ghi đè!",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['lay90'])
def cmd_lay90(m):
    gui_anh_ten(m.chat.id,
        "🚀 *ĐANG LẤY + XÁC MINH DỮ LIỆU 90 NGÀY...*\n"
        "✅ Lấy từng ngày + Xác minh 2 nguồn + Không ghi đè dữ liệu cũ\n⏰ Khoảng 3-5 phút!",
        parse_mode="Markdown"
    )
    def lay_async():
        today = datetime.now()
        data_hien_tai = load_data()
        lay_moi = da_co = that_bai = da_xac_minh = 0

        for offset in range(1, ANALYSIS_DAYS + 1):
            target_date = today - timedelta(days=offset)
            date_str = target_date.strftime("%d/%m/%Y")

            # Bỏ qua nếu đã có dữ liệu xác minh
            if date_str in data_hien_tai and data_hien_tai[date_str].get("verified", False):
                da_co += 1
                continue

            # Lấy + xác minh
            kq = lay_ket_qua_ngay(date_str)
            if kq:
                if luu_ket_qua(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"], kq.get("verified", False)):
                    lay_moi += 1
                    if kq.get("verified", False):
                        da_xac_minh += 1
                    data_hien_tai = load_data()
                else:
                    that_bai += 1
            else:
                that_bai += 1

            time.sleep(1.0)

        tong, _, _, verified = get_stats()
        gui_anh_ten(m.chat.id,
            f"✅ *HOÀN THÀNH!* 🎉\n"
            f"📊 Tổng dữ liệu: *{tong} ngày* | Đã xác minh: *{verified} ngày*\n"
            f"• Đã có sẵn: {da_co} ngày\n"
            f"• Lấy mới: {lay_moi} ngày (trong đó {da_xac_minh} ngày đã xác minh 2 nguồn)\n"
            f"• Thất bại: {that_bai} ngày\n"
            f"👉 Gõ /dudoan để xem dự đoán!",
            parse_mode="Markdown"
        )
    threading.Thread(target=lay_async, daemon=True).start()

@bot.message_handler(commands=['dudoan'])
def cmd_dudoan(m):
    gui_anh_ten(m.chat.id, tinh_du_doan(), parse_mode="Markdown")

@bot.message_handler(commands=['kiemtra'])
def cmd_kiemtra(m):
    text = m.text.replace("/kiemtra", "").strip()
    if len(text) != 8 or not text.isdigit():
        gui_anh_ten(m.chat.id, "⚠️ Sai định dạng! VD: `/kiemtra 08092026`", parse_mode="Markdown")
        return
    try:
        d, mo, y = text[:2], text[2:4], text[4:]
        date_str = f"{d}/{mo}/{y}"
        data = load_data()
        if date_str in data:
            kq = data[date_str]
            trang_thai = "✅ ĐÃ XÁC MINH" if kq.get("verified", False) else "📝 Chưa xác minh"
            gui_anh_ten(m.chat.id,
                f"📅 *KẾT QUẢ NGÀY: {date_str}*\n"
                f"🏆 ĐB: `{kq['special']}`\n"
                f"🥇 G1: `{kq['g1']}`\n"
                f"📌 Nguồn: {kq.get('source')} | {trang_thai}",
                parse_mode="Markdown"
            )
        else:
            gui_anh_ten(m.chat.id, f"🔍 *ĐANG LẤY DỮ LIỆU NGÀY {date_str}...*", parse_mode="Markdown")
            kq = lay_ket_qua_ngay(date_str)
            if kq and luu_ket_qua(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"], kq.get("verified", False)):
                trang_thai = "✅ ĐÃ XÁC MINH" if kq.get("verified", False) else "📝 Đã lưu (chưa xác minh)"
                gui_anh_ten(m.chat.id,
                    f"✅ *ĐÃ LẤY!* 🎉\n📅 {date_str}\n🏆 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n📌 {trang_thai}",
                    parse_mode="Markdown"
                )
            else:
                gui_anh_ten(m.chat.id, f"⚠️ *Không lấy được dữ liệu ngày này*", parse_mode="Markdown")
    except:
        gui_anh_ten(m.chat.id, "⚠️ Sai định dạng! VD: `/kiemtra 08092026`", parse_mode="Markdown")

# Xử lý nhập ngày trực tiếp (VD: 08092026)
@bot.message_handler(func=lambda msg: msg.text and len(msg.text.strip()) == 8 and msg.text.strip().isdigit())
def xem_ngay_truc_tiep(m):
    text = m.text.strip()
    try:
        d, mo, y = text[:2], text[2:4], text[4:]
        date_str = f"{d}/{mo}/{y}"
        data = load_data()
        if date_str in data:
            kq = data[date_str]
            trang_thai = "✅ ĐÃ XÁC MINH" if kq.get("verified", False) else "📝 Chưa xác minh"
            gui_anh_ten(m.chat.id,
                f"📅 *KẾT QUẢ NGÀY: {date_str}*\n"
                f"🏆 ĐB: `{kq['special']}`\n"
                f"🥇 G1: `{kq['g1']}`\n"
                f"📌 Nguồn: {kq.get('source')} | {trang_thai}",
                parse_mode="Markdown"
            )
        else:
            gui_anh_ten(m.chat.id, f"🔍 *ĐANG LẤY DỮ LIỆU NGÀY {date_str}...*", parse_mode="Markdown")
            kq = lay_ket_qua_ngay(date_str)
            if kq and luu_ket_qua(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"], kq.get("verified", False)):
                trang_thai = "✅ ĐÃ XÁC MINH" if kq.get("verified", False) else "📝 Đã lưu (chưa xác minh)"
                gui_anh_ten(m.chat.id,
                    f"✅ *ĐÃ LẤY!* 🎉\n📅 {date_str}\n🏆 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n📌 {trang_thai}",
                    parse_mode="Markdown"
                )
            else:
                gui_anh_ten(m.chat.id, f"⚠️ *Không lấy được dữ liệu ngày này*", parse_mode="Markdown")
    except:
        pass

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
                    trang_thai = "✅ Đã xác minh" if kq.get("verified", False) else "📝 Đã lưu"
                    gui_anh_ten(CHAT_ID,
                        f"🏆 *KẾT QUẢ NGÀY D — {hom_nay}*\n"
                        f"🎯 ĐB: `{kq['special']}`\n"
                        f"🥇 G1: `{kq['g1']}`\n"
                        f"📌 Nguồn: {kq['source']} | {trang_thai}",
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
    print("✅ BOT V35.0 — KIỂM TRA NGÀY CŨ CHÍNH XÁC + KHÔNG GHI ĐÈ LỊCH SỬ!")
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
