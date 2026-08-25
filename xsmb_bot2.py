import os
import time
import schedule
import requests
from datetime import datetime
import re
from collections import Counter
from flask import Flask

# ========== CẤU HÌNH BOT XSMB ==========
TELEGRAM_TOKEN = "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0"
CHAT_ID = "1030583610"

status_sent = ""

app = Flask(__name__)

@app.route('/')
def health_check():
    return "✅ Bot XSMB đang hoạt động", 200

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def send_xsmb(message, max_retries=5):
    for attempt in range(max_retries):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 200:
                print(f"✅ [BOT XSMB] Đã gửi tin thành công")
                return response.json()
            else:
                print(f"⚠️ Lỗi {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Lỗi kết nối (lần {attempt+1}): {e}")
            time.sleep(3)
    print(f"❌ Thất bại sau {max_retries} lần thử")
    return None

def download_xsmb_data():
    try:
        url = "https://xsmb.com.vn/so-ket-qua-xsmb-60-ngay"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ Không tải được dữ liệu: {e}")
        return None

def parse_and_calculate(html):
    if not html:
        return None
    
    numbers = re.findall(r"\b\d{2}\b", html)
    if not numbers:
        return None
    
    freq = Counter(numbers)
    top3_loto = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:3]
    
    dau_counts = Counter([n[0] for n in numbers])
    best_dau = sorted(dau_counts.items(), key=lambda x: x[1], reverse=True)[0]
    
    return {
        "loto": [n[0] for n in top3_loto],
        "dau": best_dau[0],
        "date": datetime.now().strftime("%d/%m/%Y")
    }

def generate_signal():
    global status_sent
    
    html = download_xsmb_data()
    pred = parse_and_calculate(html)
    
    if not pred:
        return
    
    message = f"""
🔮 *TÍN HIỆU XSMB D+1*

📅 Ngày dự báo: *{pred['date']}*

━━━━━━━━━━━━━━━━

🔥 *3 LÔ RƠI*

1️⃣ *{pred['loto'][0]}*
2️⃣ *{pred['loto'][1]}*
3️⃣ *{pred['loto'][2]}*

━━━━━━━━━━━━━━━━

🎲 *ĐẦU ĐỀ*

*Đầu {pred['dau']}*

━━━━━━━━━━━━━━━━

⚠️ *Chỉ tham khảo - không đảm bảo trúng*
🎲 *Chơi có trách nhiệm*
"""
    
    current_signal = f"{pred['loto']}-{pred['dau']}"
    if current_signal != status_sent:
        send_xsmb(message)
        status_sent = current_signal
        print(f"✅ Đã gửi tín hiệu mới: {status_sent}")
    else:
        print(f"⏭ Tín hiệu không đổi, bỏ qua gửi")

def main():
    import threading
    
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Thiếu TOKEN hoặc CHAT_ID")
        return
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print("🌐 Web server đã khởi động cho Render...")
    
    schedule.every(1).hours.do(generate_signal)
    
    print("🚀 BOT XSMB ĐANG CHẠY...")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
