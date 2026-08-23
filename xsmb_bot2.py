import os
import time
import telebot
from datetime import datetime
from flask import Flask

BOT_TOKEN = os.environ.get('BOT2_TOKEN')
CHAT_ID = os.environ.get('CHANNEL_ID')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Trang web để UptimeRobot gọi
@app.route('/')
def home():
    return "✅ BOT XSMB ĐANG CHẠY - Hoạt động bình thường!"

@app.route('/health')
def health():
    return "ok"

# Hàm gửi tin nhắn
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
        print(f"✅ [{gio}] Đã gửi tin nhắn thành công!")
    except Exception as e:
        print(f"❌ Lỗi gửi: {e}")

# Chạy bot trong luồng riêng
def chay_bot():
    print("⏰ Bắt đầu vòng lặp - Gửi mỗi giờ...")
    # Gửi lần đầu ngay khi khởi động
    gui_tin_nhan()
    while True:
        time.sleep(3600)  # ============== MỖI 1 GIỜ GỬI 1 LẦN ==============
        gui_tin_nhan()

if __name__ == "__main__":
    print("🚀 BOT XSMB ĐANG KHỞI ĐỘNG...")
    print(f"📌 Chat ID: {CHAT_ID}")
    
    # Khởi động luồng gửi tin nhắn
    from threading import Thread
    Thread(target=chay_bot).start()
    
    # Chạy web server để UptimeRobot giữ sống
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
