import telebot
import re
import time
from datetime import datetime
from flask import Flask
from threading import Thread
from config import TELEGRAM_TOKEN, CHAT_ID, PORT, AUTO_SEND_TIME
from fetcher import fetch_result

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ========== FLASK — GIỮ SERVICE KHỎI NGỦ ==========
@app.route('/')
def home():
    return "✅ Bot XSMB — Đang hoạt động | Nguồn: XOSODAIPHAT + XOSO.com.vn", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# ========== LỆNH /START ==========
@bot.message_handler(commands=['start'])
def cmd_start(message):
    if str(message.chat.id) not in [CHAT_ID, CHAT_ID.replace('-100','')]:
        bot.send_message(message.chat.id, "❌ Không có quyền sử dụng bot này.")
        return
    bot.send_message(message.chat.id,
        "🤖 **BOT XSMB — LẤY KẾT QUẢ THỰC**\n"
        "📡 Nguồn: XOSODAIPHAT + XOSO.com.vn\n"
        "✅ Không tạo số giả | 💾 Lưu lịch sử | ⏰ Tự động 18:35\n\n"
        "📌 Gõ ngày: **DDMMYYYY** (VD: 24082026)"
    )

# ========== XỬ LÝ TIN NHẮN — NHẬP NGÀY ==========
@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    user_id = str(message.chat.id)
    text = message.text.strip()
    if user_id not in [CHAT_ID, CHAT_ID.replace('-100','')]:
        return
    if not re.match(r"^\d{8}$", text):
        bot.send_message(user_id, "⚠️ Định dạng sai! VD: **24082026** (DDMMYYYY)")
        return
    try:
        d, m, y = text[:2], text[2:4], text[4:8]
        date_str = f"{d}/{m}/{y}"
        datetime(int(y), int(m), int(d))
        bot.send_message(user_id, f"🔍 Đang lấy dữ liệu **{date_str}**...")
        result = fetch_result(date_str)
        if not result:
            bot.send_message(user_id,
                f"⚠️ **KHÔNG CÓ DỮ LIỆU NGÀY {date_str}**\n"
                "→ Nếu là hôm nay: Chờ sau 18:35\n"
                "→ Nếu là ngày trước: Nguồn tạm không truy cập được\n"
                "❌ **Bot KHÔNG tạo số giả** — thử lại sau nhé!"
            )
            return
        # Gửi kết quả
        reply = (
            f"📅 **KẾT QUẢ XSMB — {date_str}**\n"
            f"📊 Nguồn: {result['source']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏆 **Đặc Biệt:** `{result['special']}`\n"
            f"🥈 **Giải Nhất:** `{result['g1'] or '---'}`\n"
            f"🎯 **Lô về ({len(result['loto'])} số):** `{', '.join(result['loto'])}`\n\n"
            "⚠️ *Chỉ tham khảo — Chơi có trách nhiệm!*"
        )
        bot.send_message(user_id, reply, parse_mode="Markdown")
    except ValueError:
        bot.send_message(user_id, "❌ Ngày không hợp lệ! Kiểm tra lại nhé.")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        bot.send_message(user_id, "❌ Lỗi xử lý. Thử lại sau nhé.")

# ========== TỰ ĐỘNG GỬI 18:35 ==========
def auto_scheduler():
    last_sent = ""
    print("⏰ Lịch trình tự động 18:35 đã bật")
    while True:
        try:
            now = datetime.now()
            today = now.strftime("%d/%m/%Y")
            if now.hour == 18 and 35 <= now.minute <= 45 and last_sent != today:
                print(f"⏰ Đến giờ gửi tự động: {today}")
                result = fetch_result(today)
                if result:
                    reply = (
                        f"📢 **KẾT QUẢ TỰ ĐỘNG — {today}**\n"
                        f"🏆 Đặc Biệt: `{result['special']}`\n"
                        f"🥈 Giải Nhất: `{result['g1'] or '---'}`\n"
                        f"🎯 Lô về: `{', '.join(result['loto'])}`\n\n"
                        "⚠️ Chơi có trách nhiệm!"
                    )
                    bot.send_message(CHAT_ID, reply, parse_mode="Markdown")
                    last_sent = today
                    print(f"✅ Đã gửi tự động: {today}")
            time.sleep(30)
        except Exception as e:
            print(f"❌ Lỗi lịch trình: {e}")
            time.sleep(60)

# ========== KHỞI ĐỘNG — SỬA LỖI 409 ==========
if __name__ == "__main__":
    print("="*60)
    print("🚀 BOT XSMB — HOÀN CHỈNH V2.0 | SỬA LỖI 409")
    print("📡 Nguồn: XOSODAIPHAT + XOSO.com.vn")
    print("="*60)
    
    # Xóa webhook cũ — QUAN TRỌNG!
    bot.remove_webhook()
    print("🔄 Đã xóa webhook cũ")
    
    # Khởi động Flask
    Thread(target=run_flask, daemon=True).start()
    print("🌐 Flask server đã chạy")
    
    # Khởi động lịch trình
    Thread(target=auto_scheduler, daemon=True).start()
    print("⏰ Lịch trình 18:35 đã bật")
    
    print("✅ Bot sẵn sàng! Gõ DDMMYYYY để tra cứu.")
    print("="*60)
    
    # === CHỈ 1 LUỒNG → KHÔNG LỖI 409 ===
    while True:
        try:
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=60,
                allowed_updates=['message', 'callback_query']
            )
        except Exception as e:
            print(f"⚠️ Lỗi polling: {e} — Thử lại sau 10s...")
            time.sleep(10)
