# ============================================================
# BOT XSMB — V5.5 (FIX TRIỆT ĐỂ LỖI DỮ LIỆU & GIỜ VIỆT NAM)
# ✅ Tra cứu đúng ngày | ✅ Chuẩn múi giờ VN (UTC+7) | ✅ Đủ 27 giải
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

# Khai báo múi giờ Việt Nam
VN_TZ = timezone(timedelta(hours=7))

def get_now_vn():
    return datetime.now(VN_TZ)

@app.route('/')
def home():
    return "✅ Bot XSMB V5.5 — Fix data & Timezone Active!", 200

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

# ========== CHỨC NĂNG CÀO DỮ LIỆU CHÍNH XÁC THEO NGÀY ==========
def get_xsmb_result(target_date_str=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    if not target_date_str:
        target_date_str = get_now_vn().strftime("%d/%m/%Y")

    try:
        parts = target_date_str.split("/")
        d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
        
        # API Ketqua.net / Minh Ngoc / Xoso.com.vn theo ngay
        url = f"https://xoso.com.vn/xsmb-{d}-{m}-{y}.html"
        r = requests.get(url, headers=headers, timeout=12)
        
        if r.status_code == 200 and len(r.text) > 1000:
            html = r.text
            
            def parse_prizes(pattern):
                match = re.search(pattern, html, re.I)
                if match:
                    return re.findall(r'\b\d{2,5}\b', match.group(1))
                return []

            db = parse_prizes(r'class="cls_giai_dac_biet"[^>]*>([\s\S]*?)</td>') or parse_prizes(r'giai_dac_biet[^>]*>([\s\S]*?)</td>')
            g1 = parse_prizes(r'class="cls_giai_nhat"[^>]*>([\s\S]*?)</td>') or parse_prizes(r'giai_nhat[^>]*>([\s\S]*?)</td>')
            g2 = parse_prizes(r'class="cls_giai_nhai"[^>]*>([\s\S]*?)</td>') or parse_prizes(r'giai_nhai[^>]*>([\s\S]*?)</td>')
            g3 = parse_prizes(r'class="cls_giai_ba"[^>]*>([\s\S]*?)</td>') or parse_prizes(r'giai_ba[^>]*>([\s\S]*?)</td>')
            g4 = parse_prizes(r'class="cls_giai_tu"[^>]*>([\s\S]*?)</td>') or parse_prizes(r'giai_tu[^>]*>([\s\S]*?)</td>')
            g5 = parse_prizes(r'class="cls_giai_nam"[^>]*>([\s\S]*?)</td>') or parse_prizes(r'giai_nam[^>]*>([\s\S]*?)</td>')
            g6 = parse_prizes(r'class="cls_giai_sau"[^>]*>([\s\S]*?)</td>') or parse_prizes(r'giai_sau[^>]*>([\s\S]*?)</td>')
            g7 = parse_prizes(r'class="cls_giai_bay"[^>]*>([\s\S]*?)</td>') or parse_prizes(r'giai_bay[^>]*>([\s\S]*?)</td>')

            all_prizes = db + g1 + g2 + g3 + g4 + g5 + g6 + g7
            lotos = [p[-2:] for p in all_prizes if len(p) >= 2]

            if db:
                return {
                    "date": target_date_str,
                    "special": db[0],
                    "g1": g1[0] if g1 else "------",
                    "g2": g2, "g3": g3, "g4": g4, "g5": g5, "g6": g6, "g7": g7,
                    "loto": lotos,
                    "time": get_now_vn().strftime("%H:%M:%S"),
                    "source": "Xoso.com.vn"
                }
    except Exception as e:
        print(f"⚠️ Lỗi cào ngày {target_date_str}: {e}")

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

    dau_count = Counter([n[0] for n in all_loto if len(n) == 2])
    dau = dau_count.most_common(1)[0] if dau_count else ("0", 1)

    duoi_count = Counter([n[1] for n in all_loto if len(n) == 2])
    duoi = duoi_count.most_common(1)[0] if duoi_count else ("0", 1)

    top5 = freq.most_common(5)
    xien = top3[1:] + [top5[3]] if len(top5) >= 4 else top3[1:]

    return {
        "top3": [{"num": n[0], "rate": f"~{round(n[1]/tong_ngay*100)}%", "count": n[1]} for n in top3],
        "xien": [{"num": n[0], "rate": f"~{round(n[1]/tong_ngay*100)}%"} for n in xien[:2]],
        "dau": {"num": dau[0], "rate": f"~{round(dau[1]/tong_ngay*100)}%"},
        "duoi": {"num": duoi[0], "rate": f"~{round(duoi[1]/tong_ngay*100)}%"},
        "duoi_gdb": history[-1].get("special", "")[-1] if history[-1].get("special") and len(history[-1].get("special", ""))>=5 else "?",
        "tong_ngay": tong_ngay
    }

# ========== TẠO BÁO CÁO ==========
def build_report(result, pred):
    now_str = get_now_vn().strftime("%d/%m/%Y %H:%M:%S")
    
    msg = f"📊 *KẾT QUẢ XSMB NGÀY {result['date']}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🏆 *GĐB:* `{result.get('special', '------')}`\n"
    msg += f"🥇 *Giải Nhất:* `{result.get('g1', '------')}`\n"
    
    if result.get('g2'): msg += f"🥈 *Giải Nhì:* `{' - '.join(result['g2'])}`\n"
    if result.get('g3'): msg += f"🥉 *Giải Ba:* `{' - '.join(result['g3'][:3])}`\n"
    if result.get('g4'): msg += f"🏅 *Giải Tư:* `{' - '.join(result['g4'])}`\n"
    if result.get('g5'): msg += f"🏅 *Giải Năm:* `{' - '.join(result['g5'][:3])}`\n"
    if result.get('g6'): msg += f"🏅 *Giải Sáu:* `{' - '.join(result['g6'])}`\n"
    if result.get('g7'): msg += f"🏅 *Giải Bảy:* `{' - '.join(result['g7'])}`\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📡 Nguồn: {result.get('source', 'Tổng hợp')} | 📅 {now_str}\n"
    
    if pred:
        msg += f"\n🤖 *DỰ ĐOÁN KẾT QUẢ*\n"
        msg += f"🎯 *TOP 3 LÔ:* `{pred['top3'][0]['num']}`, `{pred['top3'][1]['num']}`, `{pred['top3'][2]['num']}`\n"
        msg += f"🎯 *2 LÔ XIÊN:* `{pred['xien'][0]['num']}` - `{pred['xien'][1]['num']}`\n"
        
    msg += "\n🎲 *Chơi có trách nhiệm - Chỉ giải trí!*"
    return msg

# ========== XỬ LÝ TRA CỨU ==========
@bot.message_handler(func=lambda msg: True)
def handle_user_message(message):
    text = message.text.strip()
    d, m, y = None, None, None

    match_raw = re.search(r'^(\d{2})(\d{2})(\d{4})$', text)                  # 22082026
    match_dmy = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)        # 22/08/2026
    match_ymd = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', text)        # 2026/08/22

    if match_raw:
        d, m, y = match_raw.group(1), match_raw.group(2), match_raw.group(3)
    elif match_dmy:
        d, m, y = match_dmy.group(1).zfill(2), match_dmy.group(2).zfill(2), match_dmy.group(3)
    elif match_ymd:
        y, m, d = match_ymd.group(1), match_ymd.group(2).zfill(2), match_ymd.group(3).zfill(2)

    if d and m and y:
        target_date = f"{d}/{m}/{y}"
        bot.reply_to(message, f"🔄 Đang lấy đầy đủ 27 giải ngày {target_date}...")
        
        res = get_xsmb_result(target_date)
        if res and res.get("special") != "------":
            data = load_data()
            pred = analyze(data.get("history", []))
            reply = build_report(res, pred)
            bot.reply_to(message, reply, parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ Không tìm thấy dữ liệu XSMB ngày {target_date}!")

# ========== MAIN ==========
def main():
    print("🚀 Bot XSMB V5.5 KHỜI ĐỘNG...")
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
