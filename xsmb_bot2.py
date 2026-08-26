# ============================================================
# BOT XSMB — V5.1 (ĐÃ SỬA TOKEN + CHAT_ID + LỖI NGÀY + TỐI ƯU)
# ✅ Lưu dữ liệu tự động | ✅ Phân tích lịch sử thực tế | ✅ Gửi 18:35
# ============================================================
import os
import json
import time
import requests
import re
import threading
from datetime import datetime, timezone, timedelta
from collections import Counter
from flask import Flask

# ====================== 🔧 CHỈ SỬA Ở ĐÂY ======================
TELEGRAM_TOKEN = "8901722608:AAHnHfYsR8ilnHCHRaDUedA1ra1p0gPWda8"
CHAT_ID = "-1001030583610"       # ✅ Đã sửa đúng ID kênh của bạn
DATA_FILE = "xsmb_data.json"
CHECK_INTERVAL = 300              # Kiểm tra mỗi 5 phút (nhanh hơn)
SEND_TIME = "18:35"               # Gửi kết quả hàng ngày
# ===============================================================

app = Flask(__name__)

# ========== WEB SERVER ==========
@app.route('/')
def home():
    return "✅ Bot XSMB V5.1 — Phân tích lịch sử thực tế", 200

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

# ========== LẤY KẾT QUẢ XSMB — TỐI ƯU + ĐA NGUỒN ==========
def get_xsmb_result():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9"
    }

    # === NGUỒN 1: KQXS.VN ===
    try:
        url = "https://kqxs.vn/ket-qua-xo-so-mien-bac-truyen-thong"
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200 and len(r.text) > 500:
            # Ngày
            date_match = re.search(r'Kết quả XSMB ngày (\d{2}/\d{2}/\d{4})', r.text)
            date_str = date_match.group(1) if date_match else datetime.now().strftime("%d/%m/%Y")
            
            # Giải Đặc Biệt
            special_match = re.search(r'(?:Giải Đặc biệt|Đặc biệt)[\s\S]{0,100}?(\d{5,6})', r.text, re.I)
            special = special_match.group(1) if special_match else "------"
            
            # Tất cả số lô 2 chữ số
            lotos = re.findall(r'lottery-result-item[^>]*>(\d{2})<', r.text)
            if not lotos:
                lotos = re.findall(r'>(\d{2})<', r.text)
                lotos = [n for n in lotos if n.isdigit() and n != '00' and len(n) == 2][:27]
            
            if special != "------" and len(lotos) >= 20:
                print(f"✅ [KQXS.vn] {date_str} | GĐB: {special} | Lô: {len(lotos)} số")
                return {
                    "date": date_str,
                    "special": special,
                    "loto": lotos,
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "source": "KQXS.vn"
                }
    except Exception as e:
        print(f"⚠️ [KQXS.vn] Lỗi: {str(e)[:40]}")

    # === NGUỒN 2: XOSO.WAP.VN ===
    try:
        url = "https://xoso.wap.vn/xsmb"
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 200 and len(r.text) > 300:
            date_match = re.search(r'Ngày (\d{2}/\d{2}/\d{4})', r.text)
            date_str = date_match.group(1) if date_match else datetime.now().strftime("%d/%m/%Y")
            special_match = re.search(r'Đặc biệt.*?(\d{5,6})', r.text, re.I)
            special = special_match.group(1) if special_match else "------"
            lotos = re.findall(r'>(\d{2})<', r.text)
            lotos = [n for n in lotos if n.isdigit() and n != '00' and len(n) == 2][:27]
            if special != "------" and len(lotos) >= 20:
                print(f"✅ [Xoso.wap.vn] {date_str} | GĐB: {special}")
                return {
                    "date": date_str, "special": special, "loto": lotos,
                    "time": datetime.now().strftime("%H:%M:%S"), "source": "Xoso.wap.vn"
                }
    except Exception as e:
        print(f"⚠️ [Xoso.wap.vn] Lỗi: {str(e)[:40]}")

    print("❌ Không lấy được dữ liệu")
    return None

# ========== PHÂN TÍCH & DỰ BÁO TỪ LỊCH SỬ ==========
def analyze(history):
    """Phân tích tần suất 90 ngày gần nhất → tín hiệu chính xác hơn"""
    if len(history) < 5:
        print(f"⚠️ Chưa đủ dữ liệu: {len(history)} ngày (cần ít nhất 5)")
        return None

    all_loto = []
    for day in history:
        all_loto.extend(day.get("loto", []))

    if not all_loto or len(all_loto) < 20:
        return None

    tong_ngay = len(history)
    tong_so = len(all_loto)

    # Top 3 lô ra nhiều nhất
    freq = Counter(all_loto)
    top3 = freq.most_common(3)

    # Đầu lô ra nhiều nhất
    dau_count = Counter([n[0] for n in all_loto])
    dau = dau_count.most_common(1)[0]

    # Đuôi lô ra nhiều nhất
    duoi_count = Counter([n[1] for n in all_loto])
    duoi = duoi_count.most_common(1)[0]

    # 2 lô xiên từ top tiếp theo
    top5 = freq.most_common(5)
    xien = top3[1:] + [top5[3]] if len(top5) >= 4 else top3[1:]

    # Tỷ lệ = (số lần xuất hiện / tổng số ngày) * 100
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

# ========== GỬI TELEGRAM ==========
def send_tg(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }, timeout=30)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Lỗi gửi: {e}")
        return False

# ========== TẠO BÁO CÁO ==========
def build_report(result, pred):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    msg = f"""
📊 *KẾT QUẢ XSMB — {result['date']}*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 Giải Đặc biệt: *{result['special']}*
📡 Nguồn: {result.get('source', 'Không xác định')}
📅 Cập nhật: {now}
💾 Dữ liệu: {pred['tong_ngay']} ngày gần nhất

🤖 *DỰ ĐOÁN DỰA TRÊN TẦN SUẤT THỰC TẾ*

🎯 *TOP 3 LÔ CAO NHẤT*
🥇 {pred['top3'][0]['num']} — {pred['top3'][0]['rate']} ({pred['top3'][0]['count']} lần)
🥈 {pred['top3'][1]['num']} — {pred['top3'][1]['rate']}
🥉 {pred['top3'][2]['num']} — {pred['top3'][2]['rate']}

🎯 *2 LÔ XIÊN CAO*
🥇 {pred['xien'][0]['num']} — {pred['xien'][0]['rate']}
🥈 {pred['xien'][1]['num']} — {pred['xien'][1]['rate']}

🔢 *ĐẦU LÔ NỔI BẬT* → {pred['dau']['num']} — {pred['dau']['rate']}
🔢 *ĐUÔI LÔ NỔI BẬT* → {pred['duoi']['num']} — {pred['duoi']['rate']}

🎲 *SỐ CUỐI ĐẶC BIỆT VỪA RA*: {pred['duoi_gdb']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ *Chỉ tham khảo — Chơi có trách nhiệm!*
"""
    return msg

# ========== CHƯƠNG TRÌNH CHÍNH ==========
def main():
    print("🚀 Bot XSMB V5.1 KHỞI ĐỘNG — Phân tích lịch sử thực tế!")
    data = load_data()
    print(f"📂 Đã có {len(data['history'])} ngày dữ liệu")

    # Khởi động server
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(2)
    print("✅ Server đã chạy")

    vn_tz = timezone(timedelta(hours=7))
    last_send_date = None

    # Gửi ngay lần đầu để test
    print("📤 Lấy dữ liệu & gửi báo cáo lần đầu...")
    result = get_xsmb_result()
    
    if result:
        if data["last_date"] != result["date"]:
            data["history"].append(result)
            data["last_date"] = result["date"]
            if len(data["history"]) > 90:
                data["history"] = data["history"][-90:]
            save_data(data)
            print(f"✅ Đã lưu: {result['date']}")

        pred = analyze(data["history"])
        if pred:
            if send_tg(build_report(result, pred)):
                print("✅ Đã gửi báo cáo Telegram!")
                last_send_date = datetime.now(vn_tz).strftime("%d/%m/%Y")
            else:
                print("❌ Gửi thất bại — kiểm tra TOKEN & CHAT_ID")
        else:
            print("⚠️ Chưa đủ dữ liệu")
    else:
        print("❌ Không lấy được kết quả")

    # Vòng lặp chính — Gửi lúc 18:35 hàng ngày
    while True:
        try:
            now_vn = datetime.now(vn_tz)
            today_str = now_vn.strftime("%d/%m/%Y")
            hour, minute = now_vn.hour, now_vn.minute

            # Chỉ gửi 18:35 và chưa gửi hôm nay
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
                    if pred and send_tg(build_report(result, pred)):
                        print(f"✅ Đã gửi tự động: {today_str}")
                        last_send_date = today_str
                else:
                    print("⚠️ Không lấy được dữ liệu lúc 18:35")

            time.sleep(60)
        except Exception as e:
            print(f"⚠️ Lỗi vòng lặp: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
