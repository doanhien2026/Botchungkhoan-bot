# ==========================================
# BOT CHỨNG KHOÁN - TỐI ƯU KẾT NỐI API
# ==========================================
import os
import sys
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1030583610")

WATCH_LIST = ["ACV", "FPT", "VCB"]

# Header mô phỏng trình duyệt Chrome thật để tránh bị chặn IP
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, json=payload, timeout=15)
        return res.status_code == 200
    except Exception as e:
        print(f"❌ Lỗi gửi Telegram: {e}")
        return False

# ========== 1. NGUỒN TCBS (Rất ổn định trên GitHub) ==========
def get_stock_data_tcbs(symbol):
    try:
        url = f"https://apipub.tcbs.com.vn/stock-insight/v1/stock/second-side-price?ticker={symbol}"
        res = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json().get("data", {})
            price = float(data.get("p", 0)) / 1000  # Đổi ra nghìn đồng
            ref = float(data.get("r", 0)) / 1000
            if price > 0 and ref > 0:
                return price, ref, "TCBS"
    except Exception as e:
        print(f"⚠️ TCBS lỗi {symbol}: {e}")
    return None, None, None

# ========== 2. NGUỒN CAFEF (Dự phòng cực mạnh) ==========
def get_stock_data_cafef(symbol):
    try:
        url = f"https://s.cafef.vn/ajax/mainservice.ashx?method=getstockinfo&symbol={symbol}"
        res = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json().get("Data", {})
            price = float(data.get("GiaHienTai", 0))
            ref = float(data.get("GiaThamChieu", 0))
            if price > 0 and ref > 0:
                return price, ref, "CafeF"
    except Exception as e:
        print(f"⚠️ CafeF lỗi {symbol}: {e}")
    return None, None, None

# ========== 3. NGUỒN SSI ==========
def get_stock_data_ssi(symbol):
    try:
        url = f"https://iboard.ssi.com.vn/dchart/api/quote?symbol={symbol}"
        res = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data:
                item = data[0]
                price = float(item.get("lastPrice", 0))
                ref = float(item.get("referencePrice", 0)) or float(item.get("prevClose", 0))
                if price > 0 and ref > 0:
                    return price, ref, "SSI"
    except Exception as e:
        print(f"⚠️ SSI lỗi {symbol}: {e}")
    return None, None, None

def get_accurate_stock_data(symbol):
    # Ưu tiên TCBS -> CafeF -> SSI
    for fetch_func in [get_stock_data_tcbs, get_stock_data_cafef, get_stock_data_ssi]:
        price, ref, source = fetch_func(symbol)
        if price and price > 0 and ref > 0:
            change_pct = ((price - ref) / ref * 100)
            return {
                "symbol": symbol,
                "price": price,
                "ref": ref,
                "change_pct": change_pct,
                "source": source
            }
    return None

def analyze_trading_signal(stock):
    price = stock["price"]
    ref = stock["ref"]
    pct = stock["change_pct"]
    
    stop_loss = ref * 0.96   # Cắt lỗ -4%
    take_profit = ref * 1.07 # Chốt lời +7%
    
    if pct >= 4.5:
        signal = "💰 **BÁN CHỐT LỜI (Đạt TP T+)**"
        advice = "Đạt vùng chốt lời ngắn hạn. NÊN BÁN."
    elif pct <= -3.5:
        signal = "🚨 **BÁN CẮT LỖ (Vi Phạm SL)**"
        advice = "Vi phạm ngưỡng cắt lỗ. NÊN CẮT LỖ."
    elif pct >= 2.0:
        signal = "🚀 **MUA BREAKOUT (Lướt T+)**"
        advice = "Dòng tiền vào mạnh. Canh mua lướt sóng."
    elif -2.0 <= pct <= -0.5:
        signal = "🛒 **MUA TÍCH LŨY (Canh Chỉnh)**"
        advice = "Giá điều chỉnh nhẹ. Điểm mua an toàn."
    else:
        signal = "✊ **CANH QUAN SÁT**"
        advice = "Biến động nhỏ, tiếp tục theo dõi."
        
    return signal, advice, take_profit, stop_loss

def main():
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    msg = f"⚡ *TÍN HIỆU LƯỚT SÓNG T+ REAL-TIME*\n"
    msg += f"⏰ *Thời gian:* `{now}`\n"
    msg += "-----------------------------------\n\n"
    
    for symbol in WATCH_LIST:
        stock = get_accurate_stock_data(symbol)
        
        if not stock:
            msg += f"❌ *{symbol}*: Không lấy được dữ liệu thị trường.\n\n"
            continue
            
        signal, advice, tp, sl = analyze_trading_signal(stock)
        icon = "🟢" if stock["change_pct"] > 0 else ("🔴" if stock["change_pct"] < 0 else "🟡")
        
        msg += f"📌 *Mã: {symbol}* {icon} _({stock['source']})_\n"
        msg += f"💵 Giá HT: *{stock['price']:,.2f}* (TC: {stock['ref']:,.2f})\n"
        msg += f"📊 Biến động: *{stock['change_pct']:+.2f}%*\n"
        msg += f"🎯 Tín hiệu: {signal}\n"
        msg += f"💡 *Khuyên dùng:* _{advice}_\n"
        msg += f"🎯 Mục tiêu TP: *{tp:,.2f}* | 🛡 Cắt lỗ SL: *{sl:,.2f}*\n"
        msg += "-----------------------------------\n"

    send_telegram(msg)

if __name__ == "__main__":
    main()
