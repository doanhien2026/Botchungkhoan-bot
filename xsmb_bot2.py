# ==========================================
# BOT XSMB — ĐÃ THÊM LƯU TRỮ DỮ LIỆU V4.0
# ==========================================
import os
import json
import time
import requests
import re
from collections import Counter
from datetime import datetime
from flask import Flask, jsonify

# ===================== CẤU HÌNH — CHỈ SỬA Ở ĐÂY =====================
TELEGRAM_TOKEN = "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0"
CHAT_ID = "1030583610"
DATA_FILE = "xsmb_data.json"       # File lưu dữ liệu tự động tạo
CHECK_INTERVAL = 3600              # Kiểm tra mỗi 1 giờ (giây)
# =====================================================================

# ========== FLASK WEB SERVER ==========
app = Flask(__name__)

@app.route('/')
def health_check():
    return "✅ Bot XSMB đang hoạt động — Dữ liệu đã lưu trữ", 200

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host="0.0.0.0", port=port, use_reloader=False)
    except Exception as e:
        print(f"❌ Lỗi Flask: {e}")

# ========== QUẢN LÝ LƯU TRỮ DỮ LIỆU ==========
def load_data():
    """Đọc dữ liệu từ file — có sẵn thì đọc, không thì tạo mới"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"✅ Đọc được {len(data.get('history', []))} ngày dữ liệu từ file")
                return data
        except Exception as e:
            print(f"⚠️ File dữ liệu lỗi, tạo mới: {e}")
    # Tạo dữ liệu mặc định nếu không có file
    return {
        "history": [],       # Lịch sử kết quả XSMB
        "last_date": "",    # Ngày cập nhật cuối
        "predictions": {},  # Tín hiệu dự báo
        "created_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

def save_data(data):
    """Lưu dữ liệu ra file — tự động tạo thư mục nếu cần"""
    try:
        data["updated_at"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Đã lưu dữ liệu — Tổng: {len(data['history'])} ngày")
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu dữ liệu: {e}")
        return False

# ========== LẤY DỮ LIỆU TỪ NGUỒN ==========
def fetch_xsmb_results():
    """Lấy kết quả XSMB mới nhất từ KQXS.vn"""
    try:
        url = "https://kqxs.vn/ket-qua-xo-so-mien-bac-truyen-thong"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            # Tìm ngày và kết quả
            date_match = re.search(r'Kết quả XSMB ngày (\d{2}/\d{2}/\d{4})', response.text)
            date_str = date_match.group(1) if date_match else datetime.now().strftime("%d/%m/%Y")
            
            # Lấy giải đặc biệt
            special_match = re.search(r'Giải Đặc biệt.*?(\d{6})', response.text, re.DOTALL)
            special_num = special_match.group(1) if special_match else "000000"
            
            # Lấy tất cả số cuối 2 chữ số
            all_numbers = re.findall(r'\b(\d{2})\b', response.text)
            loto_numbers = [n for n in all_numbers if n != '00' and len(n) == 2]
            
            return {
                "date": date_str,
                "special": special_num,
                "loto": loto_numbers,
                "fetched_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
    except Exception as e:
        print(f"❌ Lỗi lấy dữ liệu: {e}")
    return None

# ========== PHÂN TÍCH & DỰ BÁO ==========
def analyze_data(data):
    """Phân tích lịch sử → tạo tín hiệu dự báo"""
    history = data.get("history", [])
    if len(history) < 10:
        return None  # Chưa đủ dữ liệu
    
    # Lấy tất cả số lô trong lịch sử
    all_loto = []
    for day in history:
        all_loto.extend(day.get("loto", []))
    
    if not all_loto:
        return None
    
    # Đếm tần suất
    freq = Counter(all_loto)
    top3 = freq.most_common(3)
    dau_counts = Counter([n[0] for n in all_loto])
    best_dau = dau_counts.most_common(1)[0]
    
    return {
        "top3_loto": [{"num": n[0], "rate": f"~{round(n[1]/len(history)*100)}%"} for n in top3],
        "best_dau": {"num": best_dau[0], "rate": f"~{round(best_dau[1]/len(history)*100)}%"},
        "special_last": history[-1].get("special", "") if history else "",
        "date_next": datetime.now().strftime("%d/%m/%Y"),
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

# ========== GỬI TELEGRAM ==========
def send_telegram(message, max_retries=5):
    for attempt in range(max_retries):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            resp = requests.post(url, json={
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }, timeout=30)
            if resp.status_code == 200:
                print("✅ Đã gửi tin Telegram")
                return True
        except Exception as e:
            print(f"⚠️ Lỗi gửi tin: {e}")
            time.sleep(3)
    return False

# ========== CHƯƠNG TRÌNH CHÍNH ==========
def main():
    print("🚀 Bot XSMB khởi động...")
    
    # Bước 1: Đọc dữ liệu đã lưu
    data = load_data()
    print(f"📂 Đã có {len(data['history'])} ngày dữ liệu")
    
    # Bước 2: Khởi động Flask
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(2)
    print("✅ Flask đã chạy")
    
    # Bước 3: Vòng lặp chính
    last_sent_date = ""
    
    while True:
        now = datetime.now()
        current_date = now.strftime("%d/%m/%Y")
        
        # Chỉ cập nhật dữ liệu mới mỗi ngày
        if data.get("last_date") != current_date:
            print(f"🔄 Đang lấy dữ liệu mới — {current_date}")
            new_result = fetch_xsmb_results()
            
            if new_result and new_result["date"] != data.get("last_date"):
                data["history"].append(new_result)
                data["last_date"] = new_result["date"]
                # Giữ chỉ 90 ngày gần nhất để file không quá lớn
                if len(data["history"]) > 90:
                    data["history"] = data["history"][-90:]
                save_data(data)
                print(f"✅ Đã cập nhật: {new_result['date']}")
        
        # Tạo tín hiệu dự báo và gửi (mỗi ngày 1 lần)
        if last_sent_date != current_date and len(data["history"]) >= 10:
            pred = analyze_data(data)
            if pred:
                msg = f"""
🎯 *DỰ BÁO XSMB — {pred['date_next']}*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Dữ liệu: {len(data['history'])} ngày | Cập nhật: {pred['generated_at']}

🏆 *TOP 3 LÔ NÓI TIẾP*
1️⃣ {pred['top3_loto'][0]['num']} | {pred['top3_loto'][0]['rate']}
2️⃣ {pred['top3_loto'][1]['num']} | {pred['top3_loto'][1]['rate']}
3️⃣ {pred['top3_loto'][2]['num']} | {pred['top3_loto'][2]['rate']}

🎲 *ĐẦU ĐỀ NÓI*
→ Đầu {pred['best_dau']['num']} | {pred['best_dau']['rate']}

🔢 *Số cuối đặc biệt vừa ra*: {pred['special_last'][-1] if pred['special_last'] else 'N/A'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ *Chỉ tham khảo — Chơi có trách nhiệm!*
💾 *Dữ liệu đã lưu tự động*
"""
                send_telegram(msg)
                last_sent_date = current_date
                print(f"📤 Đã gửi dự báo ngày {current_date}")
        
        # Ngủ đến lần kiểm tra tiếp theo
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    import threading
    main()
