# ==========================================================
# main.py — V26.0 | GỌI fetcher + data_manager | LOG RÕ RÀNG
# Token: 8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w
# Chat ID: -1001030583610
# ==========================================================

import telebot, time, threading
from datetime import datetime, timedelta
from flask import Flask
from collections import Counter
from fetcher import lay_ket_qua_xsmb
from data_manager import load_data, save_data, get_stats

# ====================== CẤU HÌNH ======================
TELEGRAM_TOKEN = "8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w"
CHAT_ID = "-1001030583610"
PORT = 10000
ANALYSIS_DAYS = 90
SEND_RESULT_TIME = "18:40"
SEND_PREDICT_TIME = "18:41"

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)

# ====================== ROOT WEB ======================
@app.route('/')
def home():
    return "✅ Bot XSMB V26.0 — Đã sẵn sàng!"

# ====================== LỆNH BOT ======================
@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id,
        "🤖 *BOT XSMB — V26.0 | LẤY DỮ LIỆU THẬT ✅*\n"
        "/lay90 = Lấy 90 ngày dữ liệu\n"
        "/status = Xem trạng thái dữ liệu\n"
        "/dudoan = Xem dự đoán\n"
        "Ngày VD: 29082026 → Xem kết quả ngày cũ\n\n"
        "📌 Gõ /lay90 → Bắt đầu lấy dữ liệu thật!",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    tong, tu, den = get_stats()
    bot.send_message(m.chat.id,
        f"📊 *TRẠNG THÁI DỮ LIỆU*\n"
        f"• Tổng ngày đã lưu: *{tong} ngày*\n"
        f"• Phạm vi: {tu} → {den}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['lay90'])
def cmd_lay90(m):
    bot.send_message(m.chat.id, "🚀 *ĐANG LẤY 90 NGÀY DỮ LIỆU...*\n⏰ Vui lòng chờ 2-3 phút!", parse_mode="Markdown")
    
    def lay_async():
        today = datetime.now()
        lay_moi = 0
        that_bai = 0
        
        for offset in range(1, ANALYSIS_DAYS + 1):
            target_date = today - timedelta(days=offset)
            date_str = target_date.strftime("%d/%m/%Y")
            
            data = load_data()
            if date_str in data:
                continue  # Đã có → bỏ qua
            
            kq = lay_ket_qua_xsmb(date_str)
            if kq and save_data(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"]):
                lay_moi += 1
            else:
                that_bai += 1
            
            time.sleep(0.8)  # Tránh bị chặn API
        
        tong, _, _ = get_stats()
        bot.send_message(m.chat.id,
            f"✅ *HOÀN THÀNH!* 🎉\n"
            f"📊 Tổng dữ liệu: {tong} ngày\n"
            f"• Lấy mới: {lay_moi} ngày\n"
            f"• Không lấy được: {that_bai} ngày\n\n"
            f"👉 Gõ /dudoan để xem dự đoán!",
            parse_mode="Markdown"
        )
    
    threading.Thread(target=lay_async, daemon=True).start()

@bot.message_handler(commands=['dudoan'])
def cmd_dudoan(m):
    data = load_data()
    tong = len(data)
    if tong < 30:
        bot.send_message(m.chat.id, f"⚠️ Cần ít nhất 30 ngày dữ liệu. Hiện có {tong} ngày.\n👉 Gõ /lay90 trước!")
        return
    
    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    so_ngay = min(ANALYSIS_DAYS, tong)
    ds = sap_xep[:so_ngay]
    
    tat_ca_lo, tat_ca_dau = [], []
    for ngay in ds:
        kq = data[ngay]
        for lo in kq.get("loto", []):
            if len(lo) == 2 and lo.isdigit():
                tat_ca_lo.append(lo)
        db = kq.get("special", "")
        if len(db) == 5 and db.isdigit():
            tat_ca_lo.append(db[-2:])
            tat_ca_dau.append(db[0])
    
    dem_lo = Counter(tat_ca_lo)
    ds_lo = [{"so": s, "lan": c, "ty_le": round(c / so_ngay * 100, 1)} for s, c in dem_lo.items()]
    ds_lo.sort(key=lambda x: -x["ty_le"])
    top3 = ds_lo[:3]
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3) >= 2 else ["00", "01"]
    
    dau_de, ty_le_dau = "9", 10.0
    if tat_ca_dau:
        d = Counter(tat_ca_dau).most_common(1)[0]
        dau_de, ty_le_dau = d[0], round(d[1] / len(tat_ca_dau) * 100, 1)
    
    ngay_mai = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    bot.send_message(m.chat.id,
        f"📊 *DỰ ĐOÁN NGÀY MAI: {ngay_mai}*\n"
        f"📈 Phân tích: {so_ngay} ngày dữ liệu thật\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *3 CON LÔ TỶ LỆ CAO NHẤT:*\n"
        f"   1 • `{top3[0]['so']}` → {top3[0]['lan']} lần | {top3[0]['ty_le']}%\n"
        f"   2 • `{top3[1]['so']}` → {top3[1]['lan']} lần | {top3[1]['ty_le']}%\n"
        f"   3 • `{top3[2]['so']}` → {top3[2]['lan']} lần | {top3[2]['ty_le']}%\n"
        f"\n🔀 *CẶP LÔ XIÊN:* `{xien[0]}` + `{xien[1]}`\n"
        f"\n🔢 *ĐẦU SỐ ĐỀ:* `{dau_de}` | {ty_le_dau}%\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ Chỉ tham khảo!",
        parse_mode="Markdown"
    )

# Xem ngày cũ
@bot.message_handler(func=lambda msg: msg.text and len(msg.text.strip()) == 8 and msg.text.strip().isdigit())
def xem_ngay_cu(m):
    text = m.text.strip()
    try:
        d, mo, y = text[:2], text[2:4], text[4:]
        date_str = f"{d}/{mo}/{y}"
        data = load_data()
        if date_str in data:
            kq = data[date_str]
            bot.send_message(m.chat.id,
                f"📅 *KẾT QUẢ NGÀY: {date_str}*\n"
                f"🏆 Đặc biệt: `{kq['special']}`\n"
                f"🥇 Giải nhất: `{kq['g1']}`\n"
                f"📌 Nguồn: {kq.get('source', 'không rõ')}",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(m.chat.id, f"⚠️ Chưa có dữ liệu ngày {date_str}. Gõ /lay90 trước!")
    except:
        bot.send_message(m.chat.id, "⚠️ Sai định dạng! VD: 29082026")

# ====================== CHẠY BOT ======================
def run_bot():
    print("✅ BOT V26.0 ĐÃ SẴN SÀNG — LẤY DỮ LIỆU THẬT!")
    try:
        bot.remove_webhook()
    except:
        pass
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=40, allowed_updates=None)
        except Exception as e:
            print(f"⚠️ Lỗi polling: {e} → thử lại sau 5s...")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False), daemon=True).start()
    run_bot()
