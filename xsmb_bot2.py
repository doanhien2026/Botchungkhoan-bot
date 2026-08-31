# ==========================================================
# BOT XSMB — V12.4 | TỰ ĐỘNG LẤY 90 NGÀY DỮ LIỆU CŨ
# ✅ Tự động lấy 90 ngày ngay khi chạy → không cần nhập tay
# ✅ 3 Nguồn dữ liệu → đảm bảo lấy được
# ✅ Tự tính & gửi dự đoán 18:35 mỗi ngày
# ==========================================================

import telebot
import requests
import json
import os
import time
from datetime import datetime, timedelta
from flask import Flask
from collections import Counter
from threading import Thread

# ====================== 🔧 CẤU HÌNH ======================
TELEGRAM_TOKEN = "8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w"
CHAT_ID = "1030583610"
PORT = int(os.environ.get("PORT", 10000))
DATA_FILE = "xsmb_data.json"
ANALYSIS_DAYS = 90
AUTO_SEND_TIME = "18:35"

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# ====================== 💾 QUẢN LÝ DỮ LIỆU ======================
def load_data():
    if not os.path.exists(DATA_FILE): return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except: return {}

def save_data(date_str, special, g1, loto):
    data = load_data()
    data[date_str] = {
        "special": special.strip(),
        "g1": g1.strip(),
        "loto": [str(x).zfill(2) for x in loto]
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except: return False

# ====================== 🌐 3 NGUỒN DỮ LIỆU — TỰ LẤY KẾT QUẢ ======================
def lay_ket_qua_ngay(date_str):
    """Lấy kết quả XSMB — thử 3 nguồn khác nhau cho chắc chắn"""
    d, m, y = date_str.split("/")
    
    # Nguồn 1: XOSO.WS — Nhanh & ổn định
    try:
        url = f"https://xoso.ws/api/xsmb?date={y}-{m}-{d}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            j = r.json()
            db = str(j.get("dacbiet", "")).strip()
            g1 = str(j.get("giainhất", "")).strip()
            lo = j.get("lo", [])
            if len(db)==5 and len(g1)==5 and len(lo)>=15:
                loto = sorted(list(set(str(x).zfill(2) for x in lo if str(x).isdigit())))
                print(f"✅ [{date_str}] Nguồn 1 thành công")
                return {"special":db, "g1":g1, "loto":loto}
    except Exception as e: print(f"⚠️ Nguồn 1 lỗi {date_str}: {e}")

    # Nguồn 2: KQXS.VN
    try:
        url = f"https://kqxs.vn/api/xsmb?date={y}-{m}-{d}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            j = r.json()
            if j.get("error") is False:
                data = j.get("data", {})
                db = str(data.get("special", "")).strip()
                g1 = str(data.get("prize1", "")).strip()
                loto = []
                for k in ["prize1","prize2","prize3","prize4","prize5","prize6","prize7","special"]:
                    v = data.get(k, "")
                    if isinstance(v, str) and len(v)==5 and v.isdigit():
                        loto.append(v[-2:])
                    elif isinstance(v, list):
                        for x in v:
                            s = str(x).strip()
                            if len(s)==5 and s.isdigit():
                                loto.append(s[-2:])
                loto = sorted(list(set(loto)))
                if len(db)==5 and len(g1)==5 and len(loto)>=15:
                    print(f"✅ [{date_str}] Nguồn 2 thành công")
                    return {"special":db, "g1":g1, "loto":loto}
    except Exception as e: print(f"⚠️ Nguồn 2 lỗi {date_str}: {e}")

    # Nguồn 3: XOSO24H
    try:
        url = f"https://xoso24h.com/api/xsmb/{y}-{m}-{d}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            j = r.json()
            db = str(j.get("db", "")).strip()
            g1 = str(j.get("g1", "")).strip()
            lo = j.get("lo", [])
            if len(db)==5 and len(g1)==5 and len(lo)>=15:
                loto = sorted(list(set(str(x).zfill(2) for x in lo if str(x).isdigit())))
                print(f"✅ [{date_str}] Nguồn 3 thành công")
                return {"special":db, "g1":g1, "loto":loto}
    except Exception as e: print(f"⚠️ Nguồn 3 lỗi {date_str}: {e}")

    print(f"❌ [{date_str}] Tất cả nguồn đều thất bại")
    return None

# ====================== 🚀 TỰ ĐỘNG LẤY 90 NGÀY DỮ LIỆU CŨ ======================
def lay_90_ngay_du_lieu():
    """Chạy 1 lần khi khởi động — tự lấy 90 ngày gần nhất"""
    print("="*50)
    print("🚀 BẮT ĐẦU TỰ LẤY DỮ LIỆU 90 NGÀY GẦN NHẤT")
    print("="*50)
    
    data = load_data()
    today = datetime.now()
    dem_moi = 0
    dem_ton_tai = 0
    dem_loi = 0

    for offset in range(1, ANALYSIS_DAYS + 1):
        target_date = today - timedelta(days=offset)
        date_str = target_date.strftime("%d/%m/%Y")
        
        # Bỏ qua nếu đã có dữ liệu
        if date_str in data:
            dem_ton_tai += 1
            continue
        
        # Lấy dữ liệu mới
        kq = lay_ket_qua_ngay(date_str)
        if kq:
            save_data(date_str, kq["special"], kq["g1"], kq["loto"])
            dem_moi += 1
            print(f"✅ Lưu: {date_str} | ĐB:{kq['special']} | Lô:{len(kq['loto'])} con")
        else:
            dem_loi += 1
        
        # Tạm dừng 0.5s → không bị chặn API
        time.sleep(0.5)
    
    tong = len(load_data())
    print("="*50)
    print(f"✅ HOÀN THÀNH!")
    print(f"• Lấy mới: {dem_moi} ngày")
    print(f"• Đã có sẵn: {dem_ton_tai} ngày")
    print(f"• Lỗi/Bỏ qua: {dem_loi} ngày")
    print(f"• TỔNG DỮ LIỆU: {tong} ngày")
    print("="*50)

# ====================== 🧠 TÍNH TOÁN DỰ ĐOÁN ======================
def tinh_du_doan():
    data = load_data()
    tong_ngay = len(data)
    
    if tong_ngay < 5:
        return None, f"⚠️ Đang lấy dữ liệu... Hiện có {tong_ngay} ngày.\nVui lòng chờ vài phút hoặc gõ /capnhat để kiểm tra lại!"
    
    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    so_ngay = min(ANALYSIS_DAYS, tong_ngay)
    ds_phan_tich = sap_xep[:so_ngay]
    
    tat_ca_lo, tat_ca_dau_de = [], []
    for ngay in ds_phan_tich:
        kq = data[ngay]
        for lo in kq.get("loto", []):
            if len(lo)==2 and lo.isdigit():
                tat_ca_lo.append(lo)
        db = kq.get("special", "")
        if len(db)==5 and db.isdigit():
            tat_ca_lo.append(db[-2:])
            tat_ca_dau_de.append(db[0])
    
    dem_lo = Counter(tat_ca_lo)
    ds_lo = [{"so":s, "lan":c, "ty_le":round(c/so_ngay*100,1)} for s,c in dem_lo.items()]
    ds_lo.sort(key=lambda x: -x["ty_le"])
    top3 = ds_lo[:3]
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3)>=2 else ["--","--"]
    
    dau_de, ty_le_dau = "--", 0
    if tat_ca_dau_de:
        dem_dau = Counter(tat_ca_dau_de).most_common(1)[0]
        dau_de, ty_le_dau = dem_dau[0], round(dem_dau[1]/len(tat_ca_dau_de)*100,1)
    
    ngay_mai = (datetime.now()+timedelta(days=1)).strftime("%d/%m/%Y")
    thong_bao = f"""
📊 **DỰ ĐOÁN NGÀY MAI: {ngay_mai}**
📈 Phân tích: {so_ngay} ngày gần nhất
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **3 CON LÔ TỶ LỆ CAO NHẤT:**
"""
    for i, lo in enumerate(top3, 1):
        thong_bao += f"   {i} • `{lo['so']}` → {lo['lan']} lần | Tỷ lệ: {lo['ty_le']}%\n"
    
    thong_bao += f"""
🔀 **CẶP LÔ XIÊN:**
   → `{xien[0]}` + `{xien[1]}`

🔢 **ĐẦU SỐ ĐỀ DỰ KIẾN:**
   → `{dau_de}` | Tỷ lệ: {ty_le_dau}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Chỉ tham khảo — Chơi có trách nhiệm!
"""
    return True, thong_bao

# ====================== ⏰ TỰ ĐỘNG GỬI MỖI NGÀY ======================
def gui_du_doan_tu_dong():
    da_gui = set()
    while True:
        now = datetime.now()
        hien_tai = now.strftime("%d/%m/%Y")
        gio_phut = now.strftime("%H:%M")
        
        if gio_phut == AUTO_SEND_TIME and hien_tai not in da_gui:
            print(f"⏰ Đến giờ tự gửi {AUTO_SEND_TIME}")
            kq_hom_nay = lay_ket_qua_ngay(hien_tai)
            if kq_hom_nay:
                save_data(hien_tai, kq_hom_nay["special"], kq_hom_nay["g1"], kq_hom_nay["loto"])
                bot.send_message(CHAT_ID,
                    f"📅 **KẾT QUẢ HÔM NAY — {hien_tai}**\n"
                    f"🏆 Đặc Biệt: `{kq_hom_nay['special']}`\n"
                    f"🥇 Giải Nhất: `{kq_hom_nay['g1']}`\n"
                    f"🎯 Tổng lô: {len(kq_hom_nay['loto'])} con",
                    parse_mode="Markdown"
                )
            ok, nd = tinh_du_doan()
            if ok: bot.send_message(CHAT_ID, nd, parse_mode="Markdown")
            da_gui.add(hien_tai)
            if len(da_gui) > 3: da_gui.clear()
        time.sleep(30)

# ====================== 📋 LỆNH BOT ======================
@app.route('/')
def home(): return "✅ Bot XSMB V12.4 — Đang lấy 90 ngày dữ liệu!"

@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id,
        "🤖 **BOT XSMB — V12.4 | TỰ ĐỘNG LẤY 90 NGÀY DỮ LIỆU**\n"
        "✅ Tự động lấy kết quả 90 ngày trước khi dự đoán\n"
        "✅ 3 Nguồn dữ liệu → đảm bảo chính xác\n"
        "✅ Tự phân tích → 3 lô + 1 xiên + Đầu số đề\n"
        "✅ ⏰ Tự gửi dự đoán mỗi ngày lúc 18:35\n\n"
        "📌 /dudoan → Xem dự đoán ngay\n"
        "📌 /status → Xem tổng số ngày đã lưu\n"
        "📌 /capnhat → Cập nhật dữ liệu + lấy thêm ngày\n"
        "📌 /lay90 → Lấy lại toàn bộ 90 ngày dữ liệu mới",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    data = load_data()
    bot.send_message(m.chat.id,
        f"📊 **TRẠNG THÁI DỮ LIỆU**\n"
        f"• Tổng ngày đã lưu: **{len(data)} ngày**\n"
        f"• Mục tiêu phân tích: {ANALYSIS_DAYS} ngày\n"
        f"• Tự gửi dự đoán mỗi ngày lúc: {AUTO_SEND_TIME}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['dudoan'])
def cmd_dudoan(m):
    ok, nd = tinh_du_doan()
    bot.send_message(m.chat.id, nd, parse_mode="Markdown")

@bot.message_handler(commands=['capnhat'])
def cmd_capnhat(m):
    msg = bot.send_message(m.chat.id, "🔄 Đang cập nhật dữ liệu mới nhất...")
    today = datetime.now().strftime("%d/%m/%Y")
    kq = lay_ket_qua_ngay(today)
    if kq:
        save_data(today, kq["special"], kq["g1"], kq["loto"])
        data = load_data()
        bot.edit_message_text(
            f"✅ Đã cập nhật {today}!\n📊 Tổng ngày: **{len(data)} ngày**",
            m.chat.id, msg.message_id
        )
    else:
        bot.edit_message_text("⚠️ Chưa có dữ liệu hôm nay hoặc nguồn tạm không phản hồi.", m.chat.id, msg.message_id)

@bot.message_handler(commands=['lay90'])
def cmd_lay90(m):
    bot.send_message(m.chat.id, "🚀 Bắt đầu lấy 90 ngày dữ liệu...\nQuá trình này mất khoảng 1-2 phút. Vui lòng chờ!")
    Thread(target=lambda: lay_90_ngay_du_lieu() and bot.send_message(m.chat.id, f"✅ Hoàn thành! Tổng dữ liệu: {len(load_data())} ngày") or None, daemon=True).start()

# ====================== 🚀 KHỞI ĐỘNG ======================
if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False), daemon=True).start()
    # Tự động lấy 90 ngày khi khởi động
    Thread(target=lay_90_ngay_du_lieu, daemon=True).start()
    # Tự động gửi dự đoán mỗi ngày
    Thread(target=gui_du_doan_tu_dong, daemon=True).start()
    print("✅ BOT ĐÃ CHẠY — Đang lấy 90 ngày dữ liệu tự động...")
    bot.polling(none_stop=True, interval=3, timeout=60)
