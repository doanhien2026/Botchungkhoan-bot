# ==========================================
# BOT CHỨNG KHOÁN - LƯỚT SÓNG NGẮN HẠN (ĐÃ TỐI ƯU LOGIC)
# ==========================================
import os
import sys
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1030583610")

WATCH_LIST = ["ACV", "FPT", "VCB"]

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

# ========== 1. ĐỒNG BỘ ĐƠN VỊ GIÁ TỪ CÁC API ==========
def get_stock_data_ssi(symbol):
    try:
        url = f"https://iboard.ssi.com.vn/dchart/api/quote?symbol={symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data:
                item = data[0]
                price = float(item.get("lastPrice", 0))
                ref = float(item.get("referencePrice", 0)) or float(item.get("prevClose", 0))
                # SSI trả về nghìn đồng sẵn
                if price > 0:
                    return price, ref, "SSI"
    except Exception:
        pass
    return None, None, None

def get_stock_data_vndirect(symbol):
    try:
        url = f"https://api-price.vndirect.com.vn/200718/prices?q=code:{symbol}"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://banggia.vndirect.com.vn/"}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data:
                item = data[0]
                price = float(item.get("price", 0))
                ref = float(item.get("basicPrice", 0))
                # Chuẩn hóa về nghìn đồng nếu trả về đồng
                if price > 1000:
                    price /= 1000
                    ref /= 1000
                if price > 0:
                    return price, ref, "VNDirect"
    except Exception:
        pass
    return None, None, None

def get_stock_data_tcbs(symbol):
    try:
        url = f"https://apipub.tcbs.com.vn/stock-insight/v1/stock/second-side-price?ticker={symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json().get("data", {})
            price = float(data.get("p", 0)) / 1000
            ref = float(data.get("r", 0)) / 1000
            if price > 0:
                return price, ref, "TCBS"
    except Exception:
        pass
    return None, None, None

def get_accurate_stock_data(symbol):
    for fetch_func in [get_stock_data_ssi, get_stock_data_vndirect, get_stock_data_tcbs]:
        price, ref, source = fetch_func(symbol)
        if price and price > 0:
            change_pct = ((price - ref) / ref * 100) if ref > 0 else 0
            return {
                "symbol": symbol,
                "price": price,
                "ref": ref,
                "change_pct": change_pct,
                "source": source
            }
    return None

# ========== 2. LOGIC TÍN HIỆU & KHU VỰC TP/SL CHUẨN ==========
def analyze_trading_signal(stock):
    price = stock["price"]
    ref = stock["ref"]
    pct = stock["change_pct"]
    
    # TP/SL cố định dựa trên Giá Tham Chiếu (Giá nền đầu ngày)
    stop_loss = ref * 0.96   # Cắt lỗ -4% so với giá tham chiếu
    take_profit = ref * 1.07 # Chốt lời +7% so với giá tham chiếu
    
    if pct >= 4.5:
        signal = "💰 **BÁN CHỐT LỜI (Đạt Mục Tiêu T+)**"
        advice = "Giá đã tiệm cận vùng chốt lời ngắn hạn (+5% đến +7%). NÊN BÁN."
    elif pct <= -3.5:
        signal = "🚨 **BÁN CẮT LỖ (Vi Phạm SL)**"
        advice = "Giá giảm quá -4% so với nền. NÊN CẮT LỖ bảo vệ vốn."
    elif pct >= 2.0:
        signal = "🚀 **MUA BREAKOUT (Lướt T+)**"
        advice = "Đang có dòng tiền đẩy giá bùng nổ. Canh mua theo sóng."
    elif -2.0 <= pct <= -0.5:
        signal = "🛒 **MUA TÍCH LŨY (Canh Chỉnh)**"
        advice = "Giá điều chỉnh nhẹ về vùng hỗ trợ. Điểm mua lướt sóng an toàn."
    else:
        signal = "✊ **CANH QUAN SÁT**"
        advice = "Giá đi ngang, chưa đủ biên độ vào lệnh."
        
    return signal, advice, take_profit, stop_loss

# ========== 3. CHƯƠNG TRÌNH CHÍNH ==========
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
