import os
import time
import telebot
from datetime import datetime

BOT_TOKEN = os.environ.get('BOT2_TOKEN')
CHAT_ID = os.environ.get('CHANNEL_ID')

if not BOT_TOKEN or not CHAT_ID:
    print("❌ Thiếu biến môi trường!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

def send_message():
    try:
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        text = f"""🎯 BOT XSMB - TEST 1 PHÚT
⏰ Thời gian: {now}

📊 Dự đoán tham khảo:
🔹 Đặc biệt: Đang cập nhật...
🔹 Loto: Đang cập nhật...
🔹 2 số cuối: Đang cập nhật...

⚠️ Chơi có trách nhiệm - Chỉ giải trí! 🎲
"""
        bot.send_message(CHAT_ID, text)
        print(f"✅ [{now}] Đã gửi tin nhắn đến {CHAT_ID}")
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi: {e}")
        return False

if __name__ == "__main__":
    print("🚀 BOT ĐANG KHỞI ĐỘNG...")
    print(f"📌 Chat ID: {CHAT_ID}")
    
    # Gửi tin nhắn đầu tiên
    send_message()
    
    # VÒNG LẶP - TEST 1 PHÚT
    print("⏰ Bắt đầu vòng lặp - Gửi mỗi 1 phút...")
    while True:
        try:
            time.sleep(60)  # ============== 60 GIÂY = 1 PHÚT ==============
            send_message()
        except Exception as e:
            print(f"🔄 Lỗi vòng lặp: {e} - Thử lại sau 60s...")
            time.sleep(60)
