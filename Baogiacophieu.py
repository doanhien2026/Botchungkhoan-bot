# =========================================================
# BOT CHỨNG KHOÁN - VERSION 2.2.0 (FIX DEPLOY FAILED & TIME)
# =========================================================
import os
import sys
import json
import time
import requests
import threading
from flask import Flask
from datetime import datetime, timezone, timedelta

# --- KHỞI TẠO FLASK WEB SERVICE ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Chứng Khoán Ver 2.2.0 - Active 24/7", 200

# --- THÔNG SỐ CẤU HÌNH ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1030583610")
WATCH_LIST = ["ACV", "FPT", "VCB"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Accept": "*/*",
    "Accept-Language": "vi-VN,vi;q=0.9",
    "Connection": "keep-alive"
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
        res = requests.post(url, json=payload, timeout=12)
        return res.status_code == 200
    except Exception as e:
        print(f"❌ Lỗi gửi Telegram: {e}")
        return False

def parse_price(val):
    if val is None or val == "":
        return 0.0
    try:
        val = float(val)
        return val / 1000.0 if val >= 500 else val
    except ValueError:
        return 0.0

# --- THU THẬP DỮ LIỆU ĐA NGUỒN (VER 2.2.0) ---
def fetch_stock_data(symbol):
    # Nguồn 1: SSI iBoard API
    try:
        url = f"https://iboard.ssi.com.vn/dchart/api/quote?symbol={symbol}"
        res = requests.get(url, headers=HEADERS, timeout=6)
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data:
                item = data[0]
                price = parse_price(item.get("lastPrice") or item.get("referencePrice"))
                ref = parse_price(item.get("referencePrice") or item.get("prevClose"))
                if price > 0 and ref > 0:
                    return price, ref, "SSI"
    except Exception:
        pass

    # Nguồn 2: TCBS API
    try:
        url = f"https://apipub.tcbs.com.vn/stock-insight/v1/stock/second-side-price?ticker={symbol}"
        res = requests.get(url, headers=HEADERS, timeout=6, verify=False)
        if res.status_code == 200:
            data = res.json().get("data", {})
            price = parse_price(data.get("p") or data.get("r"))
            ref = parse_price(data.get("r"))
            if price > 0 and ref > 0:
                return price, ref, "TCBS"
    except Exception:
        pass

    # Nguồn 3: VPS API
    try:
        url = f"https://bgapidatafeed.vps.com.vn/getstockdata/{symbol}"
        res = requests.get(url, headers=HEADERS, timeout=6)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                price = parse_price(item.get("lastPrice") or item.get("closePrice") or item.get("r"))
                ref = parse_price(item.get("r"))
                if price > 0 and ref > 0:
                    return price, ref, "VPS"
    except Exception:
        pass

    return None, None, None

def run_stock_bot():
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # TÍNH MÚI GIỜ VIỆT NAM (UTC+7) TỰ ĐỘNG CHUẨN 100%
    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    now_str = now_vn.strftime("%d/%m/%Y %H:%M:%S")
    
    msg = f"📊 *BÁO CÁO CHỨNG KHOÁN (VER 2.2.0)*\n"
    msg += f"⏰ *Thời gian VN:* `{now_str}`\n"
    msg += "-----------------------------------\n\n"
    
    valid_count = 0
    
    for symbol in WATCH_LIST:
        price, ref, source = fetch_stock_data(symbol)
        
        if not price:
            msg += f"⚠️ *{symbol}*: Không lấy được dữ liệu\n"
            continue
            
        valid_count += 1
        pct = ((price - ref) / ref * 100) if ref > 0 else 0
        icon = "🟢" if pct > 0 else ("🔴" if pct < 0 else "🟡")
        
        msg += f"📌 *Mã: {symbol}* {icon} _({source})_\n"
        msg += f"💵 Giá: *{price:,.2f}* (TC: {ref:,.2f})\n"
        msg += f"📊 Biến động: *{pct:+.2f}%*\n"
        msg += "-----------------------------------\n"

        time.sleep(1)

    send_telegram(msg)

def start_bot_thread():
    time.sleep(3) # Đợi Flask server khởi chạy ổn định rồi mới quét giá
    run_stock_bot()

if __name__ == "__main__":
    # Khởi chạy luồng lấy giá ngầm
    t = threading.Thread(target=start_bot_thread)
    t.daemon = True
    t.start()
    
    # Mở Web Server trên Port môi trường của Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
