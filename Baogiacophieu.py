# =========================================================
# BOT CHỨNG KHOÁN - VERSION 2.5.0 (FIX BYPASS WAF & BLOCK IP)
# =========================================================
import os
import sys
import time
import requests
import threading
from flask import Flask
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Chứng Khoán Ver 2.5.0 - Active 24/7", 200

# --- THÔNG SỐ CẤU HÌNH ---
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
        res = requests.post(url, json=payload, timeout=12)
        return res.status_code == 200
    except Exception as e:
        print(f"❌ Lỗi gửi Telegram: {e}")
        return False

def parse_price(val):
    if val is None or val == "":
        return 0.0
    try:
        val = float(str(val).replace(',', ''))
        return val / 1000.0 if val >= 500 else val
    except ValueError:
        return 0.0

# --- THU THẬP DỮ LIỆU ĐA NGUỒN CHỐNG CHẶN IP (VER 2.5.0) ---
def fetch_stock_data(symbol):
    headers_mobile = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Referer": "https://m.cafef.vn/"
    }

    # Nguồn 1: CafeF Realtime Mobile API (Bypass IP ngoại cực tốt)
    try:
        url = f"https://m.cafef.vn/ajax/GetPriceHistory.ashx?symbol={symbol}"
        res = requests.get(url, headers=headers_mobile, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if data and "Data" in data and len(data["Data"]) > 0:
                item = data["Data"][0]
                price = parse_price(item.get("GiaDongCua") or item.get("GiaKhopLenh"))
                ref = parse_price(item.get("GiaThamChieu"))
                if price > 0 and ref > 0:
                    return price, ref, "CafeF"
    except Exception:
        pass

    # Nguồn 2: Vietstock Public Mobile API
    try:
        url = f"https://finance.vietstock.vn/data/getstockinfo?code={symbol}"
        headers_vs = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}
        res = requests.get(url, headers=headers_vs, timeout=8)
        if res.status_code == 200:
            data = res.json()
            price = parse_price(data.get("LastPrice") or data.get("ClosePrice"))
            ref = parse_price(data.get("ReferencePrice"))
            if price > 0 and ref > 0:
                return price, ref, "Vietstock"
    except Exception:
        pass

    # Nguồn 3: SSI iBoard History API
    try:
        now_ts = int(time.time())
        url = f"https://iboard.ssi.com.vn/dchart/api/history?resolution=1&symbol={symbol}&from={now_ts-86400}&to={now_ts}"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if data.get("s") == "ok" and len(data.get("c", [])) > 0:
                price = parse_price(data["c"][-1])
                ref = parse_price(data["o"][0])
                if price > 0 and ref > 0:
                    return price, ref, "SSI-History"
    except Exception:
        pass

    return None, None, None

def run_stock_bot():
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    vn_tz = timezone(timedelta(hours=7))
    now_vn = datetime.now(vn_tz)
    now_str = now_vn.strftime("%d/%m/%Y %H:%M:%S")
    
    msg = f"📊 *BÁO CÁO CHỨNG KHOÁN (VER 2.5.0)*\n"
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
    time.sleep(3)
    run_stock_bot()

if __name__ == "__main__":
    t = threading.Thread(target=start_bot_thread)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
