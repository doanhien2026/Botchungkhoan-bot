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

CP_TELEGRAM_TOKEN = os.getenv("CP_TELEGRAM_TOKEN", "")
CP_CHAT_ID = os.getenv("CP_CHAT_ID", "")

# Danh sách mã cần theo dõi
WATCH_LIST = ["ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
              "MBB", "MSN", "NVL", "POW", "SAB", "SHB", "SSB", "SSI", "TCB", "TPB",
              "VCB", "VHM", "VIB", "VIC", "VNM", "VPB", "VRE", "VTG", "MWG", "ACV"]

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
    support = round(recent['low'].min(), -5)
    resistance = round(recent['high'].max(), -5)
    return int(support), int(resistance)

# === HÀM GỬI TIN RIÊNG CHO BOT CỔ PHIẾU ===
def send_cophieu(message, max_retries=5):
    for attempt in range(max_retries):
        try:
            url = f"https://api.telegram.org/bot{CP_TELEGRAM_TOKEN}/sendMessage"
            data = {
                "chat_id": CP_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            response = requests.post(url, data=data, timeout=15)
            if response.status_code == 200:
                print(f"✅ [BOT CỔ PHIẾU] Đã gửi tin thành công")
                return response.json()
        except Exception as e:
            print(f"⚠️ [BOT CỔ PHIẾU] Lỗi lần {attempt+1}: {e}")
            time.sleep(10)
    print("❌ [BOT CỔ PHIẾU] Gửi thất bại")
    return None

def analyze_stock(symbol):
    try:
        end_date = date.today().strftime('%Y-%m-%d')
        start_date = (date.today() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        df = stock_historical_data(symbol, start_date, end_date, "1D")
        if len(df) < 20:
            return None
        
        df['ma5'] = calc_ma(df['close'], 5)
        df['ma10'] = calc_ma(df['close'], 10)
        df['rsi'] = calc_rsi(df['close'], RSI_PERIOD)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        price = int(round(latest['close'], -5))
        prev_price = int(round(prev['close'], -5))
        change_pct = round((price - prev_price) / prev_price * 100, 2) if prev_price > 0 else 0
        
        ma5 = int(round(latest['ma5'], -5))
        ma10 = int(round(latest['ma10'], -5))
        rsi = round(latest['rsi'], 1) if not np.isnan(latest['rsi']) else 50.0
        
        support, resistance = calc_support_resistance(df)
        
        buy_wait = False
        sell_wait = False
        hold = False
        mua_note = ""
        ban_note = ""
        hold_note = ""
        target_sell = resistance
        stop_loss = support
        
        if price >= support and price < (support + (resistance - support) * 0.3):
            buy_wait = True
            mua_note = f"Chờ giá điều chỉnh về {support:,} VND — Giá hiện tại {price:,} VND gần hỗ trợ"
        else:
            mua_note = f"Chờ giá điều chỉnh về vùng hỗ trợ {support:,} VND"
        
        if price <= resistance and price > (support + (resistance - support) * 0.7):
            sell_wait = True
            ban_note = f"Chờ giá lên mục tiêu {resistance:,} VND — Giá hiện tại {price:,} VND gần kháng cự"
        else:
            ban_note = f"Chờ giá lên mục tiêu {resistance:,} VND"
        
        if ma5 > ma10 and rsi < 70:
            hold = True
            hold_note = "Xu hướng tăng tốt"
        elif ma5 < ma10 and rsi > 30:
            hold = False
        
        source_date = df.iloc[-1]['time'].split()[0] if 'time' in df.columns else end_date
        
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
        print(f"❌ [BOT CỔ PHIẾU] Lỗi phân tích {symbol}: {e}")
        return None

def generate_message():
    now = datetime.now()
    vietnam_time = now.strftime("%d/%m/%Y %H:%M:%S")
    weekday = now.weekday()
    hour = now.hour
    is_trading_hour = (weekday < 5) and (9 <= hour < 15)
    status_text = "✅ TRONG GIỜ GIAO DỊCH - THỊ TRƯỜNG ĐANG MỞ CỬA" if is_trading_hour else "🔒 NGOÀI GIỜ GIAO DỊCH - THỊ TRƯỜNG ĐÓNG CỬA"
    
    message = f"🔔 THÔNG BÁO TRẠNG THÁI CỔ PHIẾU\n"
    message += f"Ngày giờ: {vietnam_time}\n"
    message += f"{status_text}\n\n"
    message += "⚠️ Cảnh báo: Chỉ tham khảo — tự quyết định giao dịch!\n"
    message += "─" * 30 + "\n\n"
    
    for symbol in WATCH_LIST:
        data = analyze_stock(symbol)
        if not data:
            continue
        
        message += f"📊 {data['symbol']} – Giá: {data['price']:,} VND | Thay đổi: {data['change_pct']:+.2f}%\n"
        message += f"📡 Nguồn: 🔒 Giá phiên cuối (lưu lúc {data['source_date']} 15:00:00)\n"
        message += f"📈 MA5: {data['ma5']:,} | MA10: {data['ma10']:,} | RSI: {data['rsi']}\n"
        message += f"🛡️ Hỗ trợ: {data['support']:,} | Kháng cự: {data['resistance']:,}\n\n"
        
        buy_icon = "🟡" if data['buy_wait'] else "⚪"
        sell_icon = "🟡" if data['sell_wait'] else "⚪"
        message += f"📊 TÍN HIỆU: {buy_icon} TÍN HIỆU MUA CHỜ | {sell_icon} TÍN HIỆU BÁN CHỜ\n"
        
        message += "🎯 KHUYẾN NGHỊ:\n"
        message += f"⏸️ MUA: {data['mua_note']}\n"
        message += f"⏸️ BÁN: {data['ban_note']}\n"
        
        if data['hold']:
            message += f"🟢 NẮM GIỮ – {data['hold_note']}\n"
            message += f"💰 Giá hiện tại: {data['price']:,} VND\n"
        
        message += f"🎯 Mục tiêu bán: {data['target_sell']:,} VND\n"
        message += f"🔴 Cắt lỗ dưới: {data['stop_loss']:,} VND\n"
        message += "─" * 30 + "\n\n"
    
    return message

def scan_all():
    print(f"\n🔄 [BOT CỔ PHIẾU] Đang tạo báo cáo... {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    message = generate_message()
    send_cophieu(message)

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 BOT CỔ PHIẾU — KHỞI ĐỘNG THÀNH CÔNG")
    print(f"📋 Theo dõi {len(WATCH_LIST)} mã cổ phiếu")
    print("⏰ Lịch gửi: 09:15, 11:30, 14:30, 15:30 hàng ngày")
    print("🔄 Chạy 24/7 — không tự dừng")
    print("=" * 50)
    
    scan_all()
    
    schedule.every().day.at("09:15").do(scan_all)
    schedule.every().day.at("11:30").do(scan_all)
    schedule.every().day.at("14:30").do(scan_all)
    schedule.every().day.at("15:30").do(scan_all)
    
    while True:
        schedule.run_pending()
        time.sleep(30)
