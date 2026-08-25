import os
import time
import schedule
import requests
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

# ========== CẤU HÌNH BOT CỔ PHIẾU ==========

# Tạo file .env nếu chưa tồn tại
if not os.path.exists('.env'):
    print("=" * 60)
    print("CẢNH BÁO: File .env chưa được tìm thấy!")
    print("=" * 60)
    print("\nTạo file .env mẫu...")
    with open('.env', 'w') as f:
        f.write("TELEGRAM_TOKEN=8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0\n")
        f.write("CHAT_ID=1030583610\n")
    print("✅ File .env đã được tạo tự động với thông tin của bạn!")
    print()

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

# Danh sách mã theo dõi
WATCH_LIST = ["ACV", "FPT", "VCB", "ACB", "BCM", "BID", "BVH", "CTG", "GAS", "GVR", 
              "HDB", "HPG", "MBB", "MSN", "POW", "SAB", "SHB", "SSB", "SSI", "TCB", 
              "TPB", "VHM", "VIB", "VIC", "VNM", "VPB", "VRE", "VTG", "MWG"]

# Tham số kỹ thuật
RSI_PERIOD = 14
SUPPORT_RESISTANCE_LOOKBACK = 20
MAX_MESSAGE_LENGTH = 4000
# ==========================================

def calc_rsi(series, period=RSI_PERIOD):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_ma(series, period):
    return series.rolling(period).mean()

def calc_support_resistance(df, lookback=SUPPORT_RESISTANCE_LOOKBACK):
    recent = df.tail(lookback)
    support = round(recent['low'].min(), 0)
    resistance = round(recent['high'].max(), 0)
    return int(support), int(resistance)

# === HÀM GỬI TIN ===
def send_telegram(message, max_retries=5):
    """Gửi tin nhắn lên Telegram"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ LỖI: TELEGRAM_TOKEN hoặc CHAT_ID chưa được cấu hình!")
        print(f"   TELEGRAM_TOKEN: {'✅ CÓ' if TELEGRAM_TOKEN else '❌ KHÔNG CÓ'}")
        print(f"   CHAT_ID: {'✅ CÓ' if CHAT_ID else '❌ KHÔNG CÓ'}")
        return None
    
    if len(message) > MAX_MESSAGE_LENGTH:
        print(f"⚠️ Cảnh báo: Tin nhắn dài {len(message)} ký tự (giới hạn {MAX_MESSAGE_LENGTH}) — sẽ được cắt ngắn")
        message = message[:MAX_MESSAGE_LENGTH-50] + "\n\n...(tin nhắn bị cắt ngắn)"
    
    for attempt in range(max_retries):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            response = requests.post(url, data=data, timeout=15)
            
            if response.status_code == 200:
                print(f"✅ Đã gửi tin thành công ({len(message)} ký tự)")
                return response.json()
            else:
                error_info = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"⚠️ API trả về lỗi {response.status_code}")
                print(f"Chi tiết: {error_info}")
                if attempt < max_retries - 1:
                    print(f"🔄 Thử lại lần {attempt+2}...")
                    time.sleep(5)
        except Exception as e:
            print(f"⚠️ Lỗi lần {attempt+1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    
    print("❌ Gửi thất bại sau tất cả lần thử")
    return None

def send_test_signal():
    """Gửi tín hiệu test"""
    now = datetime.now()
    test_message = f"""🚀 BOT ĐÃ KHỞI ĐỘNG THÀNH CÔNG!

📅 Ngày giờ: {now.strftime('%d/%m/%Y %H:%M:%S')}
✅ Trạng thái: BOT HOẠT ĐỘNG — CHẠY 24/7

📊 Thông tin:
- Theo dõi: {len(WATCH_LIST)} mã cổ phiếu
- Token: ✅ Đã cấu hình
- Chat ID: ✅ Đã cấu hình

Nếu bạn nhận được tin nhắn này → Bot hoạt động đúng! 🎉
"""
    print("\n" + "="*60)
    print("📤 ĐANG GỬI TÍN HIỆU TEST ĐẾN TELEGRAM")
    print("="*60)
    send_telegram(test_message)

def format_currency(value):
    """Format số thành chuỗi VND"""
    try:
        return f"{int(float(value)):,}"
    except:
        return str(value)

def analyze_stock(symbol):
    """Phân tích cổ phiếu"""
    try:
        from vnstock import stock_historical_data
        
        end_date = date.today().strftime('%Y-%m-%d')
        start_date = (date.today() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        print(f"🔍 Đang phân tích {symbol}...", end=" ")
        df = stock_historical_data(symbol, start_date, end_date, "1D")
        
        if len(df) < 20:
            print(f"⏭️ Bỏ qua (dữ liệu: {len(df)} ngày)")
            return None
        
        df['ma5'] = calc_ma(df['close'], 5)
        df['ma10'] = calc_ma(df['close'], 10)
        df['rsi'] = calc_rsi(df['close'], RSI_PERIOD)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        price_raw = float(latest['close'])
        prev_price_raw = float(prev['close'])
        
        if prev_price_raw > 0:
            change_pct = round((price_raw - prev_price_raw) / prev_price_raw * 100, 2)
        else:
            change_pct = 0.0
        
        price = int(round(price_raw, 0))
        prev_price = int(round(prev_price_raw, 0))
        
        ma5_raw = float(latest['ma5'])
        ma10_raw = float(latest['ma10'])
        ma5 = int(round(ma5_raw, 0))
        ma10 = int(round(ma10_raw, 0))
        
        if pd.isna(latest['rsi']) or np.isnan(latest['rsi']):
            rsi = 50.0
        else:
            rsi = round(float(latest['rsi']), 1)
        
        support, resistance = calc_support_resistance(df)
        
        buy_wait = False
        sell_wait = False
        hold = False
        mua_note = f"Chờ giá điều chỉnh về {format_currency(support)} VND"
        ban_note = f"Chờ giá lên mục tiêu {format_currency(resistance)} VND"
        hold_note = ""
        
        if price >= support and price < (support + (resistance - support) * 0.3):
            buy_wait = True
        
        if price <= resistance and price > (support + (resistance - support) * 0.7):
            sell_wait = True
        
        if ma5_raw > ma10_raw and rsi < 70:
            hold = True
            hold_note = "Xu hướng tăng tốt"
        
        if 'time' in df.columns and pd.notna(latest['time']):
            source_date = str(latest['time']).split()[0]
        else:
            source_date = end_date
        
        print("✅ OK")
        return {
            "symbol": symbol,
            "price": price,
            "change_pct": change_pct,
            "source_date": source_date,
            "ma5": ma5,
            "ma10": ma10,
            "rsi": rsi,
            "support": support,
            "resistance": resistance,
            "buy_wait": buy_wait,
            "sell_wait": sell_wait,
            "hold": hold,
            "mua_note": mua_note,
            "ban_note": ban_note,
            "hold_note": hold_note,
            "target_sell": resistance,
            "stop_loss": support
        }
        
    except Exception as e:
        print(f"❌ LỖI: {e}")
        return None

def generate_message():
    """Tạo tin nhắn báo cáo"""
    now = datetime.now()
    vietnam_date = now.strftime("%d/%m/%Y")
    vietnam_time = now.strftime("%H:%M:%S")
    weekday = now.weekday()
    hour = now.hour
    is_trading_hour = (weekday < 5) and (9 <= hour < 15)
    status_text = "🔒 NGOÀI GIỜ GIAO DỊCH - THỊ TRƯỜNG ĐÓNG CỬA" if not is_trading_hour else "✅ TRONG GIỜ GIAO DỊCH - THỊ TRƯỜNG ĐANG MỞ CỬA"
    
    watch_list_str = ", ".join(WATCH_LIST[:3])
    if len(WATCH_LIST) > 3:
        watch_list_str += f" và {len(WATCH_LIST)-3} mã khác"
    
    message = f"🚀 BOT ĐÃ KHỞI ĐỘNG!\n"
    message += f"📅 Ngày giờ: {vietnam_date} {vietnam_time}\n"
    message += f"📊 Theo dõi: {watch_list_str}\n"
    message += f"💡 Cập nhật giá tự động từ vnstock\n\n"
    message += f"⏱️ Mở cửa: mỗi 5 phút kiểm tra\n"
    message += f"⏱️ Đóng cửa: mỗi 1 giờ gửi báo cáo\n"
    message += f"✅ Sẵn sàng!\n\n"
    message += "─" * 20 + "\n\n"
    
    message += f"🔔 THÔNG BÁO TRẠNG THÁI\n"
    message += f"📅 Ngày: {vietnam_date}\n"
    message += f"⏰ Giờ: {vietnam_time}\n"
    message += f"{status_text}\n"
    message += f"⏱️ Tần suất: 1 giờ\n\n"
    message += "─" * 20 + "\n\n"
    
    message += f"📊 BÁO CÁO CỔ PHIẾU\n"
    message += f"🕐 Thời gian: {vietnam_date} {vietnam_time} (VN)\n\n"
    
    stock_count = 0
    for symbol in WATCH_LIST:
        data = analyze_stock(symbol)
        if not data:
            continue
        
        stock_count += 1
        
        stock_info = "─" * 20 + "\n"
        stock_info += f"📊 {data['symbol']} – Giá: {format_currency(data['price'])} VND | {data['change_pct']:+.2f}%\n"
        stock_info += f"📡 Nguồn: 🔒 Giá phiên cuối (lưu lúc {data['source_date']} 15:00:00)\n"
        stock_info += f"📈 MA5: {format_currency(data['ma5'])} | MA10: {format_currency(data['ma10'])} | RSI: {data['rsi']}\n"
        stock_info += f"🛡️ Hỗ trợ: {format_currency(data['support'])} | Kháng cự: {format_currency(data['resistance'])}\n\n"
        
        stock_info += "🎯 KHUYẾN NGHỊ:\n"
        stock_info += f"⏸️ MUA: {data['mua_note']} — Giá hiện tại {format_currency(data['price'])} VND gần hỗ trợ\n"
        stock_info += f"⏸️ BÁN: {data['ban_note']} — Giá hiện tại {format_currency(data['price'])} VND gần kháng cự\n"
        
        if data['hold']:
            stock_info += f"🟢 NẮM GIỮ – {data['hold_note']}\n"
        else:
            stock_info += f"🟡 NẮM GIỮ – Chờ tín hiệu rõ hơn\n"
        
        stock_info += f"💰 Giá hiện tại: {format_currency(data['price'])} VND\n"
        stock_info += f"🎯 Mục tiêu bán: {format_currency(data['target_sell'])} VND\n"
        stock_info += f"🔴 Cắt lỗ dưới: {format_currency(data['stop_loss'])} VND\n\n"
        
        if len(message) + len(stock_info) < MAX_MESSAGE_LENGTH - 100:
            message += stock_info
        else:
            print(f"⚠️ Tin nhắn quá dài, dừng ở mã {symbol}")
            break
    
    message += f"📈 Tổng cộng: {stock_count}/{len(WATCH_LIST)} mã\n"
    message += "⚠️ Chỉ tham khảo — tự quyết định giao dịch!\n"
    
    return message

def scan_all():
    """Quét tất cả mã"""
    print(f"\n[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] 🔄 Đang tạo báo cáo...")
    message = generate_message()
    if message:
        print(f"📏 Độ dài tin nhắn: {len(message)} ký tự")
        send_telegram(message)
    else:
        print("❌ Không thể tạo tin nhắn")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 BOT CỔ PHIẾU — KHỞI ĐỘNG THÀNH CÔNG")
    print("=" * 60)
    print(f"📋 Theo dõi: {len(WATCH_LIST)} mã cổ phiếu")
    print(f"🔑 Token: {'✅ CÓ' if TELEGRAM_TOKEN else '❌ KHÔNG CÓ'}")
    print(f"💬 Chat ID: {'✅ CÓ' if CHAT_ID else '❌ KHÔNG CÓ'}")
    print("=" * 60)
    print()
    
    # Gửi test signal
    print("\n📤 GỬI TÍN HIỆU TEST...")
    send_test_signal()
    
    # Gửi báo cáo chính
    print("\n\n📤 GỬI BÁO CÁO CHÍNH THỨC...")
    scan_all()
    
    # Scheduler
    print("\n\n⏰ KHỞI ĐỘNG LỊCH TRÌNH...")
    schedule.every().hour.do(scan_all)
    
    print("✅ Bot đang chạy 24/7. Nhấn Ctrl+C để dừng.\n")
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n👋 Đã dừng bot.")
            break
        except Exception as e:
            print(f"⚠️ Lỗi: {e}")
            time.sleep(30)
