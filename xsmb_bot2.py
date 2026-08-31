# ==========================================================
# BOT XSMB — V12.0 | TỰ ĐỘNG HOÀN TOÀN — BỎ NHẬP TAY
# ✅ Tự lấy dữ liệu thực tế từ nguồn KQXS
# ✅ Tự tính 90 ngày → 3 lô + 1 xiên + Đầu số đề
# ✅ Tự động gửi dự đoán NGÀY MAI (D+1) mỗi ngày
# ✅ Gõ /dudoan → xem ngay bất kỳ lúc nào
# ✅ Không cần nhập tay — KHÔNG /nhap nữa!
# Token: 8933441659:AAHbDy-fYsR8ilnHCHRaDUedA1ra1p0gPWda8
# Chat ID: 1030583610
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
TELEGRAM_TOKEN = "8933441659:AAHbDy-fYsR8ilnHCHRaDUedA1ra1p0gPWda8"
CHAT_ID = "1030583610"
PORT = int(os.environ.get("PORT", 10000))
DATA_FILE = "xsmb_data.json"
ANALYSIS_DAYS = 90
AUTO_SEND_TIME = "18:35"  # Gửi dự đoán mỗi ngày lúc 18:35

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

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
        "loto": [x.strip() for x in loto]
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except: return False

# ====================== 🌐 TỰ LẤY DỮ LIỆU THỰC TẾ ======================
def lay_ket_qua_api(date_str):
    """Tự lấy kết quả từ nguồn dữ liệu thực tế — không cần nhập tay!"""
    d, m, y = date_str.split("/")
    # Nguồn 1: KQXS.VN
    try:
        url = f"https://kqxs.vn/api/xsmb?date={y}-{m}-{d}"
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            j = r.json()
            if j.get("error") is False:
                data = j.get("data", {})
                special = str(data.get("special", "")).strip()
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
                if len(special)==5 and len(g1)==5 and len(loto)>=15:
                    print(f"✅ Lấy thành công {date_str} — ĐB:{special} G1:{g1} Lô:{len(loto)}")
                    return {"special":special, "g1":g1, "loto":loto}
    except Exception as e:
        print(f"⚠️ Nguồn 1 lỗi: {e}")
    
    # Nguồn 2 dự phòng
    try:
        url = f"https://api-xoso.onrender.com/xsmb?d={d}&m={m}&y={y}"
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            j = r.json()
            special = str(j.get("db", "")).strip()
            g1 = str(j.get("g1", "")).strip()
            loto = sorted(list(set(str(x).zfill(2) for x in j.get("lo", []) if str(x).isdigit())))
            if len(special)==5 and len(g1)==5 and len(loto)>=15:
                print(f"✅ Lấy Nguồn 2 thành công {date_str}")
                return {"special":special, "g1":g1, "loto":loto}
    except Exception as e:
        print(f"⚠️ Nguồn 2 lỗi: {e}")
    
    print(f"❌ Không lấy được dữ liệu {date_str}")
    return None

# ====================== 🧠 TÍNH TOÁN DỰ ĐOÁN 90 NGÀY ======================
def tinh_du_doan():
    data = load_data()
    tong_ngay = len(data)
    
    if tong_ngay < 3:
        return None, f"⚠️ Đang tự động lấy dữ liệu... Hiện có {tong_ngay} ngày. Vui lòng chờ vài phút!"
    
    # Lấy 90 ngày gần nhất
    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    so_ngay = min(ANALYSIS_DAYS, tong_ngay)
    ds_phan_tich = sap_xep[:so_ngay]
    
    tat_ca_lo = []
    tat_ca_dau_de = []
    
    for ngay in ds_phan_tich:
        kq = data[ngay]
        # Lấy tất cả lô
        for lo in kq.get("loto", []):
            if len(lo)==2 and lo.isdigit():
                tat_ca_lo.append(lo)
        # Thêm 2 số cuối ĐB + lấy đầu số
        db = kq.get("special", "")
        if len(db)==5 and db.isdigit():
            tat_ca_lo.append(db[-2:])
            tat_ca_dau_de.append(db[0])
    
    # Tính tần suất & tỷ lệ
    dem_lo = Counter(tat_ca_lo)
    ds_lo = [{"so":s, "lan":c, "ty_le":round(c/so_ngay*100,1)} for s,c in dem_lo.items()]
    ds_lo.sort(key=lambda x: -x["ty_le"])
    top3 = ds_lo[:3]
    
    # Cặp xiên = 2 con cao nhất
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3)>=2 else ["--","--"]
    
    # Đầu số đề
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

# ====================== 🤖 TỰ ĐỘNG LẤY DỮ LIỆU CŨ ======================
def tu_lay_du_lieu_cu():
    """Tự động lấy dữ liệu 90 ngày gần nhất khi bot khởi động"""
    print("🔄 Bắt đầu tự lấy dữ liệu 90 ngày...")
    data = load_data()
    today = datetime.now()
    count_moi = 0
    
    for offset in range(1, ANALYSIS_DAYS + 1):
        target = today - timedelta(days=offset)
        date_str = target.strftime("%d/%m/%Y")
        if date_str in data:
            continue  # Đã có → bỏ qua
        kq = lay_ket_qua_api(date_str)
        if kq:
            save_data(date_str, kq["special"], kq["g1"], kq["loto"])
            count_moi += 1
        time.sleep(1)  # Tránh gọi quá nhanh
    
    print(f"✅ Hoàn thành! Lấy thêm {count_moi} ngày mới. Tổng: {len(load_data())} ngày.")

# ====================== ⏰ TỰ ĐỘNG GỬI DỰ ĐOÁN MỖI NGÀY ======================
def gui_du_doan_tu_dong():
    """Mỗi ngày lúc 18:35 tự gửi dự đoán + cập nhật kết quả ngày vừa qua"""
    da_gui = set()
    while True:
        now = datetime.now()
        hien_tai = now.strftime("%d/%m/%Y")
        gio_phut = now.strftime("%H:%M")
        
        # Lúc 18:35 mỗi ngày → cập nhật kết quả hôm nay + gửi dự đoán
        if gio_phut == AUTO_SEND_TIME and hien_tai not in da_gui:
            print(f"⏰ Đến giờ tự gửi {AUTO_SEND_TIME}")
            
            # 1. Cập nhật kết quả ngày hôm nay
            kq_hom_nay = lay_ket_qua_api(hien_tai)
            if kq_hom_nay:
                save_data(hien_tai, kq_hom_nay["special"], kq_hom_nay["g1"], kq_hom_nay["loto"])
                # Gửi thông báo kết quả vừa ra
                bot.send_message(CHAT_ID,
                    f"📅 **KẾT QUẢ HÔM NAY — {hien_tai}**\n"
                    f"🏆 Đặc Biệt: `{kq_hom_nay['special']}`\n"
                    f"🥇 Giải Nhất: `{kq_hom_nay['g1']}`\n"
                    f"🎯 Số lô: {len(kq_hom_nay['loto'])} con",
                    parse_mode="Markdown"
                )
            
            # 2. Gửi dự đoán ngày mai
            ok, nd = tinh_du_doan()
            if ok:
                bot.send_message(CHAT_ID, nd, parse_mode="Markdown")
            
            da_gui.add(hien_tai)
            # Xóa đánh dấu sau nửa đêm
            if len(da_gui) > 3:
                da_gui.clear()
        
        time.sleep(30)  # Kiểm tra mỗi 30 giây

# ====================== 📋 LỆNH BOT ======================
@app.route('/')
def home():
    return "✅ Bot XSMB V12.0 — TỰ ĐỘNG HOÀN TOÀN! Bỏ nhập tay."

@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id,
        "🤖 **BOT XSMB — V12.0 | TỰ ĐỘNG HOÀN TOÀN**\n"
        "✅ ❌ BỎ NHẬP TAY — Tự lấy dữ liệu thực tế!\n"
        "✅ Tự phân tích 90 ngày → 3 lô + 1 xiên + Đầu số đề\n"
        "✅ ⏰ Tự động gửi dự đoán NGÀY MAI lúc 18:35 mỗi ngày\n\n"
        "📌 /dudoan → Xem dự đoán ngay bất kỳ lúc nào\n"
        "📌 /status → Xem tổng số ngày đã lưu\n"
        "📌 /capnhat → Cập nhật dữ liệu mới nhất\n\n"
        "💡 Dữ liệu tự động lấy từ nguồn KQXS — không cần nhập gì!",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    data = load_data()
    bot.send_message(m.chat.id,
        f"📊 **TRẠNG THÁI DỮ LIỆU**\n"
        f"• Tổng ngày đã lưu: **{len(data)} ngày**\n"
        f"• Tự động gửi dự đoán mỗi ngày lúc: {AUTO_SEND_TIME}\n"
        f"• Nguồn dữ liệu: KQXS.VN + API-XOSO (thực tế)",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['dudoan'])
def cmd_dudoan(m):
    ok, nd = tinh_du_doan()
    bot.send_message(m.chat.id, nd, parse_mode="Markdown")

@bot.message_handler(commands=['capnhat'])
def cmd_capnhat(m):
    bot.send_message(m.chat.id, "🔄 Đang cập nhật dữ liệu mới nhất...")
    today = datetime.now().strftime("%d/%m/%Y")
    kq = lay_ket_qua_api(today)
    if kq:
        save_data(today, kq["special"], kq["g1"], kq["loto"])
        bot.send_message(m.chat.id, f"✅ Đã cập nhật {today}! Tổng: {len(load_data())} ngày.")
    else:
        bot.send_message(m.chat.id, "⚠️ Chưa có dữ liệu hôm nay hoặc nguồn tạm không phản hồi.")

# ====================== 🚀 KHỞI ĐỘNG ======================
if __name__ == "__main__":
    bot.remove_webhook()
    # Chạy Flask cho Render không tắt
    Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False), daemon=True).start()
    
    # Tự lấy dữ liệu cũ khi khởi động
    Thread(target=tu_lay_du_lieu_cu, daemon=True).start()
    
    # Tự động gửi dự đoán mỗi ngày
    Thread(target=gui_du_doan_tu_dong, daemon=True).start()
    
    print("✅ BOT ĐÃ CHẠY — TỰ ĐỘNG LẤY DỮ LIỆU + TỰ GỬI DỰ ĐOÁN!")
    print(f"⏰ Tự gửi mỗi ngày lúc: {AUTO_SEND_TIME}")
    bot.polling(none_stop=True, interval=3, timeout=60)
