import os
import json
import time
import re
import threading
import telebot
from collections import Counter
from flask import Flask

from config import TELEGRAM_TOKEN, CHAT_ID, DATA_FILE, PORT
from fetcher import get_xsmb_result, get_now_vn

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@app.route('/')
def home():
    return "✅ Bot XSMB Active!", 200

def run_server():
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"history": [], "last_date": "", "updated_at": ""}

def save_data(data):
    try:
        data["updated_at"] = get_now_vn().strftime("%d/%m/%Y %H:%M:%S")
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Lỗi lưu file: {e}")

def analyze(history):
    if not history: 
        return None
        
    all_loto = []
    dau_de_list = []
    
    for day in history:
        all_loto.extend(day.get("loto", []))
        sp = str(day.get("special", ""))
        if len(sp) >= 2:
            dau_de_list.append(sp[-2])

    if not all_loto: 
        return None

    tong_ngay = max(len(history), 1)
    freq = Counter(all_loto)
    top3 = freq.most_common(3)
    while len(top3) < 3: 
        top3.append(("00", 1))
    top5 = freq.most_common(5)
    xien = top3[1:] + [top5[3]] if len(top5) >= 4 else top3[1:]

    top_dau_de = "0"
    if dau_de_list:
        freq_dau = Counter(dau_de_list)
        top_dau_de = freq_dau.most_common(1)[0][0]

    return {
        "top3": [{"num": n[0], "rate": f"~{round(n[1]/tong_ngay*100)}%"} for n in top3],
        "xien": [{"num": n[0], "rate": f"~{round(n[1]/tong_ngay*100)}%"} for n in xien[:2]],
        "dau_de": top_dau_de
    }

def build_report(result, pred):
    now_str = get_now_vn().strftime("%d/%m/%Y %H:%M:%S")
    msg = f"📊 *KẾT QUẢ XSMB NGÀY {result['date']}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🏆 *GĐB:* `{result.get('special', '------')}`\n"
    msg += f"🥇 *Giải Nhất:* `{result.get('g1', '------')}`\n"
    if result.get('g2'): msg += f"🥈 *Giải Nhì:* `{' - '.join(result['g2'])}`\n"
    if result.get('g3'): msg += f"🥉 *Giải Ba:* `{' - '.join(result['g3'])}`\n"
    if result.get('g4'): msg += f"🏅 *Giải Tư:* `{' - '.join(result['g4'])}`\n"
    if result.get('g5'): msg += f"🏅 *Giải Năm:* `{' - '.join(result['g5'])}`\n"
    if result.get('g6'): msg += f"🏅 *Giải Sáu:* `{' - '.join(result['g6'])}`\n"
    if result.get('g7'): msg += f"🏅 *Giải Bảy:* `{' - '.join(result['g7'])}`\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📡 Nguồn: {result.get('source', 'XSMB Online')} | 📅 {now_str}\n"
    
    if pred:
        msg += f"\n🤖 *DỰ ĐOÁN THỐNG KÊ*\n"
        msg += f"🎯 *TOP 3 LÔ:* `{pred['top3'][0]['num']}`, `{pred['top3'][1]['num']}`, `{pred['top3'][2]['num']}`\n"
        msg += f"🎯 *2 LÔ XIÊN:* `{pred['xien'][0]['num']}` - `{pred['xien'][1]['num']}`\n"
        msg += f"🎯 *ĐẦU SỐ ĐỀ:* Đầu `{pred['dau_de']}`\n"
    msg += "\n🎲 *Chơi có trách nhiệm - Chỉ giải trí!*"
    return msg

@bot.message_handler(func=lambda msg: True)
def handle_user_message(message):
    text = message.text.strip()
    d, m, y = None, None, None
    match_raw = re.search(r'^(\d{2})(\d{2})(\d{4})$', text)
    match_dmy = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)

    if match_raw:
        d, m, y = match_raw.group(1), match_raw.group(2), match_raw.group(3)
    elif match_dmy:
        d, m, y = match_dmy.group(1).zfill(2), match_dmy.group(2).zfill(2), match_dmy.group(3)

    if d and m and y:
        target_date = f"{d}/{m}/{y}"
        bot.reply_to(message, f"🔄 Đang tra cứu kết quả ngày {target_date}...")
        res = get_xsmb_result(target_date)
        if res and res.get("special"):
            data = load_data()
            pred = analyze(data.get("history", []))
            bot.reply_to(message, build_report(res, pred), parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ Không tìm thấy dữ liệu XSMB cho ngày {target_date}!")

def auto_send_daily():
    data = load_data()
    last_send_date = None
    while True:
        try:
            now_vn = get_now_vn()
            today_str = now_vn.strftime("%d/%m/%Y")
            if now_vn.hour == 18 and now_vn.minute >= 35 and last_send_date != today_str:
                result = get_xsmb_result()
                if result:
                    if data["last_date"] != result["date"]:
                        data["history"].append(result)
                        data["last_date"] = result["date"]
                        save_data(data)
                    pred = analyze(data["history"])
                    if CHAT_ID:
                        bot.send_message(CHAT_ID, build_report(result, pred), parse_mode="Markdown")
                    last_send_date = today_str
            time.sleep(60)
        except Exception:
            time.sleep(60)

if __name__ == "__main__":
    # Khởi chạy Flask server
    threading.Thread(target=run_server, daemon=True).start()
    
    # Khởi chạy luồng tự động gửi tin nhắn
    threading.Thread(target=auto_send_daily, daemon=True).start()
    
    # Ngắt kết nối Webhook cũ trước khi Polling để tránh lỗi 409
    try:
        print("🔄 Đang ngắt kết nối session cũ...")
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(3)
    except Exception as e:
        print(f"⚠️ Lỗi xóa Webhook: {e}")

    # Nhận tin nhắn liên tục
    while True:
        try:
            print("🚀 Bot bắt đầu nhận tin nhắn (Polling)...")
            bot.polling(non_stop=True, interval=1, timeout=30)
        except Exception as e:
            print(f"⚠️ Polling bị ngắt ({e}), thử lại sau 5s...")
            time.sleep(5)
