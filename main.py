import os
import re
import time
from datetime import datetime
from flask import Flask
from threading import Thread
import telebot
from config import TELEGRAM_TOKEN, CHAT_ID, PORT
from fetcher import get_xsmb_result, get_xsmb_prediction, get_now_vn

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)
print(f"✅ Token OK | Gửi đến: {CHAT_ID}")

@app.route('/')
def home():
    return "✅ Bot XSMB Đang hoạt động!", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# === GỬI BÁO CÁO TỰ ĐỘNG ===
def send_auto_report():
    today_str = get_now_vn().strftime("%d/%m/%Y")
    data = get_xsmb_result(today_str)
    if not data:
        bot.send_message(CHAT_ID, f"⚠️ Chưa lấy được dữ liệu {today_str}")
        return
    pred = get_xsmb_prediction(today_str)
    
    msg = f"📊 <b>KẾT QUẢ & DỰ BÁO XSMB — {today_str}</b>\n"
    msg += f"<i>Nguồn: {data.get('source', 'Không xác định')}</i>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🔴 <b>Đặc Biệt:</b> <code>{data['special']}</code>\n"
    msg += f"🥇 <b>Giải Nhất:</b> <code>{data['g1']}</code>\n"
    if 'g2' in data and data['g2']:
        msg += f"🥈 <b>Giải Nhì:</b> {', '.join(f'<code>{x}</code>' for x in data['g2'])}\n"
    if 'g3' in data and data['g3']:
        msg += f"🥉 <b>Giải Ba:</b> {', '.join(f'<code>{x}</code>' for x in data['g3'])}\n"
    if 'loto' in data and data['loto']:
        msg += f"🎲 <b>Lô về:</b> {', '.join(f'<code>{x}</code>' for x in sorted(set(data['loto'])))}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🔮 <b>DỰ BÁO</b>\n"
    msg += f"🎯 Bạch Thủ: <code>{pred['bach_thu']}</code>\n"
    msg += f"👯 Song Thủ: <code>{', '.join(pred['song_thu'])}</code>\n"
    msg += f"💥 Lô Xiên: <code>{', '.join(pred['lo_xiu'])}</code>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "<i>⚠️ Chỉ tham khảo — Chơi có trách nhiệm!</i>"
    
    bot.send_message(CHAT_ID, msg, parse_mode="HTML")
    print(f"✅ Đã gửi báo cáo: {today_str}")

# === LỊCH TRÌNH 18:35 ===
def auto_scheduler():
    last_send = None
    while True:
        try:
            now = get_now_vn()
            today = now.strftime("%d/%m/%Y")
            if now.hour == 18 and now.minute >= 35 and last_send != today:
                send_auto_report()
                last_send = today
            time.sleep(60)
        except Exception as e:
            print(f"⚠️ Lỗi: {e}")
            time.sleep(60)

# === LỆNH BOT ===
@bot.message_handler(commands=['start', 'help'])
def welcome(msg):
    bot.reply_to(msg, "🤖 <b>BOT XSMB</b>\n• Nhập ngày: VD <code>27082026</code>\n• /dubao → Dự báo\n• Tự gửi 18:35 lên kênh!", parse_mode="HTML")

@bot.message_handler(commands=['dubao'])
def dubao(msg):
    m = re.search(r'\b(\d{2})(\d{2})(\d{4})\b', msg.text)
    d = f"{m.group(1)}/{m.group(2)}/{m.group(3)}" if m else get_now_vn().strftime("%d/%m/%Y")
    p = get_xsmb_prediction(d)
    bot.reply_to(msg, f"🔮 <b>DỰ BÁO {p['date']}</b>\n🎯 Bạch Thủ: <code>{p['bach_thu']}</code>\n👯 Song Thủ: <code>{', '.join(p['song_thu'])}</code>\n💥 Lô Xiên: <code>{', '.join(p['lo_xiu'])}</code>", parse_mode="HTML")

@bot.message_handler(func=lambda m: True)
def lookup(msg):
    m = re.search(r'\b(\d{2})(\d{2})(\d{4})\b', msg.text)
    if not m:
        bot.reply_to(msg, "⚠️ Nhập ngày dạng: <code>27082026</code>", parse_mode="HTML")
        return
    d = f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
    status = bot.reply_to(msg, f"🔄 Đang lấy {d}...", parse_mode="HTML")
    data = get_xsmb_result(d)
    if data:
        reply = f"📉 <b>KẾT QUẢ {data['date']}</b>\n<i>Nguồn: {data['source']}</i>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔴 Đặc Biệt: <code>{data['special']}</code>\n🥇 Giải Nhất: <code>{data['g1']}</code>"
        if 'g2' in data and data['g2']: reply += f"\n🥈 Giải Nhì: {', '.join(f'<code>{x}</code>' for x in data['g2'])}"
        if 'g3' in data and data['g3']: reply += f"\n🥉 Giải Ba: {', '.join(f'<code>{x}</code>' for x in data['g3'])}"
        if 'loto' in data and data['loto']: reply += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🎲 Lô về: {', '.join(f'<code>{x}</code>' for x in sorted(set(data['loto'])))}"
        bot.edit_message_text(reply, chat_id=status.chat.id, message_id=status.message_id, parse_mode="HTML")
    else:
        bot.edit_message_text("❌ Không lấy được dữ liệu!", chat_id=status.chat.id, message_id=status.message_id, parse_mode="HTML")

# === KHỞI ĐỘNG ===
if __name__ == '__main__':
    print("🚀 BOT KHỞI ĐỘNG...")
    Thread(target=run_flask, daemon=True).start()
    Thread(target=auto_scheduler, daemon=True).start()
    bot.remove_webhook()
    print("✅ Bot sẵn sàng!")
    # ✅ ĐÃ XÓA skip_pending_updates — KHÔNG CÒN LỖI NỮA!
    bot.infinity_polling()
