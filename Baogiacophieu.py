# Thêm vào đầu file, cùng với các import
import requests
import time

def send_telegram_safe(message, max_retries=5):
    """Gửi tin nhắn với thử lại khi lỗi mạng"""
    for attempt in range(max_retries):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, data=data, timeout=15)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"⚠️ Lỗi mạng, thử lại lần {attempt+1}/{max_retries}: {e}")
            time.sleep(10)  # Chờ 10 giây rồi thử lại
    print("❌ Gửi thất bại sau nhiều lần thử")
    return None
