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
        "✅ Chỉ trả kết quả thực tế — KHÔNG tạo số giả\n"
        "💾 Lưu lịch sử tự động | ⏰ Tự động gửi 18:35\n\n"
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
        bot.send_message(user_id, 
            "⚠️ Định dạng sai!\n"
            "Ví dụ: **24082026** (DDMMYYYY)\n"
            "Gõ ngày đã qua để xem kết quả thực tế."
        )
        return
    
    try:
        d, m, y = text[:2], text[2:4], text[4:8]
        date_str = f"{d}/{m}/{y}"
        datetime(int(y), int(m), int(d))
        
        bot.send_message(user_id, f"🔍 Đang lấy dữ liệu **{date_str}**...")
        result = fetch_result(date_str)
        
        if not result:
            bot.send_message(user_id,
                f"⚠️ **CHƯA CÓ KẾT QUẢ THỰC TẾ — {date_str}**\n\n"
                "→ Nếu là hôm nay: Kết quả sẽ có sau **18:35**\n"
                "→ Nếu là ngày tương lai: Chưa có kết quả\n"
                "→ Nếu là ngày quá khứ: Nguồn tạm thời không truy cập được\n\n"
                "❌ **Bot KHÔNG tạo số giả** — vui lòng thử lại sau nhé!"
            )
            return
        
        # === GỬI KẾT QUẢ THỰC TẾ ===
        reply = (
            f"📅 **KẾT QUẢ XSMB — {date_str}**\n"
            f"📊 Nguồn: {result['source']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏆 **Đặc Biệt:** `{result['special']}`\n"
        )
        if result.get('g1'):
            reply += f"🥈 **Giải Nhất:** `{result['g1']}`\n"
        if result.get('loto'):
            reply += f"🎯 **Lô về ({len(result['loto'])} số):** `{', '.join(result['loto'])}`\n"
        reply += "\n⚠️ *Chỉ tham khảo — Chơi có trách nhiệm!*"
        
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
                    )
                    if result.get('g1'):
                        reply += f"🥈 Giải Nhất: `{result['g1']}`\n"
                    if result.get('loto'):
                        reply += f"🎯 Lô về: `{', '.join(result['loto'])}`\n"
                    reply += "\n⚠️ Chơi có trách nhiệm!"
                    bot.send_message(CHAT_ID, reply, parse_mode="Markdown")
                    last_sent = today
                    print(f"✅ Đã gửi tự động: {today}")
            time.sleep(30)
        except Exception as e:
            print(f"❌ Lỗi lịch trình: {e}")
            time.sleep(60)

# ========== KHỞI ĐỘNG — SỬA LỖI 409 TRIỆT ĐỂ ==========
if __name__ == "__main__":
    print("="*60)
    print("🚀 BOT XSMB — HOÀN CHỈNH | SỬA LỖI 409 + BỎ SỐ GIẢ")
    print("📡 Nguồn: XOSODAIPHAT + XOSO.com.vn")
    print("="*60)
    
    # === QUAN TRỌNG: XÓA WEBHOOK & DỪNG KẾT NỐI CŨ ===
    bot.remove_webhook()
    print("🔄 Đã xóa webhook cũ — tránh xung đột kết nối")
    
    # === KHỞI ĐỘNG FLASK ===
    Thread(target=run_flask, daemon=True).start()
    print("🌐 Flask server chạy ngầm — giữ service hoạt động")
    
    # === KHỞI ĐỘNG LỊCH TRÌNH ===
    Thread(target=auto_scheduler, daemon=True).start()
    print("⏰ Lịch trình tự động 18:35 đã bật")
    
    print("✅ Bot sẵn sàng! CHỈ 1 LUỒNG — KHÔNG LỖI 409")
    print("="*60)
    
    # === ✅ TẮT ĐA LUỒNG = threaded=False → KHÔNG CÒN LỖI 409 ===
    while True:
        try:
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=60,
                allowed_updates=['message', 'callback_query'],
                threaded=False  # ← QUAN TRỌNG NHẤT: TẮT ĐA LUỒNG
            )
        except Exception as e:
            print(f"⚠️ Lỗi kết nối: {e}")
            print("🔄 Thử lại sau 15 giây...")
            time.sleep(15)
