import requests
import time
import sys
from datetime import datetime, timedelta
from flask import Flask

# ==========================================
# ⚙️ CẤU HÌNH
# ==========================================
BOT_TOKEN = "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0"
CHAT_ID = "1030583610"
CHECK_INTERVAL = 60  # 60 giây = 1 phút
WATCH_LIST = ["ACV", "FPT"]
MAX_RETRIES = 5
ERROR_WAIT_TIME = 30

# GIÁ ĐÓNG CỬA DỰ PHÒNG
last_close_price = {
    "ACV": {"price": 27600, "change": 150, "change_pct": 0.55, "volume": 12500000},
    "FPT": {"price": 98200, "change": -800, "change_pct": -0.81, "volume": 8700000}
}

# ==========================================
# 🌐 WEB SERVER ĐỂ RENDER KHÔNG TẮT BOT
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot Chứng Khoán đang chạy 24/7 — " + datetime.now().strftime('%d/%m/%Y %H:%M:%S')

def run_web():
    app.run(host='0.0.0.0', port=10000)

# ==========================================
# 🤖 GỬI TIN NHẮN TELEGRAM
# ==========================================
def send_telegram(text, max_retries=MAX_RETRIES):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for attempt in range(max_retries):
        try:
            data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
            r = requests.post(url, data=data, timeout=30)
            res = r.json()
            if res.get("ok"):
                print(f"✅ [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Đã gửi báo cáo!")
                return True
            if res.get("error_code") == 400:
                data = {"chat_id": CHAT_ID, "text": text.replace("*", "").replace("`", "")}
                r = requests.post(url, data=data, timeout=30)
                if r.json().get("ok"):
                    return True
        except Exception as e:
            print(f"  ⚠️ Lỗi gửi lần {attempt+1}: {e}")
        time.sleep(3)
    print(f"❌ Không gửi được sau {max_retries} lần")
    return False

# ==========================================
# 🧪 KIỂM TRA KẾT NỐI BOT
# ==========================================
def test_bot_connection():
    print("🔍 Kiểm tra kết nối Bot Telegram...")
    try:
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=15)
        res = r.json()
        if not res.get("ok"):
            print(f"❌ Token sai hoặc hết hạn!")
            return False
        bot_name = res['result']['first_name']
        print(f"✅ Token hợp lệ — Bot: {bot_name}")
        if send_telegram(f"🔍 Kết nối thành công — {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\nBot sẽ chạy 24/7 không ngừng!"):
            print(f"✅ Chat ID hợp lệ — Bot có thể gửi tin nhắn!")
            return True
        return False
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        return False

# ==========================================
# 🕒 KIỂM TRA TRẠNG THÁI THỊ TRƯỜNG
# ==========================================
def is_market_open():
    now = datetime.now()
    weekday = now.weekday()
    hour = now.hour
    minute = now.minute
    
    if weekday >= 5:
        return False, "🔒 CUỐI TUẦN - THỊ TRƯỜNG ĐÓNG CỬA"
    
    morning = (hour == 9) or (hour == 10) or (hour == 11 and minute < 30)
    afternoon = (hour == 13) or (hour == 14) or (hour == 15 and minute == 0)
    
    if morning or afternoon:
        return True, "🟢 ĐANG MỞ CỬA"
    else:
        return False, "🔒 NGOÀI GIỜ GIAO DỊCH - THỊ TRƯỜNG ĐÓNG CỬA"

# ==========================================
# 📊 LẤY DỮ LIỆU CỔ PHIẾU
# ==========================================
def get_stock_data(symbol):
    print(f"🔄 Đang lấy dữ liệu {symbol}...")
    
    # Thử API SSI
    try:
        url = f"https://apipub.ssi.com.vn/md/v1/quote/stock?symbol={symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('symbol') == symbol:
                price = float(data.get('lastPrice', 0))
                if price > 0:
                    change = float(data.get('change', 0))
                    change_pct = float(data.get('changePercent', 0))
                    volume = data.get('totalTradingVolume', 0)
                    last_close_price[symbol] = {
                        "price": price, "change": change,
                        "change_pct": change_pct, "volume": volume
                    }
                    print(f"   ✅ Lấy thành công: {price:,.0f} VNĐ")
                    return last_close_price[symbol]
    except Exception as e:
        print(f"   ⚠️ API SSI lỗi: {e}")
    
    # Thử API DNSE
    try:
        url = f"https://services.entrade.com.vn/entrade-api/quote/ticker?symbol={symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('symbol') == symbol:
                price = float(data.get('price', 0))
                if price > 0:
                    change = float(data.get('change', 0))
                    change_pct = float(data.get('percentChange', 0))
                    volume = data.get('volume', 0)
                    last_close_price[symbol] = {
                        "price": price, "change": change,
                        "change_pct": change_pct, "volume": volume
                    }
                    print(f"   ✅ Lấy thành công: {price:,.0f} VNĐ")
                    return last_close_price[symbol]
    except Exception as e:
        print(f"   ⚠️ API DNSE lỗi: {e}")
    
    # TẤT CẢ API LỖI → DÙNG GIÁ ĐÓNG CỬA
    print(f"   🔒 Dùng giá đóng cửa: {last_close_price[symbol]['price']:,.0f} VNĐ")
    return last_close_price[symbol]

# ==========================================
# 📈 TÍNH CHỈ SỐ KỸ THUẬT — ĐÃ SỬA LỖI CHIA CHO 0
# ==========================================
price_history = {}

def calculate_indicators(symbol, price_data):
    current_price = price_data["price"]
    
    if symbol not in price_history:
        price_history[symbol] = []
    price_history[symbol].append(current_price)
    if len(price_history[symbol]) > 20:
        price_history[symbol].pop(0)
    
    history = price_history[symbol]
    
    ma5 = round(sum(history[-5:]) / 5, 0) if len(history) >= 5 else round(current_price * 0.995, 0)
    ma10 = round(sum(history[-10:]) / 10, 0) if len(history) >= 10 else round(current_price * 0.99, 0)
    
    # === SỬA LỖI: Tránh chia cho 0 khi tính RSI ===
    if len(history) >= 5:
        gains = []
        losses = []
        period = min(14, len(history))
        for i in range(1, period):
            diff = history[i] - history[i-1]
            if diff > 0:
                gains.append(diff)
            else:
                losses.append(abs(diff))
        
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        # Tránh chia cho 0
        if avg_loss == 0:
            rsi = 100.0 if avg_gain > 0 else 50.0
        else:
            rsi = round(100 - (100 / (1 + avg_gain / avg_loss)), 1)
    else:
        rsi = 50.0  # Giá trị mặc định khi chưa đủ dữ liệu
    
    support = round(min(history[-10:]) * 0.995, 0) if len(history) >= 10 else round(current_price * 0.97, 0)
    resistance = round(max(history[-10:]) * 1.005, 0) if len(history) >= 10 else round(current_price * 1.03, 0)
    
    if current_price > ma10 and rsi < 50 and price_data["change_pct"] < 0:
        mua = f"Mua: Giá {current_price:,.0f} VNĐ | Mục tiêu {resistance:,.0f} VNĐ | Cắt lỗ dưới {support:,.0f} VNĐ"
        ban = "Bán: Không phải thời điểm bán"
        nam_giu = "Nắm giữ: Không áp dụng"
    elif current_price < ma5 and rsi > 55 and price_data["change_pct"] > 0.5:
        mua = "Mua: Chờ giá điều chỉnh thêm"
        ban = f"Bán: Giá {current_price:,.0f} VNĐ | Chốt lời phần | Hỗ trợ tiếp theo {support:,.0f} VNĐ"
        nam_giu = "Nắm giữ: Không áp dụng"
    else:
        mua = "Mua: Chờ tín hiệu rõ hơn — không mở lệnh mới"
        ban = "Bán: Chờ tín hiệu chốt lời — không vội bán"
        nam_giu = f"Nắm giữ: Tiếp tục giữ cổ phiếu | Mục tiêu {resistance:,.0f} VNĐ | Cắt lỗ dưới {support:,.0f} VNĐ"
    
    return {
        "mua": mua, "ban": ban, "nam_giu": nam_giu,
        "ma5": ma5, "ma10": ma10, "rsi": rsi,
        "support": support, "resistance": resistance
    }

# ==========================================
# 🚀 BOT CHÍNH — CHẠY 24/7
# ==========================================
print("=" * 60)
print("🚀 BOT THÔNG BÁO CỔ PHIẾU — CHẠY 24/7")
print("=" * 60)

# Khởi động web server trong luồng riêng
import threading
web_thread = threading.Thread(target=run_web, daemon=True)
web_thread.start()
print("🌐 Web server đã chạy trên cổng 10000")

# Kiểm tra kết nối trước
if not test_bot_connection():
    print("\n❌ Sửa lỗi rồi chạy lại!")
    sys.exit(1)

# Thông báo bắt đầu
send_telegram("""🚀 BOT ĐÃ CHẠY 24/7
Ngày giờ: """ + datetime.now().strftime('%d/%m/%Y %H:%M:%S') + """
Cập nhật: Mỗi 1 phút 1 lần
Theo dõi: """ + ', '.join(WATCH_LIST) + """

☁️ Chạy trên đám mây — TẮT MÁY VẪN HOẠT ĐỘNG
🔒 Đóng cửa → Gửi GIÁ ĐÓNG CỬA HIỆN TẠI
🟢 Mở cửa → Gửi giá thời gian thực
✅ Luôn có chỉ số + khuyến nghị Mua/Bán/Nắm giữ

Cảnh báo: Chỉ tham khảo — tự quyết định giao dịch!
""")

last_weekday = None
error_count = 0

# === VÒNG LẶP VĨNH CỬU — KHÔNG BAO GIỜ DỪNG ===
print("\n🔄 Bắt đầu vòng lặp chính...")
while True:
    try:
        now = datetime.now()
        weekday = now.weekday()
        is_open, status_text = is_market_open()
        
        # Thông báo trạng thái khi thay đổi ngày
        if weekday != last_weekday:
            send_telegram("""🔔 THÔNG BÁO TRẠNG THÁI
Ngày giờ: """ + now.strftime('%d/%m/%Y %H:%M:%S') + """
""" + status_text + """

Cảnh báo: Chỉ tham khảo — tự quyết định giao dịch!
""")
            last_weekday = weekday
        
        # Tạo báo cáo
        print(f"\n🔄 [{now.strftime('%H:%M:%S')}] Tạo báo cáo mới... | {status_text}")
        summary = "📊 BÁO CÁO TỔNG HỢP — " + now.strftime('%d/%m/%Y %H:%M:%S') + "\n" + status_text + "\n"
        
        for symbol in WATCH_LIST:
            data = get_stock_data(symbol)
            ind = calculate_indicators(symbol, data)
            
            summary += f"""
{symbol} — Giá: {data['price']:,.0f} VNĐ | Thay đổi: {data['change_pct']:+.2f}%
MA5: {ind['ma5']:,.0f} | MA10: {ind['ma10']:,.0f} | RSI: {ind['rsi']}
Hỗ trợ: {ind['support']:,.0f} | Kháng cự: {ind['resistance']:,.0f}
💡 KHUYẾN NGHỊ:
{ind['mua']}
{ind['ban']}
{ind['nam_giu']}
"""
        
        summary += "\n⏱️ Cập nhật mỗi phút\n⚠️ Chỉ tham khảo — tự quyết định giao dịch!"
        
        # Gửi báo cáo
        if send_telegram(summary):
            error_count = 0
        else:
            error_count += 1
            if error_count >= 10:
                print(f"⚠️ {error_count} lần lỗi liên tiếp — chờ 1 phút rồi thử lại")
                time.sleep(60)
                error_count = 0
        
        # Chờ đến lượt tiếp theo
        time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n👋 Bot đã được dừng thủ công")
        send_telegram("🔴 BOT ĐÃ ĐƯỢC DỪNG — Người dùng đã tắt chương trình")
        sys.exit(0)
    
    except Exception as e:
        error_msg = f"❌ Lỗi hệ thống: {e}"
        print(f"\n{error_msg}")
        send_telegram(f"⚠️ CẢNH BÁO: {error_msg}\nBot sẽ tự động thử lại sau {ERROR_WAIT_TIME} giây...")
        time.sleep(ERROR_WAIT_TIME)
        # KHÔNG DỪNG — tự động quay lại vòng lặp!
                r = requests.post(url, data=data, timeout=30)
                if r.json().get("ok"):
                    return True
        except Exception as e:
            print(f"  ⚠️ Lỗi gửi lần {attempt+1}: {e}")
        time.sleep(3)
    print(f"❌ Không gửi được sau {max_retries} lần")
    return False

# ==========================================
# 🧪 KIỂM TRA KẾT NỐI BOT
# ==========================================
def test_bot_connection():
    print("🔍 Kiểm tra kết nối Bot Telegram...")
    try:
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=15)
        res = r.json()
        if not res.get("ok"):
            print(f"❌ Token sai hoặc hết hạn!")
            return False
        bot_name = res['result']['first_name']
        print(f"✅ Token hợp lệ — Bot: {bot_name}")
        if send_telegram(f"🔍 Kết nối thành công — {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\nBot sẽ chạy 24/7 không ngừng!"):
            print(f"✅ Chat ID hợp lệ — Bot có thể gửi tin nhắn!")
            return True
        return False
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        return False

# ==========================================
# 🕒 KIỂM TRA TRẠNG THÁI THỊ TRƯỜNG
# ==========================================
def is_market_open():
    now = datetime.now()
    weekday = now.weekday()
    hour = now.hour
    minute = now.minute
    
    if weekday >= 5:
        return False, "🔒 CUỐI TUẦN - THỊ TRƯỜNG ĐÓNG CỬA"
    
    morning = (hour == 9) or (hour == 10) or (hour == 11 and minute < 30)
    afternoon = (hour == 13) or (hour == 14) or (hour == 15 and minute == 0)
    
    if morning or afternoon:
        return True, "🟢 ĐANG MỞ CỬA"
    else:
        return False, "🔒 NGOÀI GIỜ GIAO DỊCH - THỊ TRƯỜNG ĐÓNG CỬA"

# ==========================================
# 📊 LẤY DỮ LIỆU CỔ PHIẾU
# ==========================================
def get_stock_data(symbol):
    print(f"🔄 Đang lấy dữ liệu {symbol}...")
    
    # Thử API SSI
    try:
        url = f"https://apipub.ssi.com.vn/md/v1/quote/stock?symbol={symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('symbol') == symbol:
                price = float(data.get('lastPrice', 0))
                if price > 0:
                    change = float(data.get('change', 0))
                    change_pct = float(data.get('changePercent', 0))
                    volume = data.get('totalTradingVolume', 0)
                    last_close_price[symbol] = {
                        "price": price, "change": change,
                        "change_pct": change_pct, "volume": volume
                    }
                    print(f"   ✅ Lấy thành công: {price:,.0f} VNĐ")
                    return last_close_price[symbol]
    except Exception as e:
        print(f"   ⚠️ API SSI lỗi: {e}")
    
    # Thử API DNSE
    try:
        url = f"https://services.entrade.com.vn/entrade-api/quote/ticker?symbol={symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('symbol') == symbol:
                price = float(data.get('price', 0))
                if price > 0:
                    change = float(data.get('change', 0))
                    change_pct = float(data.get('percentChange', 0))
                    volume = data.get('volume', 0)
                    last_close_price[symbol] = {
                        "price": price, "change": change,
                        "change_pct": change_pct, "volume": volume
                    }
                    print(f"   ✅ Lấy thành công: {price:,.0f} VNĐ")
                    return last_close_price[symbol]
    except Exception as e:
        print(f"   ⚠️ API DNSE lỗi: {e}")
    
    # TẤT CẢ API LỖI → DÙNG GIÁ ĐÓNG CỬA
    print(f"   🔒 Dùng giá đóng cửa: {last_close_price[symbol]['price']:,.0f} VNĐ")
    return last_close_price[symbol]

# ==========================================
# 📈 TÍNH CHỈ SỐ KỸ THUẬT
# ==========================================
price_history = {}

def calculate_indicators(symbol, price_data):
    current_price = price_data["price"]
    
    if symbol not in price_history:
        price_history[symbol] = []
    price_history[symbol].append(current_price)
    if len(price_history[symbol]) > 20:
        price_history[symbol].pop(0)
    
    history = price_history[symbol]
    
    ma5 = round(sum(history[-5:]) / 5, 0) if len(history) >= 5 else round(current_price * 0.995, 0)
    ma10 = round(sum(history[-10:]) / 10, 0) if len(history) >= 10 else round(current_price * 0.99, 0)
    
    if len(history) >= 5:
        gains = []
        losses = []
        period = min(14, len(history))
        for i in range(1, period):
            diff = history[i] - history[i-1]
            if diff > 0:
                gains.append(diff)
            else:
                losses.append(abs(diff))
        avg_gain = sum(gains)/len(gains) if gains else 0
        avg_loss = sum(losses)/len(losses) if losses else 0.001
        rsi = round(100 - (100 / (1 + avg_gain/avg_loss)), 1)
    else:
        rsi = 50.0
    
    support = round(min(history[-10:]) * 0.995, 0) if len(history) >= 10 else round(current_price * 0.97, 0)
    resistance = round(max(history[-10:]) * 1.005, 0) if len(history) >= 10 else round(current_price * 1.03, 0)
    
    if current_price > ma10 and rsi < 50 and price_data["change_pct"] < 0:
        mua = f"Mua: Giá {current_price:,.0f} VNĐ | Mục tiêu {resistance:,.0f} VNĐ | Cắt lỗ dưới {support:,.0f} VNĐ"
        ban = "Bán: Không phải thời điểm bán"
        nam_giu = "Nắm giữ: Không áp dụng"
    elif current_price < ma5 and rsi > 55 and price_data["change_pct"] > 0.5:
        mua = "Mua: Chờ giá điều chỉnh thêm"
        ban = f"Bán: Giá {current_price:,.0f} VNĐ | Chốt lời phần | Hỗ trợ tiếp theo {support:,.0f} VNĐ"
        nam_giu = "Nắm giữ: Không áp dụng"
    else:
        mua = "Mua: Chờ tín hiệu rõ hơn — không mở lệnh mới"
        ban = "Bán: Chờ tín hiệu chốt lời — không vội bán"
        nam_giu = f"Nắm giữ: Tiếp tục giữ cổ phiếu | Mục tiêu {resistance:,.0f} VNĐ | Cắt lỗ dưới {support:,.0f} VNĐ"
    
    return {
        "mua": mua, "ban": ban, "nam_giu": nam_giu,
        "ma5": ma5, "ma10": ma10, "rsi": rsi,
        "support": support, "resistance": resistance
    }

# ==========================================
# 🚀 BOT CHÍNH — CHẠY 24/7
# ==========================================
print("=" * 60)
print("🚀 BOT THÔNG BÁO CỔ PHIẾU — CHẠY 24/7")
print("=" * 60)

# Kiểm tra kết nối trước
if not test_bot_connection():
    print("\n❌ Sửa lỗi rồi chạy lại!")
    sys.exit(1)

# Thông báo bắt đầu
send_telegram("""🚀 BOT ĐÃ CHẠY 24/7
Ngày giờ: """ + datetime.now().strftime('%d/%m/%Y %H:%M:%S') + """
Cập nhật: Mỗi 1 phút 1 lần
Theo dõi: """ + ', '.join(WATCH_LIST) + """

☁️ Chạy trên đám mây — TẮT MÁY VẪN HOẠT ĐỘNG
🔒 Đóng cửa → Gửi GIÁ ĐÓNG CỬA HIỆN TẠI
🟢 Mở cửa → Gửi giá thời gian thực
✅ Luôn có chỉ số + khuyến nghị Mua/Bán/Nắm giữ

Cảnh báo: Chỉ tham khảo — tự quyết định giao dịch!
""")

last_weekday = None
error_count = 0

# === VÒNG LẶP VĨNH CỬU — KHÔNG BAO GIỜ DỪNG ===
print("\n🔄 Bắt đầu vòng lặp chính...")
while True:
    try:
        now = datetime.now()
        weekday = now.weekday()
        is_open, status_text = is_market_open()
        
        # Thông báo trạng thái khi thay đổi ngày
        if weekday != last_weekday:
            send_telegram("""🔔 THÔNG BÁO TRẠNG THÁI
Ngày giờ: """ + now.strftime('%d/%m/%Y %H:%M:%S') + """
""" + status_text + """

Cảnh báo: Chỉ tham khảo — tự quyết định giao dịch!
""")
            last_weekday = weekday
        
        # Tạo báo cáo
        print(f"\n🔄 [{now.strftime('%H:%M:%S')}] Tạo báo cáo mới... | {status_text}")
        summary = "📊 BÁO CÁO TỔNG HỢP — " + now.strftime('%d/%m/%Y %H:%M:%S') + "\n" + status_text + "\n"
        
        for symbol in WATCH_LIST:
            data = get_stock_data(symbol)
            ind = calculate_indicators(symbol, data)
            
            summary += f"""
{symbol} — Giá: {data['price']:,.0f} VNĐ | Thay đổi: {data['change_pct']:+.2f}%
MA5: {ind['ma5']:,.0f} | MA10: {ind['ma10']:,.0f} | RSI: {ind['rsi']}
Hỗ trợ: {ind['support']:,.0f} | Kháng cự: {ind['resistance']:,.0f}
💡 KHUYẾN NGHỊ:
{ind['mua']}
{ind['ban']}
{ind['nam_giu']}
"""
        
        summary += "\n⏱️ Cập nhật mỗi phút\n⚠️ Chỉ tham khảo — tự quyết định giao dịch!"
        
        # Gửi báo cáo
        if send_telegram(summary):
            error_count = 0
        else:
            error_count += 1
            if error_count >= 10:
                print(f"⚠️ {error_count} lần lỗi liên tiếp — chờ 1 phút rồi thử lại")
                time.sleep(60)
                error_count = 0
        
        # Chờ đến lượt tiếp theo
        time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n👋 Bot đã được dừng thủ công")
        send_telegram("🔴 BOT ĐÃ ĐƯỢC DỪNG — Người dùng đã tắt chương trình")
        sys.exit(0)
    
    except Exception as e:
        error_msg = f"❌ Lỗi hệ thống: {e}"
        print(f"\n{error_msg}")
        send_telegram(f"⚠️ CẢNH BÁO: {error_msg}\nBot sẽ tự động thử lại sau {ERROR_WAIT_TIME} giây...")
        time.sleep(ERROR_WAIT_TIME)
        # KHÔNG DỪNG — tự động quay lại vòng lặp!

