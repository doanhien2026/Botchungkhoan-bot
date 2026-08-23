import os
import time
import telebot
from datetime import datetime

# Lấy biến môi trường
BOT_TOKEN = os.environ.get('BOT2_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

if not BOT_TOKEN or not CHANNEL_ID:
    print("❌ Thiếu BOT2_TOKEN hoặc CHANNEL_ID")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

def send_signal():
    try:
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        message = f"""🎯 BOT XSMB - TÍN HIỆU NGÀY {now}

📊 Dự đoán tham khảo:
🔹 Đặc biệt: Đang cập nhật...
🔹 Loto: Đang cập nhật...
🔹 2 số cuối: Đang cập nhật...

⚠️ Lưu ý: Đây là dự đoán tham khảo, vui lòng kiểm tra kết quả chính thức tại trang XSMB
Chơi có trách nhiệm - Chỉ giải trí! 🎲
"""
        bot.send_message(CHANNEL_ID, message)
        print(f"✅ [{now}] Đã gửi tin nhắn thành công!")
    except Exception as e:
        print(f"❌ Lỗi gửi tin nhắn: {e}")

if __name__ == "__main__":
    print("🚀 BOT XSMB ĐANG KHỞI ĐỘNG...")
    print(f"📌 Token: {BOT_TOKEN[:15]}...")
    print(f"📌 Chat ID: {CHANNEL_ID}")
    print("=" * 50)
    
    # Gửi tin nhắn ngay khi khởi động
    send_signal()
    
    # Vòng lặp tự động chạy mỗi 6 giờ
    while True:
        try:
            now = datetime.now()
            print(f"⏰ [{now.strftime('%d/%m/%Y %H:%M:%S')}] Đợi gửi tin nhắn tiếp theo...")
            
            # Đợi 6 giờ = 21600 giây
            time.sleep(21600)
            
            # Gửi tin nhắn
            send_signal()
            
        except KeyboardInterrupt:
            print("👋 Bot dừng lại bởi người dùng")
            break
        except Exception as e:
            print(f"❌ Lỗi vòng lặp: {e}")
            time.sleep(60)  # Nếu lỗi thì đợi 1 phút rồi thử lại
