# ==========================================
# BOT CHỨNG KHOÁN 24/7 - RENDER WEB SERVICE
# ==========================================
import os
import sys
import json
import time
import requests
import threading
from flask import Flask
from datetime import datetime, timedelta, timezone

# --- KHỞI TẠO FLASK ĐỂ LÀM WEB SERVICE TRÊN RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Chứng Khoán đang hoạt động 24/7!", 200

# --- CẤU HÌNH THÔNG SỐ ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1030583610")
WATCH_LIST = ["ACV", "FPT", "VCB"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
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
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"❌ Lỗi gửi Telegram: {e}")
        return False

def parse_price(val):
    if val is None or val == "":
        return 0.0
    try:
        val = float(val)
        if val >= 500:
            return val / 1000.0
        return val
    except ValueError:
        return 0.0

# --- LẤY GIÁ TRỰC TIẾP KHÔNG QUA PROXY TRUNG GIAN TRÁCH TIMEOUT ---
def get_stock_data_direct(symbol):
    # Cách 1: API VPS Trực tiếp
    try:
        url = f"https://bgapidatafeed.vps.com.vn/getstockdata/{symbol}"
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                price = parse_price(item.get("lastPrice") or item.get("closePrice") or item.get("r"))
                ref = parse_price(item.get("r"))
                if price > 0 and ref > 0:
                    return price, ref, "VPS"
    except Exception as e:
        print(f"⚠️ VPS lỗi [{symbol}]: {e}")

    # Cách 2: API TCBS Trực tiếp
    try:
        url = f"https://apipub.tcbs.com.vn/stock-insight/v1/stock/second-side-price?ticker={symbol}"
        res = requests.get(url, headers=HEADERS, timeout=8, verify=False)
        if res.status_code == 200:
            data = res.json().get("data", {})
            price = parse_price(data.get("p") or data.get("r"))
            ref = parse_price(data.get("r"))
            if price > 0 and ref > 0:
                return price, ref, "TCBS"
    except Exception as e:
        print(f"⚠️ TCBS lỗi [{symbol}]: {e}")

    # Cách 3: API Vietstock Dự phòng
    try:
        url = f"https://finance.vietstock.vn/data/getstockinfo?code={symbol}"
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json()
            price = parse_price(data.get("LastPrice") or data.get("ReferencePrice"))
            ref = parse_price(data.get("ReferencePrice"))
            if price > 0 and ref > 0:
                return price, ref, "Vietstock"
    except Exception as e:
        print(f"⚠️ Vietstock lỗi [{symbol}]: {e}")

    return None, None, None

def analyze_signal(price, ref, is_market_closed):
    pct = ((price - ref) / ref * 100) if ref > 0 else 0
    stop_loss = ref * 0.96   
    take_profit = ref * 1.07 
    
    if is_market_closed:
        if pct >= 2.0:
            signal = "🟢 **TĂNG MẠNH CUỐI PHIÊN**"
            advice = "Tín hiệu tích cực. Nắm giữ cho T+."
        elif pct <= -2.0:
            signal = "🔴 **GIẢM MẠNH CUỐI PHIÊN**"
            advice = "Lực bán áp đảo. Cân nhắc hạ tỷ trọng."
        else:
            signal = "🟡 **ĐÓNG CỬA TÍCH LŨY**"
            advice = "Giá đi ngang, tiếp tục quan sát."
    else:
        if pct >= 4.5:
            signal = "💰 **BÁN CHỐT LỜI (Đạt TP T+)**"
            advice = "Đạt mục tiêu chốt lời ngắn hạn. NÊN BÁN."
        elif pct <= -3.5:
            signal = "🚨 **BÁN CẮT LỖ (Vi Phạm SL)**"
            advice = "Vi phạm ngưỡng rủi ro. NÊN CẮT LỖ."
        elif pct >= 2.0:
            signal = "🚀 **MUA BREAKOUT (Lướt T+)**"
            advice = "Dòng tiền vào mạnh. Canh mua gia tăng."
        elif -2.0 <= pct <= -0.5:
            signal = "🛒 **MUA TÍCH LŨY (Canh Chỉnh)**"
            advice = "Giá điều chỉnh nhẹ. Vùng mua an toàn."
        else:
            signal = "✊ **CANH QUAN SÁT**"
            advice = "Biến động hẹp, theo dõi thêm."
        
    return pct, signal, advice, take_profit, stop_loss

def run_stock_bot():
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    now_str = now_vn.strftime("%d/%m/%Y %H:%M:%S")
    current_hour = now_vn.hour
    
    is_market_closed = current_hour >= 15 or current_hour < 8
    
    if is_market_closed:
        msg = f"📊 *BÁO CÁO KẾT THÚC PHIÊN GIAO DỊCH*\n"
    else:
        msg = f"⚡ *TÍN HIỆU LƯỚT SÓNG T+ REAL-TIME*\n"
        
    msg += f"⏰ *Thời gian VN:* `{now_str}`\n"
    msg += "-----------------------------------\n\n"
    
    valid_count = 0
    
    for symbol in WATCH_LIST:
        price, ref, source = get_stock_data_direct(symbol)
        
        if not price:
            print(f"❌ Không lấy được dữ liệu cho mã {symbol}")
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

        time.sleep(1.5)

    if valid_count > 0:
        send_telegram(msg)
        print(f"✅ Đã gửi báo cáo thành công cho {valid_count}/{len(WATCH_LIST)} mã!")
    else:
        print("⚠️ Không lấy được dữ liệu từ các nguồn.")

# --- CHẠY LUỒNG QUÉT GIÁ NGHẦM ĐỂ CÓ THỂ MỞ PORT 10000 ---
def start_bot_thread():
    run_stock_bot()

if __name__ == "__main__":
    # Kích hoạt luồng gửi Telegram
    t = threading.Thread(target=start_bot_thread)
    t.start()
    
    # Bắt buộc khởi chạy Flask trên Port môi trường của Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
