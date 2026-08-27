import os
import re
import telebot
from flask import Flask
from threading import Thread
from fetcher import get_xsmb_result, get_xsmb_prediction

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot XSMB Server Active"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Dán Token thật của bạn vào giữa ngoặc kép bên dưới (Hàm .strip() sẽ tự làm sạch khoảng trắng)
RAW_TOKEN = "ĐIỀN_TOKEN_BOT_CỦA_BẠN_VÀO_ĐÂY"
TOKEN = RAW_TOKEN.strip()

bot = telebot.TeleBot(TOKEN)

# 1. Lệnh /start
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg = (
        "🤖 <b>BOT KẾT QUẢ VÀ DỰ BÁO XSMB</b>\n\n"
        "• Nhập 8 chữ số để xem <b>Kết quả</b> (VD: <code>10082026</code>)\n"
        "• Gõ <code>/dubao</code> hoặc <code>/dubao 10082026</code> để xem <b>Dự báo Lô/Đề</b>"
    )
    bot.reply_to(message, msg, parse_mode="HTML")

# 2. Lệnh /dubao (Tín hiệu Dự Báo)
@bot.message_handler(commands=['dubao'])
def handle_dubao(message):
    text = message.text.strip()
    match = re.search(r'\b(\d{2})(\d{2})(\d{4})\b', text)
    
    if match:
        formatted_date = f"{match.group(1)}/{match.group(2)}/{match.group(3)}"
    else:
        from fetcher import get_now_vn
        formatted_date = get_now_vn().strftime("%d/%m/%Y")
        
    pred = get_xsmb_prediction(formatted_date)
    
    msg = f"🔮 <b>DỰ BÁO KẾT QUẢ XSMB NGÀY {pred['date']}</b> 🔮\n"
    msg += "-----------------------------------\n"
    msg += f"🎯 <b>Bạch Thủ Lô:</b> <code>{pred['bach_thu']}</code>\n"
    msg += f"👯 <b>Song Thủ Lô:</b> <code>{', '.join(pred['song_thu'])}</code>\n"
    msg += f"💥 <b>Xuyên 2 / Lô Xiên:</b> <code>{', '.join(pred['lo_xiu'])}</code>\n"
    msg += "-----------------------------------\n"
    msg += "⚠️ <i>Lưu ý: Dữ liệu dự báo chỉ mang tính chất tham khảo.</i>"
    
    bot.reply_to(message, msg, parse_mode="HTML")

# 3. Tra cứu Kết Quả theo Ngày
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
        msg += f"<i>(Nguồn: {data['source']})</i>\n"
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
        msg += f"🎲 <b>Lô về:</b> {', '.join([f'<code>{x}</code>' for x in sorted(list(set(data['loto'])))])}"
        
        bot.edit_message_text(msg, chat_id=status_msg.chat.id, message_id=status_msg.message_id, parse_mode="HTML")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending_updates=True)
