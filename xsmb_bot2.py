# ==========================================================
# BOT XSMB — V17.0 | ✅ CHỈ LƯU DỮ LIỆU THẬT, KHÔNG TẠO SỐ GIẢ!
# ✅ Token: 8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w
# ✅ Chat ID: -1001030583610
# ==========================================================

import telebot
import json
import os
import re
import time
from datetime import datetime, timedelta
from flask import Flask
from collections import Counter
from threading import Thread
from fetcher import lay_ket_qua_xsmb

# ====================== 🔧 CẤU HÌNH ======================
TELEGRAM_TOKEN = "8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w"
CHAT_ID = "-1001030583610"
PORT = int(os.environ.get("PORT", 10000))
DATA_FILE = "xsmb_data.json"
ANALYSIS_DAYS = 90
SEND_RESULT_TIME = "18:40"
SEND_PREDICT_TIME = "18:41"

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ====================== 💾 QUẢN LÝ DỮ LIỆU — CHỈ LƯU KHI THẬT! ======================
def load_data():
    if not os.path.exists(DATA_FILE): return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict): return {}
            cleaned = {}
            for k, v in data.items():
                if re.fullmatch(r"\d{2}/\d{2}/\d{4}", k):
                    if isinstance(v, dict) and "special" in v and "g1" in v and "loto" in v:
                        if len(v.get("special",""))==5 and len(v.get("g1",""))==5:
                            cleaned[k] = v
            return cleaned
    except Exception as e:
        print(f"⚠️ File dữ liệu lỗi → tạo mới: {e}")
        try: os.remove(DATA_FILE)
        except: pass
        return {}

def save_data(date_str, special, g1, loto):
    """✅ CHỈ LƯU KHI DỮ LIỆU ĐÚNG ĐỊNH DẠNG — KHÔNG LƯU SAI!"""
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", date_str):
        print(f"❌ Không lưu — ngày sai: {date_str}")
        return False
    if len(special)!=5 or not special.isdigit():
        print(f"❌ Không lưu — ĐB sai: {special}")
        return False
    if len(g1)!=5 or not g1.isdigit():
        print(f"❌ Không lưu — G1 sai: {g1}")
        return False
    data = load_data()
    data[date_str] = {
        "special": special.strip(),
        "g1": g1.strip(),
        "loto": [str(x).zfill(2) for x in loto if str(x).isdigit() and len(str(x))==2]
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu: {e}")
        return False

# ====================== 🆕 LẤY 90 NGÀY — CHỈ LẤY THẬT, KHÔNG TẠO SỐ GIẢ! ======================
def lay_90_ngay_thuc():
    print("🚀 BẮT ĐẦU LẤY 90 NGÀY KẾT QUẢ THẬT...")
    print("⚠️ KHÔNG TẠO SỐ GIẢ NỮA! Chỉ lưu khi lấy được từ nguồn thật!")
    today = datetime.now()
    dem_thuc = 0
    dem_that_bai = 0
    data = load_data()

    if len(data) < 5:
        print("⚠️ Dữ liệu còn ít — đang lấy từ nguồn thật, vui lòng chờ...")

    for offset in range(1, ANALYSIS_DAYS + 1):
        target_date = today - timedelta(days=offset)
        date_str = target_date.strftime("%d/%m/%Y")
        
        if date_str in data:
            continue
        
        kq = lay_ket_qua_xsmb(date_str)
        if kq and save_data(date_str, kq["special"], kq["g1"], kq["loto"]):
            dem_thuc += 1
            print(f"✅ [{dem_thuc}] {date_str} | ĐB:{kq['special']} | {kq['source']}")
        else:
            dem_that_bai += 1
            print(f"❌ {date_str} | KHÔNG LẤY ĐƯỢC → Bỏ qua, không lưu số giả!")
        
        time.sleep(1)
    
    tong = len(load_data())
    print(f"\n✅ HOÀN THÀNH! Tổng: {tong} ngày THẬT | Lấy mới: {dem_thuc} | Thất bại: {dem_that_bai}")
    
    if tong < 30:
        print(f"⚠️ Dữ liệu chỉ có {tong} ngày — dự đoán có thể chưa chính xác!")
    return tong

# ====================== 📊 PHẠM VI DỮ LIỆU ======================
def get_pham_vi():
    data = load_data()
    if not data: return "--", "--"
    try:
        sap = sorted([datetime.strptime(k, "%d/%m/%Y") for k in data.keys()])
        return sap[0].strftime("%d/%m/%Y"), sap[-1].strftime("%d/%m/%Y")
    except: return "--", "--"

# ====================== 🧠 TÍNH DỰ ĐOÁN ======================
def tinh_du_doan():
    data = load_data()
    tong = len(data)
    if tong < 30:
        return f"⚠️ Cần ít nhất 30 ngày dữ liệu THẬT. Hiện có {tong} ngày.\n👉 Gõ /lay90 để lấy đủ dữ liệu thật!"
    
    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    so_ngay = min(ANALYSIS_DAYS, tong)
    ds = sap_xep[:so_ngay]
    
    tat_ca_lo, tat_ca_dau = [], []
    for ngay in ds:
        kq = data[ngay]
        for lo in kq.get("loto", []):
            if len(lo)==2 and lo.isdigit(): tat_ca_lo.append(lo)
        db = kq.get("special", "")
        if len(db)>=5 and db.isdigit():
            tat_ca_lo.append(db[-2:])
            tat_ca_dau.append(db[0])
    
    if not tat_ca_lo:
        return "⚠️ Dữ liệu lô trống. Gõ /lay90 để lấy dữ liệu thật!"
    
    dem_lo = Counter(tat_ca_lo)
    ds_lo = [{"so":s, "lan":c, "ty_le":round(c/so_ngay*100,1)} for s,c in dem_lo.items()]
    ds_lo.sort(key=lambda x: -x["ty_le"])
    top3 = ds_lo[:3]
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3)>=2 else ["00","01"]
    
    dau_de, ty_le_dau = "9", 10.0
    if tat_ca_dau:
        d = Counter(tat_ca_dau).most_common(1)[0]
        dau_de, ty_le_dau = d[0], round(d[1]/len(tat_ca_dau)*100,1)
    
    ngay_mai = (datetime.now()+timedelta(days=1)).strftime("%d/%m/%Y")
    return f"""
📊 **DỰ ĐOÁN NGÀY MAI (D+1): {ngay_mai}**
📈 Phân tích: {so_ngay} ngày DỮ LIỆU THẬT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **3 CON LÔ TỶ LỆ CAO NHẤT:**
   1 • `{top3[0]['so']}` → {top3[0]['lan']} lần | Tỷ lệ: {top3[0]['ty_le']}%
   2 • `{top3[1]['so']}` → {top3[1]['lan']} lần | Tỷ lệ: {top3[1]['ty_le']}%
   3 • `{top3[2]['so']}` → {top3[2]['lan']} lần | Tỷ lệ: {top3[2]['ty_le']}%

🔀 **CẶP LÔ XIÊN:**
   → `{xien[0]}` + `{xien[1]}`

🔢 **ĐẦU SỐ ĐỀ DỰ KIẾN:**
   → `{dau_de}` | Tỷ lệ: {ty_le_dau}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Dữ liệu từ nguồn thật — Chỉ tham khảo!
"""

# ====================== ⏰ TỰ ĐỘNG GỬI ======================
def gui_tu_dong():
    da_gui_kq, da_gui_dd = set(), set()
    while True:
        try:
            now = datetime.now()
            hom_nay = now.strftime("%d/%m/%Y")
            gio = now.strftime("%H:%M")
            
            if gio == SEND_RESULT_TIME and hom_nay not in da_gui_kq:
                kq_homnay = lay_ket_qua_xsmb(hom_nay)
                if kq_homnay and save_data(hom_nay, kq_homnay["special"], kq_homnay["g1"], kq_homnay["loto"]):
                    bot.send_message(CHAT_ID,
                        f"🏆 **KẾT QUẢ NGÀY D — {hom_nay}**\n"
                        f"🎯 Đặc Biệt: `{kq_homnay['special']}`\n🥇 Giải Nhất: `{kq_homnay['g1']}`\n📌 Nguồn: {kq_homnay['source']}",
                        parse_mode="Markdown"
                    )
                da_gui_kq.add(hom_nay)
            
            if gio == SEND_PREDICT_TIME and hom_nay not in da_gui_dd:
                bot.send_message(CHAT_ID, tinh_du_doan(), parse_mode="Markdown")
                da_gui_dd.add(hom_nay)
            
            if len(da_gui_kq) > 3: da_gui_kq.clear()
            if len(da_gui_dd) > 3: da_gui_dd.clear()
            time.sleep(30)
        except Exception as e:
            print(f"⚠️ Lỗi luồng tự động gửi: {e}")
            time.sleep(10)

# ====================== 📋 LỆNH BOT ======================
@app.route('/')
def home(): return "✅ Bot XSMB V17.0 | CHỈ LƯU DỮ LIỆU THẬT!"

@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id,
        "🤖 **BOT XSMB — V17.0 | CHỈ DỮ LIỆU THẬT ✅**\n"
        "✅ KHÔNG TẠO SỐ GIẢ NỮA! Chỉ lưu khi lấy được từ nguồn thật\n"
        "✅ /lay90 = Lấy 90 ngày dữ liệu THẬT\n"
        "✅ /dudoan = Dự đoán từ dữ liệu thật\n"
        "✅ /status = Xem trạng thái dữ liệu\n"
        "✅ /capnhat = Cập nhật kết quả hôm nay\n"
        "✅ ⏰ 18:40 Kết quả D | 18:41 Dự đoán D+1\n\n"
        "📌 Gõ /lay90 → bắt đầu! ⭐",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    tu, den = get_pham_vi()
    bot.send_message(m.chat.id,
        f"📊 **TRẠNG THÁI DỮ LIỆU**\n"
        f"• Tổng ngày đã lưu: **{len(load_data())} ngày**\n"
        f"• Phạm vi dữ liệu: **{tu} → {den}**\n"
        f"• ⏰ Gửi Kết quả D: {SEND_RESULT_TIME}\n"
        f"• ⏰ Gửi Dự đoán D+1: {SEND_PREDICT_TIME}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['dudoan'])
def cmd_dudoan(m):
    bot.send_message(m.chat.id, tinh_du_doan(), parse_mode="Markdown")

@bot.message_handler(commands=['lay90'])
def cmd_lay90(m):
    msg = bot.send_message(m.chat.id, "🚀 ĐANG LẤY DỮ LIỆU THẬT...\n⏰ Khoảng 2-3 phút, vui lòng chờ!")
    def tao_va_bao():
        tong = lay_90_ngay_thuc()
        bot.edit_message_text(
            f"✅ **HOÀN THÀNH!** 🎉\n📊 Tổng dữ liệu THẬT: **{tong} ngày**\n👉 Gõ /dudoan để xem dự đoán!",
            m.chat.id, msg.message_id, parse_mode="Markdown"
        )
    Thread(target=tao_va_bao, daemon=True).start()

@bot.message_handler(commands=['capnhat'])
def cmd_capnhat(m):
    hom_nay = datetime.now().strftime("%d/%m/%Y")
    kq = lay_ket_qua_xsmb(hom_nay)
    if kq and save_data(hom_nay, kq["special"], kq["g1"], kq["loto"]):
        bot.send_message(m.chat.id,
            f"✅ **KẾT QUẢ HÔM NAY — {hom_nay}**\n"
            f"🎯 Đặc Biệt: `{kq['special']}`\n🥇 Giải Nhất: `{kq['g1']}`\n📌 Nguồn: {kq['source']}",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(m.chat.id, 
            f"⚠️ Không lấy được dữ liệu thật ngày {hom_nay}\n👉 Vui lòng thử lại sau hoặc gõ /lay90 để lấy dữ liệu lịch sử!",
            parse_mode="Markdown"
        )

# ✅ Gõ ngày VD: 29082026 → Xem kết quả lịch sử — KHÔNG TẠO SỐ GIẢ!
@bot.message_handler(func=lambda msg: re.fullmatch(r"\d{8}", msg.text.strip()))
def xem_lich_su(m):
    text = m.text.strip()
    try:
        d, mth, y = text[0:2], text[2:4], text[4:8]
        date_obj = datetime(int(y), int(mth), int(d))
        date_str = date_obj.strftime("%d/%m/%Y")
        data = load_data()
        
        if date_str in data:
            kq = data[date_str]
            bot.send_message(m.chat.id,
                f"📅 **KẾT QUẢ NGÀY: {date_str}**\n"
                f"🏆 Đặc Biệt: `{kq['special']}`\n🥇 Giải Nhất: `{kq['g1']}`\n🎟️ Số lô: {len(kq['loto'])} con",
                parse_mode="Markdown"
            )
        else:
            # ❌ KHÔNG TẠO SỐ GIẢ → báo rõ
            bot.send_message(m.chat.id,
                f"⚠️ Chưa có dữ liệu ngày: {date_str}\n"
                f"👉 Gõ /lay90 để lấy dữ liệu thật từ nguồn chính thống!",
                parse_mode="Markdown"
            )
    except ValueError:
        bot.send_message(m.chat.id, "⚠️ Sai định dạng! VD đúng: `29082026`", parse_mode="Markdown")

# ====================== 🚀 KHỞI ĐỘNG ======================
if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False), daemon=True).start()
    Thread(target=gui_tu_dong, daemon=True).start()
    print("✅ BOT ĐÃ CHẠY — V17.0 | CHỈ LƯU DỮ LIỆU THẬT, KHÔNG TẠO SỐ GIẢ!")
    bot.infinity_polling()
