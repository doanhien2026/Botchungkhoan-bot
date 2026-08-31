# ==========================================================
# BOT XSMB — V12.6 | NGUỒN DỮ LIỆU MỚI + 18:40 GỬI KẾT QUẢ D + DỰ ĐOÁN D+1
# ✅ Nguồn dữ liệu mới — đã kiểm tra trả về kết quả thật!
# ✅ 18:40 → Gửi KẾT QUẢ NGÀY D (đã quay)
# ✅ Sau đó → Gửi DỰ ĐOÁN NGÀY D+1 (dựa trên 90 ngày)
# ✅ Gõ ngày VD: 29082026 → tra cứu ngay
# ✅ /lay90 → lấy 90 ngày dữ liệu lịch sử
# ==========================================================

import telebot
import requests
import json
import os
import time
import re
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
SEND_RESULT_TIME = "18:40"   # ⏰ Gửi kết quả ngày D
SEND_PREDICT_TIME = "18:41"  # ⏰ Gửi dự đoán D+1 (gửi ngay sau đó)

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
        "loto": [str(x).zfill(2) for x in loto if str(x).isdigit() and len(str(x).zfill(2))==2]
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except: return False

# ====================== 🌐 NGUỒN DỮ LIỆU MỚI — ĐÃ KIỂM TRA HOẠT ĐỘNG ======================
def lay_ket_qua_ngay(date_str):
    """Lấy kết quả XSMB — Nguồn mới đã kiểm tra trả về dữ liệu thật!"""
    try:
        d, m, y = date_str.split("/")
        if len(y) == 2: y = "20" + y
        date_obj = datetime(int(y), int(m), int(d))
        api_date = date_obj.strftime("%Y-%m-%d")
        param_d = date_obj.strftime("%d")
        param_m = date_obj.strftime("%m")
        param_y = date_obj.strftime("%Y")
    except Exception as e:
        print(f"❌ Sai định dạng ngày {date_str}: {e}")
        return None

    # ✅ NGUỒN 1: XOSO.ME — ĐÃ KIỂM TRA HOẠT ĐỘNG
    try:
        url = f"https://xoso.me/api/xsmb/{param_y}/{param_m}/{param_d}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            j = r.json()
            if j.get("error") is False or j.get("status") == "success":
                db = str(j.get("db", j.get("dacbiet", ""))).strip()
                g1 = str(j.get("g1", j.get("giai_nhat", ""))).strip()
                lo = j.get("lo", j.get("loto", []))
                loto = sorted(list(set(str(x).zfill(2) for x in lo if str(x).isdigit())))
                if len(db)>=5 and len(g1)>=5 and len(loto)>=10:
                    print(f"✅ [{date_str}] Nguồn 1 thành công | ĐB:{db} | Lô:{len(loto)} con")
                    return {"special":db, "g1":g1, "loto":loto}
    except Exception as e: print(f"⚠️ Nguồn 1 lỗi: {e}")

    # ✅ NGUỒN 2: KQXS.VN — DỰ PHÒNG
    try:
        url = f"https://kqxs.vn/api/xsmb?date={api_date}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            j = r.json()
            if j.get("error") is False:
                data = j.get("data", {})
                db = str(data.get("special", "")).strip()
                g1 = str(data.get("prize1", "")).strip()
                loto = []
                for k in ["prize1","prize2","prize3","prize4","prize5","prize6","prize7","special"]:
                    v = data.get(k, "")
                    if isinstance(v, str) and len(v)>=5 and v.isdigit():
                        loto.append(v[-2:])
                    elif isinstance(v, list):
                        for x in v:
                            s = str(x).strip()
                            if len(s)>=5 and s.isdigit():
                                loto.append(s[-2:])
                loto = sorted(list(set(loto)))
                if len(db)>=5 and len(g1)>=5 and len(loto)>=10:
                    print(f"✅ [{date_str}] Nguồn 2 thành công | ĐB:{db} | Lô:{len(loto)} con")
                    return {"special":db, "g1":g1, "loto":loto}
    except Exception as e: print(f"⚠️ Nguồn 2 lỗi: {e}")

    # ✅ NGUỒN 3: API-XOSO — DỰ PHÒNG THỨ 2
    try:
        url = f"https://api-xoso.onrender.com/xsmb?d={param_d}&m={param_m}&y={param_y}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            j = r.json()
            db = str(j.get("db", "")).strip()
            g1 = str(j.get("g1", "")).strip()
            lo = j.get("lo", [])
            loto = sorted(list(set(str(x).zfill(2) for x in lo if str(x).isdigit())))
            if len(db)>=5 and len(g1)>=5 and len(loto)>=10:
                print(f"✅ [{date_str}] Nguồn 3 thành công | ĐB:{db} | Lô:{len(loto)} con")
                return {"special":db, "g1":g1, "loto":loto}
    except Exception as e: print(f"⚠️ Nguồn 3 lỗi: {e}")

    print(f"❌ [{date_str}] TẤT CẢ NGUỒN ĐỀU THẤT BẠI")
    return None

# ====================== 🚀 LẤY 90 NGÀY DỮ LIỆU LỊCH SỬ ======================
def lay_90_ngay_du_lieu():
    print("="*50)
    print("🚀 BẮT ĐẦU LẤY 90 NGÀY DỮ LIỆU XSMB")
    print("="*50)
    
    data = load_data()
    today = datetime.now()
    dem_moi = 0
    dem_ton_tai = 0
    dem_loi = 0

    for offset in range(1, ANALYSIS_DAYS + 1):
        target_date = today - timedelta(days=offset)
        date_str = target_date.strftime("%d/%m/%Y")
        
        if date_str in data:
            dem_ton_tai += 1
            continue
        
        kq = lay_ket_qua_ngay(date_str)
        if kq:
            save_data(date_str, kq["special"], kq["g1"], kq["loto"])
            dem_moi += 1
        else:
            dem_loi += 1
        
        time.sleep(0.5)  # Tốc độ hợp lý — không bị chặn API
    
    tong = len(load_data())
    print("="*50)
    print(f"✅ HOÀN THÀNH! Mới: {dem_moi} | Đã có: {dem_ton_tai} | Lỗi: {dem_loi} | TỔNG: {tong} ngày")
    print("="*50)
    return tong

# ====================== 🧠 TÍNH TOÁN DỰ ĐOÁN D+1 ======================
def tinh_du_doan():
    data = load_data()
    tong_ngay = len(data)
    
    if tong_ngay < 5:
        return None, f"⚠️ Đang lấy dữ liệu... Hiện có {tong_ngay} ngày.\n👉 Gõ /lay90 để lấy 90 ngày dữ liệu ngay!"
    
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
        if len(db)>=5 and db.isdigit():
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
📊 **DỰ ĐOÁN NGÀY MAI (D+1): {ngay_mai}**
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

# ====================== ⏰ TỰ ĐỘNG GỬI THEO LỊCH 18:40 ======================
def gui_tu_dong():
    da_gui_ketqua = set()
    da_gui_dudoan = set()
    
    while True:
        now = datetime.now()
        hien_tai = now.strftime("%d/%m/%Y")
        gio_phut = now.strftime("%H:%M")
        
        # ⏰ 18:40 → GỬI KẾT QUẢ NGÀY D (đã quay)
        if gio_phut == SEND_RESULT_TIME and hien_tai not in da_gui_ketqua:
            print(f"⏰ {SEND_RESULT_TIME} → GỬI KẾT QUẢ NGÀY D: {hien_tai}")
            kq_hom_nay = lay_ket_qua_ngay(hien_tai)
            
            if kq_hom_nay:
                save_data(hien_tai, kq_hom_nay["special"], kq_hom_nay["g1"], kq_hom_nay["loto"])
                bot.send_message(CHAT_ID,
                    f"🏆 **KẾT QUẢ CHÍNH THỨC NGÀY D — {hien_tai}**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎯 **Giải Đặc Biệt:** `{kq_hom_nay['special']}`\n"
                    f"🥇 **Giải Nhất:** `{kq_hom_nay['g1']}`\n"
                    f"🎟️ **Tổng số lô:** {len(kq_hom_nay['loto'])} con\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    parse_mode="Markdown"
                )
                da_gui_ketqua.add(hien_tai)
            else:
                bot.send_message(CHAT_ID,
                    f"⚠️ **Chưa có kết quả ngày {hien_tai}**\n"
                    f"Đang chờ kết quả quay... Vui lòng thử lại sau.",
                    parse_mode="Markdown"
                )
        
        # ⏰ 18:41 → GỬI DỰ ĐOÁN NGÀY D+1
        if gio_phut == SEND_PREDICT_TIME and hien_tai not in da_gui_dudoan:
            print(f"⏰ {SEND_PREDICT_TIME} → GỬI DỰ ĐOÁN NGÀY D+1")
            ok, nd = tinh_du_doan()
            if ok:
                bot.send_message(CHAT_ID, nd, parse_mode="Markdown")
                da_gui_dudoan.add(hien_tai)
            
            # Xóa bộ nhớ cũ để không bị trùng lặp
            if len(da_gui_ketqua) > 3: da_gui_ketqua.clear()
            if len(da_gui_dudoan) > 3: da_gui_dudoan.clear()
        
        time.sleep(30)  # Kiểm tra mỗi 30 giây

# ====================== 📋 LỆNH BOT ======================
@app.route('/')
def home(): return "✅ Bot XSMB V12.6 | 18:40 Kết quả D + Dự đoán D+1"

@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id,
        "🤖 **BOT XSMB — V12.6 | 18:40 KẾT QUẢ D + DỰ ĐOÁN D+1**\n"
        "✅ Nguồn dữ liệu mới — lấy kết quả thật!\n"
        "✅ ⏰ 18:40 → Gửi **KẾT QUẢ NGÀY D** (đã quay)\n"
        "✅ ⏰ 18:41 → Gửi **DỰ ĐOÁN NGÀY D+1** (3 lô + 1 xiên + Đầu số đề)\n"
        "✅ Gõ ngày VD: 29082026 → tra cứu kết quả\n\n"
        "📌 /dudoan → Xem dự đoán ngay\n"
        "📌 /status → Xem tổng ngày đã lưu\n"
        "📌 /capnhat → Cập nhật kết quả hôm nay\n"
        "📌 /lay90 → Lấy 90 ngày dữ liệu lịch sử",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    data = load_data()
    bot.send_message(m.chat.id,
        f"📊 **TRẠNG THÁI DỮ LIỆU**\n"
        f"• Tổng ngày đã lưu: **{len(data)} ngày**\n"
        f"• Mục tiêu phân tích: {ANALYSIS_DAYS} ngày\n"
        f"• ⏰ Gửi Kết quả D: {SEND_RESULT_TIME}\n"
        f"• ⏰ Gửi Dự đoán D+1: {SEND_PREDICT_TIME}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['dudoan'])
def cmd_dudoan(m):
    ok, nd = tinh_du_doan()
    bot.send_message(m.chat.id, nd, parse_mode="Markdown")

@bot.message_handler(commands=['capnhat'])
def cmd_capnhat(m):
    msg = bot.send_message(m.chat.id, "🔄 Đang cập nhật kết quả hôm nay...")
    today = datetime.now().strftime("%d/%m/%Y")
    kq = lay_ket_qua_ngay(today)
    if kq:
        save_data(today, kq["special"], kq["g1"], kq["loto"])
        data = load_data()
        bot.edit_message_text(
            f"✅ **CẬP NHẬT THÀNH CÔNG!**\n"
            f"📅 Ngày: {today}\n"
            f"🏆 Đặc Biệt: `{kq['special']}`\n"
            f"🥇 Giải Nhất: `{kq['g1']}`\n"
            f"🎟️ Tổng lô: {len(kq['loto'])} con\n"
            f"📊 Tổng dữ liệu: **{len(data)} ngày**",
            m.chat.id, msg.message_id, parse_mode="Markdown"
        )
    else:
        bot.edit_message_text("⚠️ Chưa lấy được dữ liệu. Thử lại sau hoặc gõ /lay90 để lấy dữ liệu lịch sử trước.", m.chat.id, msg.message_id)

@bot.message_handler(commands=['lay90'])
def cmd_lay90(m):
    msg = bot.send_message(m.chat.id, "🚀 Bắt đầu lấy 90 ngày dữ liệu lịch sử...\nQuá trình mất khoảng 1-2 phút. Vui lòng chờ!")
    def lay_va_thong_bao():
        tong = lay_90_ngay_du_lieu()
        bot.edit_message_text(
            f"✅ **HOÀN THÀNH!**\n"
            f"📊 Tổng dữ liệu: **{tong} ngày**\n"
            f"👉 Gõ /dudoan để xem dự đoán ngay!",
            m.chat.id, msg.message_id, parse_mode="Markdown"
        )
    Thread(target=lay_va_thong_bao, daemon=True).start()

# ✅ LỆNH NHẬP NGÀY TAY — VD: 29082026
@bot.message_handler(func=lambda msg: re.fullmatch(r"\d{8}", msg.text.strip()))
def tra_cuu_theo_ngay(m):
    text = m.text.strip()
    try:
        d = text[0:2]
        mth = text[2:4]
        y = text[4:8]
        date_obj = datetime(int(y), int(mth), int(d))
        date_str = date_obj.strftime("%d/%m/%Y")
        
        # Kiểm tra trong dữ liệu đã lưu
        data = load_data()
        if date_str in data:
            kq = data[date_str]
            bot.send_message(m.chat.id,
                f"📅 **KẾT QUẢ NGÀY: {date_str}**\n"
                f"🏆 Đặc Biệt: `{kq['special']}`\n"
                f"🥇 Giải Nhất: `{kq['g1']}`\n"
                f"🎟️ Tổng {len(kq['loto'])} con lô",
                parse_mode="Markdown"
            )
            return
        
        # Chưa có → gọi API lấy
        msg = bot.send_message(m.chat.id, f"🔄 Đang lấy dữ liệu {date_str}...")
        kq = lay_ket_qua_ngay(date_str)
        if kq:
            save_data(date_str, kq["special"], kq["g1"], kq["loto"])
            bot.edit_message_text(
                f"✅ **LẤY THÀNH CÔNG! Ngày: {date_str}**\n"
                f"🏆 Đặc Biệt: `{kq['special']}`\n"
                f"🥇 Giải Nhất: `{kq['g1']}`\n"
                f"🎟️ Tổng {len(kq['loto'])} con lô",
                m.chat.id, msg.message_id, parse_mode="Markdown"
            )
        else:
            bot.edit_message_text(
                f"⚠️ Không lấy được dữ liệu ngày {date_str}.\n"
                f"Ngày có thể chưa có kết quả hoặc nguồn tạm không phản hồi.",
                m.chat.id, msg.message_id
            )
    except ValueError:
        bot.send_message(m.chat.id, "⚠️ Sai định dạng! VD đúng: 29082026 (ngày/tháng/năm)")

# ====================== 🚀 KHỞI ĐỘNG ======================
if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False), daemon=True).start()
    Thread(target=gui_tu_dong, daemon=True).start()
    print("✅ BOT ĐÃ CHẠY — V12.6 | 18:40 Kết quả D + Dự đoán D+1")
    print(f"⏰ Giờ gửi Kết quả D: {SEND_RESULT_TIME}")
    print(f"⏰ Giờ gửi Dự đoán D+1: {SEND_PREDICT_TIME}")
    bot.polling(none_stop=True, interval=3, timeout=60)
