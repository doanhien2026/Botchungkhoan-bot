import os
import re
import telebot
from flask import Flask
from threading import Thread
from fetcher import get_xsmb_result

# 1. Khởi tạo Flask Web Server (Giữ cho Render luôn Active)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot XSMB đang chạy bình thường!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. Lấy Token Telegram từ biến môi trường
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Chưa cấu hình TELEGRAM_BOT_TOKEN trong Environment Variables!")

bot = telebot.TeleBot(TOKEN)

# Hàm định dạng Bảng kết quả gửi sang Telegram
def format_xsmb_message(data):
    msg = f"<b>📉 KẾT QUẢ XSMB NGÀY {data['date']} 📉</b>\n"
    msg += f"<i>(Nguồn: {data.get('source', 'Tổng hợp')})</i>\n"
    msg += "-----------------------------------\n"
    msg += f"🔴 <b>Đặc Biệt:</b> <code>{data['special']}</code>\n"
    msg += f"🥇 <b>Giải Nhất:</b> <code>{data['g1']}</code>\n"
    msg += f"🥈 <b>Giải Nhì:</b> {', '.join([f'<code>{x}</code>' for x in data['g2']])}\n"
    msg += f"🥉 <b>Giải Ba:</b> {', '.join([f'<code>{x}</code>' for x in data['g3']])}\n"
    msg += f"4️⃣ <b>Giải Tư:</b> {', '.join([f'<code>{x}</code>' for x in data['g4']])}\n"
    msg += f"5️⃣ <b>Giải Năm:</b> {', '.join([f'<code>{x}</code>' for x in data['g5']])}\n"
    msg += f"6️⃣ <b>Giải Sáu:</b> {', '.join([f'<code>{x}</code>' for x in data['g6']])}\n"
    msg += f"7️⃣ <b>Giải Bảy:</b> {', '.join([f'<code>{x}</code>' for x in data['g7']])}\n"
    msg += "-----------------------------------\n"
    
    # Bảng Lô Tố
    lotos = sorted(list(set(data.get('loto', []))))
    msg += f"🎲 <b>Lô về:</b> {', '.join([f'<code>{x}</code>' for x in lotos])}"
    return msg

# 3. Lệnh /start
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 <b>Chào mừng bạn đến với Bot Tra Cứu XSMB!</b>\n\n"
        "Hãy nhập ngày bạn muốn tra cứu theo cú pháp:\n"
        "• <code>10082026</code> (8 chữ số)\n"
        "• Hoặc <code>10/08/2026</code>"
    )
    bot.reply_to(message, welcome_text, parse_mode="HTML")

# 4. Xử lý tin nhắn chứa ngày tra cứu (Đã lọc sạch văn bản rác)
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    text = message.text.strip()
    
    # Bóc tách duy nhất chuỗi 8 chữ số (Ví dụ: 10082026) hoặc định dạng DD/MM/YYYY
    match_digits = re.search(r'\b(\d{2})(\d{2})(\d{4})\b', text)
    match_slash = re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', text)
    
    formatted_date = None
    if match_digits:
        d, m, y = match_digits.group(1), match_digits.group(2), match_digits.group(3)
        formatted_date = f"{d}/{m}/{y}"
    elif match_slash:
        d, m, y = match_slash.group(1).zfill(2), match_slash.group(2).zfill(2), match_slash.group(3)
        formatted_date = f"{d}/{m}/{y}"

    if not formatted_date:
        bot.reply_to(message, "⚠️ Vui lòng nhập đúng định dạng ngày (Ví dụ: <code>10082026</code> hoặc <code>10/08/2026</code>)", parse_mode="HTML")
        return

    # Thông báo đang tra cứu
    status_msg = bot.reply_to(message, f"🔄 Đang tra cứu kết quả ngày <b>{formatted_date}</b>...", parse_mode="HTML")

    # Gọi hàm tra cứu từ fetcher.py
    data = get_xsmb_result(formatted_date)

    if data:
        response_text = format_xsmb_message(data)
        bot.edit_message_text(
            response_text, 
            chat_id=status_msg.chat.id, 
            message_id=status_msg.message_id, 
            parse_mode="HTML"
        )
    else:
        bot.edit_message_text(
            f"❌ Không tìm thấy dữ liệu XSMB cho ngày <b>{formatted_date}</b>!", 
            chat_id=status_msg.chat.id, 
            message_id=status_msg.message_id, 
            parse_mode="HTML"
        )

# 5. Khởi chạy Bot và Server
if __name__ == '__main__':
    # Chạy Web Server ở luồng riêng
    server_thread = Thread(target=run_flask)
    server_thread.start()
    
    # Khởi chạy Telegram Bot (Xóa webhook cũ để tránh xung đột)
    bot.remove_webhook()
    print("🤖 Bot XSMB đã sẵn sàng nhận tin nhắn...")
    bot.infinity_polling(skip_pending_updates=True)
