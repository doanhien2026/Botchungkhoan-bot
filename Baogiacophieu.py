# ==========================================
# BOT CHỨNG KHOÁN - BÁO GIÁ PHIÊN KẾT THÚC
# ==========================================
import os
import sys
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1030583610")

WATCH_LIST = ["ACV", "FPT", "VCB"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
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

# ========== LẤY GIÁ CHỐT PHIÊN KHÔNG BỊ LỖI SAU 15H00 ==========
def get_stock_data(symbol):
    # Nguồn 1: TCBS API (Rất ổn định sau giờ đóng cửa)
    try:
        url = f"https://apipub.tcbs.com.vn/stock-insight/v1/stock/second-side-price?ticker={symbol}"
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json().get("data", {})
            price = float(data.get("p", 0)) / 1000
            ref = float(data.get("r", 0)) / 1000
            if price > 0 and ref > 0:
                return price, ref, "TCBS"
    except Exception:
        pass

    # Nguồn 2: SSI API
    try:
        url = f"https://iboard.ssi.com.vn/dchart/api/quote?symbol={symbol}"
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data:
                item = data[0]
                price = float(item.get("lastPrice", 0))
                ref = float(item.get("referencePrice", 0)) or float(item.get("prevClose", 0))
                if price > 0 and ref > 0:
                    return price, ref, "SSI"
    except Exception:
        pass

    return None, None, None

def analyze_trading_signal(price, ref, is_market_closed):
    pct = ((price - ref) / ref * 100) if ref > 0 else 0
    stop_loss = ref * 0.96   # SL -4%
    take_profit = ref * 1.07 # TP +7%
    
    if is_market_closed:
        # Logic tổng kết cuối phiên
        if pct >= 3.0:
            signal = "🟢 **TĂNG MANH CUỐI PHIÊN**"
            advice = "Phiên giao dịch tích cực. Tiếp tục nắm giữ cho T+."
        elif pct <= -3.0:
            signal = "🔴 **GIẢM MẠNH CUỐI PHIÊN**"
            advice = "Xu hướng xấu. Cân nhắc hạ tỷ trọng phiên kế tiếp."
        else:
            signal = "🟡 **ĐÓNG CỬA ĐI NGANG**"
            advice = "Giá tích lũy, theo dõi lực cầu phiên sau."
    else:
        # Logic trong giờ giao dịch
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
        
    return pct, signal, advice, take_profit, stop_loss

def main():
    now_dt = datetime.now()
    now_str = now_dt.strftime("%d/%m/%Y %H:%M:%S")
    current_hour = now_dt.hour
    
    # Kiểm tra xem có phải phiên tổng kết đóng cửa không (Sau 15h00)
    is_market_closed = current_hour >= 15 or current_hour < 8
    
    if is_market_closed:
        msg = f"📊 *BÁO CÁO KẾT THÚC PHIÊN GIAO DỊCH*\n"
    else:
        msg = f"⚡ *TÍN HIỆU LƯỚT SÓNG T+ REAL-TIME*\n"
        
    msg += f"⏰ *Thời gian:* `{now_str}`\n"
    msg += "-----------------------------------\n\n"
    
    valid_data_count = 0
    
    for symbol in WATCH_LIST:
        price, ref, source = get_stock_data(symbol)
        
        if not price:
            print(f"⚠️ Không lấy được dữ liệu cho {symbol}")
            continue
            
        valid_data_count += 1
        pct, signal, advice, tp, sl = analyze_trading_signal(price, ref, is_market_closed)
        icon = "🟢" if pct > 0 else ("🔴" if pct < 0 else "🟡")
        
        msg += f"📌 *Mã: {symbol}* {icon} _({source})_\n"
        msg += f"💵 Giá đóng cửa: *{price:,.2f}* (TC: {ref:,.2f})\n"
        msg += f"📊 Biến động phiên: *{pct:+.2f}%*\n"
        msg += f"🎯 Trạng thái: {signal}\n"
        msg += f"💡 *Đánh giá:* _{advice}_\n"
        msg += f"🎯 Mục tiêu TP: *{tp:,.2f}* | 🛡 Cắt lỗ SL: *{sl:,.2f}*\n"
        msg += "-----------------------------------\n"

    if valid_data_count > 0:
        send_telegram(msg)
        print(f"✅ Đã gửi báo cáo phiên thành công!")

if __name__ == "__main__":
    main()
