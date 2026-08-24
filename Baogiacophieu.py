import requests
import time
import sys
from datetime import datetime, timedelta, timezone

# ==========================================
# ⚙️ CẤU HÌNH — ĐÃ ĐIỀN SẴN CỦA BẠN
# ==========================================
BOT_TOKEN = "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0"
CHAT_ID = "1030583610"
CHECK_INTERVAL_OPEN = 300    # 🟢 Mở cửa: 5 phút = 300 giây
CHECK_INTERVAL_CLOSED = 3600 # 🔒 Đóng cửa: 1 giờ = 3600 giây
WATCH_LIST = ["ACV", "FPT", "VCB"]
MAX_RETRIES = 5
ERROR_WAIT_TIME = 30

# ==========================================
# 🕐 LẤY NGÀY GIỜ VIỆT NAM (UTC+7)
# ==========================================
def get_vietnam_now():
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    vietnam_tz = timezone(timedelta(hours=7))
    return utc_now.astimezone(vietnam_tz)

# ==========================================
# 💾 LƯU GIÁ CUỐI CÙNG ĐÃ LẤY ĐƯỢC
# ==========================================
last_known_data = {
    "ACV": {"price": 0, "change": 0, "change_pct": 0, "saved_at": "Chưa có dữ liệu"},
    "FPT": {"price": 0, "change": 0, "change_pct": 0, "saved_at": "Chưa có dữ liệu"},
    "VCB": {"price": 0, "change": 0, "change_pct": 0, "saved_at": "Chưa có dữ liệu"}
}

price_history = {"ACV": [], "FPT": [], "VCB": []}

# ==========================================
# 🤖 GỬI TIN NHẮN TELEGRAM
# ==========================================
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    for attempt in range(MAX_RETRIES):
        try:
            print(f"📤 Gửi tin nhắn... (lần {attempt+1})")
            resp = requests.post(url, data=payload, timeout=30)
            result = resp.json()
            if resp.status_code == 200 and result.get("ok"):
                print("✅ Gửi thành công!")
                return True
            print(f"⚠️ Lỗi: {result}")
        except Exception as e:
            print(f"❌ Lỗi kết nối: {e}")
        time.sleep(2)
    return False

# ==========================================
# 🧪 KIỂM TRA KẾT NỐI BAN ĐẦU
# ==========================================
def test_bot_connection():
    now = get_vietnam_now()
    print("=" * 60)
    print("🔍 KIỂM TRA KẾT NỐI BOT TELEGRAM")
    print(f"🕐 Giờ Việt Nam: {now.strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    try:
        resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=15)
        data = resp.json()
        if resp.status_code == 200 and data.get("ok"):
            bot = data["result"]
            print(f"✅ Token hợp lệ — Bot: {bot.get('first_name')} (@{bot.get('username')})")
        else:
            print(f"❌ Token sai: {data}")
            return False
    except Exception as e:
        print(f"❌ Lỗi kết nối Telegram: {e}")
        return False
    
    return send_telegram_message("""🚀 <b>BOT ĐÃ KHỞI ĐỘNG THÀNH CÔNG!</b>

📅 Ngày giờ: """ + get_vietnam_now().strftime('%d/%m/%Y %H:%M:%S') + """
📊 Theo dõi: ACV, FPT, VCB

⏱️ Mở cửa → Báo cáo mỗi 5 phút (giá thực tế từ API)
⏱️ Đóng cửa → Báo cáo mỗi 1 giờ (giá phiên cuối đã lưu)

<b>✅ Sẵn sàng!</b>
""")

# ==========================================
# 🕒 KIỂM TRA THỊ TRƯỜNG MỞ/ĐÓNG CỬA
# ==========================================
def is_market_open():
    now = get_vietnam_now()
    weekday = now.weekday()
    hour, minute = now.hour, now.minute
    
    if weekday >= 5:
        return False, "🔒 CUỐI TUẦN - THỊ TRƯỜNG ĐÓNG CỬA"
    
    morning = (hour == 9) or (hour == 10) or (hour == 11 and minute < 30)
    afternoon = 13 <= hour < 15
    
    if morning or afternoon:
        return True, "🟢 ĐANG MỞ CỬA"
    return False, "🔒 NGOÀI GIỜ GIAO DỊCH - THỊ TRƯỜNG ĐÓNG CỬA"

# ==========================================
# 📊 LẤY GIÁ — DÙNG NGUỒN MỚI: STOCKINVEST & CAFEF
# ==========================================
def get_stock_data(symbol, is_market_open_now):
    now = get_vietnam_now()
    print(f"\n🔄 Lấy giá {symbol} | Thị trường: {'🟢 MỞ CỬA' if is_market_open_now else '🔒 ĐÓNG CỬA'} | {now.strftime('%H:%M:%S')}")
    
    # 🔒 KHI ĐÓNG CỬA → DÙNG GIÁ ĐÃ LƯU
    if not is_market_open_now:
        cached = last_known_data.get(symbol, {})
        if cached.get("price", 0) > 0:
            print(f"   🔒 Dùng giá đã lưu: {cached['saved_at']}")
            return {
                "price": cached["price"],
                "change": cached["change"],
                "change_pct": cached["change_pct"],
                "source": f"🔒 Giá phiên cuối — lưu lúc {cached['saved_at']}"
            }
        print(f"   ⚠️ Chưa có dữ liệu nào được lưu cho {symbol}")
        return None
    
    # 🟢 KHI MỞ CỬA → GỌI API
    data = None
    
    # NGUỒN 1: StockInvest API — đơn giản & miễn phí
    try:
        url = f"https://api.stockinvest.com.vn/v2/quote?symbol={symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            res = r.json()
            if res.get("symbol") == symbol:
                price = float(res.get("lastPrice", 0))
                if price > 0:
                    change = float(res.get("change", 0))
                    change_pct = float(res.get("changePercent", 0))
                    data = {
                        "price": price,
                        "change": change,
                        "change_pct": change_pct,
                        "source": "🟢 StockInvest — GIÁ THỜI GIAN THỰC"
                    }
                    print(f"   ✅ [StockInvest] {symbol}: {price:,.0f} VNĐ | {change_pct:+.2f}%")
    except Exception as e:
        print(f"   ⚠️ StockInvest lỗi: {e}")
    
    # NGUỒN 2: CafeF API
    if data is None:
        try:
            url = f"https://cafef.vn/du-lieu/quote.ashx?symbol={symbol}"
            headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://cafef.vn/"}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                res = r.json()
                if res.get("Symbol") == symbol:
                    price = float(res.get("LastPrice", 0))
                    if price > 0:
                        change = float(res.get("Change", 0))
                        change_pct = float(res.get("ChangePercent", 0))
                        data = {
                            "price": price,
                            "change": change,
                            "change_pct": change_pct,
                            "source": "🟢 CafeF — GIÁ THỜI GIAN THỰC"
                        }
                        print(f"   ✅ [CafeF] {symbol}: {price:,.0f} VNĐ | {change_pct:+.2f}%")
        except Exception as e:
            print(f"   ⚠️ CafeF lỗi: {e}")
    
    # NGUỒN 3: Vietstock API
    if data is None:
        try:
            url = f"https://api.vietstock.vn/data/quote?symbol={symbol}"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                res = r.json()
                if res.get("symbol") == symbol:
                    price = float(res.get("price", 0))
                    if price > 0:
                        change = float(res.get("change", 0))
                        change_pct = float(res.get("percentChange", 0))
                        data = {
                            "price": price,
                            "change": change,
                            "change_pct": change_pct,
                            "source": "🟢 Vietstock — GIÁ THỜI GIAN THỰC"
                        }
                        print(f"   ✅ [Vietstock] {symbol}: {price:,.0f} VNĐ | {change_pct:+.2f}%")
        except Exception as e:
            print(f"   ⚠️ Vietstock lỗi: {e}")
    
    # 💾 LƯU GIÁ MỚI NHẤT
    if data:
        last_known_data[symbol] = {
            "price": data["price"],
            "change": data["change"],
            "change_pct": data["change_pct"],
            "saved_at": get_vietnam_now().strftime('%d/%m/%Y %H:%M:%S')
        }
        print(f"   💾 Đã lưu giá mới cho {symbol}")
        return data
    
    # ❌ Tất cả API lỗi → dùng giá đã lưu
    print(f"   ⚠️ Tất cả API lỗi → dùng giá đã lưu (nếu có)")
    cached = last_known_data.get(symbol, {})
    if cached.get("price", 0) > 0:
        return {
            "price": cached["price"],
            "change": cached["change"],
            "change_pct": cached["change_pct"],
            "source": f"⚠️ API lỗi — dùng giá lưu lúc {cached['saved_at']}"
        }
    return None

# ==========================================
# 📈 TÍNH CHỈ SỐ & KHUYẾN NGHỊ
# ==========================================
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
    
    rsi = 50.0
    if len(history) >= 5:
        gains, losses = [], []
        for i in range(1, min(14, len(history))):
            diff = history[i] - history[i-1]
            if diff > 0: gains.append(diff)
            else: losses.append(abs(diff))
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        if avg_loss == 0:
            rsi = 100.0 if avg_gain > 0 else 50.0
        else:
            rsi = round(100 - (100 / (1 + avg_gain / avg_loss)), 1)
    
    support = round(min(history[-10:]) * 0.995, 0) if len(history) >= 10 else round(current_price * 0.97, 0)
    resistance = round(max(history[-10:]) * 1.005, 0) if len(history) >= 10 else round(current_price * 1.03, 0)
    
    if current_price < ma5 and current_price < support:
        mua = f"✅ <b>MUA NGAY:</b> Giá {current_price:,.0f} VND — Đã điều chỉnh về hỗ trợ {support:,.0f} VND"
    elif abs(current_price - support) / support < 0.01:
        mua = f"⏸️ <b>MUA CHỜ:</b> Giá {current_price:,.0f} VND gần hỗ trợ {support:,.0f} VND"
    else:
        mua = f"⏸️ <b>MUA:</b> Chờ giá điều chỉnh về {support:,.0f} VND"
    
    if current_price > ma5 and current_price > resistance:
        ban = f"✅ <b>BÁN NGAY:</b> Giá {current_price:,.0f} VND — Đã chạm kháng cự {resistance:,.0f} VND"
    elif abs(current_price - resistance) / resistance < 0.01:
        ban = f"⏸️ <b>BÁN CHỜ:</b> Giá {current_price:,.0f} VND gần kháng cự {resistance:,.0f} VND"
    else:
        ban = f"⏸️ <b>BÁN:</b> Chờ giá lên mục tiêu {resistance:,.0f} VND"
    
    if ma5 > ma10 and rsi > 50 and support < current_price < resistance:
        hold = "🟢 <b>NẮM GIỮ — Xu hướng tăng tốt</b>"
    elif ma5 < ma10 and rsi < 50:
        hold = "🔴 <b>CÂN NHẮC GIẢM TỶ TRỌNG — Xu hướng yếu</b>"
    else:
        hold = "🟡 <b>NẮM GIỮ — Chờ tín hiệu rõ hơn</b>"
    
    nam_giu = f"""{hold}
💰 Giá hiện tại: <b>{current_price:,.0f} VND</b>
🎯 Mục tiêu bán: {resistance:,.0f} VND
🛑 Cắt lỗ dưới: {support:,.0f} VND"""
    
    return {"mua": mua, "ban": ban, "nam_giu": nam_giu, "ma5": ma5, "ma10": ma10, "rsi": rsi, "support": support, "resistance": resistance}

# ==========================================
# 🚀 CHƯƠNG TRÌNH CHÍNH
# ==========================================
def main():
    now = get_vietnam_now()
    print("=" * 60)
    print("🚀 BOT CỔ PHIẾU — GIÁ THỜI GIAN THỰC")
    print(f"🕐 Giờ Việt Nam: {now.strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    print(f"📊 Theo dõi: {', '.join(WATCH_LIST)}")
    print(f"⏱️ Mở cửa: mỗi {CHECK_INTERVAL_OPEN//60} phút | Đóng cửa: mỗi {CHECK_INTERVAL_CLOSED//60//60} giờ")
    print("=" * 60)
    
    if not test_bot_connection():
        print("\n❌ Kiểm tra kết nối thất bại!")
        sys.exit(1)
    
    last_weekday = None
    
    while True:
        try:
            now = get_vietnam_now()
            weekday = now.weekday()
            is_open, status_text = is_market_open()
            interval = CHECK_INTERVAL_OPEN if is_open else CHECK_INTERVAL_CLOSED
            interval_text = "5 phút" if is_open else "1 giờ"
            
            if weekday != last_weekday:
                send_telegram_message("""🔔 <b>THÔNG BÁO TRẠNG THÁI</b>
📅 Ngày: """ + now.strftime('%d/%m/%Y') + """
🕐 Giờ: """ + now.strftime('%H:%M:%S') + """
""" + status_text + """
⏱️ Tần suất: """ + interval_text + """
""")
                last_weekday = weekday
            
            print(f"\n{'='*60}")
            print(f"⏰ [{now.strftime('%d/%m/%Y %H:%M:%S')}] Bắt đầu chu kỳ mới")
            print(f"Trạng thái: {status_text} | Tần suất: {interval_text}")
            print(f"{'='*60}")
            
            msg = "<b>📊 BÁO CÁO CỔ PHIẾU</b>\n"
            msg += f"🕐 Thời gian: {now.strftime('%d/%m/%Y %H:%M:%S')} (VN)\n"
            has_data = False
            
            for symbol in WATCH_LIST:
                data = get_stock_data(symbol, is_open)
                if not data:
                    msg += f"\n——————————————————\n📊 {symbol} — ❌ KHÔNG CÓ DỮ LIỆU\n"
                    continue
                
                has_data = True
                ind = calculate_indicators(symbol, data)
                change_pct = f"{data['change_pct']:+.2f}%"
                
                msg += f"""
——————————————————
📊 <b>{symbol}</b> — Giá: <b>{data['price']:,.0f} VND</b> | {change_pct}
📡 Nguồn: {data['source']}
📉 MA5: {ind['ma5']:,.0f} | MA10: {ind['ma10']:,.0f} | RSI: {ind['rsi']}
🛡️ Hỗ trợ: {ind['support']:,.0f} | Kháng cự: {ind['resistance']:,.0f}

🎯 <b>KHUYẾN NGHỊ:</b>
{ind['mua']}
{ind['ban']}
{ind['nam_giu']}
"""
            
            if not has_data:
                send_telegram_message("❌ KHÔNG LẤY ĐƯỢC DỮ LIỆU — Tất cả API hiện không phản hồi!")
            else:
                msg += f"\n——————————————————\n⏱️ Báo cáo mỗi {interval_text}\n⚠️ <i>Chỉ tham khảo — tự quyết định giao dịch!</i>"
                send_telegram_message(msg)
            
            print(f"\n💤 Ngủ {interval_text}...")
            time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n👋 Bot dừng bởi người dùng")
            send_telegram_message("🔴 <b>BOT ĐÃ DỪNG</b> — " + get_vietnam_now().strftime('%d/%m/%Y %H:%M:%S'))
            sys.exit(0)
        except Exception as e:
            err = "❌ <b>LỖI:</b> " + str(e) + "\n🕐 " + get_vietnam_now().strftime('%d/%m/%Y %H:%M:%S')
            print(f"\n{err}")
            send_telegram_message(err)
            time.sleep(ERROR_WAIT_TIME)

if __name__ == "__main__":
    main()
