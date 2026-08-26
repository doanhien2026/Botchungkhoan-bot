# ============================================================
# BOT XSMB — V5.3 (CẬP NHẬT ĐẦY ĐỦ 27 GIẢI TỪ CODE V5.1)
# ✅ Lưu dữ liệu tự động | ✅ Phân tích lịch sử | ✅ Đủ 27 giải XSMB
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

# ====================== 🔧 CHỈ SỬA Ở ĐÂY ======================
TELEGRAM_TOKEN = "8901722608:AAHnHfYsR8ilnHCHRaDUedA1ra1p0gPWda8"
CHAT_ID = "-1001030583610"       # ID kênh/nhóm của bạn
DATA_FILE = "xsmb_data.json"
CHECK_INTERVAL = 300              # Kiểm tra mỗi 5 phút
SEND_TIME = "18:35"               # Gửi kết quả hàng ngày
# ===============================================================

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ========== WEB SERVER ==========
@app.route('/')
def home():
    return "✅ Bot XSMB V5.3 — Phân tích lịch sử + Đủ 27 giải Active!", 200

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

# ========== QUẢN LÝ LƯU TRỮ DỮ LIỆU ==========
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
        data["updated_at"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu: {e}")
        return False

# ========== LẤY DỮ LIỆU XSMB ĐẦY ĐỦ 27 GIẢI ==========
def get_xsmb_result(target_date_str=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9"
    }

    # BƯỚC 1: Lấy theo ngày cụ thể (hoặc ngày hôm nay) từ API VOH
    if not target_date_str:
        now_date = datetime.now()
        target_date_str = now_date.strftime("%d/%m/%Y")

    try:
        parts = target_date_str.split("/")
        d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
        url = f"https://voh.com.vn/api/v1/lottery/xsmb?date={y}-{m}-{d}"
        r = requests.get(url, headers=headers, timeout=12)
        
        if r.status_code == 200:
            res = r.json().get("data", {}) or r.json().get("result", {})
            if res and (res.get("special") or res.get("giai_dac_biet")):
                def parse_list(key):
                    val = res.get(key, [])
                    return [str(x) for x in val] if isinstance(val, list) else ([str(val)] if val else [])

                db = parse_list("special") or parse_list("giai_dac_biet")
                g1 = parse_list("first") or parse_list("giai_nhat")
                g2 = parse_list("second") or parse_list("giai_nhai")
                g3 = parse_list("third") or parse_list("giai_ba")
                g4 = parse_list("fourth") or parse_list("giai_tu")
                g5 = parse_list("fifth") or parse_list("giai_nam")
                g6 = parse_list("sixth") or parse_list("giai_sau")
                g7 = parse_list("seventh") or parse_list("giai_bay")

                # Lấy 27 bộ số lô (2 số cuối của mỗi giải)
                all_prizes = db + g1 + g2 + g3 + g4 + g5 + g6 + g7
                lotos = [p[-2:] for p in all_prizes if len(p) >= 2]

                if db and len(lotos) >= 20:
                    return {
                        "date": target_date_str,
                        "special": db[0],
                        "g1": g1[0] if g1 else "------",
                        "g2": g2, "g3": g3, "g4": g4, "g5": g5, "g6": g6, "g7": g7,
                        "loto": lotos,
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "source": "VOH API"
                    }
    except Exception as e:
        print(f"⚠️ Lỗi cào VOH API ngày {target_date_str}: {e}")

    # BƯỚC 2: Dự phòng cào KQXS.vn nếu API VOH lỗi
    try:
        url = "https://kqxs.vn/ket-qua-xo-so-mien-bac-truyen-thong"
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200 and len(r.text) > 500:
            date_match = re.search(r'Kết quả XSMB ngày (\d{2}/\d{2}/\d{4})', r.text)
            date_str = date_match.group(1) if date_match else target_date_str
            
            special_match = re.search(r'(?:Giải Đặc biệt|Đặc biệt)[\s\S]{0,100}?(\d{5,6})', r.text, re.I)
            special = special_match.group(1) if special_match else "------"
            
            lotos = re.findall(r'lottery-result-item[^>]*>(\d{2})<', r.text)
            if not lotos:
                lotos = re.findall(r'>(\d{2})<', r.text)
                lotos = [n for n in lotos if n.isdigit() and n != '00' and len(n) == 2][:27]
            
            if special != "------" and len(lotos) >= 20:
                return {
                    "date": date_str,
                    "special": special,
                    "loto": lotos,
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "source": "KQXS.vn"
                }
    except Exception as e:
        print(f"⚠️ [KQXS.vn] Lỗi: {e}")

    return None

# ========== PHÂN TÍCH & DỰ BÁO TỪ LỊCH SỬ (V5.1) ==========
def analyze(history):
    if len(history) < 1:
        return None

    all_loto = []
    for day in history:
        all_loto.extend(day.get("loto", []))

    if not all_loto:
        return None

    tong_ngay = max(len(history), 1)
    tong_so = len(all_loto)

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
        "top3": [
            {"num": n[0], "rate": f"~{round(n[1]/tong_ngay*100)}%", "count": n[1]} 
            for n in top3
        ],
        "xien": [
            {"num": n[0], "rate": f"~{round(n[1]/tong_ngay*100)}%"} 
            for n in xien[:2]
        ],
        "dau": {"num": dau[0], "rate": f"~{round(dau[1]/tong_ngay*100)}%"},
        "duoi": {"num": duoi[0], "rate": f"~{round(duoi[1]/tong_ngay*100)}%"},
        "duoi_gdb": history[-1].get("special", "")[-1] if history[-1].get("special") and len(history[-1].get("special", ""))>=5 else "?",
        "tong_ngay": tong_ngay,
        "tong_so": tong_so
    }

# ========== TẠO BÁO CÁO CÓ ĐỦ 27 GIẢI XSMB ==========
def build_report(result, pred):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    msg = f"📊 *KẾT QUẢ XSMB — {result['date']}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🏆 *GĐB:* `{result.get('special', '------')}`\n"
    msg += f"🥇 *Giải Nhất:* `{result.get('g1', '------')}`\n"
    
    if 'g2' in result and result['g2']: msg += f"🥈 *Giải Nhì:* `{' - '.join(result['g2'])}`\n"
    if 'g3' in result and result['g3']: msg += f"🥉 *Giải Ba:* `{' - '.join(result['g3'][:3])}`\n"
    if 'g4' in result and result['g4']: msg += f"🏅 *Giải Tư:* `{' - '.join(result['g4'])}`\n"
    if 'g5' in result and result['g5']: msg += f"🏅 *Giải Năm:* `{' - '.join(result['g5'][:3])}`\n"
    if 'g6' in result and result['g6']: msg += f"🏅 *Giải Sáu:* `{' - '.join(result['g6'])}`\n"
    if 'g7' in result and result['g7']: msg += f"🏅 *Giải Bảy:* `{' - '.join(result['g7'])}`\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📡 Nguồn: {result.get('source', 'Tổng hợp')} | 📅 {now}\n"
    if pred:
        msg += f"💾 Dữ liệu: {pred['tong_ngay']} ngày gần nhất\n\n"
        msg += "🤖 *DỰ ĐOÁN DỰA TRÊN TẦN SUẤT THỰC TẾ*\n\n"
        msg += "🎯 *TOP 3 LÔ CAO NHẤT*\n"
        msg += f"🥇 `{pred['top3'][0]['num']}` — {pred['top3'][0]['rate']} ({pred['top3'][0]['count']} lần)\n"
        msg += f"🥈 `{pred['top3'][1]['num']}` — {pred['top3'][1]['rate']}\n"
        msg += f"🥉 `{pred['top3'][2]['num']}` — {pred['top3'][2]['rate']}\n\n"
        msg += "🎯 *2 LÔ XIÊN CAO*\n"
        msg += f"🥇 `{pred['xien'][0]['num']}` — {pred['xien'][0]['rate']}\n"
        msg += f"🥈 `{pred['xien'][1]['num']}` — {pred['xien'][1]['rate']}\n\n"
        msg += f"🔢 *ĐẦU LÔ NỔI BẬT* → `{pred['dau']['num']}` — {pred['dau']['rate']}\n"
        msg += f"🔢 *ĐUÔI LÔ NỔI BẬT* → `{pred['duoi']['num']}` — {pred['duoi']['rate']}\n"
        msg += f"🎲 *SỐ CUỐI ĐẶC BIỆT VỪA RA*: `{pred['duoi_gdb']}`\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "⚠️ *Chỉ tham khảo — Chơi có trách nhiệm!*"
    return msg

# ========== XỬ LÝ TRA CỨU THEO TIN NHẮN NGƯỜI DÙNG ==========
@bot.message_handler(func=lambda msg: True)
def handle_user_message(message):
    text = message.text.strip()
    d, m, y = None, None, None

    match_raw = re.search(r'^(\d{2})(\d{2})(\d{4})$', text)                  # 24082026
    match_dmy = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)        # 24/08/2026
    match_ymd = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', text)        # 2026/08/24

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
            bot.reply_to(message, f"❌ Chưa có dữ liệu XSMB ngày {target_date}!")

# ========== CHƯƠNG TRÌNH CHÍNH ==========
def main():
    print("🚀 Bot XSMB V5.3 KHỞI ĐỘNG — Đầy đủ 27 giải!")
    data = load_data()
    print(f"📂 Đã có {len(data['history'])} ngày dữ liệu")

    # Khởi động server
    threading.Thread(target=run_server, daemon=True).start()
    
    # Lắng nghe tin nhắn tra cứu từ Telegram
    def start_bot_polling():
        while True:
            try:
                bot.remove_webhook()
                bot.polling(none_stop=True, interval=2, timeout=20)
            except Exception as e:
                time.sleep(5)

    threading.Thread(target=start_bot_polling, daemon=True).start()
    time.sleep(2)
    print("✅ Web Server & Telegram Polling đã hoạt động")

    vn_tz = timezone(timedelta(hours=7))
    last_send_date = None

    # Vòng lặp kiểm tra tự động gửi lúc 18:35 hằng ngày
    while True:
        try:
            now_vn = datetime.now(vn_tz)
            today_str = now_vn.strftime("%d/%m/%Y")
            hour, minute = now_vn.hour, now_vn.minute

            if hour == 18 and minute >= 35 and last_send_date != today_str:
                print(f"⏰ Đến giờ gửi: {today_str}")
                result = get_xsmb_result()
                
                if result:
                    if data["last_date"] != result["date"]:
                        data["history"].append(result)
                        data["last_date"] = result["date"]
                        if len(data["history"]) > 90:
                            data["history"] = data["history"][-90:]
                        save_data(data)
                    
                    pred = analyze(data["history"])
                    if pred:
                        bot.send_message(CHAT_ID, build_report(result, pred), parse_mode="Markdown")
                        print(f"✅ Đã gửi tự động ngày {today_str}")
                        last_send_date = today_str
            time.sleep(60)
        except Exception as e:
            print(f"⚠️ Lỗi vòng lặp: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
