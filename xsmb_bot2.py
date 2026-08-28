# ============================================================
# 🤖 BOT XSMB — V7.4 NHẬN KẾT QUẢ NGAY
# ✅ TOKEN ĐÚNG: 8901722608:...
# ✅ CHAT_ID: 1030583610
# ✅ Tự gửi kết quả XSMB + dự đoán
# ============================================================
import os
import json
import time
import requests
import re
import threading
from datetime import datetime
from collections import Counter
from flask import Flask

# ====================== 🔧 ĐÃ ĐIỀN SẴN — KHÔNG SỬA ======================
TELEGRAM_TOKEN = "8901722608:AAHnHfYsR8i1nHCHRaDUedA1ra1p0gPWda8"
CHAT_ID = "1030583610"
DATA_FILE = "xsmb_data.json"
CHECK_INTERVAL = 3600  # Kiểm tra mỗi 1 giờ
# ============================================================================

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot XSMB Đang hoạt động — Nhận kết quả tại Telegram!", 200

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

# ========== QUẢN LÝ DỮ LIỆU ==========
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "history" not in data: data["history"] = []
                if "last_date" not in data: data["last_date"] = ""
                return data
        except:
            pass
    return {"history": [], "last_date": ""}

def save_data(data):
    try:
        data["updated_at"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

# ========== LẤY KẾT QUẢ XSMB ==========
def get_xsmb_result():
    try:
        url = "https://kqxs.vn/ket-qua-xo-so-mien-bac-truyen-thong"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code != 200:
            return None
        date_match = re.search(r'Kết quả XSMB ngày (\d{2}/\d{2}/\d{4})', r.text)
        date_str = date_match.group(1) if date_match else datetime.now().strftime("%d/%m/%Y")
        special_match = re.search(r'Giải Đặc biệt.*?(\d{6})', r.text, re.DOTALL)
        special = special_match.group(1) if special_match else "------"
        lotos = re.findall(r'\b(\d{2})\b', r.text)
        lotos = [n for n in lotos if n != '00' and len(n) == 2][:27]
        return {
            "date": date_str,
            "special": special,
            "loto": lotos,
            "time": datetime.now().strftime("%H:%M:%S")
        }
    except Exception as e:
        print(f"❌ Lỗi lấy kết quả: {e}")
        return None

# ========== PHÂN TÍCH & DỰ ĐOÁN ==========
def analyze(history):
    if len(history) < 1:
        return None
    all_loto = []
    for day in history:
        all_loto.extend(day.get("loto", []))
    if not all_loto:
        return None
    freq = Counter(all_loto)
    top3 = freq.most_common(3)
    dau = Counter([n[0] for n in all_loto]).most_common(1)[0]
    duoi = Counter([n[1] for n in all_loto]).most_common(1)[0]
    return {
        "top3": [{"num": n[0], "rate": f"~{round(n[1]/len(history)*100)}%"} for n in top3],
        "dau": {"num": dau[0], "rate": f"~{round(dau[1]/len(history)*100)}%"},
        "duoi": {"num": duoi[0], "rate": f"~{round(duoi[1]/len(history)*100)}%"},
        "duoi_db": history[-1].get("special", "")[-1] if history[-1].get("special") else "?"
    }

# ========== GỬI KẾT QUẢ ĐẾN TELEGRAM ==========
def send_tg(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }, timeout=30)
        print(f"📤 Gửi Telegram: {'✅ THÀNH CÔNG' if r.status_code==200 else f'❌ Lỗi {r.status_code}'}")
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Lỗi gửi: {e}")
        return False

# ========== TẠO BÁO CÁO KẾT QUẢ ==========
def build_report(result, pred):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return f"""
📊 *KẾT QUẢ XSMB — {result['date']}*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 Giải Đặc biệt: *{result['special']}*
📅 Cập nhật: {now}

🤖 *DỰ ĐOÁN DỰA TRÊN LỊCH SỬ*

🎯 *TOP 3 LÔ NÓI TIẾP*
1️⃣ {pred['top3'][0]['num']} — {pred['top3'][0]['rate']}
2️⃣ {pred['top3'][1]['num']} — {pred['top3'][1]['rate']}
3️⃣ {pred['top3'][2]['num']} — {pred['top3'][2]['rate']}

🔢 *ĐẦU LÔ NÓI* → {pred['dau']['num']} — {pred['dau']['rate']}
🔢 *ĐUÔI LÔ NÓI* → {pred['duoi']['num']} — {pred['duoi']['rate']}

🎲 *SỐ CUỐI ĐẶC BIỆT*: {pred['duoi_db']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ *Chỉ tham khảo — Chơi có trách nhiệm!*
"""

# ========== CHƯƠNG TRÌNH CHÍNH ==========
def main():
    print("🚀 Bot XSMB V7.4 khởi động...")
    data = load_data()
    print(f"📂 Đã có {len(data['history'])} ngày dữ liệu")

    # Khởi động web server
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(2)
    print("✅ Server đã chạy")

    # 📤 GỬI KẾT QUẢ NGAY LẦN ĐẦU
    print("📤 Đang lấy kết quả & gửi...")
    result = get_xsmb_result()

    if result:
        # Lưu dữ liệu nếu ngày mới
        if data["last_date"] != result["date"]:
            data["history"].append(result)
            data["last_date"] = result["date"]
            if len(data["history"]) > 90:
                data["history"] = data["history"][-90:]
            save_data(data)
            print(f"✅ Đã lưu kết quả ngày: {result['date']}")

        # Tạo dự đoán & gửi
        pred = analyze(data["history"])
        if pred:
            send_tg(build_report(result, pred))
            print("✅ Đã gửi kết quả + dự đoán!")
        else:
            print("⚠️ Chưa đủ dữ liệu để phân tích")
    else:
        print("❌ Không lấy được kết quả XSMB")

    # 🔄 Vòng lặp tự động cập nhật
    last_check_date = datetime.now().strftime("%d/%m/%Y")
    while True:
        time.sleep(CHECK_INTERVAL)
        today = datetime.now().strftime("%d/%m/%Y")
        if last_check_date != today:
            print(f"🔄 Kiểm tra kết quả mới — {today}")
            result = get_xsmb_result()
            if result and data["last_date"] != result["date"]:
                data["history"].append(result)
                data["last_date"] = result["date"]
                if len(data["history"]) > 90:
                    data["history"] = data["history"][-90:]
                save_data(data)
                pred = analyze(data["history"])
                if pred:
                    send_tg(build_report(result, pred))
                    print(f"✅ Đã gửi kết quả ngày {today}")
            last_check_date = today

if __name__ == "__main__":
    main()
