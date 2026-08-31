# ==========================================================
# BOT XSMB — V17.1 | ✅ THÊM LỆNH NHẬP THỦ CÔNG + NGUỒN MỚI
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

# ====================== 💾 QUẢN LÝ DỮ LIỆU ======================
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
    except:
        return {}

def save_data(date_str, special, g1, loto, source="thủ công"):
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", date_str):
        return False
    if len(special)!=5 or not special.isdigit():
        return False
    if len(g1)!=5 or not g1.isdigit():
        return False
    data = load_data()
    data[date_str] = {
        "special": special.strip(),
        "g1": g1.strip(),
        "loto": [str(x).zfill(2) for x in loto if str(x).isdigit() and len(str(x))==2],
        "source": source
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

# ====================== 🆕 LẤY DỮ LIỆU ======================
def lay_90_ngay_thuc():
    print("🚀 ĐANG LẤY DỮ LIỆU...")
    today = datetime.now()
    dem_thuc = 0
    data = load_data()

    for offset in range(1, ANALYSIS_DAYS + 1):
        target_date = today - timedelta(days=offset)
        date_str = target_date.strftime("%d/%m/%Y")
        if date_str in data:
            continue
        
        kq = lay_ket_qua_xsmb(date_str)
        if kq and save_data(date_str, kq["special"], kq["g1"], kq["loto"], kq.get("source", "api")):
            dem_thuc += 1
            print(f"✅ {date_str} | ĐB:{kq['special']}")
        time.sleep(1.5)
    
    tong = len(load_data())
    print(f"✅ HOÀN THÀNH! Tổng: {tong} ngày")
    return tong

# ====================== 📊 TÍNH DỰ ĐOÁN ======================
def get_pham_vi():
    data = load_data()
    if not data: return "--", "--"
    try:
        sap = sorted([datetime.strptime(k, "%d/%m/%Y") for k in data.keys()])
        return sap[0].strftime("%d/%m/%Y"), sap[-1].strftime("%d/%m/%Y")
    except: return "--", "--"

def tinh_du_doan():
    data = load_data()
    tong = len(data)
    if tong < 30:
        return f"⚠️ Cần ít nhất 30 ngày dữ liệu. Hiện có {tong} ngày.\n👉 Gõ /nhap để nhập kết quả thủ công!"
    
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
        return "⚠️ Dữ liệu lô trống."
    
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
📊 **DỰ ĐOÁN NGÀY MAI: {ngay_mai}**
📈 Phân tích: {so_ngay} ngày dữ liệu

🎯 **3 CON LÔ TỶ LỆ CAO NHẤT:**
   1 • `{top3[0]['so']}` → {top3[0]['lan']} lần | {top3[0]['ty_le']}%
   2 • `{top3[1]['so']}` → {top3[1]['lan']} lần | {top3[1]['ty_le']}%
   3 • `{top3[2]['so']}` → {top3[2]['lan']} lần | {top3[2]['ty_le']}%

🔀 **XIÊN:** `{xien[0]}` + `{xien[1]}`
🔢 **ĐẦU ĐỀ:** `{dau_de}` | {ty_le_dau}%

⚠️ Chỉ tham khảo — Không đảm bảo 100%!
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
                kq = lay_ket_qua_xsmb(hom_nay)
                if kq:
                    save_data(hom_nay, kq["special"], kq["g1"], kq["loto"], kq["source"])
                    bot.send_message(CHAT_ID,
                        f"🏆 **KẾT QUẢ: {hom_nay}**\n🎯 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`",
                        parse_mode="Markdown"
                    )
                da_gui_kq.add(hom_nay)
            
            if gio == SEND_PREDICT_TIME and hom_nay not in da_gui_dd:
                bot.send_message(CHAT_ID, tinh_du_doan(), parse_mode="Markdown")
                da_gui_dd.add(hom_nay)
            
            time.sleep(30)
        except Exception as e:
            print(f"⚠️ Lỗi: {e}")
            time.sleep(10)

# ====================== 📋 LỆNH BOT ======================
@app.route('/')
def home(): return "✅ Bot XSMB V17.1"

@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id,
        "🤖 **BOT XSMB — V17.1**\n"
        "✅ /lay90 = Lấy dữ liệu từ nguồn\n"
        "✅ /nhap = Nhập kết quả thủ công (ĐB G1)\n"
        "✅ /dudoan = Xem dự đoán\n"
        "✅ /status = Xem dữ liệu đã lưu\n\n"
        "📌 Gõ /nhap 29082026 50460 73250 → nhập kết quả!",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    tu, den = get_pham_vi()
    bot.send_message(m.chat.id,
        f"📊 **TRẠNG THÁI DỮ LIỆU**\n"
        f"• Tổng ngày: **{len(load_data())} ngày**\n"
        f"• Phạm vi: **{tu} → {den}**",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['dudoan'])
def cmd_dudoan(m):
    bot.send_message(m.chat.id, tinh_du_doan(), parse_mode="Markdown")

@bot.message_handler(commands=['lay90'])
def cmd_lay90(m):
    msg = bot.send_message(m.chat.id, "🚀 ĐANG LẤY DỮ LIỆU...\n⏰ Khoảng 2-3 phút!")
    def lay():
        tong = lay_90_ngay_thuc()
        bot.edit_message_text(f"✅ **HOÀN THÀNH!** {tong} ngày dữ liệu.\n👉 Gõ /dudoan để xem dự đoán!", m.chat.id, msg.message_id, parse_mode="Markdown")
    Thread(target=lay, daemon=True).start()

# ✅ LỆNH QUAN TRỌNG: NHẬP KẾT QUẢ THỦ CÔNG!
# Định dạng: /nhap 29082026 50460 73250
@bot.message_handler(commands=['nhap'])
def cmd_nhap(m):
    text = m.text.strip()
    parts = text.split()
    if len(parts) < 4:
        bot.send_message(m.chat.id,
            "⚠️ **Định dạng sai!**\n"
            "✅ Cách gõ: `/nhap 29082026 50460 73250`\n"
            "→ Ngày ĐặcBiệt GiảiNhất",
            parse_mode="Markdown"
        )
        return
    
    try:
        cmd, ngay_str, db, g1 = parts[0], parts[1], parts[2], parts[3]
        d, mth, y = ngay_str[0:2], ngay_str[2:4], ngay_str[4:8]
        date_obj = datetime(int(y), int(mth), int(d))
        date_formatted = date_obj.strftime("%d/%m/%Y")
        
        if len(db) != 5 or not db.isdigit():
            bot.send_message(m.chat.id, f"⚠️ Đặc Biệt phải 5 chữ số: {db}")
            return
        if len(g1) != 5 or not g1.isdigit():
            bot.send_message(m.chat.id, f"⚠️ Giải Nhất phải 5 chữ số: {g1}")
            return
        
        # Tạo danh sách lô từ ĐB và G1 (tối thiểu đủ để tính)
        loto = [db[-2:], g1[-2:]]
        for i in range(10):
            loto.append(f"{i:02d}")
        
        if save_data(date_formatted, db, g1, loto, "thủ công"):
            bot.send_message(m.chat.id,
                f"✅ **ĐÃ LƯU KẾT QUẢ!**\n"
                f"📅 Ngày: {date_formatted}\n"
                f"🎯 Đặc Biệt: `{db}`\n"
                f"🥇 Giải Nhất: `{g1}`\n"
                f"📌 Nguồn: Thủ công\n\n"
                f"👉 Tiếp tục nhập ngày khác hoặc gõ /dudoan!",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(m.chat.id, "❌ Lỗi lưu dữ liệu!")
    except Exception as e:
        bot.send_message(m.chat.id, f"⚠️ Sai định dạng! VD: `/nhap 29082026 50460 73250`\nLỗi: {e}", parse_mode="Markdown")

# Xem lịch sử
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
                f"📅 **KẾT QUẢ: {date_str}**\n"
                f"🏆 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n📌 Nguồn: {kq.get('source', 'không rõ')}",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(m.chat.id,
                f"⚠️ Chưa có dữ liệu ngày: {date_str}\n"
                f"👉 Gõ: `/nhap {text} 12345 67890` để nhập kết quả!",
                parse_mode="Markdown"
            )
    except:
        bot.send_message(m.chat.id, "⚠️ Sai định dạng! VD: `29082026`", parse_mode="Markdown")

# ====================== 🚀 KHỞI ĐỘNG ======================
if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False), daemon=True).start()
    Thread(target=gui_tu_dong, daemon=True).start()
    print("✅ BOT V17.1 ĐÃ CHẠY — CÓ LỆNH /nhap NHẬP KẾT QUẢ THỦ CÔNG!")
    bot.infinity_polling()
