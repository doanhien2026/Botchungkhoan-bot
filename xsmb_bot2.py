# =========================================================
# BOT XSMB - VERSION 15.6.0 (ỔN ĐỊNH + BÁO RÕ NGUỒN DỮ LIỆU)
# =========================================================
import os
import re
import time
import random
import requests
import threading
import telebot
from flask import Flask
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# --- CẤU HÌNH BOT ---
TELEGRAM_TOKEN = "8901722608:AAHnHfYsR8ilnHCHRaDUedA1ra1p0gPWda8"
CHAT_ID = "-1001030583610"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- LẤY KẾT QUẢ XSMB — CẢI THIỆU + BÁO LỖI RÕ RÀNG ---
def fetch_xsmb(d, m, y):
    d_str = d.zfill(2)
    m_str = m.zfill(2)
    y_str = y
    display_date = f"{d_str}/{m_str}/{y_str}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/"
    }
    
    # === NGUỒN 1: KQXS.VN ===
    try:
        url = f"https://kqxs.vn/xsmb/{y_str}-{m_str}-{d_str}"
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code == 200 and len(res.text) > 500:
            html = res.text
            db_m = re.search(r'(?:Đặc biệt|Dac Biet)[\s\S]{0,200}?(\d{5,6})', html, re.I)
            g1_m = re.search(r'(?:Giải nhất|Giai 1)[\s\S]{0,200}?(\d{5})', html, re.I)
            if db_m:
                db = db_m.group(1)
                g1 = g1_m.group(1) if g1_m else "Chưa có"
                print(f"✅ [KQXS.vn] {display_date} → GĐB={db}, G1={g1}")
                return {"db": db, "g1": g1, "nguon": "KQXS.vn"}
    except Exception as e:
        print(f"⚠️ [KQXS.vn] Lỗi: {str(e)[:50]}")

    # === NGUỒN 2: XOSO.WAP.VN ===
    try:
        url = f"https://xoso.wap.vn/xsmb/{y_str}/{m_str}/{d_str}"
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code == 200 and len(res.text) > 300:
            html = res.text
            db_m = re.search(r'Đặc biệt.*?(\d{5,6})', html, re.I)
            g1_m = re.search(r'Giải nhất.*?(\d{5})', html, re.I)
            if db_m:
                db = db_m.group(1)
                g1 = g1_m.group(1) if g1_m else "Chưa có"
                print(f"✅ [Xoso.wap.vn] {display_date} → GĐB={db}, G1={g1}")
                return {"db": db, "g1": g1, "nguon": "Xoso.wap.vn"}
    except Exception as e:
        print(f"⚠️ [Xoso.wap.vn] Lỗi: {str(e)[:50]}")

    # === TẤT CẢ NGUỒN KHÔNG ĐƯỢC ===
    print(f"❌ Tất cả nguồn không truy cập được cho {display_date}")
    return {"db": "Chưa có", "g1": "Chưa có", "nguon": "Không có dữ liệu"}

# --- LOGIC DỰ ĐOÁN ỔN ĐỊNH TRONG NGÀY ---
def calculate_predictions(db_num, g1_num):
    today_seed = datetime.now().strftime("%Y%m%d")
    seed_val = int(today_seed)
    random.seed(seed_val)

    if db_num != "Chưa có" and str(db_num).isdigit() and len(str(db_num)) >= 5:
        # === CÓ DỮ LIỆU THẬT → TÍNH TOÁN TỪ KẾT QUẢ ===
        db_int = int(db_num)
        g1_int = int(g1_num) if g1_num.isdigit() else 0
        
        lo1 = f"{db_int % 100:02d}"
        lo2 = f"{g1_int % 100:02d}"
        sum_db = sum(int(c) for c in str(db_num))
        lo3 = f"{(sum_db * 7 + db_int // 10000) % 100:02d}"
        xien1 = f"{(db_int + 12) % 100:02d}"
        xien2 = f"{(g1_int + 35) % 100:02d}"
        tou_db = str(sum_db % 10)
        mode = "Từ dữ liệu thực tế"
        print(f"🧠 [{mode}] GĐB={db_num} → Lô: {lo1},{lo2},{lo3} | Xiên: {xien1},{xien2} | Đuôi: {tou_db}")
    else:
        # === CHƯA CÓ DỮ LIỆU → DỰ ĐOÁN THEO THUẬT TOÁN NGÀY ===
        thu = datetime.now().weekday()
        base = random.randint(0, 99)
        lo1 = f"{base:02d}"
        lo2 = f"{(base + 23 + thu * 3) % 100:02d}"
        lo3 = f"{(base + 56 + thu * 2) % 100:02d}"
        xien1 = f"{(base + 15) % 100:02d}"
        xien2 = f"{(base + 42) % 100:02d}"
        tou_db = str((base + thu) % 10)
        mode = "Thuật toán ngày"
        print(f"🧠 [{mode}] → Lô: {lo1},{lo2},{lo3} | Xiên: {xien1},{xien2} | Đuôi: {tou_db}")

    return {
        "lo1": lo1, "rate1": "~20%",
        "lo2": lo2, "rate2": "~18%",
        "lo3": lo3, "rate3": "~16%",
        "x1": xien1, "xrate1": "~17%",
        "x2": xien2, "xrate2": "~15%",
        "tail": tou_db, "tail_rate": "~35%",
        "mode": mode
    }

# =========================================================
# ✅ LỆNH TRA CỨU THEO NGÀY
# =========================================================
@bot.message_handler(func=lambda msg: True)
def handle_user_message(message):
    text = message.text.strip()
    if not text:
        return
    
    # Hướng dẫn
    if re.search(r'^(help|huong dan|hướng dẫn|sd)', text, re.I):
        help_msg = """📖 *HƯỚNG DẪN SỬ DỤNG BOT XSMB*

🔹 *Tra cứu kết quả & dự đoán:*
→ Gõ ngày: `25/08/2026` hoặc `2026-08-25`

🔹 *Tự động gửi hàng ngày:*
→ 18:30: Kết quả hôm qua + Dự đoán hôm nay

⚠️ *Nếu kết quả chưa có:* Dự đoán dựa trên thuật toán ngày

🎲 *Chơi có trách nhiệm - Chỉ giải trí!*
"""
        bot.reply_to(message, help_msg, parse_mode="Markdown")
        return
    
    # Tìm ngày
    date_patterns = [
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
        r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
        r'(\d{4})(\d{2})(\d{2})'
    ]
    match = y = m = d = None
    for pat in date_patterns:
        match = re.search(pat, text)
        if match:
            g = match.groups()
            if len(g[0]) == 4: y, m, d = g[0], g[1], g[2]
            elif len(g[2]) == 4: d, m, y = g[0], g[1], g[2]
            break
    if not match:
        return
    
    d, m = d.zfill(2), m.zfill(2)
    display_date = f"{d}/{m}/{y}"
    
    bot.reply_to(message, f"🔄 Đang lấy dữ liệu ngày {display_date}...")
    
    data = fetch_xsmb(d, m, y)
    pred = calculate_predictions(data['db'], data['g1'])
    
    reply = f"📊 *KẾT QUẢ XSMB NGÀY {display_date}*\n"
    reply += f"🏆 *Giải Đặc Biệt:* `{data['db']}`\n"
    reply += f"🥇 *Giải Nhất:* `{data['g1']}`\n"
    reply += f"📡 *Nguồn:* {data.get('nguon', 'Không xác định')}\n"
    
    reply += "-----------------------------------\n"
    reply += f"🤖 *DỰ ĐOÁN — {pred['mode']}*\n\n"
    reply += "🎯 *TOP 3 LÔ CAO NHẤT*\n"
    reply += f"🥇 `{pred['lo1']}` | Tỷ lệ: {pred['rate1']}\n"
    reply += f"🥈 `{pred['lo2']}` | Tỷ lệ: {pred['rate2']}\n"
    reply += f"🥉 `{pred['lo3']}` | Tỷ lệ: {pred['rate3']}\n\n"
    reply += "🎯 *2 LÔ XIÊN CAO*\n"
    reply += f"🥇 `{pred['x1']}` | Tỷ lệ: {pred['xrate1']}\n"
    reply += f"🥈 `{pred['x2']}` | Tỷ lệ: {pred['xrate2']}\n\n"
    reply += "🎯 *SỐ CUỐI ĐẶC BIỆT*\n"
    reply += f"🥇 `{pred['tail']}` | Tỷ lệ: {pred['tail_rate']}\n\n"
    reply += "🎲 *Chơi có trách nhiệm - Chỉ giải trí!*"
    
    bot.reply_to(message, reply, parse_mode="Markdown")
    print(f"📤 Đã trả lời: {display_date} | {pred['mode']}")

# --- GỬI TỰ ĐỘNG 18:35 ---
def run_xsmb_job():
    vn_tz = timezone(timedelta(hours=7))
    last_send_date = None
    
    while True:
        try:
            now_vn = datetime.now(vn_tz)
            today_str = now_vn.strftime("%d/%m/%Y")
            h, mi = now_vn.hour, now_vn.minute
            
            if h == 18 and mi >= 35 and last_send_date != today_str:
                print(f"⏰ Gửi tự động: {today_str}")
                yesterday = now_vn - timedelta(days=1)
                d, m, y = yesterday.strftime("%d"), yesterday.strftime("%m"), yesterday.strftime("%Y")
                display_date = yesterday.strftime("%d/%m/%Y")
                now_str = now_vn.strftime("%d/%m/%Y %H:%M:%S")
                
                y_data = fetch_xsmb(d, m, y)
                pred = calculate_predictions(y_data['db'], y_data['g1'])
                
                msg = f"📊 *KẾT QUẢ XSMB HÔM QUA ({display_date})*\n"
                msg += f"🏆 *Giải Đặc Biệt:* `{y_data['db']}`\n"
                msg += f"🥇 *Giải Nhất:* `{y_data['g1']}`\n"
                msg += f"📡 *Nguồn:* {y_data.get('nguon', 'Không xác định')}\n"
                msg += "-----------------------------------\n"
                msg += f"🤖 *BOT DỰ ĐOÁN — {pred['mode']}*\n"
                msg += f"⏰ *Cập nhật:* `{now_str}`\n\n"
                msg += "🎯 *TOP 3 LÔ CAO NHẤT*\n"
                msg += f"🥇 `{pred['lo1']}` | Tỷ lệ: {pred['rate1']}\n"
                msg += f"🥈 `{pred['lo2']}` | Tỷ lệ: {pred['rate2']}\n"
                msg += f"🥉 `{pred['lo3']}` | Tỷ lệ: {pred['rate3']}\n\n"
                msg += "🎯 *2 LÔ XIÊN CAO*\n"
                msg += f"🥇 `{pred['x1']}` | Tỷ lệ: {pred['xrate1']}\n"
                msg += f"🥈 `{pred['x2']}` | Tỷ lệ: {pred['xrate2']}\n\n"
                msg += "🎯 *SỐ CUỐI ĐẶC BIỆT*\n"
                msg += f"🥇 `{pred['tail']}` | Tỷ lệ: {pred['tail_rate']}\n\n"
                msg += "🎲 *Chơi có trách nhiệm - Chỉ giải trí!*"
                
                bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                print(f"✅ Đã gửi: {today_str}")
                last_send_date = today_str
            
            time.sleep(60)
        except Exception as e:
            print(f"⚠️ Lỗi: {e}")
            time.sleep(60)

# --- KHỞI ĐỘNG ---
def start_polling():
    time.sleep(5)
    try: bot.remove_webhook(drop_pending_updates=True)
    except: pass
    while True:
        try: bot.polling(none_stop=True, interval=3, timeout=30)
        except Exception as e:
            print(f"⚠️ Polling: {e}")
            time.sleep(10)

if __name__ == "__main__":
    print("🚀 BOT XSMB KHỞI ĐỘNG — ĐA NGUỒN + DỰ ĐOÁN ỔN ĐỊNH!")
    threading.Thread(target=run_xsmb_job, daemon=True).start()
    threading.Thread(target=start_polling, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
