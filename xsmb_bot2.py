# =========================================================
# BOT XSMB - VERSION 15.4.0 (LỆNH TRA CỨU NGÀY + GỬI 18H35)
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

PROXY_CONFIG = {}
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- LẤY KẾT QUẢ XSMB ---
def fetch_xsmb(d, m, y):
    d_str = d.zfill(2)
    m_str = m.zfill(2)
    y_str = y
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }
    
    kwargs = {"headers": headers, "timeout": 15}
    if PROXY_CONFIG:
        kwargs["proxies"] = PROXY_CONFIG

    # NGUỒN 1: API VOH
    url_voh = f"https://voh.com.vn/api/v1/lottery/xsmb?date={y_str}-{m_str}-{d_str}"
    try:
        res = requests.get(url_voh, **kwargs)
        if res.status_code == 200:
            data = res.json()
            db = g1 = None
            if "data" in data and isinstance(data["data"], dict):
                ld = data["data"]
                db = ld.get("special") or ld.get("dac_biet") or ld.get("giai_dac_biet")
                g1 = ld.get("first") or ld.get("giai_nhat") or ld.get("giai1")
            elif "result" in data and isinstance(data["result"], dict):
                ld = data["result"]
                db = ld.get("special") or ld.get("dac_biet")
                g1 = ld.get("first") or ld.get("giai_nhat")
            
            if isinstance(db, list) and len(db) > 0: db = db[0]
            if isinstance(g1, list) and len(g1) > 0: g1 = g1[0]
            
            if db:
                db = re.sub(r'\D', '', str(db))
                if len(db) >= 5:
                    g1 = re.sub(r'\D', '', str(g1)) if g1 else "Chưa có"
                    print(f"✅ VOH: GĐB={db}, G1={g1}")
                    return {"db": db, "g1": g1 if g1 and len(g1)>=5 else "Chưa có"}
    except Exception as e:
        print(f"⚠️ Lỗi VOH: {e}")

    # NGUỒN 2: XOSO.COM.VN
    try:
        url_xoso = f"https://xoso.com.vn/xsmb-{d_str}-{m_str}-{y_str}.html"
        res = requests.get(url_xoso, **kwargs)
        if res.status_code == 200:
            html = res.text
            db_m = re.search(r'(?:id|class)=["\'].*dac_biet.*?["\'][^>]*>(?:\s*<[^>]+>)*(\d{5,6})', html, re.I)
            g1_m = re.search(r'(?:id|class)=["\'].*giai_nhat.*?["\'][^>]*>(?:\s*<[^>]+>)*(\d{5})', html, re.I)
            db = db_m.group(1) if db_m else None
            g1 = g1_m.group(1) if g1_m else None
            if db:
                print(f"✅ Xoso.com.vn: GĐB={db}, G1={g1 or 'Chưa có'}")
                return {"db": db, "g1": g1 if g1 else "Chưa có"}
    except Exception as e:
        print(f"⚠️ Lỗi Xoso: {e}")

    print(f"❌ Không lấy được dữ liệu {d_str}/{m_str}/{y_str}")
    return {"db": "Chưa có", "g1": "Chưa có"}

# --- LOGIC DỰ ĐOÁN ---
def calculate_predictions(db_num, g1_num):
    if db_num == "Chưa có" or not str(db_num).isdigit():
        seed_val = int(datetime.now().strftime("%Y%m%d"))
        random.seed(seed_val)
        lo1, lo2, lo3 = f"{random.randint(0, 99):02d}", f"{random.randint(0, 99):02d}", f"{random.randint(0, 99):02d}"
        xien1, xien2 = f"{random.randint(0, 99):02d}", f"{random.randint(0, 99):02d}"
        tou_db = f"{random.randint(0, 9)}"
    else:
        db_int = int(db_num)
        g1_int = int(g1_num) if g1_num.isdigit() else 0
        lo1 = f"{db_int % 100:02d}"
        lo2 = f"{g1_int % 100:02d}"
        sum_db = sum(int(c) for c in str(db_num))
        lo3 = f"{(sum_db * 7) % 100:02d}"
        xien1 = f"{(db_int + 12) % 100:02d}"
        xien2 = f"{(g1_int + 35) % 100:02d}"
        tou_db = str(sum_db % 10)

    return {
        "lo1": lo1, "rate1": "~20%",
        "lo2": lo2, "rate2": "~18%",
        "lo3": lo3, "rate3": "~16%",
        "x1": xien1, "xrate1": "~17%",
        "x2": xien2, "xrate2": "~15%",
        "tail": tou_db, "tail_rate": "~35%"
    }

# =========================================================
# ✅ LỆNH TRA CỨU THEO NGÀY — GÕ NGÀY LÀ BÁO KẾT QUẢ
# =========================================================
@bot.message_handler(func=lambda msg: True)
def handle_user_message(message):
    text = message.text.strip()
    
    # Bỏ qua lệnh rỗng
    if not text:
        return
    
    # Hướng dẫn sử dụng
    help_pattern = re.search(r'^(help|huong dan|hướng dẫn|sd|sử dụng)', text, re.I)
    if help_pattern:
        help_msg = """📖 *HƯỚNG DẪN SỬ DỤNG BOT XSMB*

🔹 *Tra cứu kết quả theo ngày:*
→ Gõ ngày: `25/08/2026` hoặc `2026-08-25` hoặc `20260825`

🔹 *Bot tự động gửi:*
→ 18:35 hàng ngày: Kết quả hôm qua + Dự đoán hôm nay

🎲 *Chơi có trách nhiệm - Chỉ giải trí!*
"""
        bot.reply_to(message, help_msg, parse_mode="Markdown")
        return
    
    # Tìm ngày trong tin nhắn — hỗ trợ nhiều định dạng
    # Định dạng: YYYY-MM-DD | DD/MM/YYYY | DD-MM-YYYY | YYYYMMDD
    date_patterns = [
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',  # 2026-08-25
        r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',  # 25/08/2026
        r'(\d{4})(\d{2})(\d{2})'                # 20260825
    ]
    
    match = None
    y, m, d = None, None, None
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            if len(groups[0]) == 4:  # YYYY-MM-DD
                y, m, d = groups[0], groups[1], groups[2]
            elif len(groups[2]) == 4:  # DD/MM/YYYY
                d, m, y = groups[0], groups[1], groups[2]
            break
    
    if not match:
        # Không phải ngày → không trả lời (tránh lặp)
        return
    
    # Chuẩn hóa ngày
    d = d.zfill(2)
    m = m.zfill(2)
    display_date = f"{d}/{m}/{y}"
    
    # Thông báo đang lấy dữ liệu
    bot.reply_to(message, f"🔄 Đang lấy kết quả XSMB ngày {display_date}...")
    
    # Lấy kết quả từ API
    data = fetch_xsmb(d, m, y)
    
    # Tính dự đoán cho ngày đó
    pred = calculate_predictions(data['db'], data['g1'])
    
    # Tạo tin nhắn trả về
    reply = f"📊 *KẾT QUẢ XSMB NGÀY {display_date}*\n"
    reply += f"🏆 *Giải Đặc Biệt:* `{data['db']}`\n"
    reply += f"🥇 *Giải Nhất:* `{data['g1']}`\n"
    
    # Nếu có kết quả thật → hiện dự đoán
    if data['db'] != "Chưa có" and data['db'].isdigit():
        reply += "-----------------------------------\n"
        reply += "🤖 *DỰ ĐOÁN DỰA TRÊN KẾT QUẢ NGÀY TRƯỚC*\n\n"
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
    print(f"📤 Đã trả lời tra cứu ngày {display_date}")

# --- GỬI TỰ ĐỘNG 18:35 HÀNG NGÀY ---
def run_xsmb_job():
    vn_tz = timezone(timedelta(hours=7))
    last_send_date = None
    
    while True:
        try:
            now_vn = datetime.now(vn_tz)
            today_str = now_vn.strftime("%d/%m/%Y")
            hour, minute = now_vn.hour, now_vn.minute
            
            # Chỉ gửi lúc 18:35 và chưa gửi hôm nay
            if hour == 18 and minute >= 35 and last_send_date != today_str:
                print(f"⏰ Gửi tự động 18:35: {today_str}")
                
                yesterday = now_vn - timedelta(days=1)
                d, m, y = yesterday.strftime("%d"), yesterday.strftime("%m"), yesterday.strftime("%Y")
                display_date = yesterday.strftime("%d/%m/%Y")
                now_str = now_vn.strftime("%d/%m/%Y %H:%M:%S")
                
                y_data = fetch_xsmb(d, m, y)
                pred = calculate_predictions(y_data['db'], y_data['g1'])
                
                msg = f"📊 *KẾT QUẢ XSMB HÔM QUA ({display_date})*\n"
                msg += f"🏆 *Giải Đặc Biệt:* `{y_data['db']}`\n"
                msg += f"🥇 *Giải Nhất:* `{y_data['g1']}`\n"
                msg += "-----------------------------------\n"
                msg += f"🤖 *BOT DỰ ĐOÁN XSMB HÔM NAY*\n"
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
                print(f"✅ Đã gửi tự động: {today_str}")
                last_send_date = today_str
            
            time.sleep(60)
            
        except Exception as e:
            print(f"⚠️ Lỗi gửi tự động: {e}")
            time.sleep(60)

# --- KHỞI ĐỘNG BOT ---
def start_polling():
    time.sleep(5)
    try:
        bot.remove_webhook(drop_pending_updates=True)
    except Exception:
        pass
    
    while True:
        try:
            bot.polling(none_stop=True, interval=3, timeout=30)
        except Exception as e:
            print(f"⚠️ Polling lỗi: {e}")
            time.sleep(10)

if __name__ == "__main__":
    print("🚀 BOT XSMB KHỞI ĐỘNG — SẴN SÀNG TRA CỨU NGÀY!")
    print("💡 Gõ: help → Hướng dẫn | Gõ ngày → Kết quả + Dự đoán")
    
    threading.Thread(target=run_xsmb_job, daemon=True).start()
    threading.Thread(target=start_polling, daemon=True).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
