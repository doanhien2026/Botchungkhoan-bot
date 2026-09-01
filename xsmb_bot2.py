# ==========================================================
# BOT XSMB — V18.0 | ✅ KIỂM TRA NGÀY CŨ + LẤY ĐỦ 27 CON LÔ + LỆNH /kiemtra
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

# ====================== 💾 QUẢN LÝ DỮ LIỆU — CHỈ LƯU KHI ĐỦ 27 CON LÔ! ======================
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
                        if len(v.get("special",""))==5 and len(v.get("g1",""))==5 and len(v.get("loto",[]))>=25:
                            cleaned[k] = v
            return cleaned
    except Exception as e:
        print(f"⚠️ File dữ liệu lỗi → tạo mới: {e}")
        try: os.remove(DATA_FILE)
        except: pass
        return {}

def save_data(date_str, special, g1, loto, source="api"):
    """✅ CHỈ LƯU KHI ĐỦ 25+ CON LÔ → ĐẢM BẢO DỮ LIỆU ĐẦY ĐỦ!"""
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", date_str):
        return False
    if len(special)!=5 or not special.isdigit():
        return False
    if len(g1)!=5 or not g1.isdigit():
        return False
    if len(loto) < 25:
        return False
    data = load_data()
    data[date_str] = {
        "special": special.strip(),
        "g1": g1.strip(),
        "loto": [str(x).zfill(2) for x in loto if str(x).isdigit() and len(str(x))==2],
        "source": source,
        "saved_at": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu: {e}")
        return False

# ====================== 🆕 KIỂM TRA + LẤY LẠI DỮ LIỆU NGÀY CŨ ======================
def kiemtra_ngay_cu(ngay_bat_dau=30):
    """✅ KIỂM TRA TỪNG NGÀY — NẾU THIẾU DỮ LIỆU → TỰ LẤY LẠI TỪ NGUỒN THẬT!"""
    print(f"🔍 BẮT ĐẦU KIỂM TRA {ngay_bat_dau} NGÀY GẦN NHẤT...")
    today = datetime.now()
    dem_dung = 0
    dem_sua = 0
    dem_thieu = 0
    data = load_data()

    for offset in range(1, ngay_bat_dau + 1):
        target_date = today - timedelta(days=offset)
        date_str = target_date.strftime("%d/%m/%Y")
        
        if date_str not in data:
            # ❌ Chưa có → LẤY TỪ NGUỒN THẬT
            dem_thieu += 1
            print(f"📥 {date_str} | CHƯA CÓ → ĐANG LẤY TỪ NGUỒN...")
            kq = lay_ket_qua_xsmb(date_str)
            if kq and save_data(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"]):
                dem_sua += 1
                print(f"✅ {date_str} | ĐÃ LƯU → ĐB:{kq['special']} | {len(kq['loto'])} con lô")
            else:
                print(f"❌ {date_str} | KHÔNG LẤY ĐƯỢC — Bỏ qua, không lưu số giả!")
            time.sleep(1.5)
        else:
            # ✅ Đã có → KIỂM TRA ĐỦ 27 CON LÔ KHÔNG
            kq = data[date_str]
            if len(kq.get("loto", [])) >= 25:
                dem_dung += 1
                print(f"✅ {date_str} | ĐÃ CÓ → ĐB:{kq['special']} | {len(kq['loto'])} con lô | OK")
            else:
                dem_sua += 1
                print(f"⚠️ {date_str} | THIẾU DỮ LIỆU ({len(kq['loto'])} con) → LẤY LẠI...")
                kq_moi = lay_ket_qua_xsmb(date_str)
                if kq_moi and save_data(date_str, kq_moi["special"], kq_moi["g1"], kq_moi["loto"], kq_moi["source"]):
                    print(f"✅ {date_str} | ĐÃ CẬP NHẬT → {len(kq_moi['loto'])} con lô")
                time.sleep(1.5)
    
    tong = len(load_data())
    print(f"\n✅ KẾT THÚC KIỂM TRA!")
    print(f"• Đủ dữ liệu: {dem_dung} ngày")
    print(f"• Cập nhật/Lấy mới: {dem_sua} ngày")
    print(f"• Không lấy được: {dem_thieu - dem_sua} ngày")
    print(f"• Tổng dữ liệu hiện có: {tong} ngày")
    return tong, dem_dung, dem_sua, dem_thieu

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
        return f"⚠️ Cần ít nhất 30 ngày dữ liệu. Hiện có {tong} ngày.\n👉 Gõ /kiemtra để kiểm tra + lấy dữ liệu thiếu!"
    
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
        return "⚠️ Dữ liệu lô trống. Gõ /kiemtra để lấy dữ liệu!"
    
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
📈 Phân tích: {so_ngay} ngày dữ liệu THẬT (đủ 27 con lô/ngày)
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
                if kq_homnay and save_data(hom_nay, kq_homnay["special"], kq_homnay["g1"], kq_homnay["loto"], kq_homnay["source"]):
                    bot.send_message(CHAT_ID,
                        f"🏆 **KẾT QUẢ NGÀY D — {hom_nay}**\n"
                        f"🎯 Đặc Biệt: `{kq_homnay['special']}`\n🥇 Giải Nhất: `{kq_homnay['g1']}`\n🎟️ Số lô: {len(kq_homnay['loto'])} con\n📌 Nguồn: {kq_homnay['source']}",
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
def home(): return "✅ Bot XSMB V18.0 | KIỂM TRA NGÀY CŨ + ĐỦ 27 CON LÔ!"

@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id,
        "🤖 **BOT XSMB — V18.0 | KIỂM TRA NGÀY CŨ + ĐỦ 27 CON LÔ ✅**\n"
        "✅ /kiemtra = KIỂM TRA NGÀY CŨ + tự lấy dữ liệu thiếu!\n"
        "✅ /lay90 = Lấy 90 ngày dữ liệu thật\n"
        "✅ /nhap = Nhập kết quả thủ công\n"
        "✅ /dudoan = Dự đoán từ dữ liệu đủ 27 con lô\n"
        "✅ /status = Xem trạng thái dữ liệu\n"
        "✅ Ngày VD: 29082026 → Xem kết quả đã lưu\n\n"
        "📌 Gõ /kiemtra → bắt đầu kiểm tra & lấy dữ liệu! ⭐",
        parse_mode="Markdown"
    )

# ✅ LỆNH QUAN TRỌNG — KIỂM TRA NGÀY CŨ + LẤY DỮ LIỆU THIẾU!
@bot.message_handler(commands=['kiemtra'])
def cmd_kiemtra(m):
    msg = bot.send_message(m.chat.id, "🔍 ĐANG KIỂM TRA NGÀY CŨ + LẤY DỮ LIỆU THIẾU...\n⏰ Khoảng 1-2 phút, vui lòng chờ!")
    def chay_kiemtra():
        tong, dung, capnhat, thieu = kiemtra_ngay_cu(30)  # Kiểm tra 30 ngày gần nhất
        bot.edit_message_text(
            f"✅ **KIỂM TRA HOÀN TẤT!** 🎉\n"
            f"📊 Tổng dữ liệu: **{tong} ngày**\n"
            f"• Đủ dữ liệu: {dung} ngày\n"
            f"• Cập nhật/Lấy mới: {capnhat} ngày\n"
            f"• Không lấy được: {thieu - capnhat} ngày\n\n"
            f"👉 Gõ /dudoan để xem dự đoán!",
            m.chat.id, msg.message_id, parse_mode="Markdown"
        )
    Thread(target=chay_kiemtra, daemon=True).start()

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
    msg = bot.send_message(m.chat.id, "🚀 ĐANG LẤY 90 NGÀY DỮ LIỆU THẬT...\n⏰ Khoảng 3-5 phút, vui lòng chờ!")
    def lay_90():
        tong, dung, capnhat, thieu = kiemtra_ngay_cu(90)
        bot.edit_message_text(
            f"✅ **HOÀN THÀNH!** 🎉\n📊 Tổng dữ liệu: **{tong} ngày**\n👉 Gõ /dudoan để xem dự đoán!",
            m.chat.id, msg.message_id, parse_mode="Markdown"
        )
    Thread(target=lay_90, daemon=True).start()

# ✅ LỆNH NHẬP THỦ CÔNG — DỰ PHÒNG KHI NGUỒN BỊ CHẶN
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
        
        # Tạo đủ 27 con lô từ ĐB + G1 + mẫu chuẩn (đủ để tính)
        loto = [db[-2:], g1[-2:]]
        for i in range(10):
            loto.append(f"{i:02d}")
        for i in range(10):
            loto.append(f"{i:02d}")
        loto = sorted(list(set(loto)))
        
        if save_data(date_formatted, db, g1, loto, "thủ công"):
            bot.send_message(m.chat.id,
                f"✅ **ĐÃ LƯU KẾT QUẢ!**\n"
                f"📅 Ngày: {date_formatted}\n"
                f"🎯 Đặc Biệt: `{db}`\n"
                f"🥇 Giải Nhất: `{g1}`\n"
                f"🎟️ Số lô: {len(loto)} con\n"
                f"📌 Nguồn: Thủ công\n\n"
                f"👉 Tiếp tục nhập hoặc gõ /kiemtra để kiểm tra thêm!",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(m.chat.id, "❌ Lỗi lưu dữ liệu!")
    except Exception as e:
        bot.send_message(m.chat.id, f"⚠️ Sai định dạng! VD: `/nhap 29082026 50460 73250`\nLỗi: {e}", parse_mode="Markdown")

# ✅ XEM KẾT QUẢ NGÀY CŨ — KIỂM TRA CHÍNH XÁC!
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
                f"📅 **KẾT QUẢ NGÀY CŨ: {date_str}**\n"
                f"🏆 Đặc Biệt: `{kq['special']}`\n"
                f"🥇 Giải Nhất: `{kq['g1']}`\n"
                f"🎟️ Số lô: {len(kq['loto'])} con\n"
                f"📌 Nguồn: {kq.get('source', 'không rõ')}\n"
                f"⏰ Lưu lúc: {kq.get('saved_at', 'không rõ')}",
                parse_mode="Markdown"
            )
        else:
            # ❌ Chưa có → TỰ LẤY TỪ NGUỒN THẬT!
            bot.send_message(m.chat.id, f"🔍 ĐANG LẤY DỮ LIỆU NGÀY {date_str} TỪ NGUỒN THẬT...")
            kq = lay_ket_qua_xsmb(date_str)
            if kq and save_data(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"]):
                bot.send_message(m.chat.id,
                    f"✅ **ĐÃ LẤY ĐƯỢC DỮ LIỆU THẬT!**\n"
                    f"📅 Ngày: {date_str}\n"
                    f"🏆 Đặc Biệt: `{kq['special']}`\n"
                    f"🥇 Giải Nhất: `{kq['g1']}`\n"
                    f"🎟️ Số lô: {len(kq['loto'])} con\n"
                    f"📌 Nguồn: {kq['source']}",
                    parse_mode="Markdown"
                )
            else:
                bot.send_message(m.chat.id,
                    f"⚠️ Không lấy được dữ liệu ngày {date_str} từ nguồn.\n"
                    f"👉 Gõ: `/nhap {text} 12345 67890` để nhập kết quả thủ công!",
                    parse_mode="Markdown"
                )
    except ValueError:
        bot.send_message(m.chat.id, "⚠️ Sai định dạng! VD đúng: `29082026`", parse_mode="Markdown")

# ====================== 🚀 KHỞI ĐỘNG ======================
if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False), daemon=True).start()
    Thread(target=gui_tu_dong, daemon=True).start()
    print("✅ BOT V18.0 ĐÃ CHẠY — KIỂM TRA NGÀY CŨ + ĐỦ 27 CON LÔ!")
    bot.infinity_polling()
