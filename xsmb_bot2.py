# ============================================================
# BOT XSMB — V5.6 (CHUYỂN SANG DÙNG API API/JSON TRỰC TIẾP)
# ✅ Khắc phục lỗi 403 Forbidden | ✅ Đủ 27 giải | ✅ Chuẩn UTC+7
# ============================================================
import os
import json
import time
import requests
import re
import threading
import telebot
from datetime import datetime, timezone, timedelta
from collections import Counter
from flask import Flask

# ====================== 🔧 CẤU HÌNH ======================
TELEGRAM_TOKEN = "8901722608:AAHnHfYsR8ilnHCHRaDUedA1ra1p0gPWda8"
CHAT_ID = "-1001030583610"
DATA_FILE = "xsmb_data.json"
SEND_TIME = "18:35"
# =========================================================

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
VN_TZ = timezone(timedelta(hours=7))

def get_now_vn():
    return datetime.now(VN_TZ)

@app.route('/')
def home():
    return "✅ Bot XSMB V5.6 — API Direct Active!", 200

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"history": [], "last_date": "", "updated_at": ""}

def save_data(data):
    try:
        data["updated_at"] = get_now_vn().strftime("%d/%m/%Y %H:%M:%S")
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu: {e}")
        return False

# ========== API LẤY KẾT QUẢ XSMB THEO NGÀY ==========
def get_xsmb_result(target_date_str=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    }

    if not target_date_str:
        target_date_str = get_now_vn().strftime("%d/%m/%Y")

    parts = target_date_str.split("/")
    d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
    formatted_date = f"{y}-{m}-{d}"

    # Nguồn 1: API JSON Xoso.me
    try:
        url_api = f"https://api.xoso.me/api/v1/lottery/result/xsmb?date={formatted_date}"
        r = requests.get(url_api, headers=headers, timeout=10)
        if r.status_code == 200:
            res_json = r.json()
            data = res_json.get("data") or res_json
            if data and "special" in data:
                db = str(data.get("special", [""])[0] if isinstance(data.get("special"), list) else data.get("special"))
                g1 = str(data.get("first", [""])[0] if isinstance(data.get("first"), list) else data.get("first"))
                
                def fmt(val):
                    if isinstance(val, list): return [str(x) for x in val]
                    return [str(val)] if val else []

                all_prizes = [db, g1]
                for key in ["second", "third", "fourth", "fifth", "sixth", "seventh"]:
                    all_prizes.extend(fmt(data.get(key, [])))
                
                lotos = [p[-2:] for p in all_prizes if len(p) >= 2]

                return {
                    "date": target_date_str,
                    "special": db,
                    "g1": g1,
                    "g2": fmt(data.get("second")),
                    "g3": fmt(data.get("third")),
                    "g4": fmt(data.get("fourth")),
                    "g5": fmt(data.get("fifth")),
                    "g6": fmt(data.get("sixth")),
                    "g7": fmt(data.get("seventh")),
                    "loto": lotos,
                    "source": "Xoso.me API"
                }
    except Exception as e:
        print(f"⚠️ API 1 Lỗi: {e}")

    # Nguồn 2: Backup Cào HTML trực tiếp Minh Ngọc
    try:
        url_mn = f"https://www.minhngoc.com.vn/gettruoctiep/mien-bac/{d}-{m}-{y}.html"
        r = requests.get(url_mn, headers=headers, timeout=10)
        if r.status_code == 200 and len(r.text) > 100:
            html = r.text
            numbers = re.findall(r'\b\d{2,5}\b', html)
            if len(numbers) >= 27:
                db = numbers[0]
                g1 = numbers[1]
                lotos = [n[-2:] for n in numbers[:27]]
                return {
                    "date": target_date_str,
                    "special": db,
                    "g1": g1,
                    "g2": numbers[2:4],
                    "g3": numbers[4:10],
                    "g4": numbers[10:14],
                    "g5": numbers[14:20],
                    "g6": numbers[20:23],
                    "g7": numbers[23:27],
                    "loto": lotos,
                    "source": "Minh Ngọc API"
                }
    except Exception as e:
        print(f"⚠️ API 2 Lỗi: {e}")

    return None

# ========== PHÂN TÍCH THỐNG KÊ ==========
def analyze(history):
    if len(history) < 1:
        return None

    all_loto = []
    for day in history:
        all_loto.extend(day.get("loto", []))

    if not all_loto:
        return None

    tong_ngay = max(len(history), 1)
    freq = Counter(all_loto)
    top3 = freq.most_common(3)
    while len(top3) < 3:
        top3.append(("00", 1))

    top5 = freq.most_common(5)
    xien = top3[1:] + [top5[3]] if len(top5) >= 4 else top3[1:]

    return {
        "top3": [{"num": n[0], "rate": f"~{round(n[1]/tong_ngay*100)}%"} for n in top3],
        "xien": [{"num": n[0], "rate": f"~{round(n[1]/tong_ngay*100)}%"} for n in xien[:2]],
    }

# ========== BÁO CÁO KẾT QUẢ ==========
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
    msg += f"📡 Nguồn: {result.get('source', 'API Direct')} | 📅 {now_str}\n"
    
    if pred:
        msg += f"\n🤖 *DỰ ĐOÁN THỐNG KÊ*\n"
        msg += f"🎯 *TOP 3 LÔ:* `{pred['top3'][0]['num']}`, `{pred['top3'][1]['num']}`, `{pred['top3'][2]['num']}`\n"
        msg += f"🎯 *2 LÔ XIÊN:* `{pred['xien'][0]['num']}` - `{pred['xien'][1]['num']}`\n"
        
    msg += "\n🎲 *Chơi có trách nhiệm - Chỉ giải trí!*"
    return msg

# ========== BẮT TÍN HIỆU TIN NHẮN TELEGRAM ==========
@bot.message_handler(func=lambda msg: True)
def handle_user_message(message):
    text = message.text.strip()
    d, m, y = None, None, None

    match_raw = re.search(r'^(\d{2})(\d{2})(\d{4})$', text)
    match_dmy = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
    match_ymd = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', text)

    if match_raw:
        d, m, y = match_raw.group(1), match_raw.group(2), match_raw.group(3)
    elif match_dmy:
        d, m, y = match_dmy.group(1).zfill(2), match_dmy.group(2).zfill(2), match_dmy.group(3)
    elif match_ymd:
        y, m, d = match_ymd.group(1), match_ymd.group(2).zfill(2), match_ymd.group(3).zfill(2)

    if d and m and y:
        target_date = f"{d}/{m}/{y}"
        bot.reply_to(message, f"🔄 Đang tra cứu kết quả ngày {target_date}...")
        
        res = get_xsmb_result(target_date)
        if res and res.get("special"):
            data = load_data()
            pred = analyze(data.get("history", []))
            reply = build_report(res, pred)
            bot.reply_to(message, reply, parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ Không tìm thấy dữ liệu XSMB cho ngày {target_date} (Hoặc chưa tới giờ quay)!")

# ========== MAIN ==========
def main():
    print("🚀 Bot XSMB V5.6 API Direct KHỜI ĐỘNG...")
    data = load_data()

    threading.Thread(target=run_server, daemon=True).start()
    
    def start_bot_polling():
        while True:
            try:
                bot.remove_webhook()
                bot.polling(none_stop=True, interval=2, timeout=20)
            except Exception:
                time.sleep(5)

    threading.Thread(target=start_bot_polling, daemon=True).start()

    last_send_date = None

    while True:
        try:
            now_vn = get_now_vn()
            today_str = now_vn.strftime("%d/%m/%Y")
            hour, minute = now_vn.hour, now_vn.minute

            if hour == 18 and minute >= 35 and last_send_date != today_str:
                result = get_xsmb_result()
                if result:
                    if data["last_date"] != result["date"]:
                        data["history"].append(result)
                        data["last_date"] = result["date"]
                        if len(data["history"]) > 90:
                            data["history"] = data["history"][-90:]
                        save_data(data)
                    
                    pred = analyze(data["history"])
                    bot.send_message(CHAT_ID, build_report(result, pred), parse_mode="Markdown")
                    last_send_date = today_str
            time.sleep(60)
        except Exception as e:
            time.sleep(60)

if __name__ == "__main__":
    main()
