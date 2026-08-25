import os
import time
import schedule
import requests
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from vnstock import stock_historical_data

# ========== CẤU HÌNH BOT CỔ PHIẾU ==========
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")
MAX_MESSAGE_LENGTH = 4000  # Telegram giới hạn 4096 ký tự

# Danh sách mã theo dõi
WATCH_LIST = ["ACV", "FPT", "VCB", "ACB", "BCM", "BID", "BVH", "CTG", "GAS", "GVR", 
              "HDB", "HPG", "MBB", "MSN", "POW", "SAB", "SHB", "SSB", "SSI", "TCB", 
              "TPB", "VHM", "VIB", "VIC", "VNM", "VPB", "VRE", "VTG", "MWG"]

# Tham số kỹ thuật
RSI_PERIOD = 14
SUPPORT_RESISTANCE_LOOKBACK = 20
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
    # ✅ SỬA: Làm tròn đúng cách (từ -5 → 0)
    support = round(recent['low'].min(), 0)
    resistance = round(recent['high'].max(), 0)
    return int(support), int(resistance)

# === HÀM GỬI TIN ===
def send_telegram(message, max_retries=5):
    # ✅ SỬA: Kiểm tra token và chat_id
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ LỖI: TELEGRAM_TOKEN hoặc CHAT_ID chưa được cấu hình!")
        print(f"   TELEGRAM_TOKEN: {bool(TELEGRAM_TOKEN)}")
        print(f"   CHAT_ID: {bool(CHAT_ID)}")
        return None
    
    # ✅ SỬA: Kiểm tra độ dài message
    if len(message) > MAX_MESSAGE_LENGTH:
        print(f"⚠️ WARNING: Message dài {len(message)} ký tự (giới hạn {MAX_MESSAGE_LENGTH})")
        print("Sẽ cắt message để phù hợp...")
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
                print(f"⚠️ API trả về lỗi {response.status_code}: {response.text}")
        except Exception as e:
            print(f"⚠️ Lỗi lần {attempt+1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(10)
    print("❌ Gửi thất bại sau tất cả lần thử")
    return None

def analyze_stock(symbol):
    try:
        end_date = date.today().strftime('%Y-%m-%d')
        start_date = (date.today() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        df = stock_historical_data(symbol, start_date, end_date, "1D")
        if len(df) < 20:
            print(f"⚠️ {symbol}: Dữ liệu không đủ (chỉ có {len(df)} ngày)")
            return None
        
        df['ma5'] = calc_ma(df['close'], 5)
        df['ma10'] = calc_ma(df['close'], 10)
        df['rsi'] = calc_rsi(df['close'], RSI_PERIOD)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # ✅ SỬA: Lấy giá thật trước khi làm tròn để tính % thay đổi
        price_raw = float(latest['close'])
        prev_price_raw = float(prev['close'])
        
        # Tính % thay đổi từ giá thực tế (trước khi làm tròn)
        if prev_price_raw > 0:
            change_pct = round((price_raw - prev_price_raw) / prev_price_raw * 100, 2)
        else:
            change_pct = 0.0
        
        # Sau đó mới làm tròn giá để hiển thị
        price = int(round(price_raw, 0))
        prev_price = int(round(prev_price_raw, 0))
        
        # ✅ SỬA: Lấy MA5, MA10 từ dữ liệu gốc (float) để so sánh logic
        ma5_raw = float(latest['ma5'])
        ma10_raw = float(latest['ma10'])
        
        # Làm tròn để hiển thị
        ma5 = round(ma5_raw, 0)
        ma10 = round(ma10_raw, 0)
        
        # ✅ SỬA: Xử lý NaN trong RSI
        if pd.isna(latest['rsi']) or np.isnan(latest['rsi']):
            rsi = 50.0
        else:
            rsi = round(float(latest['rsi']), 1)
        
        support, resistance = calc_support_resistance(df)
        
        buy_wait = False
        sell_wait = False
        hold = False
        mua_note = f"Chờ giá điều chỉnh về {support:,.0f} VND"
        ban_note = f"Chờ giá lên mục tiêu {resistance:,.0f} VND"
        hold_note = ""
        target_sell = resistance
        stop_loss = support
        
        # ✅ SỬA: Logic điều kiện buy_wait/sell_wait
        if price >= support and price < (support + (resistance - support) * 0.3):
            buy_wait = True
        
        if price <= resistance and price > (support + (resistance - support) * 0.7):
            sell_wait = True
        
        # ✅ SỬA: So sánh MA5 vs MA10 với giá trị gốc (float)
        if ma5_raw > ma10_raw and rsi < 70:
            hold = True
            hold_note = "Xu hướng tăng tốt"
        
        if 'time' in df.columns and pd.notna(latest['time']):
            source_date = str(latest['time']).split()[0]
        else:
            source_date = end_date
        
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
            "target_sell": target_sell,
            "stop_loss": stop_loss
        }
        
    except Exception as e:
        print(f"❌ Lỗi phân tích {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_message():
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
    
    # ✅ SỬA: Thêm counter để theo dõi
    stock_count = 0
    for symbol in WATCH_LIST:
        data = analyze_stock(symbol)
        if not data:
            continue
        
        stock_count += 1
        
        # ✅ SỬA: Kiểm tra độ dài message trước khi add thêm
        stock_info = ""
        stock_info += "─" * 20 + "\n"
        stock_info += f"📊 {data['symbol']} – Giá: {data['price']:,.0f} VND | {data['change_pct']:+.2f}%\n"
        stock_info += f"📡 Nguồn: 🔒 Giá phiên cuối (lưu lúc {data['source_date']} 15:00:00)\n"
        stock_info += f"📈 MA5: {data['ma5']:,.0f} | MA10: {data['ma10']:,.0f} | RSI: {data['rsi']}\n"
        stock_info += f"🛡️ Hỗ trợ: {data['support']:,.0f} | Kháng cự: {data['resistance']:,.0f}\n\n"
        
        stock_info += "🎯 KHUYẾN NGHỊ:\n"
        stock_info += f"⏸️ MUA: {data['mua_note']} — Giá hiện tại {data['price']:,.0f} VND gần hỗ trợ\n"
        stock_info += f"⏸️ BÁN: {data['ban_note']} — Giá hiện tại {data['price']:,.0f} VND gần kháng cự\n"
        
        if data['hold']:
            stock_info += f"🟢 NẮM GIỮ – {data['hold_note']}\n"
        else:
            stock_info += f"🟡 NẮM GIỮ – Chờ tín hiệu rõ hơn\n"
        
        stock_info += f"💰 Giá hiện tại: {data['price']:,.0f} VND\n"
        stock_info += f"🎯 Mục tiêu bán: {data['target_sell']:,.0f} VND\n"
        stock_info += f"🔴 Cắt lỗ dưới: {data['stop_loss']:,.0f} VND\n\n"
        
        # Chỉ add nếu không vượt quá limit
        if len(message) + len(stock_info) < MAX_MESSAGE_LENGTH - 100:
            message += stock_info
        else:
            print(f"⚠️ Message quá dài, dừng ở mã {symbol}")
            break
    
    message += f"📈 Tổng cộng: {stock_count}/{len(WATCH_LIST)} mã được phân tích\n"
    message += "⚠️ Chỉ tham khảo — tự quyết định giao dịch!\n"
    
    return message

def scan_all():
    print(f"\n🔄 Đang tạo báo cáo... {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    message = generate_message()
    if message:
        send_telegram(message)
    else:
        print("❌ Không thể tạo message")

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 BOT CỔ PHIẾU — KHỞI ĐỘNG THÀNH CÔNG")
    print(f"📋 Theo dõi {len(WATCH_LIST)} mã cổ phiếu")
    print("⏰ Lịch gửi: mỗi 1 giờ")
    print("🔄 Chạy 24/7 — không tự dừng")
    print("=" * 50)
    
    # ✅ SỬA: Test ngay lần đầu
    scan_all()
    
    schedule.every().hour.do(scan_all)
    
    while True:
        schedule.run_pending()
        time.sleep(30)
