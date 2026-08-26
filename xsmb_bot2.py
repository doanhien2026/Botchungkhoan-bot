# ============================================================
# BOT XSMB — HOÀN CHỈNH V5.0
# ✅ Tự lưu dữ liệu | ✅ Gửi ngay khi chạy | ✅ Dễ sửa nhất
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

# ====================== 🔧 CHỈ SỬA Ở ĐÂY ======================
TELEGRAM_TOKEN = "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0"
CHAT_ID = "1030583610"
DATA_FILE = "xsmb_data.json"   # File tự tạo, không cần tạo thủ công
CHECK_INTERVAL = 3600           # Kiểm tra mỗi 1 giờ (giây)
SEND_TIME = "18:35"             # Gửi kết quả hàng ngày
# ===============================================================

app = Flask(__name__)

# ========== WEB SERVER ==========
@app.route('/')
def home():
    return "✅ Bot XSMB V5.0 — Đang hoạt động & Lưu dữ liệu tự động", 200

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

# ========== QUẢN LÝ LƯU TRỮ DỮ LIỆU ==========
def load_data():
    """Đọc dữ liệu — có thì đọc, không thì tạo mới"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    # Tạo mới nếu file lỗi / chưa có
    return {
        "history": [],
        "last_date": "",
        "updated_at": ""
    }

def save_data(data):
    """Lưu dữ liệu ra file"""
    try:
        data["updated_at"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu: {e}")
        return False

# ========== LẤY KẾT QUẢ XSMB ==========
def get_xsmb_result():
    """Lấy kết quả mới nhất từ KQXS.vn"""
    try:
        url = "https://kqxs.vn/ket-qua-xo-so-mien-bac-truyen-thong"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code != 200:
            return None

        # Ngày
        date_match = re.search(r'Kết quả XSMB ngày (\d{2}/\d{2}/\d{4})', r.text)
        date_str = date_match.group(1) if date_match else datetime.now().strftime("%d/%m/%Y")

        # Giải đặc biệt
        special_match = re.search(r'Giải Đặc biệt.*?(\d{6})', r.text, re.DOTALL)
        special = special_match.group(1) if special_match else "------"

        # Tất cả số lô 2 chữ số
        lotos = re.findall(r'<td class="lottery-result-item">(\d{2})</td>', r.text)
        if not lotos:
            lotos = re.findall(r'\b(\d{2})\b', r.text)
            lotos = [n for n in lotos if n != '00' and len(n) == 2][:27]

        return {
            "date": date_str,
            "special": special,
            "loto": lotos,
            "time": datetime.now().strftime("%H:%M:%S")
        }
    except Exception as e:
        print(f"❌ Lỗi lấy dữ liệu: {e}")
        return None

# ========== PHÂN TÍCH & DỰ BÁO ==========
def analyze(history):
    """Phân tích lịch sử → tạo tín hiệu"""
    if len(history) < 10:
        return None

    all_loto = []
    for day in history:
        all_loto.extend(day.get("loto", []))

    if not all_loto:
        return None

    # Top 3 lô nhiều nhất
    freq = Counter(all_loto)
    top3 = freq.most_common(3)

    # Đầu lô nhiều nhất
    dau = Counter([n[0] for n in all_loto]).most_common(1)[0]

    # Đuôi lô nhiều nhất
    duoi = Counter([n[1] for n in all_loto]).most_common(1)[0]

    return {
        "top3": [{"num": n[0], "rate": f"~{round(n[1]/len(history)*100)}%"} for n in top3],
        "dau": {"num": dau[0], "rate": f"~{round(dau[1]/len(history)*100)}%"},
        "duoi": {"num": duoi[0], "rate": f"~{round(duoi[1]/len(history)*100)}%"},
        "nguoi_duoi": history[-1].get("special", "")[-1] if history[-1].get("special") else "?"
    }

# ========== GỬI TELEGRAM ==========
def send_tg(text):
    """Gửi tin nhắn Telegram"""
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
        print(f"❌ Lỗi gửi Telegram: {e}")
        return False

# ========== TẠO BÁO CÁO ==========
def build_report(result, pred):
    """Tạo nội dung báo cáo đẹp"""
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    msg = f"""
📊 *KẾT QUẢ XSMB — {result['date']}*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 Giải Đặc biệt: *{result['special']}*
📅 Cập nhật: {now}
💾 Dữ liệu đã lưu tự động

🤖 *DỰ ĐOÁN DỰA TRÊN LỊCH SỬ*

🎯 *TOP 3 LÔ NÓI TIẾP*
1️⃣ {pred['top3'][0]['num']} — {pred['top3'][0]['rate']}
2️⃣ {pred['top3'][1]['num']} — {pred['top3'][1]['rate']}
3️⃣ {pred['top3'][2]['num']} — {pred['top3'][2]['rate']}

🔢 *ĐẦU LÔ NÓI* → {pred['dau']['num']} — {pred['dau']['rate']}
🔢 *ĐUÔI LÔ NÓI* → {pred['duoi']['num']} — {pred['duoi']['rate']}

🎲 *SỐ CUỐI ĐẶC BIỆT VỪA RA*: {pred['nguoi_duoi']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ *Chỉ tham khảo — Chơi có trách nhiệm!*
"""
    return msg

# ========== CHƯƠNG TRÌNH CHÍNH ==========
def main():
    print("🚀 Bot XSMB V5.0 khởi động...")

    # 1. Tải dữ liệu đã lưu
    data = load_data()
    print(f"📂 Đã có {len(data['history'])} ngày dữ liệu")

    # 2. Khởi động web server
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(2)
    print("✅ Server đã chạy")

    # 3. GỬI BÁO CÁO NGAY LẦN ĐẦU — để kiểm tra
    print("📤 Đang lấy dữ liệu & gửi báo cáo...")
    result = get_xsmb_result()

    if result:
        # Thêm vào lịch sử nếu ngày mới
        if data["last_date"] != result["date"]:
            data["history"].append(result)
            data["last_date"] = result["date"]
            # Giữ 90 ngày gần nhất
            if len(data["history"]) > 90:
                data["history"] = data["history"][-90:]
            save_data(data)
            print(f"✅ Đã lưu dữ liệu: {result['date']}")

        # Tạo dự báo & gửi
        pred = analyze(data["history"])
        if pred:
            msg = build_report(result, pred)
            if send_tg(msg):
                print("✅ Đã gửi báo cáo Telegram!")
            else:
                print("❌ Gửi tin thất bại — kiểm tra TOKEN & CHAT_ID")
        else:
            print("⚠️ Chưa đủ dữ liệu để dự báo (cần ít nhất 10 ngày)")
    else:
        print("❌ Không lấy được kết quả XSMB")

    # 4. Vòng lặp cập nhật định kỳ
    last_check_date = datetime.now().strftime("%d/%m/%Y")

    while True:
        time.sleep(CHECK_INTERVAL)
        today = datetime.now().strftime("%d/%m/%Y")

        # Chỉ cập nhật 1 lần mỗi ngày
        if last_check_date != today:
            print(f"🔄 Kiểm tra dữ liệu mới — {today}")
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
                    print(f"✅ Đã gửi báo cáo ngày {today}")
            last_check_date = today

if __name__ == "__main__":
    main()
