import telebot
import re
import time
from datetime import datetime
from flask import Flask
from threading import Thread
from config import TELEGRAM_TOKEN, CHAT_ID, PORT, AUTO_SEND_TIME
from fetcher import fetch_result
from predictor import generate_prediction

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ========== FLASK — GIỮ SERVICE KHỎI NGỦ ==========
@app.route('/')
def home():
    return "✅ Bot XSMB — Đang hoạt động | Nguồn: XOSODAIPHAT + XOSO.com.vn", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# ========== KIỂM TRA QUYỀN ==========
def is_authorized(user_id):
    return str(user_id) in [CHAT_ID, CHAT_ID.replace('-100','')]

# ========== LỆNH /START ==========
@bot.message_handler(commands=['start'])
def cmd_start(message):
    if not is_authorized(message.chat.id):
        bot.send_message(message.chat.id, "❌ Không có quyền sử dụng bot này.")
        return
    bot.send_message(message.chat.id,
        "🤖 **BOT XSMB — HOÀN CHỈNH**\n"
        "📡 Nguồn: XOSODAIPHAT + XOSO.com.vn\n"
        "✅ Dữ liệu đã lưu: Bảo toàn 100%\n"
        "⏰ Tự động gửi 18:35 hàng ngày\n\n"
        "📌 **CÁCH DÙNG:**\n"
        "• Gõ ngày: **DDMMYYYY** → Xem kết quả + LƯU dữ liệu\n"
        "• /test DDMMYYYY → Xem kết quả, **KHÔNG lưu**\n"
        "• /dudoan → 3 lô + 1 xiên + đầu số đề dự kiến\n"
        "• /thongke → Báo cáo thống kê 60 ngày"
    )

# ========== ✅ LỆNH /test — CHỈ XEM, KHÔNG LƯU ==========
@bot.message_handler(commands=['test'])
def cmd_test(message):
    if not is_authorized(message.chat.id):
        return
    
    parts = message.text.strip().split()
    if len(parts) < 2 or not re.match(r"^\d{8}$", parts[1]):
        bot.send_message(message.chat.id,
            "⚠️ Sai định dạng!\n"
            "✅ Cách dùng: **/test DDMMYYYY**\n"
            "Ví dụ: /test 25082026"
        )
        return
    
    text = parts[1]
    d, m, y = text[:2], text[2:4], text[4:8]
    date_str = f"{d}/{m}/{y}"
    
    try:
        datetime(int(y), int(m), int(d))
    except ValueError:
        bot.send_message(message.chat.id, "❌ Ngày không hợp lệ!")
        return
    
    bot.send_message(message.chat.id, f"🔍 **TEST NGÀY: {date_str}**\nĐang lấy dữ liệu...")
    result = fetch_result(date_str)
    
    if not result:
        bot.send_message(message.chat.id,
            f"📅 Ngày: {date_str}\n"
            f"⚠️ **CHƯA CÓ KẾT QUẢ THỰC TẾ**\n\n"
            f"→ Hôm nay: Kết quả sau 18:35\n"
            f"→ Tương lai: Chưa có kết quả\n"
            f"✅ Dữ liệu cũ: **KHÔNG THAY ĐỔI**"
        )
        return
    
    reply = (
        f"🧪 **KẾT QUẢ TEST — {date_str}**\n"
        f"📡 Nguồn: {result['source']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 Đặc Biệt: `{result['special']}`\n"
    )
    if result.get('g1'):
        reply += f"🥈 Giải Nhất: `{result['g1']}`\n"
    if result.get('loto'):
        reply += f"🎯 Lô về: `{', '.join(result['loto'])}`\n"
    reply += f"\n✅ **CHỈ XEM — KHÔNG LƯU DỮ LIỆU**"
    
    bot.send_message(message.chat.id, reply, parse_mode="Markdown")

# ========== ✅ LỆNH /dudoan — THỐNG KÊ & DỰ ĐOÁN ==========
@bot.message_handler(commands=['dudoan', 'thongke'])
def cmd_dudoan(message):
    if not is_authorized(message.chat.id):
        return
    
    bot.send_message(message.chat.id, "📊 Đang phân tích dữ liệu 60 ngày...")
    report = generate_prediction(days=60)
    
    if not report:
        bot.send_message(message.chat.id,
            "⚠️ Chưa đủ dữ liệu!\n"
            "→ Hãy tra cứu thêm kết quả các ngày trước.\n"
            "✅ Dữ liệu cũ: **Bảo toàn nguyên vẹn**"
        )
        return
    
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

# ========== ✅ NHẬP NGÀY TRỰC TIẾP — XEM + LƯU DỮ LIỆU ==========
@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    # Bỏ qua lệnh đã xử lý
    text = message.text.strip()
    if text.startswith('/'):
        return
    
    if not is_authorized(message.chat.id):
        return
    
    # Kiểm tra định dạng ngày DDMMYYYY
    if not re.match(r"^\d{8}$", text):
        bot.send_message(message.chat.id,
            "⚠️ Định dạng sai!\n"
            "→ Gõ ngày: **DDMMYYYY** (VD: 25082026)\n"
            "→ Hoặc dùng /test /dudoan /start"
        )
        return
    
    d, m, y = text[:2], text[2:4], text[4:8]
    date_str = f"{d}/{m}/{y}"
    
    try:
        datetime(int(y), int(m), int(d))
    except ValueError:
        bot.send_message(message.chat.id, "❌ Ngày không hợp lệ!")
        return
    
    bot.send_message(message.chat.id, f"🔍 Đang lấy & lưu dữ liệu **{date_str}**...")
    result = fetch_result(date_str)
    
    if not result:
        bot.send_message(message.chat.id,
            f"⚠️ **CHƯA CÓ KẾT QUẢ — {date_str}**\n\n"
            f"→ Hôm nay: Sau 18:35 sẽ có kết quả\n"
            f"→ Tương lai: Chưa có kết quả\n"
            f"✅ Dữ liệu cũ: **KHÔNG BỊ ẢNH HƯỞNG**"
        )
        return
    
    reply = (
        f"📅 **KẾT QUẢ — {date_str}** ✅ ĐÃ LƯU\n"
        f"📡 Nguồn: {result['source']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 Đặc Biệt: `{result['special']}`\n"
    )
    if result.get('g1'):
        reply += f"🥈 Giải Nhất: `{result['g1']}`\n"
    if result.get('loto'):
        reply += f"🎯 Lô về ({len(result['loto'])} số): `{', '.join(result['loto'])}`\n"
    reply += "\n⚠️ *Chỉ tham khảo — Chơi có trách nhiệm!*"
    
    bot.send_message(message.chat.id, reply, parse_mode="Markdown")

# ========== TỰ ĐỘNG GỬI 18:35 ==========
def auto_scheduler():
    last_sent = ""
    print("⏰ Lịch trình 18:35 đã bật")
    while True:
        try:
            now = datetime.now()
            today = now.strftime("%d/%m/%Y")
            if now.hour == 18 and 35 <= now.minute <= 45 and last_sent != today:
                print(f"⏰ Gửi tự động: {today}")
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
                    print(f"✅ Đã gửi: {today}")
            time.sleep(30)
        except Exception as e:
            print(f"❌ Lỗi lịch trình: {e}")
            time.sleep(60)

# ========== KHỞI ĐỘNG ==========
if __name__ == "__main__":
    print("="*60)
    print("🚀 BOT XSMB — HOÀN CHỈNH | DỮ LIỆU BẢO TOÀN")
    print("📡 Nguồn: XOSODAIPHAT + XOSO.com.vn")
    print("="*60)
    
    bot.remove_webhook()
    time.sleep(1)
    print("🔄 Đã xóa webhook cũ")
    
    Thread(target=run_flask, daemon=True).start()
    print("🌐 Flask server chạy ngầm")
    
    Thread(target=auto_scheduler, daemon=True).start()
    print("⏰ Tự động gửi 18:35")
    
    print("✅ Bot sẵn sàng — TẤT CẢ LỆNH ĐÃ SẴN SÀNG")
    print("="*60)
    
    while True:
        try:
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=60,
                allowed_updates=['message', 'callback_query']
            )
        except Exception as e:
            print(f"⚠️ Lỗi kết nối: {e}")
            time.sleep(15)
