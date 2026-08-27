import os
import re
from datetime import datetime, timezone, timedelta
from flask import Flask
from threading import Thread
import telebot
from config import TELEGRAM_TOKEN, CHAT_ID, PORT, DATA_FILE
from fetcher import get_xsmb_result, get_xsmb_prediction, get_now_vn

app = Flask(__name__)

# === KHỞI TẠO BOT — ĐỌC TOKEN TỪ CONFIG.PY ===
bot = telebot.TeleBot(TELEGRAM_TOKEN)
print(f"✅ Token đã nạp: {TELEGRAM_TOKEN[:20]}...")
print(f"✅ Gửi đến Chat ID: {CHAT_ID}")

# === WEB SERVER ===
@app.route('/')
def home():
    return "✅ Bot XSMB Server Active — Đang hoạt động", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# === HÀM GỬI TỰ ĐỘNG LÊN KÊNH ===
def send_auto_report():
    """Gửi kết quả + dự báo tự động đến kênh"""
    now = get_now_vn()
    today_str = now.strftime("%d/%m/%Y")
    
    # Lấy kết quả hôm nay
    data = get_xsmb_result(today_str)
    if not data:
        bot.send_message(CHAT_ID, f"⚠️ Chưa lấy được dữ liệu ngày {today_str}")
        return
    
    # Lấy dự báo
    pred = get_xsmb_prediction(today_str)
    
    # Tạo báo cáo
    msg = f"""
📊 <b>KẾT QUẢ & DỰ BÁO XSMB — {today_str}</b>
<i>Nguồn: {data.get('source', 'Không xác định')}</i>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 <b>Đặc Biệt:</b> <code>{data['special']}</code>
🥇 <b>Giải Nhất:</b> <code>{data['g1']}</code>
"""
    # An toàn xử lý các giải có thể thiếu
    if 'g2' in data and data['g2']:
        msg += f"🥈 <b>Giải Nhì:</b> {', '.join(f'<code>{x}</code>' for x in data['g2'])}\n"
    if 'g3' in data and data['g3']:
        msg += f"🥉 <b>Giải Ba:</b> {', '.join(f'<code>{x}</code>' for x in data['g3'])}\n"
    if 'g4' in data and data['g4']:
        msg += f"4️⃣ <b>Giải Tư:</b> {', '.join(f'<code>{x}</code>' for x in data['g4'])}\n"
    if 'loto' in data and data['loto']:
        msg += f"🎲 <b>Lô về:</b> {', '.join(f'<code>{x}</code>' for x in sorted(set(data['loto'])))}\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🔮 <b>DỰ BÁO DỰ KIẾN</b>\n"
    msg += f"🎯 <b>Bạch Thủ Lô:</b> <code>{pred['bach_thu']}</code>\n"
    msg += f"👯 <b>Song Thủ Lô:</b> <code>{', '.join(pred['song_thu'])}</code>\n"
    msg += f"💥 <b>Lô Xiên:</b> <code>{', '.join(pred['lo_xiu'])}</code>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "<i>⚠️ Chỉ tham khảo — Chơi có trách nhiệm!</i>"
    
    bot.send_message(CHAT_ID, msg, parse_mode="HTML")
    print(f"✅ Đã gửi báo cáo tự động đến kênh: {today_str}")

# === VÒNG LẶP TỰ ĐỘNG GỬI 18:35 ===
def auto_scheduler():
    """Kiểm tra thời gian & gửi báo cáo mỗi ngày 18:35"""
    last_send_date = None
    while True:
        try:
            now = get_now_vn()
            today_str = now.strftime("%d/%m/%Y")
            hour, minute = now.hour, now.minute
            
            # Gửi vào 18:35, chỉ gửi 1 lần/ngày
            if hour == 18 and minute >= 35 and last_send_date != today_str:
                send_auto_report()
                last_send_date = today_str
            
            # Kiểm tra mỗi 60 giây
            import time
            time.sleep(60)
        except Exception as e:
            print(f"⚠️ Lỗi lịch trình: {e}")
            import time
            time.sleep(60)

# === LỆNH BOT ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg = (
        "🤖 <b>BOT KẾT QUẢ VÀ DỰ BÁO XSMB</b>\n\n"
        "• Nhập 8 chữ số để xem <b>Kết quả</b> (VD: <code>10082026</code>)\n"
        "• Gõ <code>/dubao</code> hoặc <code>/dubao 10082026</code> để xem <b>Dự báo Lô/Đề</b>\n"
        "• Tự động gửi kết quả hàng ngày vào 18:35 lên kênh!"
    )
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(commands=['dubao'])
def handle_dubao(message):
    text = message.text.strip()
    match = re.search(r'\b(\d{2})(\d{2})(\d{4})\b', text)
    
    if match:
        formatted_date = f"{match.group(1)}/{match.group(2)}/{match.group(3)}"
    else:
        formatted_date = get_now_vn().strftime("%d/%m/%Y")
        
    pred = get_xsmb_prediction(formatted_date)
    
    msg = f"🔮 <b>DỰ BÁO KẾT QUẢ XSMB NGÀY {pred['date']}</b> 🔮\n"
    msg += "-----------------------------------\n"
    msg += f"🎯 <b>Bạch Thủ Lô:</b> <code>{pred['bach_thu']}</code>\n"
    msg += f"👯 <b>Song Thủ Lô:</b> <code>{', '.join(pred['song_thu'])}</code>\n"
    msg += f"💥 <b>Xuyên 2 / Lô Xiên:</b> <code>{', '.join(pred['lo_xiu'])}</code>\n"
    msg += "-----------------------------------\n"
    msg += "<i>⚠️ Chỉ tham khảo — Chơi có trách nhiệm!</i>"
    
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    text = message.text.strip()
    match_digits = re.search(r'\b(\d{2})(\d{2})(\d{4})\b', text)
    
    if not match_digits:
        bot.reply_to(message, "⚠️ Cú pháp không hợp lệ. Nhập ngày dạng <code>10082026</code> hoặc gõ <code>/dubao</code>", parse_mode="HTML")
        return

    d, m, y = match_digits.group(1), match_digits.group(2), match_digits.group(3)
    formatted_date = f"{d}/{m}/{y}"

    status_msg = bot.reply_to(message, f"🔄 Đang lấy dữ liệu ngày <b>{formatted_date}</b>...", parse_mode="HTML")

    data = get_xsmb_result(formatted_date)

    if data:
        msg = f"📉 <b>KẾT QUẢ XSMB NGÀY {data['date']}</b> 📉\n"
        msg += f"<i>(Nguồn: {data.get('source', 'Không xác định')})</i>\n"
        msg += "-----------------------------------\n"
        msg += f"🔴 <b>Đặc Biệt:</b> <code>{data['special']}</code>\n"
        msg += f"🥇 <b>Giải Nhất:</b> <code>{data['g1']}</code>\n"
        
        # An toàn: chỉ hiển thị giải khi có dữ liệu
        if 'g2' in data and data['g2']:
            msg += f"🥈 <b>Giải Nhì:</b> {', '.join(f'<code>{x}</code>' for x in data['g2'])}\n"
        if 'g3' in data and data['g3']:
            msg += f"🥉 <b>Giải Ba:</b> {', '.join(f'<code>{x}</code>' for x in data['g3'])}\n"
        if 'g4' in data and data['g4']:
            msg += f"4️⃣ <b>Giải Tư:</b> {', '.join(f'<code>{x}</code>' for x in data['g4'])}\n"
        if 'g5' in data and data['g5']:
            msg += f"5️⃣ <b>Giải Năm:</b> {', '.join(f'<code>{x}</code>' for x in data['g5'])}\n"
        if 'g6' in data and data['g6']:
            msg += f"6️⃣ <b>Giải Sáu:</b> {', '.join(f'<code>{x}</code>' for x in data['g6'])}\n"
        if 'g7' in data and data['g7']:
            msg += f"7️⃣ <b>Giải Bảy:</b> {', '.join(f'<code>{x}</code>' for x in data['g7'])}\n"
        if 'loto' in data and data['loto']:
            msg += "-----------------------------------\n"
            msg += f"🎲 <b>Lô về:</b> {', '.join(f'<code>{x}</code>' for x in sorted(set(data['loto'])))}\n"
        
        bot.edit_message_text(msg, chat_id=status_msg.chat.id, message_id=status_msg.message_id, parse_mode="HTML")
    else:
        bot.edit_message_text("❌ Không lấy được dữ liệu. Vui lòng thử lại sau!", 
                              chat_id=status_msg.chat.id, message_id=status_msg.message_id, parse_mode="HTML")

# === KHỞI ĐỘNG ===
if __name__ == '__main__':
    print("🚀 BOT XSMB KHỞI ĐỘNG — Đang khởi động...")
    
    # Khởi động Web Server
    Thread(target=run_flask, daemon=True).start()
    print("✅ Web Server đã chạy")
    
    # Khởi động lịch trình tự động gửi báo cáo
    Thread(target=auto_scheduler, daemon=True).start()
    print("✅ Lịch trình tự động 18:35 đã bật")
    
    # Bắt đầu lắng nghe lệnh Telegram
    bot.remove_webhook()
    print("🤖 Bot đang lắng nghe lệnh...")
    bot.infinity_polling(skip_pending_updates=True)
