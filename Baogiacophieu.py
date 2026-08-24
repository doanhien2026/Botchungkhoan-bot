import requests
import time
from datetime import datetime, timedelta, timezone

# ==========================================
# ⚙️ CẤU HÌNH — ĐÃ ĐIỀN SẴN TOKEN & ID CỦA BẠN
# ==========================================
BOT_TOKEN = "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0"
CHAT_ID = "1030583610"
CHECK_INTERVAL_OPEN = 300    # Mở cửa: mỗi 5 phút = 300 giây
CHECK_INTERVAL_CLOSED = 3600 # Đóng cửa: mỗi 1 giờ = 3600 giây
WATCH_LIST = ["ACV", "FPT", "VCB"]
MAX_RETRIES = 3
ERROR_WAIT_TIME = 30

# ==========================================
# 💰 CẬP NHẬT GIÁ THỰC TẾ TẠI ĐÂY
# Xem trên Cafef/SSI rồi sửa số giá, thay đổi %, tỷ lệ %
# ==========================================
CURRENT_PRICES = {
    "ACV": {"price": 41500, "change": 300, "change_pct": 0.73},
    "FPT": {"price": 72500, "change": 800, "change_pct": 1.12},
    "VCB": {"price": 96200, "change": -300, "change_pct": -0.31}
}

# ==========================================
# 🕐 LẤY NGÀY GIỜ VIỆT NAM
# ==========================================
def get_vietnam_now():
    return datetime.now(timezone(timedelta(hours=7)))

# ==========================================
# 💾 LƯU GIÁ & LỊCH SỬ TÍNH TOÁN
# ==========================================
last_known_data = {
    "ACV": {"price": 41500, "change": 300, "change_pct": 0.73, "saved_at": "24/08/2026 10:30:00"},
    "FPT": {"price": 72500, "change": 800, "change_pct": 1.12, "saved_at": "24/08/2026 10:30:00"},
    "VCB": {"price": 96200, "change": -300, "change_pct": -0.31, "saved_at": "24/08/2026 10:30:00"}
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
            resp = requests.post(url, data=payload, timeout=30)
            result = resp.json()
            if resp.status_code == 200 and result.get("ok"):
                print("✅ Gửi tin nhắn thành công!")
                return True
        except Exception as e:
            print(f"❌ Lỗi gửi tin: {e}")
        time.sleep(2)
    return False

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
# 📊 LẤY GIÁ TỪ DANH SÁCH BẠN CẬP NHẬT
# ==========================================
def get_stock_data(symbol, is_market_open_now):
    now = get_vietnam_now()
    print(f"\n🔄 Lấy giá {symbol} | {now.strftime('%H:%M:%S')}")
    
    cp = CURRENT_PRICES.get(symbol, {})
    price = cp.get("price", 0)
    
    if price <= 0:
        cached = last_known_data.get(symbol, {})
        return {
            "price": cached["price"],
            "change": cached["change"],
            "change_pct": cached["change_pct"],
            "source": f"⚠️ Chưa cập nhật giá mới — dùng giá lưu lúc {cached['saved_at']}"
        }
    
    last_known_data[symbol] = {
        "price": price,
        "change": cp.get("change", 0),
        "change_pct": cp.get("change_pct", 0),
        "saved_at": now.strftime('%d/%m/%Y %H:%M:%S')
    }
    
    return {
        "price": price,
        "change": cp.get("change", 0),
        "change_pct": cp.get("change_pct", 0),
        "source": "🟢 GIÁ BẠN CẬP NHẬT THỦ CÔNG"
    }

# ==========================================
# 📈 TÍNH CHỈ SỐ KỸ THUẬT & KHUYẾN NGHỊ
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
    
    return {
        "mua": mua,
        "ban": ban,
        "nam_giu": nam_giu,
        "ma5": ma5,
        "ma10": ma10,
        "rsi": rsi,
        "support": support,
        "resistance": resistance
    }

# ==========================================
# 🚀 CHƯƠNG TRÌNH CHÍNH
# ==========================================
def main():
    now = get_vietnam_now()
    print("=" * 60)
    print("🚀 BOT CỔ PHIẾU — CHẠY TRÊN GITHUB")
    print(f"🕐 Giờ Việt Nam: {now.strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    send_telegram_message("""🚀 <b>BOT ĐÃ KHỞI ĐỘNG TRÊN GITHUB!</b>

📅 Ngày giờ: """ + get_vietnam_now().strftime('%d/%m/%Y %H:%M:%S') + """
📊 Theo dõi: ACV, FPT, VCB
💡 Cập nhật giá ở phần CURRENT_PRICES

⏱️ Mở cửa: mỗi 5 phút
⏱️ Đóng cửa: mỗi 1 giờ

<b>✅ Sẵn sàng!</b>
""")
    
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
            
            print(f"\n⏰ [{now.strftime('%d/%m/%Y %H:%M:%S')}] Chu kỳ mới")
            
            msg = "<b>📊 BÁO CÁO CỔ PHIẾU</b>\n"
            msg += f"🕐 Thời gian: {now.strftime('%d/%m/%Y %H:%M:%S')} (VN)\n"
            has_data = False
            
            for symbol in WATCH_LIST:
                data = get_stock_data(symbol, is_open)
                if not data or data.get("price", 0) == 0:
                    msg += f"\n————————————\n📊 {symbol} — ❌ KHÔNG CÓ DỮ LIỆU\n"
                    continue
                
                has_data = True
                ind = calculate_indicators(symbol, data)
                change_pct = f"{data['change_pct']:+.2f}%"
                
                msg += f"""
————————————
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
                send_telegram_message("❌ KHÔNG CÓ DỮ LIỆU — Cập nhật giá vào code!")
            else:
                msg += f"\n————————————\n⏱️ Báo cáo mỗi {interval_text}\n⚠️ <i>Chỉ tham khảo — tự quyết định giao dịch!</i>"
                send_telegram_message(msg)
            
            print(f"💤 Ngủ {interval_text}...")
            time.sleep(interval)
        
        except Exception as e:
            err = "❌ <b>LỖI:</b> " + str(e) + "\n🕐 " + get_vietnam_now().strftime('%d/%m/%Y %H:%M:%S')
            print(f"\n{err}")
            send_telegram_message(err)
            time.sleep(ERROR_WAIT_TIME)

if __name__ == "__main__":
    main()
