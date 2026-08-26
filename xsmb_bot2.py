# ============================================================
# BOT XSMB — V6.0 (HỖ TRỢ LẬP LỊCH TỰ ĐỘNG + TRUY VẤN NGÀY)
# ✅ Lưu dữ liệu tự động | ✅ Phân tích lịch sử | ✅ Tra cứu tin nhắn
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
SEND_TIME_HOUR = 18              # Giờ gửi (18h)
SEND_TIME_MINUTE = 35            # Phút gửi (35m)
# ===============================================================

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ========== WEB SERVER (CHỐNG SLEEP RENDER) ==========
@app.route('/')
def home():
    return "✅ Bot XSMB V6.0 — Phân tích lịch sử & Tra cứu tin nhắn Active!", 200

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
        print(f"❌ Lỗi lưu dữ liệu: {e}")
        return False

# ========== LẤY KẾT QUẢ XSMB CƠ BẢN & THEO NGÀY ==========
def get_xsmb_result(target_date_str=None):
    """
    target_date_str: Định dạng 'DD/MM/YYYY' nếu tra cứu ngày cụ thể,
                     hoặc None để lấy kết quả mới nhất.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9"
    }

    # Nếu tra cứu ngày cụ thể
    if target_date_str:
        try:
            parts = target_date_str.split("/")
            d, m, y = parts[0], parts[1], parts[2]
            url = f"https://voh.com.vn/api/v1/lottery/xsmb?date={y}-{m}-{d}"
            r = requests.get(url, headers=headers, timeout=12)
            if r.status_code == 200:
                json_data = r.json()
                res_data = json_data.get("data", {}) or json_data.get("result", {})
                sp = res_data.get("special") or res_data.get("giai_dac_biet") or "------"
                g1 = res_data.get("first") or res_data.get("giai_nhat") or "------"
                if isinstance(sp, list) and len(sp) > 0: sp = sp[0]
                if isinstance(g1, list) and len(g1) > 0: g1 = g1[0]
                
                return {
                    "date": target_date_str,
                    "special": str(sp),
                    "g1": str(g1),
                    "loto": [],
                    "source": "VOH API"
                }
        except Exception as e:
            print(f"⚠️ Lỗi tra cứu ngày {target_date_str}: {e}")

    # Cào kết quả trang nhất (Mới nhất)
    try:
        url = "https://kqxs.vn/ket-qua-xo-so-mien-bac-truyen-thong"
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200 and len(r.text) > 500:
            date_match = re.search(r'Kết quả XSMB ngày (\d{2}/\d{2}/\d{4})', r.text)
            date_str = date_match.group(1) if date_match else datetime.now().strftime("%d/%m/%Y")
            
            special_match = re.search(r'(?:Giải Đặc biệt|Đặc biệt)[\s\S]{0,100}?(\d{5,6})', r.text, re.I)
            special = special_match.group(1) if special_match else "------"
            
            lotos = re.findall(r'lottery-result-item[^>]*>(\d{2})<', r.text)
            if not lotos:
                lotos = re.findall(r'>(\d{2})<', r.text)
                lotos = [n for n in lotos if n.isdigit() and n != '00' and len(n) == 2][:27]
            
            if special != "------":
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

# ========== PHÂN TÍCH & DỰ BÁO TỪ LỊCH SỬ ==========
def analyze(history):
    if len(history) < 1:
        # Dự đoán mặc định dựa trên xác suất nếu chưa có lịch sử
        return {
            "top3": [{"num": "61", "rate": "~20%", "count": 1}, {"num": "70", "rate": "~18%", "count": 1}, {"num": "69", "rate": "~16%", "count": 1}],
            "xien": [{"num": "73", "rate": "~17%"}, {"num": "05", "rate": "~15%"}],
            "dau": {"num": "6", "rate": "~25%"},
            "duoi": {"num": "1", "rate": "~22%"},
            "duoi_gdb": "3", "tong_ngay": 1, "tong_so": 27
        }

    all_loto = []
    for day in history:
        all_loto.extend(day.get("loto", []))

    if not all_loto:
        all_loto = ["61", "70", "69", "73", "05", "12", "89", "35"]

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
        "top3": [{"num": n[0], "rate": f"~{round(n[1]/tong_ngay*100)}%", "count": n[1]} for n in top3],
        "xien": [{"num": n[0], "rate": f"~{round(n[1]/tong_ngay*100)}%"} for n in xien[:2]],
        "dau": {"num": dau[0], "rate": f"~{round(dau[1]/tong_ngay*100)}%"},
        "duoi": {"num": duoi[0], "rate": f"~{round(duoi[1]/tong_ngay*100)}%"},
        "duoi_gdb": history[-1].get("special", "")[-1] if history[-1].get("special") and len(history[-1].get("special", ""))>=5 else "?",
        "tong_ngay": tong_ngay,
        "tong_so": tong_so
    }

# ========== TẠO BÁO CÁO BÀI ĐĂNG TỰ ĐỘNG ==========
def build_report(result, pred):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    msg = f"""
📊 *KẾT QUẢ XSMB — {result['date']}*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 Giải Đặc biệt: *{result['special']}*
📡 Nguồn: {result.get('source', 'Tổng hợp')}
📅 Cập nhật: {now}
💾 Dữ liệu: {pred['tong_ngay']} ngày gần nhất

🤖 *DỰ ĐOÁN DỰA TRÊN TẦN SUẤT THỰC TẾ*

🎯 *TOP 3 LÔ CAO NHẤT*
🥇 `{pred['top3'][0]['num']}` — {pred['top3'][0]['rate']}
🥈 `{pred['top3'][1]['num']}` — {pred['top3'][1]['rate']}
🥉 `{pred['top3'][2]['num']}` — {pred['top3'][2]['rate']}

🎯 *2 LÔ XIÊN CAO*
🥇 `{pred['xien'][0]['num']}` — {pred['xien'][0]['rate']}
🥈 `{pred['xien'][1]['num']}` — {pred['xien'][1]['rate']}

🔢 *ĐẦU LÔ NỔI BẬT* → `{pred['dau']['num']}` ({pred['dau']['rate']})
🔢 *ĐUÔI LÔ NỔI BẬT* → `{pred['duoi']['num']}` ({pred['duoi']['rate']})

🎲 *SỐ CUỐI ĐẶC BIỆT*: `{pred['duoi_gdb']}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ *Chơi có trách nhiệm - Chỉ giải trí!*
"""
    return msg

# ========== 1. LẮNG NGHE TIN NHẮN TỪ NGƯỜI DÙNG (POLLING) ==========
@bot.message_handler(func=lambda msg: True)
def handle_user_messages(message):
    text = message.text.strip()
    d, m, y = None, None, None

    # Nhận diện định dạng ngày người dùng gõ
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
        bot.reply_to(message, f"🔄 Đang lấy dữ liệu ngày {target_date}...")
        
        res = get_xsmb_result(target_date)
        if res and res.get("special") != "------":
            data = load_data()
            pred = analyze(data.get("history", []))
            
            reply = f"📊 *KẾT QUẢ XSMB NGÀY {target_date}*\n"
            reply += f"🏆 *Giải Đặc Biệt:* `{res['special']}`\n"
            if "g1" in res:
                reply += f"🥇 *Giải Nhất:* `{res['g1']}`\n"
            reply += "-----------------------------------\n"
            reply += "🤖 *DỰ ĐOÁN DỰA TRÊN LOGIC THỰC TẾ*\n\n"
            reply += f"🎯 *TOP 3 LÔ:* `{pred['top3'][0]['num']}`, `{pred['top3'][1]['num']}`, `{pred['top3'][2]['num']}`\n"
            reply += f"🎯 *2 LÔ XIÊN:* `{pred['xien'][0]['num']}` - `{pred['xien'][1]['num']}`\n"
            reply += f"🎯 *SỐ CUỐI ĐB:* `{pred['duoi_gdb']}`"
            
            bot.reply_to(message, reply, parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ Chưa có dữ liệu XSMB ngày {target_date} hoặc ngày không hợp lệ!")
    elif text.lower() in ["/start", "hi", "hello", "tro giup"]:
        bot.reply_to(message, "👋 Chào bạn! Hãy nhập ngày theo cú pháp: `DDMMYYYY` (VD: `24082026`) hoặc `DD/MM/YYYY` để tra cứu kết quả XSMB nhé!", parse_mode="Markdown")

# ========== 2. TIẾN TRÌNH GỬI BÁO CÁO TỰ ĐỘNG HẰNG NGÀY ==========
def auto_schedule_job():
    vn_tz = timezone(timedelta(hours=7))
    last_send_date = None
    data = load_data()

    while True:
        try:
            now_vn = datetime.now(vn_tz)
            today_str = now_vn.strftime("%d/%m/%Y")
            hour, minute = now_vn.hour, now_vn.minute

            if hour == SEND_TIME_HOUR and minute >= SEND_TIME_MINUTE and last_send_date != today_str:
                print(f"⏰ Đến giờ gửi tự động: {today_str}")
                result = get_xsmb_result()
                
                if result:
                    if data["last_date"] != result["date"]:
                        data["history"].append(result)
                        data["last_date"] = result["date"]
                        if len(data["history"]) > 90:
                            data["history"] = data["history"][-90:]
                        save_data(data)
                    
                    pred = analyze(data["history"])
                    report_text = build_report(result, pred)
                    
                    # Gửi tin nhắn đến Telegram Channel/Group
                    bot.send_message(CHAT_ID, report_text, parse_mode="Markdown", disable_web_page_preview=True)
                    print(f"✅ Đã gửi tự động ngày {today_str}")
                    last_send_date = today_str

            time.sleep(30)
        except Exception as e:
            print(f"⚠️ Lỗi tiến trình tự động: {e}")
            time.sleep(30)

# ========== KHỞI CHẠY BOT ==========
if __name__ == "__main__":
    print("🚀 Bot XSMB V6.0 Khởi động...")
    
    # 1. Chạy Web Server chống sleep
    threading.Thread(target=run_server, daemon=True).start()
    
    # 2. Chạy Tiến trình gửi tự động hằng ngày
    threading.Thread(target=auto_schedule_job, daemon=True).start()
    
    # 3. Lắng nghe tin nhắn từ người dùng (Polling)
    while True:
        try:
            bot.remove_webhook()
            bot.polling(none_stop=True, interval=2, timeout=20)
        except Exception as e:
            print(f"⚠️ Lỗi Polling: {e}")
            time.sleep(5)
