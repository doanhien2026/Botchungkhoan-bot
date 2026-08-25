import os
import time
import requests
from datetime import datetime
from flask import Flask

# ========== CẤU HÌNH BOT CHỨNG KHOÁN ==========
TELEGRAM_TOKEN = "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0"
CHAT_ID = "1030583610"
WATCH_LIST = ["ACV", "FPT", "VCB"]
CHECK_INTERVAL = 300

last_signals = {}

app = Flask(__name__)

@app.route('/')
def health_check():
    return "✅ Bot Chứng Khoán đang hoạt động", 200

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def send_telegram(message, max_retries=5):
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
                print(f"✅ [BOT CK] Đã gửi tin thành công")
                return response.json()
            else:
                print(f"⚠️ Lỗi {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Lỗi kết nối (lần {attempt+1}): {e}")
            time.sleep(3)
    print(f"❌ Thất bại sau {max_retries} lần thử")
    return None

def get_stock_price(symbol):
    try:
        url = f"https://api.cafef.vn/quote/{symbol}.chn"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return {
                    "symbol": symbol,
                    "price": data[0].get("LastPrice", 0),
                    "change": data[0].get("Change", 0),
                    "change_percent": data[0].get("ChangePercent", 0)
                }
        return None
    except Exception as e:
        print(f"❌ Lỗi lấy giá {symbol}: {e}")
        return None

def analyze_stock(stock_data):
    if not stock_data or stock_data["price"] == 0:
        return "N/A"
    
    price = stock_data["price"]
    change = stock_data["change"]
    
    if change > 0:
        return "MUA"
    elif change < 0:
        return "BÁN"
    else:
        return "NẮM GIỮ"

def generate_report():
    global last_signals
    
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    message = f"📊 *BÁO CÁO CHỨNG KHOÁN* — {now}\n\n"
    
    has_change = False
    
    for symbol in WATCH_LIST:
        data = get_stock_price(symbol)
        if not data:
            message += f"⚠️ *{symbol}*: Không lấy được dữ liệu\n\n"
            continue
        
        signal = analyze_stock(data)
        current_key = f"{symbol}-{data['price']}-{signal}"
        
        if last_signals.get(symbol) != current_key:
            last_signals[symbol] = current_key
            has_change = True
        
        message += f"""📌 *{symbol}*
💰 Giá: *{data['price']:,}*
📈 Thay đổi: *{data['change']:+.2f}* ({data['change_percent']:+.2f}%)
📋 Khuyến nghị: *{signal}*

"""
    
    if has_change or not last_signals:
        send_telegram(message)
        print(f"✅ Đã gửi báo cáo chứng khoán — {now}")
    else:
        print(f"⏭ Không có thay đổi, bỏ qua gửi — {now}")

def main():
    import threading
    
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Thiếu TOKEN hoặc CHAT_ID")
        return
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print("🌐 Web server đã khởi động cho Render...")
    
    print("🚀 BOT CHỨNG KHOÁN ĐANG CHẠY...")
    generate_report()
    
    while True:
        time.sleep(CHECK_INTERVAL)
        generate_report()

if __name__ == "__main__":
    main()
