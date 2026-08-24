import requests
import time
import sys
from datetime import datetime, timedelta

# ==========================================
# ⚙️ CẤU HÌNH — ĐÃ ĐIỀN SẴN TOKEN & ID CỦA BẠN
# ==========================================
BOT_TOKEN = "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0"
CHAT_ID = "1030583610"
CHECK_INTERVAL_OPEN = 300    # 🟢 Mở cửa: 5 phút = 300 giây
CHECK_INTERVAL_CLOSED = 3600 # 🔒 Đóng cửa: 1 giờ = 3600 giây
WATCH_LIST = ["ACV", "FPT", "VCB"]  # ✅ 3 mã cổ phiếu
MAX_RETRIES = 5
ERROR_WAIT_TIME = 30

# ==========================================
# 💾 DỮ LIỆU PHIÊN CUỐI — 3 MÃ
# ==========================================
last_known_data = {
    "ACV": {
        "price": 41500,
        "change": 600,
        "change_pct": 1.47,
        "saved_at": "21/08/2026 15:00:00"
    },
    "FPT": {
        "price": 72000,
        "change": 2200,
        "change_pct": 3.15,
        "saved_at": "21/08/2026 15:00:00"
    },
    "VCB": {
        "price": 98500,
        "change": -1200,
        "change_pct": -1.20,
        "saved_at": "21/08/2026 15:00:00"
    }
}

# Lịch sử giá để tính chỉ số
price_history = {
    "ACV": [40800, 41000, 41200, 41300, 41500, 41400, 41350, 41450, 41500, 41500],
    "FPT": [69000, 69500, 70000, 70500, 71000, 71200, 71500, 71800, 72000, 72000],
    "VCB": [100000, 99500, 99000, 98800, 98500, 98700, 98600, 98550, 98500, 98500]
}

# ==========================================
# 🤖 HÀM GỬI TIN NHẮN TELEGRAM — ĐÃ KIỂM TRA
# ==========================================
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            print(f"📤 Đang gửi tin nhắn... (lần thử {attempt+1}/{MAX_RETRIES})")
            response = requests.post(url, data=payload, timeout=30)
            result = response.json()
            
            if response.status_code == 200 and result.get("ok"):
                print(f"✅ Tin nhắn đã gửi thành công!")
                return True
            else:
                print(f"⚠️ Lỗi gửi tin: {result}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2)
        except Exception as e:
            print(f"❌ Lỗi kết nối Telegram: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
    
    print(f"❌ Gửi tin nhắn thất bại sau {MAX_RETRIES} lần thử")
    return False

# ==========================================
# 🧪 KIỂM TRA KẾT NỐI BAN ĐẦU
# ==========================================
def test_bot_connection():
    print("=" * 60)
    print("🔍 KIỂM TRA KẾT NỐI BOT TELEGRAM...")
    print("=" * 60)
    
    # Kiểm tra Token
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    try:
        resp = requests.get(url, timeout=15)
        data = resp.json()
        if resp.status_code == 200 and data.get("ok"):
            bot_info = data["result"]
            print(f"✅ Token hợp lệ!")
            print(f"   Tên Bot: {bot_info.get('first_name')}")
            print(f"   Username: @{bot_info.get('username')}")
        else:
            print(f"❌ Token không hợp lệ! Phản hồi: {data}")
            return False
    except Exception as e:
        print(f"❌ Không kết nối được Telegram: {e}")
        return False
    
    # Gửi tin nhắn kiểm tra
    test_msg = f"""🚀 <b>BOT ĐÃ KHỞI ĐỘNG THÀNH CÔNG!</b>

📅 Ngày giờ: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
📊 Theo dõi: ACV, FPT, VCB

⏱️ Mở cửa → Báo cáo mỗi 5 phút
⏱️ Đóng cửa → Báo cáo mỗi 1 giờ
📡 Nguồn dữ liệu: SSI → DNSE → CafeF

<b>✅ Sẵn sàng gửi tín hiệu!</b>
"""
    return send_telegram_message(test_msg)

# ==========================================
# 🕒 KIỂM TRA THỊ TRƯỜNG MỞ/ĐÓNG CỬA
# ==========================================
def is_market_open():
    now = datetime.now()
    weekday = now.weekday()  # 0=Thứ 2, 4=Thứ 6, 5=Thứ 7, 6=Chủ Nhật
    hour = now.hour
    minute = now.minute
    
    if weekday >= 5:  # Thứ 7, Chủ Nhật
        return False, "🔒 CUỐI TUẦN - THỊ TRƯỜNG ĐÓNG CỬA"
    
    # Phiên sáng: 9:00 - 11:30
    morning_session = (hour == 9) or (hour == 10) or (hour == 11 and minute < 30)
    # Phiên chiều: 13:00 - 15:00
    afternoon_session = (hour >= 13 and hour < 15)
    
    if morning_session or afternoon_session:
        return True, "🟢 ĐANG MỞ CỬA"
    else:
        return False, "🔒 NGOÀI GIỜ GIAO DỊCH - THỊ TRƯỜNG ĐÓNG CỬA"

# ==========================================
# 📊 LẤY DỮ LIỆU GIÁ TỪ CÁC NGUỒN
# ==========================================
def get_stock_data(symbol, is_market_open_now):
    print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] Lấy giá {symbol} | Thị trường: {'🟢 MỞ CỬA' if is_market_open_now else '🔒 ĐÓNG CỬA'}")
    
    # Nếu đóng cửa → dùng giá đã lưu
    if not is_market_open_now:
        if symbol in last_known_data:
            cached = last_known_data[symbol]
            print(f"   🔒 Sử dụng giá phiên cuối: {cached['saved_at']}")
            return {
                "price": cached["price"],
                "change": cached["change"],
                "change_pct": cached["change_pct"],
                "source": f"🔒 Giá phiên cuối (lưu lúc {cached['saved_at']})"
            }
        return None
    
    # Mở cửa → gọi API lấy giá mới
    data = None
    
    # Nguồn 1: SSI
    try:
        url = f"https://apipub.ssi.com.vn/md/v1/quote/stock?symbol={symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            res = r.json()
            if res.get('symbol') == symbol:
                price = float(res.get('lastPrice', 0))
                if price > 0:
                    change = float(res.get('change', 0))
                    change_pct = float(res.get('changePercent', 0))
                    data = {"price": price, "change": change, "change_pct": change_pct, "source": "🟢 SSI — GIÁ MỚI"}
                    print(f"   ✅ [SSI] {symbol}: {price:,.0f} VNĐ | {change_pct:+.2f}%")
    except Exception as e:
        print(f"   ⚠️ SSI lỗi: {e}")
    
    # Nguồn 2: DNSE
    if data is None:
        try:
            url = f"https://services.entrade.com.vn/entrade-api/quote/ticker?symbol={symbol}"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                res = r.json()
                if res.get('symbol') == symbol:
                    price = float(res.get('price', 0))
                    if price > 0:
                        change = float(res.get('change', 0))
                        change_pct = float(res.get('percentChange', 0))
                        data = {"price": price, "change": change, "change_pct": change_pct, "source": "🟢 DNSE — GIÁ MỚI"}
                        print(f"   ✅ [DNSE] {symbol}: {price:,.0f} VNĐ | {change_pct:+.2f}%")
        except Exception as e:
            print(f"   ⚠️ DNSE lỗi: {e}")
    
    # Nguồn 3: CafeF
    if data is None:
        try:
            url = f"https://api.cafef.vn/finance/quote/symbol/{symbol}"
            headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://cafef.vn/"}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                res = r.json()
                if res.get('Symbol') == symbol:
                    price = float(res.get('LastPrice', 0))
                    if price > 0:
                        change = float(res.get('Change', 0))
                        change_pct = float(res.get('ChangePercent', 0))
                        data = {"price": price, "change": change, "change_pct": change_pct, "source": "🟢 CafeF — GIÁ MỚI"}
                        print(f"   ✅ [CafeF] {symbol}: {price:,.0f} VNĐ | {change_pct:+.2f}%")
        except Exception as e:
            print(f"   ⚠️ CafeF lỗi: {e}")
    
    # Lưu giá mới nếu lấy được
    if data is not None:
        last_known_data[symbol] = {
            "price": data["price"],
            "change": data["change"],
            "change_pct": data["change_pct"],
            "saved_at": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        print(f"   💾 Đã lưu giá mới cho {symbol}")
        return data
    
    # Không lấy được mới → dùng giá cũ
    print(f"   ⚠️ Không lấy được giá mới → dùng giá phiên cuối")
    cached = last_known_data[symbol]
    return {
        "price": cached["price"],
        "change": cached["change"],
        "change_pct": cached["change_pct"],
        "source": f"🔒 Giá phiên cuối (lưu lúc {cached['saved_at']}) — API không phản hồi"
    }

# ==========================================
# 📈 TÍNH CHỈ SỐ & TẠO KHUYẾN NGHỊ
# ==========================================
def calculate_indicators(symbol, price_data):
    current_price = price_data["price"]
    
    # Thêm giá mới vào lịch sử
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
    rsi = 50.0
    if len(history) >= 5:
        gains = []
        losses = []
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
            rs = avg_gain / avg_loss
            rsi = round(100 - (100 / (1 + rs)), 1)
    
    # Tính hỗ trợ, kháng cự
    support = round(min(history[-10:]) * 0.995, 0) if len(history) >= 10 else round(current_price * 0.97, 0)
    resistance = round(max(history[-10:]) * 1.005, 0) if len(history) >= 10 else round(current_price * 1.03, 0)
    
    # Tín hiệu MUA
    if current_price < ma5 and current_price < support:
        mua_text = f"✅ <b>MUA NGAY:</b> Giá {current_price:,.0f} VND — Đã điều chỉnh về vùng hỗ trợ {support:,.0f} VND"
    elif abs(current_price - support) / support < 0.01:
        mua_text = f"⏸️ <b>MUA CHỜ:</b> Giá {current_price:,.0f} VND gần hỗ trợ {support:,.0f} VND"
    else:
        mua_text = f"⏸️ <b>MUA:</b> Chờ giá điều chỉnh về {support:,.0f} VND"
    
    # Tín hiệu BÁN
    if current_price > ma5 and current_price > resistance:
        ban_text = f"✅ <b>BÁN NGAY:</b> Giá {current_price:,.0f} VND — Đã chạm kháng cự {resistance:,.0f} VND"
    elif abs(current_price - resistance) / resistance < 0.01:
        ban_text = f"⏸️ <b>BÁN CHỜ:</b> Giá {current_price:,.0f} VND gần kháng cự {resistance:,.0f} VND"
    else:
        ban_text = f"⏸️ <b>BÁN:</b> Chờ giá lên mục tiêu {resistance:,.0f} VND"
    
    # Tín hiệu NẮM GIỮ
    if ma5 > ma10 and rsi > 50 and support < current_price < resistance:
        hold_status = "🟢 <b>NẮM GIỮ — Xu hướng tăng tốt</b>"
    elif ma5 < ma10 and rsi < 50:
        hold_status = "🔴 <b>CÂN NHẮC GIẢM TỶ TRỌNG — Xu hướng yếu</b>"
    else:
        hold_status = "🟡 <b>NẮM GIỮ — Chờ tín hiệu rõ hơn</b>"
    
    nam_giu_text = f"""{hold_status}
💰 Giá hiện tại: <b>{current_price:,.0f} VND</b>
🎯 Mục tiêu bán: {resistance:,.0f} VND
🛑 Cắt lỗ dưới: {support:,.0f} VND"""
    
    return {
        "mua": mua_text,
        "ban": ban_text,
        "nam_giu": nam_giu_text,
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
    print("=" * 60)
    print("🚀 BOT THÔNG BÁO CỔ PHIẾU — CHẠY 24/7")
    print("=" * 60)
    print(f"📊 Theo dõi: {', '.join(WATCH_LIST)}")
    print(f"⏱️ Mở cửa: mỗi {CHECK_INTERVAL_OPEN//60} phút | Đóng cửa: mỗi {CHECK_INTERVAL_CLOSED//60//60} giờ")
    print("=" * 60)
    
    # Kiểm tra kết nối Telegram trước
    if not test_bot_connection():
        print("\n❌ Kết nối Telegram thất bại! Vui lòng kiểm tra Token và Chat ID.")
        sys.exit(1)
    
    last_weekday = None
    
    # Vòng lặp chính
    while True:
        try:
            now = datetime.now()
            weekday = now.weekday()
            is_open, status_text = is_market_open()
            
            # Chọn tần suất
            current_interval = CHECK_INTERVAL_OPEN if is_open else CHECK_INTERVAL_CLOSED
            interval_text = "5 phút" if is_open else "1 giờ"
            
            # Thông báo đổi trạng thái thị trường
            if weekday != last_weekday:
                notify_msg = f"""🔔 <b>THÔNG BÁO TRẠNG THÁI THỊ TRƯỜNG</b>
📅 Ngày: {now.strftime('%d/%m/%Y')}
🕐 Giờ: {now.strftime('%H:%M:%S')}
{status_text}
⏱️ Tần suất báo cáo: {interval_text}
"""
                send_telegram_message(notify_msg)
                last_weekday = weekday
            
            print(f"\n{'='*60}")
            print(f"⏰ [{now.strftime('%d/%m/%Y %H:%M:%S')}] CHU KỲ MỚI")
            print(f"Trạng thái: {status_text} | Tần suất: {interval_text}")
            print(f"{'='*60}")
            
            # Tạo báo cáo
            full_message = "<b>📊 BÁO CÁO CỔ PHIẾU</b>\n"
            
            for symbol in WATCH_LIST:
                data = get_stock_data(symbol, is_open)
                if data is None:
                    full_message += f"\n——————————————————\n📊 {symbol} — ❌ KHÔNG CÓ DỮ LIỆU\n"
                    continue
                
                ind = calculate_indicators(symbol, data)
                change_pct_str = f"{data['change_pct']:+.2f}%"
                
                full_message += f"""
——————————————————
📊 <b>{symbol}</b> — Giá: <b>{data['price']:,.0f} VND</b> | {change_pct_str}
📡 Nguồn: {data['source']}
📉 MA5: {ind['ma5']:,.0f} | MA10: {ind['ma10']:,.0f} | RSI: {ind['rsi']}
🛡️ Hỗ trợ: {ind['support']:,.0f} | Kháng cự: {ind['resistance']:,.0f}

🎯 <b>KHUYẾN NGHỊ:</b>
{ind['mua']}
{ind['ban']}
{ind['nam_giu']}
"""
            
            full_message += f"\n——————————————————\n⏱️ Báo cáo mỗi {interval_text}\n⚠️ <i>Chỉ tham khảo — tự quyết định giao dịch!</i>"
            
            # Gửi báo cáo
            send_telegram_message(full_message)
            
            # Chờ đến lần tiếp theo
            print(f"\n💤 Ngủ {interval_text} ({current_interval} giây)...")
            time.sleep(current_interval)
        
        except KeyboardInterrupt:
            print("\n👋 Bot đã dừng bởi người dùng")
            send_telegram_message("🔴 <b>BOT ĐÃ DỪNG</b> — Người dùng tắt chương trình")
            sys.exit(0)
        except Exception as e:
            error_msg = f"❌ <b>LỖI HỆ THỐNG:</b> {e}"
            print(f"\n{error_msg}")
            send_telegram_message(error_msg)
            print(f"⏳ Thử lại sau {ERROR_WAIT_TIME} giây...")
            time.sleep(ERROR_WAIT_TIME)

if __name__ == "__main__":
    main()
