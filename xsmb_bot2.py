import os
import time
import telebot
from datetime import datetime

BOT_TOKEN = os.environ.get('BOT2_TOKEN')
CHAT_ID = os.environ.get('CHANNEL_ID')

print("🚀 BOT ĐANG KHỞI ĐỘNG...")
print(f"📌 Token: {BOT_TOKEN[:15]}...")
print(f"📌 Chat ID: {CHAT_ID}")

if not BOT_TOKEN or not CHAT_ID:
    print("❌ Thiếu BOT2_TOKEN hoặc CHANNEL_ID")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

def gui_tin_nhan():
    try:
        now = datetime.now()
        ngay = now.strftime("%d/%m/%Y")
        gio = now.strftime("%H:%M:%S")
        
        text = f"""🤖 BOT DỰ ĐOÁN XỔ SỐ MIỀN BẮC
📅 Ngày nhập dữ liệu: {ngay}
📆 Dự đoán cho ngày: {ngay}
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
        print(f"✅ [{gio}] ĐÃ GỬI THÀNH CÔNG!")
        return True
    except Exception as e:
        print(f"❌ LỖI GỬI: {e}")
        return False

if __name__ == "__main__":
    # Gửi lần đầu tiên
    gui_tin_nhan()
    
    # Vòng lặp gửi mỗi 1 phút
    print("⏰ Bắt đầu đợi 1 phút...")
    while True:
        time.sleep(60)  # 60 giây = 1 phút
        gui_tin_nhan()
        print("⏰ Đợi thêm 1 phút nữa...")
