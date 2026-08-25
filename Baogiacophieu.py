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
    print("CANH BAO: File .env chua duoc tim thay!")
    print("=" * 60)
    print("\nTao file .env mau...")
    with open('.env', 'w') as f:
        f.write("TELEGRAM_TOKEN=your_bot_token_here\n")
        f.write("CHAT_ID=your_chat_id_here\n")
    print("OK: File .env da duoc tao")
    print("Vui long cap nhat TELEGRAM_TOKEN va CHAT_ID trong file .env")
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
        print("LỖI: TELEGRAM_TOKEN hoặc CHAT_ID chưa được cấu hình!")
        print(f"   TELEGRAM_TOKEN: {'CO' if TELEGRAM_TOKEN else 'KHONG CO'}")
        print(f"   CHAT_ID: {'CO' if CHAT_ID else 'KHONG CO'}")
        print("\nVui lòng sửa file .env:")
        print(f"   File .env: {os.path.abspath('.env')}")
        return None
    
    if len(message) > MAX_MESSAGE_LENGTH:
        print(f"WARNING: Message dai {len(message)} ky tu (gioi han {MAX_MESSAGE_LENGTH})")
        message = message[:MAX_MESSAGE_LENGTH-50] + "\n\n...(tin nhan bi cat ngan)"
    
    for attempt in range(max_retries):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": message,
            }
            response = requests.post(url, data=data, timeout=15)
            
            if response.status_code == 200:
                print(f"OK: Da gui tin thanh cong ({len(message)} ky tu)")
                return response.json()
            else:
                error_info = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                print(f"WARNING: API tra ve loi {response.status_code}")
                print(f"Chi tiet: {error_info}")
                if attempt < max_retries - 1:
                    print(f"Retry lan {attempt+2}...")
                    time.sleep(5)
        except Exception as e:
            print(f"WARNING: Loi lan {attempt+1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    
    print("FAILED: Gui that bai sau tat ca lan thu")
    return None

def send_test_signal():
    """Gửi tín hiệu test"""
    now = datetime.now()
    test_message = f"""TEST SIGNAL - BOT DANG HOAT DONG

Thoi gian: {now.strftime('%d/%m/%Y %H:%M:%S')}
Status: BOT KICH HOAT - DANG CHAY 24/7

Thong tin:
- Theo doi: {len(WATCH_LIST)} ma co phieu
- Token co: {'CO' if TELEGRAM_TOKEN else 'KHONG CO'}
- Chat ID co: {'CO' if CHAT_ID else 'KHONG CO'}

Neu nhan duoc tin nhan nay, Bot da hoat dong dung!!!
"""
    print("\n" + "="*60)
    print("SENDING TEST SIGNAL TO TELEGRAM")
    print("="*60)
    print(f"Chat ID: {CHAT_ID}")
    print(f"Message: {test_message[:100]}...")
    print()
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
        
        print(f"Analyzing {symbol}...", end=" ")
        df = stock_historical_data(symbol, start_date, end_date, "1D")
        
        if len(df) < 20:
            print(f"Skip (data: {len(df)} days)")
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
        mua_note = f"Cho gia dieu chinh ve {format_currency(support)} VND"
        ban_note = f"Cho gia len muc tieu {format_currency(resistance)} VND"
        hold_note = ""
        
        if price >= support and price < (support + (resistance - support) * 0.3):
            buy_wait = True
        
        if price <= resistance and price > (support + (resistance - support) * 0.7):
            sell_wait = True
        
        if ma5_raw > ma10_raw and rsi < 70:
            hold = True
            hold_note = "Xu huong tang tot"
        
        if 'time' in df.columns and pd.notna(latest['time']):
            source_date = str(latest['time']).split()[0]
        else:
            source_date = end_date
        
        print("OK")
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
        print(f"FAILED: {e}")
        return None

def generate_message():
    """Tạo tin nhắn báo cáo"""
    now = datetime.now()
    vietnam_date = now.strftime("%d/%m/%Y")
    vietnam_time = now.strftime("%H:%M:%S")
    weekday = now.weekday()
    hour = now.hour
    is_trading_hour = (weekday < 5) and (9 <= hour < 15)
    status_text = "NGOAI GIO GIAO DICH" if not is_trading_hour else "TRONG GIO GIAO DICH"
    
    watch_list_str = ", ".join(WATCH_LIST[:3])
    if len(WATCH_LIST) > 3:
        watch_list_str += f" va {len(WATCH_LIST)-3} ma khac"
    
    message = "BOT DA KHOI DONG!\n"
    message += f"Ngay gio: {vietnam_date} {vietnam_time}\n"
    message += f"Theo doi: {watch_list_str}\n"
    message += f"Cap nhat gia tu dong\n\n"
    message += "Mo cua: moi 5 phut kiem tra\n"
    message += "Dong cua: moi 1 gio gui bao cao\n"
    message += "San sang!\n\n"
    message += "=" * 30 + "\n\n"
    
    message += "THONG BAO TRANG THAI\n"
    message += f"Ngay: {vietnam_date}\n"
    message += f"Gio: {vietnam_time}\n"
    message += f"Status: {status_text}\n"
    message += "Tan suat: 1 gio\n\n"
    message += "=" * 30 + "\n\n"
    
    message += "BAO CAO CO PHIEU\n"
    message += f"Thoi gian: {vietnam_date} {vietnam_time}\n\n"
    
    stock_count = 0
    for symbol in WATCH_LIST:
        data = analyze_stock(symbol)
        if not data:
            continue
        
        stock_count += 1
        
        stock_info = ""
        stock_info += "=" * 30 + "\n"
        stock_info += f"{data['symbol']} - Gia: {format_currency(data['price'])} VND | {data['change_pct']:+.2f}%\n"
        stock_info += f"Nguon: Gia phien cuoi ({data['source_date']})\n"
        stock_info += f"MA5: {format_currency(data['ma5'])} | MA10: {format_currency(data['ma10'])} | RSI: {data['rsi']}\n"
        stock_info += f"Ho tro: {format_currency(data['support'])} | Khang cu: {format_currency(data['resistance'])}\n\n"
        
        stock_info += "KHUYEN NGHI:\n"
        stock_info += f"MUA: {data['mua_note']}\n"
        stock_info += f"BAN: {data['ban_note']}\n"
        
        if data['hold']:
            stock_info += f"NAM GIU - {data['hold_note']}\n"
        else:
            stock_info += "NAM GIU - Cho tin hieu\n"
        
        stock_info += f"Gia: {format_currency(data['price'])} VND\n"
        stock_info += f"Target: {format_currency(data['target_sell'])} VND\n"
        stock_info += f"Stop loss: {format_currency(data['stop_loss'])} VND\n\n"
        
        if len(message) + len(stock_info) < MAX_MESSAGE_LENGTH - 100:
            message += stock_info
        else:
            print(f"WARNING: Message qua dai, dung o ma {symbol}")
            break
    
    message += f"Tong cong: {stock_count}/{len(WATCH_LIST)} ma\n"
    message += "Chu y: Chi tham khao - tu quyet dinh!\n"
    
    return message

def scan_all():
    """Quét tất cả mã"""
    print(f"\n[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Dang tao bao cao...")
    message = generate_message()
    if message:
        print(f"Message length: {len(message)} ky tu")
        send_telegram(message)
    else:
        print("Khong the tao message")

if __name__ == "__main__":
    print("=" * 60)
    print("BOT CO PHIEU - KHOI DONG THANH CONG")
    print("=" * 60)
    print(f"Theo doi: {len(WATCH_LIST)} ma co phieu")
    print(f"Token: {'CO' if TELEGRAM_TOKEN else <<<ERROR>>>'KHONG CO'}")
    print(f"Chat ID: {'CO' if CHAT_ID else 'KHONG CO'}")
    print(f"File .env: {os.path.abspath('.env')}")
    print("=" * 60)
    print()
    
    # Gửi test signal
    print("\nGUI TEST SIGNAL...")
    send_test_signal()
    
    # Gửi báo cáo chính
    print("\n\nGUI BAO CAO CHINH THUC...")
    scan_all()
    
    # Scheduler
    print("\n\nKhoi dong scheduler...")
    schedule.every().hour.do(scan_all)
    
    print("Bot dang chay. Nhan Ctrl+C de dung.\n")
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)
        except KeyboardInterrupt:
            print("\nDung bot.")
            break
        except Exception as e:
            print(f"Loi: {e}")
            time.sleep(30)
