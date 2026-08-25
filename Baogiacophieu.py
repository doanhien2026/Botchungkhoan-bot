# ==========================================
# BOT CHỨNG KHOÁN - CHẠY TRÊN GITHUB ACTIONS
# ==========================================
import os
import sys
import requests
from datetime import datetime, timedelta, timezone

# ========== CẤU HÌNH BẢO MẬT ==========
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1030583610")

WATCH_LIST = ["ACV", "FPT", "VCB"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

# ========== HÀM GỬI TELEGRAM ==========
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

# ========== LẤY GIÁ CHUẨN TỪ CÁC NGUỒN KHÔNG BỊ CHẶN IP ==========
def get_stock_data(symbol):
    # Nguồn 1: TCBS API (Ưu tiên số 1 trên Server quốc tế)
    try:
        url = f"https://apipub.tcbs.com.vn/stock-insight/v1/stock/second-side-price?ticker={symbol}"
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json().get("data", {})
            price = float(data.get("p", 0)) / 1000
            ref = float(data.get("r", 0)) / 1000
            if price > 0 and ref > 0:
                return price, ref, "TCBS"
    except Exception as e:
        print(f"⚠️ TCBS lỗi [{symbol}]: {e}")

    # Nguồn 2: Vietstock API (Dự phòng)
    try:
        url = f"https://finance.vietstock.vn/data/getquote?stockcode={symbol}"
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                price = float(item.get("LastPrice", 0))
                ref = float(item.get("ReferencePrice", 0))
                if price > 0 and ref > 0:
                    return price, ref, "Vietstock"
    except Exception as e:
        print(f"⚠️ Vietstock lỗi [{symbol}]: {e}")

    return None, None, None

# ========== LOGIC PHÂN TÍCH LƯỚT SÓNG T+ ==========
def analyze_signal(price, ref, is_market_closed):
    pct = ((price - ref) / ref * 100) if ref > 0 else 0
    stop_loss = ref * 0.96   # SL -4%
    take_profit = ref * 1.07 # TP +7%
    
    if is_market_closed:
        if pct >= 2.0:
            signal = "🟢 **TĂNG MẠNH CUỐI PHIÊN**"
            advice = "Phiên tích cực. Tín hiệu tốt cho T+."
        elif pct <= -2.0:
            signal = "🔴 **GIẢM MẠNH CUỐI PHIÊN**"
            advice = "Lực bán mạnh. Cần chú ý quản trị rủi ro."
        else:
            signal = "🟡 **ĐÓNG CỬA TÍCH LŨY**"
            advice = "Giá ổn định, quan sát phiên kế tiếp."
    else:
        if pct >= 4.5:
            signal = "💰 **BÁN CHỐT LỜI (Đạt TP T+)**"
            advice = "Chạm vùng mục tiêu ngắn hạn. NÊN BÁN."
        elif pct <= -3.5:
            signal = "🚨 **BÁN CẮT LỖ (Vi Phạm SL)**"
            advice = "Chạm ngưỡng rủi ro. NÊN CẮT LỖ."
        elif pct >= 2.0:
            signal = "🚀 **MUA BREAKOUT (Lướt T+)**"
            advice = "Dòng tiền bùng nổ. Canh mua gia tăng."
        elif -2.0 <= pct <= -0.5:
            signal = "🛒 **MUA TÍCH LŨY (Canh Chỉnh)**"
            advice = "Điều chỉnh nhẹ. Điểm vào an toàn."
        else:
            signal = "✊ **CANH QUAN SÁT**"
            advice = "Biến động hẹp, tiếp tục theo dõi."
        
    return pct, signal, advice, take_profit, stop_loss

# ========== CHƯƠNG TRÌNH CHÍNH (CHẠY 1 LẦN DỒI TẮT) ==========
def main():
    # Quy đổi sang giờ Việt Nam (UTC+7)
    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    now_str = now_vn.strftime("%d/%m/%Y %H:%M:%S")
    current_hour = now_vn.hour
    
    # Kiểm tra đóng cửa sàn (Sau 15h00 hoặc trước 8h30)
    is_market_closed = current_hour >= 15 or current_hour < 8
    
    if is_market_closed:
        msg = f"📊 *BÁO CÁO KẾT THÚC PHIÊN GIAO DỊCH*\n"
    else:
        msg = f"⚡ *TÍN HIỆU LƯỚT SÓNG T+ REAL-TIME*\n"
        
    msg += f"⏰ *Thời gian VN:* `{now_str}`\n"
    msg += "-----------------------------------\n\n"
    
    valid_count = 0
    
    for symbol in WATCH_LIST:
        price, ref, source = get_stock_data(symbol)
        
        if not price:
            print(f"❌ Không lấy được dữ liệu cho {symbol}")
            continue
            
        valid_count += 1
        pct, signal, advice, tp, sl = analyze_signal(price, ref, is_market_closed)
        icon = "🟢" if pct > 0 else ("🔴" if pct < 0 else "🟡")
        
        msg += f"📌 *Mã: {symbol}* {icon} _({source})_\n"
        msg += f"💵 Giá: *{price:,.2f}* (TC: {ref:,.2f})\n"
        msg += f"📊 Biến động: *{pct:+.2f}%*\n"
        msg += f"🎯 Tín hiệu: {signal}\n"
        msg += f"💡 *Đánh giá:* _{advice}_\n"
        msg += f"🎯 Mục tiêu TP: *{tp:,.2f}* | 🛡 Cắt lỗ SL: *{sl:,.2f}*\n"
        msg += "-----------------------------------\n"

    # CHỈ GỬI TELEGRAM NẾU LẤY ĐƯỢC DỮ LIỆU (Chống spam tin nhắn lỗi)
    if valid_count > 0:
        send_telegram(msg)
        print(f"✅ Đã gửi báo cáo thành công cho {valid_count}/{len(WATCH_LIST)} mã!")
    else:
        print("⚠️ Tất cả các nguồn API đều thất bại. Không gửi Telegram.")

if __name__ == "__main__":
    main()
