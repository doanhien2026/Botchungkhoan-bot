import os
import time
import re
import schedule
import requests
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta, timezone
from bs4 import BeautifulSoup

# ========== CẤU HÌNH MÚI GIỜ VIỆT NAM ==========
VN_TZ = timezone(timedelta(hours=7), 'Asia/Ho_Chi_Minh')

def get_vietnam_time():
    """Lấy thời gian hiện tại theo Giờ Việt Nam (UTC+7)"""
    return datetime.now(VN_TZ)
# ==============================================

# ========== CẤU HÌNH BOT CỔ PHIẾU ==========
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0")
CHAT_ID = os.getenv("CHAT_ID", "1030583610")

# Danh sách mã theo dõi
WATCH_LIST = ["ACV", "FPT", "VCB", "ACB", "BCM", "BID", "BVH", "CTG", "GAS", "GVR", 
              "HDB", "HPG", "MBB", "MSN", "POW", "SAB", "SHB", "SSB", "SSI", "TCB", 
              "TPB", "VHM", "VIB", "VIC", "VNM", "VPB", "VRE", "VTG", "MWG"]

# Tham số kỹ thuật
RSI_PERIOD = 14
SUPPORT_RESISTANCE_LOOKBACK = 20
MAX_MESSAGE_LENGTH = 4000
REQUEST_TIMEOUT = 15
UPDATE_INTERVAL_MINUTES = 5  # === CẤU HÌNH: Cập nhật mỗi 5 phút ===
# ==========================================

# ========== HÀM LẤY DỮ LIỆU TỪ NGUỒN ONLINE ==========

def fetch_price_cafef(symbol):
    """Lấy giá hiện tại từ Cafef"""
    try:
        url = f"https://cafef.vn/du-lieu/{symbol}.chn"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return None, "Cafef", None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        price_tag = soup.find("span", class_="price") or soup.find("strong", class_=re.compile("price|green|red"))
        if not price_tag:
            text = response.text
            price_match = re.search(rf'{symbol}.*?(\d+\.\d+|\d+,\d+|\d+)\s*VND', text)
            if price_match:
                price_str = price_match.group(1).replace(',', '')
                price = float(price_str)
            else:
                return None, "Cafef", None
        else:
            price_str = re.sub(r'[^\d.]', '', price_tag.text.replace(',', '.'))
            if not price_str:
                return None, "Cafef", None
            price = float(price_str)
        
        return price, "Cafef", get_vietnam_time().strftime('%d/%m/%Y %H:%M')
    except Exception as e:
        print(f"⚠️ Lỗi Cafef {symbol}: {e}")
        return None, "Cafef", None

def fetch_price_vietstock(symbol):
    """Lấy giá từ Vietstock"""
    try:
        url = f"https://vietstock.vn/chart/{symbol}.htm"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return None, "Vietstock", None
        
        text = response.text
        patterns = [
            rf'"price"\s*:\s*(\d+\.?\d*)',
            rf'{symbol}.*?Giá tham chiếu.*?(\d+,\d+|\d+\.\d+)',
            rf'Giá.*?(\d{{1,3}}(?:\.\d{{3}})*|\d+)\s*VND'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace('.', '').replace(',', '.')
                price = float(price_str)
                return price, "Vietstock", get_vietnam_time().strftime('%d/%m/%Y %H:%M')
        
        return None, "Vietstock", None
    except Exception as e:
        print(f"⚠️ Lỗi Vietstock {symbol}: {e}")
        return None, "Vietstock", None

def fetch_price_tcbs(symbol):
    """Lấy giá từ TCBS API"""
    try:
        url = f"https://apipubaws.tcbs.com.vn/tcanalysis/v1/ticker/{symbol}/quote"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://tcbs.com.vn",
            "Referer": "https://tcbs.com.vn/"
        }
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            if 'lastPrice' in data:
                price = float(data['lastPrice'])
                return price, "TCBS", get_vietnam_time().strftime('%d/%m/%Y %H:%M')
        
        return None, "TCBS", None
    except Exception as e:
        print(f"⚠️ Lỗi TCBS {symbol}: {e}")
        return None, "TCBS", None

def fetch_historical_data(symbol, days=90):
    """Lấy dữ liệu lịch sử giá từ TCBS API"""
    try:
        end_date = get_vietnam_time()
        start_date = end_date - timedelta(days=days)
        
        url = f"https://apipubaws.tcbs.com.vn/tcanalysis/v1/stock-price/{symbol}?from={int(start_date.timestamp())}&to={int(end_date.timestamp())}&resolution=1D"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://tcbs.com.vn",
            "Referer": "https://tcbs.com.vn/"
        }
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        if not data or 'data' not in data:
            return None
        
        records = []
        for item in data['data']:
            records.append({
                'date': datetime.fromtimestamp(item['t'], tz=VN_TZ).strftime('%Y-%m-%d'),
                'open': float(item['o']),
                'high': float(item['h']),
                'low': float(item['l']),
                'close': float(item['c']),
                'volume': float(item['v'])
            })
        
        df = pd.DataFrame(records)
        if len(df) >= 20:
            return df.sort_values('date').reset_index(drop=True)
        
        return None
    except Exception as e:
        print(f"⚠️ Lỗi lấy dữ liệu lịch sử {symbol}: {e}")
        return None

def get_best_price(symbol):
    """Lấy giá từ nhiều nguồn, chọn nguồn hợp lệ nhất"""
    sources = [
        fetch_price_tcbs,
        fetch_price_cafef,
        fetch_price_vietstock
    ]
    
    results = []
    for source_func in sources:
        price, source_name, time_str = source_func(symbol)
        if price and price > 0:
            results.append({
                'price': price,
                'source': source_name,
                'time': time_str
            })
            print(f"  ✅ {source_name}: {price:,.0f} VND")
    
    if not results:
        return None, "Không có nguồn", None
    
    if len(results) >= 2:
        avg_price = np.mean([r['price'] for r in results])
        main_source = f"Đã tổng hợp ({len(results)} nguồn)"
        return round(avg_price, 2), main_source, results[0]['time']
    
    return results[0]['price'], results[0]['source'], results[0]['time']

# ========== HÀM TÍN HIỆU KỸ THUẬT ==========

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
    support = round(recent['low'].min(), -2)
    resistance = round(recent['high'].max(), -2)
    return int(support), int(resistance)

def analyze_trend(df, price, ma5, ma10, rsi):
    """Phân tích xu hướng & tạo tín hiệu MUA/BÁN/NẮM GIỮ"""
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else None
    
    buy_signal = False
    sell_signal = False
    hold_signal = False
    signal_strength = "Yếu"
    
    conditions_buy = [
        ma5 > ma10,
        rsi < 30,
        price <= round(latest['low'], -2) * 1.01
    ]
    
    conditions_sell = [
        ma5 < ma10,
        rsi > 70,
        price >= round(latest['high'], -2) * 0.99
    ]
    
    buy_count = sum(conditions_buy)
    sell_count = sum(conditions_sell)
    
    if buy_count >= 2:
        buy_signal = True
        signal_strength = "Mạnh" if buy_count == 3 else "Trung bình"
    elif sell_count >= 2:
        sell_signal = True
        signal_strength = "Mạnh" if sell_count == 3 else "Trung bình"
    else:
        hold_signal = True
        signal_strength = "Chờ tín hiệu"
    
    return {
        'buy': buy_signal,
        'sell': sell_signal,
        'hold': hold_signal,
        'strength': signal_strength,
        'buy_conditions': buy_count,
        'sell_conditions': sell_count
    }

# ========== HÀM GỬI TIN TELEGRAM ==========

def send_telegram(message, max_retries=5):
    """Gửi tin nhắn lên Telegram"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ LỖI: TELEGRAM_TOKEN hoặc CHAT_ID chưa được cấu hình!")
        return None
    
    if len(message) > MAX_MESSAGE_LENGTH:
        print(f"⚠️ Cảnh báo: Tin nhắn dài {len(message)} ký tự — sẽ được cắt ngắn")
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
            response = requests.post(url, data=data, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                print(f"✅ Đã gửi tin thành công ({len(message)} ký tự)")
                return response.json()
            else:
                error_info = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"⚠️ API lỗi {response.status_code}: {error_info}")
                time.sleep(5)
        except Exception as e:
            print(f"⚠️ Lỗi lần {attempt+1}: {e}")
            time.sleep(5)
    
    print("❌ Gửi thất bại")
    return None

def send_test_signal():
    """Gửi tín hiệu kiểm tra kết nối"""
    now = get_vietnam_time()
    test_message = f"""🚀 BOT CỔ PHIẾU — KHỞI ĐỘNG THÀNH CÔNG!

📅 Ngày giờ: {now.strftime('%d/%m/%Y %H:%M:%S')}
✅ Trạng thái: Đang hoạt động — CẬP NHẬT MỖI {UPDATE_INTERVAL_MINUTES} PHÚT

📊 Thông tin:
- Theo dõi: {len(WATCH_LIST)} mã cổ phiếu
- Nguồn dữ liệu: TCBS API, Cafef, Vietstock
- Tần suất: Mỗi {UPDATE_INTERVAL_MINUTES} phút gửi báo cáo mới
- Token: ✅ Đã cấu hình
- Chat ID: ✅ Đã cấu hình

Nếu nhận được tin này → Bot hoạt động đúng! 🎉
"""
    print("\n" + "="*60)
    print("📤 GỬI TÍN HIỆU TEST...")
    print("="*60)
    send_telegram(test_message)

def format_currency(value):
    """Format số thành tiền VND"""
    try:
        return f"{int(float(value)):,}"
    except:
        return str(value)

# ========== PHÂN TÍCH TỪNG CỔ PHIẾU ==========

def analyze_stock(symbol):
    """Phân tích đầy đủ 1 mã cổ phiếu từ nguồn dữ liệu thực tế"""
    try:
        print(f"\n🔍 Đang phân tích {symbol}...")
        
        price_raw, source_name, source_time = get_best_price(symbol)
        if not price_raw:
            print(f"❌ Không lấy được giá {symbol}")
            return None
        
        price = round(price_raw, 2)
        
        df = fetch_historical_data(symbol, days=90)
        if df is None or len(df) < 20:
            print(f"⚠️ Không đủ dữ liệu lịch sử {symbol} — chỉ hiển thị giá hiện tại")
            return {
                "symbol": symbol,
                "price": int(round(price, 0)),
                "change_pct": 0.0,
                "source": source_name,
                "source_time": source_time,
                "ma5": 0,
                "ma10": 0,
                "rsi": 50.0,
                "support": 0,
                "resistance": 0,
                "signal": "wait",
                "signal_text": "Chờ dữ liệu",
                "strength": "Không đủ dữ liệu",
                "target_sell": 0,
                "stop_loss": 0
            }
        
        df['ma5'] = calc_ma(df['close'], 5)
        df['ma10'] = calc_ma(df['close'], 10)
        df['rsi'] = calc_rsi(df['close'], RSI_PERIOD)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        prev_price = float(prev['close'])
        change_pct = round((price - prev_price) / prev_price * 100, 2) if prev_price > 0 else 0.0
        
        ma5 = int(round(float(latest['ma5']), 0)) if pd.notna(latest['ma5']) else 0
        ma10 = int(round(float(latest['ma10']), 0)) if pd.notna(latest['ma10']) else 0
        rsi = round(float(latest['rsi']), 1) if pd.notna(latest['rsi']) and not np.isnan(latest['rsi']) else 50.0
        
        support, resistance = calc_support_resistance(df)
        trend = analyze_trend(df, price, ma5, ma10, rsi)
        
        if trend['buy']:
            signal_text = "🟢 MUA"
            target_sell = resistance
            stop_loss = support
        elif trend['sell']:
            signal_text = "🔴 BÁN"
            target_sell = support
            stop_loss = resistance
        else:
            signal_text = "🟡 NẮM GIỮ"
            target_sell = resistance
            stop_loss = support
        
        print(f"✅ {symbol} | Giá: {format_currency(price)} | RSI: {rsi} | Tín hiệu: {signal_text}")
        
        return {
            "symbol": symbol,
            "price": int(round(price, 0)),
            "change_pct": change_pct,
            "source": source_name,
            "source_time": source_time,
            "ma5": ma5,
            "ma10": ma10,
            "rsi": rsi,
            "support": support,
            "resistance": resistance,
            "signal": signal_text,
            "strength": trend['strength'],
            "target_sell": target_sell,
            "stop_loss": stop_loss
        }
        
    except Exception as e:
        print(f"❌ Lỗi phân tích {symbol}: {e}")
        return None

# ========== TẠO BÁO CÁO ==========

def generate_message():
    """Tạo tin nhắn báo cáo — Đã bỏ phần trạng thái thừa"""
    now = get_vietnam_time()
    vietnam_date = now.strftime("%d/%m/%Y")
    vietnam_time = now.strftime("%H:%M:%S")
    
    watch_list_str = ", ".join(WATCH_LIST[:3])
    if len(WATCH_LIST) > 3:
        watch_list_str += f" và {len(WATCH_LIST)-3} mã khác"
    
    message = f"🚀 BÁO CÁO CỔ PHIẾU — CẬP NHẬT MỖI {UPDATE_INTERVAL_MINUTES} PHÚT\n"
    message += f"📅 Ngày giờ: {vietnam_date} {vietnam_time}\n"
    message += f"📊 Theo dõi: {watch_list_str}\n"
    message += f"💡 Nguồn: TCBS API, Cafef, Vietstock\n\n"
    message += f"⏱️ Tần suất: Mỗi {UPDATE_INTERVAL_MINUTES} phút tự động cập nhật\n"
    message += f"✅ Sẵn sàng!\n\n"
    message += "─" * 20 + "\n\n"
    
    message += f"📊 BÁO CÁO TÍN HIỆU\n"
    message += f"🕐 Thời gian: {vietnam_date} {vietnam_time} (VN)\n\n"
    
    stock_count = 0
    buy_count = 0
    sell_count = 0
    hold_count = 0
    
    # Ưu tiên hiển thị 3 mã chính trước
    priority_symbols = ["ACV", "FPT", "VCB"]
    other_symbols = [s for s in WATCH_LIST if s not in priority_symbols]
    ordered_list = priority_symbols + other_symbols
    
    for symbol in ordered_list:
        data = analyze_stock(symbol)
        if not data:
            continue
        
        stock_count += 1
        
        if "MUA" in data['signal']:
            buy_count += 1
        elif "BÁN" in data['signal']:
            sell_count += 1
        else:
            hold_count += 1
        
        stock_info = "─" * 20 + "\n"
        stock_info += f"📊 {data['symbol']} – Giá: {format_currency(data['price'])} VND | {data['change_pct']:+.2f}%\n"
        stock_info += f"📡 Nguồn: {data['source']} – {data['source_time']}\n"
        
        if data['ma5'] > 0 and data['ma10'] > 0:
            stock_info += f"📈 MA5: {format_currency(data['ma5'])} | MA10: {format_currency(data['ma10'])} | RSI: {data['rsi']}\n"
            stock_info += f"🛡️ Hỗ trợ: {format_currency(data['support'])} | Kháng cự: {format_currency(data['resistance'])}\n\n"
        else:
            stock_info += f"📈 Dữ liệu lịch sử chưa đủ — chỉ hiển thị giá hiện tại\n\n"
        
        stock_info += f"🎯 TÍN HIỆU: {data['signal']} ({data['strength']})\n"
        
        if data['ma5'] > 0:
            stock_info += f"💰 Giá hiện tại: {format_currency(data['price'])} VND\n"
            stock_info += f"🎯 Mục tiêu bán: {format_currency(data['target_sell'])} VND\n"
            stock_info += f"🔴 Cắt lỗ dưới: {format_currency(data['stop_loss'])} VND\n"
        
        stock_info += "\n"
        
        if len(message) + len(stock_info) < MAX_MESSAGE_LENGTH - 100:
            message += stock_info
        else:
            print(f"⚠️ Tin nhắn quá dài, dừng ở mã {symbol}")
            message += "\n⚠️ Tin nhắn bị giới hạn độ dài — vui lòng xem các báo cáo tiếp theo!\n"
            break
    
    message += "─" * 20 + "\n"
    message += f"📈 TỔNG CỘNG: {stock_count}/{len(WATCH_LIST)} mã\n"
    message += f"🟢 MUA: {buy_count} | 🔴 BÁN: {sell_count} | 🟡 NẮM GIỮ: {hold_count}\n"
    message += "⚠️ Chỉ tham khảo — tự quyết định giao dịch!\n"
    
    return message

def scan_all():
    """Quét tất cả mã và gửi báo cáo"""
    print(f"\n{'='*60}")
    print(f"[{get_vietnam_time().strftime('%d/%m/%Y %H:%M:%S')}] 🔄 CẬP NHẬT BÁO CÁO...")
    print(f"{'='*60}")
    message = generate_message()
    if message:
        print(f"📏 Độ dài tin nhắn: {len(message)} ký tự")
        send_telegram(message)
    else:
        print("❌ Không thể tạo tin nhắn")

# ========== CHẠY BOT ==========

if __name__ == "__main__":
    print("=" * 60)
    print(f"🚀 BOT CỔ PHIẾU — KHỞI ĐỘNG THÀNH CÔNG")
    print("=" * 60)
    print(f"📋 Theo dõi: {len(WATCH_LIST)} mã cổ phiếu")
    print(f"⏱️ Tần suất cập nhật: Mỗi {UPDATE_INTERVAL_MINUTES} phút")
    print(f"🔑 Token: {'✅ CÓ' if TELEGRAM_TOKEN else '❌ KHÔNG CÓ'}")
    print(f"💬 Chat ID: {'✅ CÓ' if CHAT_ID else '❌ KHÔNG CÓ'}")
    print(f"🌐 Nguồn dữ liệu: TCBS API, Cafef, Vietstock")
    print("=" * 60)
    print()
    
    # Gửi test signal
    print("\n📤 GỬI TÍN HIỆU TEST...")
    send_test_signal()
    
    # Gửi báo cáo chính lần đầu
    print("\n\n📤 GỬI BÁO CÁO CHÍNH THỨC LẦN ĐẦU...")
    scan_all()
    
    # Lên lịch tự động chạy mỗi 5 phút
    print(f"\n\n⏰ KHỞI ĐỘNG LỊCH TRÌNH — Mỗi {UPDATE_INTERVAL_MINUTES} phút gửi báo cáo mới")
    schedule.every(UPDATE_INTERVAL_MINUTES).minutes.do(scan_all)
    
    print(f"✅ Bot đang chạy 24/7 — tự động cập nhật mỗi {UPDATE_INTERVAL_MINUTES} phút")
    print("✅ Nhấn Ctrl+C để dừng bot.\n")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)  # Kiểm tra mỗi giây để chính xác hơn
        except KeyboardInterrupt:
            print("\n👋 Đã dừng bot.")
            break
        except Exception as e:
            print(f"⚠️ Lỗi: {e}")
            time.sleep(10)
