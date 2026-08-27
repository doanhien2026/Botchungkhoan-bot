import telebot
import re
import time
from datetime import datetime
from flask import Flask
from threading import Thread
from config import TELEGRAM_TOKEN, CHAT_ID, PORT
from fetcher import get_xsmb_result, get_now_vn
from data_manager import get_all_dates

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@app.route('/')
def home():
    return "✅ Bot XSMB V7.2 — Đang hoạt động & Lưu dữ liệu tự động", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.chat.id
    print(f"📩 /start từ {user_id}")
    if str(user_id) != str(CHAT_ID) and str(user_id) != str(CHAT_ID).replace('-100', ''):
        bot.send_message(user_id, "❌ Bạn không có quyền sử dụng bot này.")
        return
    bot.send_message(user_id,
        "🤖 Bot XSMB — Lấy kết quả thực từ KETQUA.net & XOSO.COM.VN\n\n"
        "📌 Gõ ngày theo định dạng: DDMMYYYY\n"
        "Ví dụ: 22082026\n\n"
        "✅ Không tạo số giả — chỉ trả kết quả thực!\n"
        "✅ Tự động lưu dữ liệu vào file JSON"
    )

@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    user_id = message.chat.id
    text = message.text.strip()
    print(f"📩 Nhận tin từ {user_id}: {text}")
    
    if str(user_id) != str(CHAT_ID) and str(user_id) != str(CHAT_ID).replace('-100', ''):
        return
    
    if not re.match(r"^\d{8}$", text):
        bot.send_message(user_id,
            "⚠️ Định dạng không đúng!\n"
            "Vui lòng gõ ngày theo định dạng: DDMMYYYY\n"
            "Ví dụ: 22082026"
        )
        return
    
    try:
        d = text[0:2]
        m = text[2:4]
        y = text[4:8]
        date_str = f"{d}/{m}/{y}"
        
        bot.send_message(user_id, f"🔍 Đang lấy dữ liệu ngày {date_str}...")
        
        result = get_xsmb_result(date_str)
        
        if not result:
            bot.send_message(user_id,
                f"⚠️ KHÔNG CÓ DỮ LIỆU NGÀY {date_str}\n\n"
                "→ Kết quả có thể chưa cập nhật (trước 18:30)\n"
                "→ Hoặc ngày không hợp lệ\n"
                "→ Hoặc nguồn dữ liệu tạm thời không truy cập được\n\n"
                "❌ Bot KHÔNG tạo số giả — vui lòng thử lại sau!"
            )
            return
        
        special = result.get("special", "Không có")
        g1 = result.get("g1", "Không có")
        loto = result.get("loto", [])
        source = result.get("source", "Không rõ")
        
        reply = (
            f"📅 NGÀY: {date_str}\n"
            f"📊 Nguồn: {source}\n"
            f"💾 Đã lưu vào file dữ liệu\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏆 Đặc Biệt: {special}\n"
            f"🥈 Giải Nhất: {g1}\n"
            f"🎯 Lô về ({len(loto)} số):\n"
        )
        if loto:
            reply += ", ".join(loto)
        else:
            reply += "Không có dữ liệu lô."
        
        bot.send_message(user_id, reply)
        print(f"✅ Đã gửi kết quả: {date_str} | ĐB: {special}")
        
    except Exception as e:
        print(f"❌ Lỗi xử lý: {str(e)}")
        bot.send_message(user_id, "❌ Lỗi xử lý. Vui lòng kiểm tra định dạng DDMMYYYY.")

def auto_scheduler():
    last_send = None
    while True:
        try:
            now = get_now_vn()
            today = now.strftime("%d/%m/%Y")
            if now.hour == 18 and now.minute >= 35 and last_send != today:
                result = get_xsmb_result(today)
                if result:
                    reply = f"📊 KẾT QUẢ TỰ ĐỘNG NGÀY {today}\n"
                    reply += f"🏆 ĐB: {result['special']} | 🥈 G1: {result['g1']}\n"
                    reply += f"🎯 Lô: {', '.join(result['loto'])}"
                    bot.send_message(CHAT_ID, reply)
                last_send = today
            time.sleep(60)
        except Exception as e:
            print(f"❌ Lỗi lịch trình: {e}")
            time.sleep(60)

# === KHỞI ĐỘNG TOÀN BỘ HỆ THỐNG ===
if __name__ == '__main__':
    print("🚀 Bot XSMB V7.2 khởi động...")
    print(f"📂 Đã có {len(get_all_dates())} ngày dữ liệu")
    
    # Khởi động Flask
    Thread(target=run_flask, daemon=True).start()
    
    # Khởi động lịch trình tự động
    Thread(target=auto_scheduler, daemon=True).start()
    
    # Xóa webhook cũ
    bot.remove_webhook()
    
    print("✅ Bot sẵn sàng! Đang lắng nghe tin nhắn Telegram...")
    
    # === QUAN TRỌNG NHẤT: Bắt đầu lắng nghe ===
    bot.infinity_polling()
