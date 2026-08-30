# ==========================================================
# BOT XSMB — V11.1 | SỬA LỖI + TÍNH 90 NGÀY THỰC TẾ
# ✅ 3 Con lô tỷ lệ cao nhất (90 ngày)
# ✅ 1 Cặp lô xiên
# ✅ Đầu số đề có xác suất cao nhất
# ✅ Đã sửa lỗi drop_pending_updates → chạy ngay trên Render
# Token: 8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w
# Chat ID: 1030583610
# ==========================================================

import telebot
import re
import json
import os
from datetime import datetime, timedelta
from flask import Flask
from collections import Counter

# ====================== 🔧 CẤU HÌNH ======================
TELEGRAM_TOKEN = "8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w"
CHAT_ID = "1030583610"
PORT = int(os.environ.get("PORT", 10000))
DATA_FILE = "xsmb_data.json"
ANALYSIS_DAYS = 90  # Phân tích 90 ngày gần nhất

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ====================== 💾 QUẢN LÝ DỮ LIỆU ======================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"Lỗi đọc dữ liệu: {e}")
        return {}

def save_data(date_str, special, g1, loto):
    data = load_data()
    data[date_str] = {
        "special": special.strip(),
        "g1": g1.strip(),
        "loto": [x.strip() for x in loto]
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Lỗi lưu: {e}")
        return False

# ====================== 🧠 LOGIC TÍNH TOÁN 90 NGÀY ======================
def phan_tich_90_ngay():
    """
    ✅ Tính toán CHÍNH XÁC từ dữ liệu thực tế:
    1. Lấy 90 ngày gần nhất
    2. Đếm tần suất từng con lô 2 chữ số
    3. Tỷ lệ % = (Số lần xuất hiện / Tổng ngày) × 100%
    4. 3 con cao nhất → 1 cặp xiên (2 con cao nhất) → đầu số đề
    """
    data = load_data()
    tong_ngay = len(data)
    
    if tong_ngay < 5:
        return {
            "du": False,
            "thong_bao": f"⚠️ Cần ít nhất 5 ngày dữ liệu để phân tích chính xác.\nHiện có: {tong_ngay} ngày.\n→ Dùng /nhap để nhập thêm kết quả!"
        }
    
    # Sắp xếp ngày từ mới nhất → cũ nhất, lấy 90 ngày gần nhất
    try:
        sap_xep_ngay = sorted(
            data.keys(),
            key=lambda d: datetime.strptime(d, "%d/%m/%Y"),
            reverse=True
        )
    except Exception as e:
        return {"du": False, "thong_bao": f"⚠️ Lỗi xử lý ngày: {e}"}
    
    # Lấy tối đa 90 ngày gần nhất
    so_ngay_phan_tich = min(ANALYSIS_DAYS, tong_ngay)
    danh_sach_phan_tich = sap_xep_ngay[:so_ngay_phan_tich]
    
    tat_ca_lo = []          # Tất cả số lô 2 chữ số
    tat_ca_dau_so_de = []   # Đầu số Giải Đặc Biệt (chữ số đầu)
    
    for ngay in danh_sach_phan_tich:
        kq = data[ngay]
        
        # Lấy danh sách lô 2 chữ số
        ds_lo = kq.get("loto", [])
        for lo in ds_lo:
            if isinstance(lo, str) and len(lo) == 2 and lo.isdigit():
                tat_ca_lo.append(lo)
        
        # Thêm 2 số cuối Giải Đặc Biệt vào danh sách lô
        gdb = kq.get("special", "")
        if isinstance(gdb, str) and len(gdb) == 5 and gdb.isdigit():
            tat_ca_lo.append(gdb[-2:])
            # Lấy đầu số Giải Đặc Biệt (chữ số đầu tiên)
            tat_ca_dau_so_de.append(gdb[0])
    
    # === Tính tần suất & tỷ lệ từng con lô ===
    dem_lo = Counter(tat_ca_lo)
    danh_sach_lo_tu_dien = []
    for so, so_lan_ra in dem_lo.items():
        ty_le = round((so_lan_ra / so_ngay_phan_tich) * 100, 1)
        danh_sach_lo_tu_dien.append({
            "so": so,
            "so_lan_ra": so_lan_ra,
            "ty_le": ty_le
        })
    
    # Sắp xếp theo tỷ lệ giảm dần → lấy 3 con cao nhất
    danh_sach_lo_tu_dien.sort(key=lambda x: -x["ty_le"])
    top3_lo = danh_sach_lo_tu_dien[:3]
    
    # === 1 Cặp lô xiên = 2 con có tỷ lệ cao nhất ===
    cap_xien = [top3_lo[0]["so"], top3_lo[1]["so"]] if len(top3_lo) >= 2 else ["--", "--"]
    
    # === Đầu số đề có tỷ lệ cao nhất ===
    dau_so_de = "--"
    ty_le_dau_so = 0.0
    if tat_ca_dau_so_de:
        dem_dau_so = Counter(tat_ca_dau_so_de)
        so_dau, so_lan_dau = dem_dau_so.most_common(1)[0]
        ty_le_dau_so = round((so_lan_dau / len(tat_ca_dau_so_de)) * 100, 1)
        dau_so_de = so_dau
    
    return {
        "du": True,
        "tong_ngay": so_ngay_phan_tich,
        "tong_nguon_du_lieu": tong_ngay,
        "top3_lo": top3_lo,
        "cap_xien": cap_xien,
        "dau_so_de": dau_so_de,
        "ty_le_dau_so": ty_le_dau_so
    }

# ====================== 📋 LỆNH BOT ======================
@app.route('/')
def home():
    return "✅ Bot XSMB V11.1 — Đã sửa lỗi + Phân tích 90 ngày"

@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id,
        "🤖 **BOT XSMB — V11.1 | PHÂN TÍCH 90 NGÀY THỰC TẾ**\n"
        "✅ Tính toán từ dữ liệu kết quả thực tế bạn nhập\n"
        "✅ 3 Con lô + 1 Cặp xiên + Đầu số đề\n"
        "✅ Tỷ lệ % = Số lần xuất hiện ÷ Tổng ngày × 100%\n\n"
        "📌 /nhap DDMMYYYY ĐB G1 LÔ1,LÔ2,... → Nhập kết quả\n"
        "📌 /dudoan → Phân tích & dự đoán\n"
        "📌 /status → Xem tổng số ngày đã lưu\n"
        "📌 DDMMYYYY → Xem dữ liệu ngày đó\n\n"
        "💡 Nhập 5-7 ngày → dự đoán chính xác hơn!",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['nhap'])
def cmd_nhap(m):
    parts = m.text.strip().split()
    if len(parts) < 4:
        return bot.send_message(m.chat.id,
            "⚠️ **Định dạng:** /nhap DDMMYYYY ĐB G1 LÔ1,LÔ2,...\n"
            "VD: /nhap 29082026 12345 67890 01,05,12,18,23,34,45,56,67,72,78,81,85,90,93",
            parse_mode="Markdown"
        )
    t, db, g1, lo_str = parts[1], parts[2], parts[3], parts[4]
    
    if not re.match(r"^\d{8}$", t):
        return bot.send_message(m.chat.id, "❌ Ngày sai định dạng! VD: 29082026")
    date_str = f"{t[:2]}/{t[2:4]}/{t[4:8]}"
    try:
        datetime(int(t[4:8]), int(t[2:4]), int(t[:2]))
    except:
        return bot.send_message(m.chat.id, "❌ Ngày không hợp lệ!")
    
    if len(db) != 5 or not db.isdigit():
        return bot.send_message(m.chat.id, "❌ Giải Đặc Biệt phải 5 chữ số!")
    if len(g1) != 5 or not g1.isdigit():
        return bot.send_message(m.chat.id, "❌ Giải Nhất phải 5 chữ số!")
    
    ds_lo = [x.strip() for x in lo_str.split(",") if x.strip() and len(x.strip()) == 2 and x.strip().isdigit()]
    if len(ds_lo) < 15:
        return bot.send_message(m.chat.id, f"⚠️ Cần ít nhất 15 số lô, mới có {len(ds_lo)}")
    
    save_data(date_str, db, g1, ds_lo)
    bot.send_message(m.chat.id,
        f"✅ **ĐÃ LƯU: {date_str}**\n"
        f"🏆 Giải Đặc Biệt: `{db}`\n"
        f"🥇 Giải Nhất: `{g1}`\n"
        f"🎯 Số lô: {len(ds_lo)} con\n\n"
        f"💡 Gõ /dudoan → xem phân tích & dự đoán!",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    data = load_data()
    bot.send_message(m.chat.id,
        f"📊 **TRẠNG THÁI DỮ LIỆU**\n"
        f"• Tổng ngày đã lưu: **{len(data)} ngày**\n"
        f"• Ngày cũ nhất: {min(data.keys()) if data else 'Chưa có'}\n"
        f"• Ngày mới nhất: {max(data.keys()) if data else 'Chưa có'}\n"
        f"• Phân tích tối đa: {ANALYSIS_DAYS} ngày gần nhất",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['dudoan'])
def cmd_dudoan(m):
    kq = phan_tich_90_ngay()
    if not kq["du"]:
        return bot.send_message(m.chat.id, kq["thong_bao"], parse_mode="Markdown")
    
    ngay_mai = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    
    noi_dung = f"""
📊 **PHÂN TÍCH DỮ LIỆU {kq['tong_ngay']} NGÀY GẦN NHẤT**
(Tổng {kq['tong_nguon_du_lieu']} ngày trong kho dữ liệu)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **3 CON LÔ CÓ TỶ LỆ RƠI CAO NHẤT:**
(Tỷ lệ = Số lần xuất hiện ÷ Tổng ngày × 100%)

"""
    for i, lo in enumerate(kq["top3_lo"], 1):
        noi_dung += f"   {i} • `{lo['so']}`  →  Xuất hiện: {lo['so_lan_ra']} lần  |  Tỷ lệ: {lo['ty_le']}%\n"
    
    noi_dung += f"""
🔀 **1 CẶP LÔ XIÊN (Kết hợp 2 con cao nhất):**
   → `{kq['cap_xien'][0]}` + `{kq['cap_xien'][1]}`

🔢 **DỰ KIẾN ĐẦU SỐ GIẢI ĐẶC BIỆT:**
   → Đầu số `{kq['dau_so_de']}`  |  Tỷ lệ: {kq['ty_le_dau_so']}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 **DỰ ĐOÁN NGÀY: {ngay_mai}**
⚠️ Chỉ tham khảo — Chơi có trách nhiệm!
"""
    bot.send_message(m.chat.id, noi_dung, parse_mode="Markdown")

# Xem dữ liệu ngày đã lưu
@bot.message_handler(func=lambda msg: not msg.text.startswith('/') and re.match(r"^\d{8}$", msg.text.strip()))
def xem_ngay(m):
    t = m.text.strip()
    date_str = f"{t[:2]}/{t[2:4]}/{t[4:8]}"
    data = load_data()
    if date_str not in data:
        return bot.send_message(m.chat.id, f"⚠️ Chưa có dữ liệu {date_str}. Dùng /nhap để nhập.")
    kq = data[date_str]
    bot.send_message(m.chat.id,
        f"📅 **KẾT QUẢ — {date_str}**\n"
        f"🏆 Giải Đặc Biệt: `{kq['special']}`\n"
        f"🥇 Giải Nhất: `{kq['g1']}`\n"
        f"🎯 Số lô về: {', '.join(f'`{n}`' for n in kq['loto'])}",
        parse_mode="Markdown"
    )

# ====================== 🚀 KHỞI ĐỘNG ======================
if __name__ == "__main__":
    bot.remove_webhook()
    from threading import Thread
    Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False), daemon=True).start()
    print("✅ BOT ĐÃ SẴN SÀNG — Phân tích 90 ngày dữ liệu thực tế!")
    # ✅ ĐÃ XÓA drop_pending_updates → tương thích với pyTelegramBotAPI 4.22.0
    bot.polling(none_stop=True, interval=3, timeout=60)
