# ==========================================
# BOT CHỨNG KHOÁN - ĐÃ SỬA NGUỒN DỮ LIỆU
# ==========================================
import os
import sys
import time
import threading
import requests
from datetime import datetime
from flask import Flask

# ========== CẤU HÌNH ==========
TELEGRAM_TOKEN = "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0"
CHAT_ID = "1030583610"
WATCH_LIST = ["ACV", "FPT", "VCB"]
CHECK_INTERVAL = 300  # 5 phút
last_signals = {}

# ========== FLASK WEB SERVER ==========
app = Flask(__name__)

@app.route('/')
def health_check():
    return "✅ Bot Chứng Khoán đang hoạt động", 200

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        print(f"🌐 Đang khởi động Flask trên cổng {port}...")
        app.run(host="0.0.0.0", port=port, use_reloader=False)
    except Exception as e:
        print(f"❌ Lỗi Flask: {e}")
        sys.exit(1)

# ========== HÀM GỬI TELEGRAM ==========
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
    return None

# ========== LẤY GIÁ TỪ NGUỒN MỚI ==========
def get_stock_price(symbol):
    # Thử nguồn 1: VnDirect API
    try:
        url = f"https://dchart.vndirect.com.vn/api/quote?symbol={symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://dchart.vndirect.com.vn/"
        }
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data and "data" in data and len(data["data"]) > 0:
                item = data["data"][0]
                return {
                    "symbol": symbol,
                    "price": float(item.get("lastPrice", 0)),
                    "change": float(item.get("change", 0)),
                    "change_percent": float(item.get("changePercent", 0))
                }
    except Exception as e:
        print(f"⚠️ Nguồn VnDirect lỗi {symbol}: {e}")
    
    # Thử nguồn 2: SSI API
    try:
        url = f"https://iboard.ssi.com.vn/dchart/api/quote?symbol={symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data and "data" in data and len(data["data"]) > 0:
                item = data["data"][0]
                return {
                    "symbol": symbol,
                    "price": float(item.get("lastPrice", 0)),
                    "change": float(item.get("change", 0)),
                    "change_percent": float(item.get("changePercent", 0))
                }
    except Exception as e:
        print(f"⚠️ Nguồn SSI lỗi {symbol}: {e}")
    
    # Thử nguồn 3: CafeF mới
    try:
        url = f"https://cafef.vn/du-lieu/ajax/ho-so-chung-khoan.ashx?symbol={symbol}&type=quote"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return {
                    "symbol": symbol,
                    "price": float(data[0].get("LastPrice", 0)),
                    "change": float(data[0].get("Change", 0)),
                    "change_percent": float(data[0].get("ChangePercent", 0))
                }
    except Exception as e:
        print(f"⚠️ Nguồn CafeF lỗi {symbol}: {e}")
    
    return None

def analyze_stock(stock_data):
    if not stock_data or stock_data["price"] == 0:
        return "N/A"
    change = stock_data["change"]
    if change > 0:
        return "MUA"
    elif change < 0:
        return "BÁN"
    return "NẮM GIỮ"

# ========== GỬI BÁO CÁO ==========
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
💰 Giá: *{data['price']:,.2f}*
📈 Thay đổi: *{data['change']:+.2f}* ({data['change_percent']:+.2f}%)
📋 Khuyến nghị: *{signal}*

"""
    if has_change or not last_signals:
        send_telegram(message)
        print(f"✅ Đã gửi báo cáo — {now}")
    else:
        print(f"⏭ Không có thay đổi — {now}")

# ========== CHƯƠNG TRÌNH CHÍNH ==========
def main():
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Thiếu TOKEN hoặc CHAT_ID")
        return
    
    # Khởi động Flask TRƯỚC
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(3)
    print("✅ Flask đã chạy, bắt đầu bot...")
    
    # Chạy lần đầu
    generate_report()
    
    # Lặp vô hạn
    while True:
        time.sleep(CHECK_INTERVAL)
        generate_report()

if __name__ == "__main__":
    main()
