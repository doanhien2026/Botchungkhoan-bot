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
        now = datetime.now()
        date_now = now.strftime("%d/%m/%Y")
        time_now = now.strftime("%H:%M:%S")
        
        text = f"""🤖 BOT DỰ ĐOÁN XỔ SỐ MIỀN BẮC
📅 Ngày nhập dữ liệu: {date_now}
📆 Dự đoán cho ngày: {date_now}
📊 Dữ liệu phân tích: 90 ngày gần nhất
⚠️ CHỈ THAM KHẢO - KHÔNG ĐẢM BẢO CHẮC CHẮN!
🎲 Xổ số hoàn toàn ngẫu nhiên, kết quả quá khứ không dự đoán tương lai. Chơi có trách nhiệm!

🎯 TOP 3 CẶP LÔ TỶ LỆ CAO NHẤT
🥇 03
🥈 25
🥉 00

🎯 2 CẶP LÔ XIÊN TỶ LỆ CAO
🥇 73
🥈 56

🎯 ĐẦU SỐ 2 SỐ CUỐI GIẢI ĐẶC BIỆT TỶ LỆ CAO NHẤT
🥇 8

🎲 Chơi có trách nhiệm - Chỉ giải trí!
"""
        bot.send_message(CHAT_ID, text)
        print(f"✅ [{time_now}] Đã gửi tin nhắn dạng cũ thành công!")
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi: {e}")
        return False

if __name__ == "__main__":
    print("🚀 BOT DẠNG CŨ ĐANG KHỞI ĐỘNG...")
    print(f"📌 Chat ID: {CHAT_ID}")
    
    # Gửi tin nhắn đầu tiên
    send_message()
    
    # VÒNG LẶP - Gửi mỗi 1 phút để test
    print("⏰ Bắt đầu vòng lặp - Gửi mỗi 1 phút...")
    while True:
        try:
            time.sleep(60)  # 60 giây = 1 phút
            send_message()
        except Exception as e:
            print(f"🔄 Lỗi vòng lặp: {e} - Thử lại sau 60s...")
            time.sleep(60)
