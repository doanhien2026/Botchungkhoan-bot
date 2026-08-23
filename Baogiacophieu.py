import requests
import time
import sys
from datetime import datetime, timedelta

# ==========================================
# ⚙️ CẤU HÌNH
# ==========================================
BOT_TOKEN = "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0"
CHAT_ID = "1030583610"
CHECK_INTERVAL = 3600  # 3600 giây = 1 giờ
WATCH_LIST = ["ACV", "FPT", "VCB", "GAS", "GMD"]
MAX_RETRIES = 5
ERROR_WAIT_TIME = 30

# ==========================================
# 💾 LƯU GIÁ PHIÊN CUỐI + THỜI GIAN LƯU
# ==========================================
last_known_data = {}  # Lưu: {symbol: {"price":..., "change":..., "change_pct":..., "saved_at":...}}

# ==========================================
# 🤖 GỬI TIN NHẮN TELEGRAM
# ==========================================
def send_telegram(text, max_retries=MAX_RETRIES):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for attempt in range(max_retries):
        try:
            data = {"chat_id": CHAT_ID, "text": text}
            r = requests.post(url, data=data, timeout=30)
            res = r.json()
            if res.get("ok"):
                print(f"✅ [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Đã gửi báo cáo!")
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
# 📊 LẤY DỮ LIỆU — 3 NGUỒN + LƯU GIÁ PHIÊN CUỐI
# ==========================================
def get_stock_data(symbol, is_market_open_now):
    print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] Lấy giá {symbol} | Thị trường: {'🟢 MỞ CỬA' if is_market_open_now else '🔒 ĐÓNG CỬA'}")
    
    # ==========================================
    # 🔒 KHI ĐÓNG CỬA → DÙNG GIÁ ĐÃ LƯU
    # ==========================================
    if not is_market_open_now:
        if symbol in last_known_data:
            cached = last_known_data[symbol]
            print(f"   🔒 DÙNG GIÁ PHIÊN CUỐI đã lưu lúc: {cached['saved_at']}")
            print(f"      → {symbol}: {cached['price']:,.0f} VNĐ | {cached['change_pct']:+.2f}%")
            return {
                "price": cached["price"],
                "change": cached["change"],
                "change_pct": cached["change_pct"],
                "source": f"🔒 Giá phiên cuối (lưu lúc {cached['saved_at']})"
            }
        else:
            print(f"   ❌ Chưa có dữ liệu nào được lưu cho {symbol}")
            return None
    
    # ==========================================
    # 🟢 KHI MỞ CỬA → GỌI API LẤY GIÁ MỚI
    # ==========================================
    data = None
    
    # NGUỒN 1: API SSI Securities
    try:
        url = f"https://apipub.ssi.com.vn/md/v1/quote/stock?symbol={symbol}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            res = r.json()
            if res.get('symbol') == symbol:
                price = float(res.get('lastPrice', 0))
                if price > 0:
                    change = float(res.get('change', 0))
                    change_pct = float(res.get('changePercent', 0))
                    data = {"price": price, "change": change, "change_pct": change_pct, "source": "🟢 SSI"}
                    print(f"   ✅ [SSI] {symbol}: {price:,.0f} VNĐ | {change_pct:+.2f}%")
    except Exception as e:
        print(f"   ⚠️ API SSI lỗi: {e}")
    
    # NGUỒN 2: API DNSE / Entrade
    if data is None:
        try:
            url = f"https://services.entrade.com.vn/entrade-api/quote/ticker?symbol={symbol}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                res = r.json()
                if res.get('symbol') == symbol:
                    price = float(res.get('price', 0))
                    if price > 0:
                        change = float(res.get('change', 0))
                        change_pct = float(res.get('percentChange', 0))
                        data = {"price": price, "change": change, "change_pct": change_pct, "source": "🟢 DNSE"}
                        print(f"   ✅ [DNSE] {symbol}: {price:,.0f} VNĐ | {change_pct:+.2f}%")
        except Exception as e:
            print(f"   ⚠️ API DNSE lỗi: {e}")
    
    # NGUỒN 3: API CAFEF
    if data is None:
        try:
            url = f"https://api.cafef.vn/finance/quote/symbol/{symbol}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://cafef.vn/"
            }
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                res = r.json()
                if res.get('Symbol') == symbol:
                    price = float(res.get('LastPrice', 0))
                    if price > 0:
                        change = float(res.get('Change', 0))
                        change_pct = float(res.get('ChangePercent', 0))
                        data = {"price": price, "change": change, "change_pct": change_pct, "source": "🟢 CafeF"}
                        print(f"   ✅ [CafeF] {symbol}: {price:,.0f} VNĐ | {change_pct:+.2f}%")
        except Exception as e:
            print(f"   ⚠️ API CafeF lỗi: {e}")
    
    # ==========================================
    # 💾 LƯU GIÁ MỚI NHẤT — Luôn cập nhật khi lấy được dữ liệu
    # ==========================================
    if data is not None:
        last_known_data[symbol] = {
            "price": data["price"],
            "change": data["change"],
            "change_pct": data["change_pct"],
            "saved_at": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        print(f"   💾 ĐÃ LƯU GIÁ PHIÊN CUỐI cho {symbol} lúc: {last_known_data[symbol]['saved_at']}")
        return data
    
    # ❌ Không lấy được dữ liệu
    print(f"   ❌ Tất cả API đều không lấy được dữ liệu cho {symbol}")
    return None

# ==========================================
# 📈 TÍNH CHỈ SỐ KỸ THUẬT + KHỔUYẾN NGHỊ CÓ GIÁ
# ==========================================
price_history = {}

def calculate_indicators(symbol, price_data):
    current_price = price_data["price"]
    
    # Lưu giá vào lịch sử
    if symbol not in price_history:
        price_history[symbol] = []
    price_history[symbol].append(current_price)
    if len(price_history[symbol]) > 20:
        price_history[symbol].pop(0)
    
    history = price_history[symbol]
    
    # Tính MA5, MA10
    ma5 = round(sum(history[-5:]) / 5, 0) if len(history) >= 5 else round(current_price * 0.995, 0)
    ma10 = round(sum(history[-10:]) / 10, 0) if len(history) >= 10 else round(current_price * 0.99, 0)
    
    # Tính RSI
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
        
        if avg_loss == 0:
            rsi = 100.0 if avg_gain > 0 else 50.0
        else:
            rsi = round(100 - (100 / (1 + avg_gain / avg_loss)), 1)
    else:
        rsi = 50.0
    
    # Tính Hỗ trợ, Kháng cự
    support = round(min(history[-10:]) * 0.995, 0) if len(history) >= 10 else round(current_price * 0.97, 0)
    resistance = round(max(history[-10:]) * 1.005, 0) if len(history) >= 10 else round(current_price * 1.03, 0)
    
    # Khuyến nghị có giá rõ ràng
    mua = f"⏸️ Mua: Chờ giá điều chỉnh về {support:,.0f} VND – chưa mở lệnh"
    ban = f"⏸️ Bán: Chờ giá lên mục tiêu {resistance:,.0f} VND – chưa chốt lời"
    nam_giu = f"✅ Nắm giữ: Giá hiện tại {current_price:,.0f} VND | Mục tiêu {resistance:,.0f} VND | Cắt lỗ dưới {support:,.0f} VND"
    
    return {
        "mua": mua, "ban": ban, "nam_giu": nam_giu,
        "ma5": ma5, "ma10": ma10, "rsi": rsi,
        "support": support, "resistance": resistance
    }

# ==========================================
# 🚀 BOT CHÍNH — CHẠY 24/7, 1 GIỜ 1 LẦN
# ==========================================
print("=" * 60)
print("🚀 BOT THÔNG BÁO CỔ PHIẾU — CHẠY 24/7")
print("=" * 60)
print("📡 Nguồn dữ liệu: SSI → DNSE → CafeF (3 nguồn thời gian thực)")
print("💾 Tự động lưu giá phiên cuối khi lấy được dữ liệu")
print("🔒 Đóng cửa → Dùng giá đã lưu + hiển thị thời gian lưu")
print("⏱️ Cập nhật mỗi 1 giờ")
print("💰 Khuyến nghị: Đã cập nhật kèm giá tham khảo cụ thể")

if not test_bot_connection():
    print("\n❌ Sửa lỗi rồi chạy lại!")
    sys.exit(1)

send_telegram("""🚀 BOT ĐÃ CHẠY 24/7
Ngày giờ: """ + datetime.now().strftime('%d/%m/%Y %H:%M:%S') + """
Cập nhật: Mỗi 1 giờ 1 lần
Theo dõi: """ + ', '.join(WATCH_LIST) + """

📡 Nguồn dữ liệu: SSI → DNSE → CafeF
💾 Tự động lưu giá phiên cuối khi lấy được dữ liệu
🔒 Đóng cửa → Dùng giá đã lưu + hiển thị thời gian lưu
💰 Khuyến nghị: Có kèm giá tham khảo cụ thể

Cảnh báo: Chỉ tham khảo — tự quyết định giao dịch!
""")

last_weekday = None
error_count = 0

print("\n🔄 Bắt đầu vòng lặp chính...")
while True:
    try:
        now = datetime.now()
        weekday = now.weekday()
        is_open, status_text = is_market_open()
        
        if weekday != last_weekday:
            send_telegram("""🔔 THÔNG BÁO TRẠNG THÁI
Ngày giờ: """ + now.strftime('%d/%m/%Y %H:%M:%S') + """
""" + status_text + """

Cảnh báo: Chỉ tham khảo — tự quyết định giao dịch!
""")
            last_weekday = weekday
        
        print(f"\n{'='*60}")
        print(f"⏰ [{now.strftime('%d/%m/%Y %H:%M:%S')}] Bắt đầu chu kỳ báo cáo mới")
        print(f"Trạng thái thị trường: {status_text}")
        print(f"{'='*60}")
        
        full_message = ""
        has_data = False
        
        for symbol in WATCH_LIST:
            data = get_stock_data(symbol, is_open)
            
            # Nếu không có dữ liệu nào từ trước → bỏ qua
            if data is None:
                full_message += f"""
——————————————————————
📊 {symbol} – ❌ CHƯA CÓ DỮ LIỆU
📡 Nguồn: Chưa lấy được giá từ API nào
⏭️ Vui lòng chờ thị trường mở cửa để bot lấy dữ liệu
"""
                continue
            
            has_data = True
            ind = calculate_indicators(symbol, data)
            change_pct_str = f"{data['change_pct']:+.2f}%"
            
            report = f"""
——————————————————————
📊 {symbol} – Giá: {data['price']:,.0f} VND | Thay đổi: {change_pct_str}
📡 Nguồn: {data['source']}
📉 MA5: {ind['ma5']:,.0f} | MA10: {ind['ma10']:,.0f} | RSI: {ind['rsi']}
🛡️ Hỗ trợ: {ind['support']:,.0f} | Kháng cự: {ind['resistance']:,.0f}
🎯 KHUYẾN NGHỊ:
{ind['mua']}
{ind['ban']}
{ind['nam_giu']}
"""
            full_message += report
        
        if not has_data:
            send_telegram("""
❌ CHƯA CÓ DỮ LIỆU
Tất cả các nguồn (SSI, DNSE, CafeF) đều không lấy được dữ liệu.
Vui lòng chờ thị trường mở cửa để bot lấy dữ liệu.
""")
        else:
            full_message += "\n——————————————————————\n⏱️ Cập nhật mỗi 1 giờ\n⚠️ Chỉ tham khảo — tự quyết định giao dịch!"
            send_telegram(full_message)
        
        print(f"\n💤 Ngủ {CHECK_INTERVAL/3600:.1f} giờ cho đến báo cáo tiếp theo...")
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
