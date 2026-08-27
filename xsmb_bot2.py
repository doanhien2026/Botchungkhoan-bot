import telebot
import re
import time
from datetime import datetime
from flask import Flask
from threading import Thread
from config import TELEGRAM_TOKEN, CHAT_ID, PORT
from fetcher import get_xsmb_result, get_now_vn
from data_manager import get_all_dates

# === KHỞI TẠO ===
app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# === FLASK ROUTE ===
@app.route('/')
def home():
    return "✅ Bot XSMB V7.4 — Đã sửa lỗi 409 | Lấy dữ liệu KETQUA.net", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# === LỆNH /START ===
@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.chat.id
    print(f"📩 /start từ {user_id}")
    
    allowed_ids = [str(CHAT_ID), str(CHAT_ID).replace('-100', '')]
    if str(user_id) not in allowed_ids:
        bot.send_message(user_id, "❌ Bạn không có quyền sử dụng bot này.")
        return
    
    bot.send_message(user_id,
        "🤖 **BOT XSMB — LẤY KẾT QUẢ THỰC**\n"
        "📡 Nguồn: KETQUA.net\n"
        "✅ Không tạo số giả — chỉ trả kết quả thực!\n"
        "💾 Tự động lưu lịch sử\n"
        "⏰ Tự động gửi 18:35 hàng ngày\n\n"
        "📌 Gõ ngày: **DDMMYYYY**\n"
        "Ví dụ: 26082026"
    )

# === XỬ LÝ TIN NHẮN ===
@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    user_id = message.chat.id
    text = message.text.strip()
    print(f"📩 [{user_id}] Nhận: {text}")
    
    allowed_ids = [str(CHAT_ID), str(CHAT_ID).replace('-100', '')]
    if str(user_id) not in allowed_ids:
        return
    
    if not re.match(r"^\d{8}$", text):
        bot.send_message(user_id,
            "⚠️ **Định dạng không đúng!**\n"
            "Vui lòng gõ ngày theo định dạng: **DDMMYYYY**\n"
            "Ví dụ: 26082026"
        )
        return
    
    try:
        d = text[0:2]
        m = text[2:4]
        y = text[4:8]
        date_str = f"{d}/{m}/{y}"
        
        datetime(int(y), int(m), int(d))
        
        bot.send_message(user_id, f"🔍 Đang lấy dữ liệu ngày **{date_str}** từ KETQUA.net...")
        
        result = get_xsmb_result(date_str)
        
        if not result:
            bot.send_message(user_id,
                f"⚠️ **KHÔNG CÓ DỮ LIỆU NGÀY {date_str}**\n\n"
                "→ Kết quả có thể **chưa cập nhật** (trước 18:35)\n"
                "→ Hoặc ngày không tồn tại\n"
                "→ Hoặc nguồn dữ liệu tạm thời không truy cập được\n\n"
                "❌ **Bot KHÔNG tạo số giả** — vui lòng thử lại sau 18:35!"
            )
            return
        
        special = result.get("special", "")
        g1 = result.get("g1", "")
        loto = result.get("loto", [])
        source = result.get("source", "KETQUA.net")
        
        reply = (
            f"📅 **KẾT QUẢ XSMB — {date_str}**\n"
            f"📊 Nguồn: {source}\n"
            f"💾 Đã lưu vào dữ liệu\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏆 **Giải Đặc Biệt:** `{special}`\n"
            f"🥈 **Giải Nhất:** `{g1}`\n"
            f"🎯 **Lô về ({len(loto)} số):**\n"
        )
        
        if loto:
            reply += f"`{', '.join(loto)}`"
        else:
            reply += "Không có dữ liệu lô."
        
        reply += "\n\n⚠️ *Chỉ tham khảo — Chơi có trách nhiệm!*"
        
        bot.send_message(user_id, reply, parse_mode="Markdown")
        print(f"✅ Đã gửi kết quả: {date_str} | ĐB: {special} | Lô: {len(loto)} số")
        
    except ValueError:
        bot.send_message(user_id, "❌ Ngày không hợp lệ! Vui lòng kiểm tra lại.")
    except Exception as e:
        print(f"❌ Lỗi xử lý: {str(e)}")
        bot.send_message(user_id, "❌ Lỗi xử lý. Vui lòng thử lại sau.")

# === TỰ ĐỘNG GỬI KẾT QUẢ MỖI NGÀY 18:35 ===
def auto_scheduler():
    last_date_sent = ""
    print("⏰ Lịch trình tự động đã bật — Gửi kết quả lúc 18:35 hàng ngày")
    
    while True:
        try:
            now = get_now_vn()
            today_str = now.strftime("%d/%m/%Y")
            
            if now.hour == 18 and 35 <= now.minute <= 45 and last_date_sent != today_str:
                print(f"⏰ Đến giờ tự động gửi kết quả ngày {today_str}")
                
                result = get_xsmb_result(today_str)
                if result:
                    reply = (
                        f"📢 **KẾT QUẢ TỰ ĐỘNG — {today_str}**\n"
                        f"🏆 Đặc Biệt: `{result['special']}`\n"
                        f"🥈 Giải Nhất: `{result['g1']}`\n"
                        f"🎯 Lô về ({len(result['loto'])} số): `{', '.join(result['loto'])}`\n\n"
                        "⚠️ Chỉ tham khảo — Chơi có trách nhiệm!"
                    )
                    bot.send_message(CHAT_ID, reply, parse_mode="Markdown")
                    last_date_sent = today_str
                    print(f"✅ Đã gửi tự động: {today_str}")
                else:
                    print(f"⚠️ Chưa có dữ liệu ngày {today_str} — bỏ qua gửi tự động")
            
            time.sleep(30)
            
        except Exception as e:
            print(f"❌ Lỗi lịch trình: {e}")
            time.sleep(60)

# === KHỞI ĐỘNG TOÀN BỘ HỆ THỐNG — ĐÃ SỬA LỖI 409 ===
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 BOT XSMB — PHIÊN BẢN V7.4 (SỬA LỖI 409)")
    print("📡 Nguồn dữ liệu: KETQUA.net")
    print("✅ Không tạo số giả | Lưu lịch sử | Tự động 18:35")
    print("=" * 60)
    print(f"📂 Đã có {len(get_all_dates())} ngày dữ liệu trong kho")
    
    # XÓA WEBHOOK CŨ — TRÁNH XUNG ĐỘT
    bot.remove_webhook()
    print("🔄 Đã xóa webhook cũ")
    
    # KHỞI ĐỘNG FLASK
    Thread(target=run_flask, daemon=True).start()
    print("🌐 Flask web server đã chạy")
    
    # KHỞI ĐỘNG LỊCH TRÌNH
    Thread(target=auto_scheduler, daemon=True).start()
    print("⏰ Lịch trình tự động đã bật — Gửi kết quả lúc 18:35 hàng ngày")
    
    print("✅ Bot đã sẵn sàng! Đang lắng nghe tin nhắn Telegram...")
    print("=" * 60)
    
    # === QUAN TRỌNG: CHỈ 1 LUỒNG → KHÔNG LỖI 409 ===
    try:
        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=60,
            allowed_updates=['message', 'callback_query']
        )
    except Exception as e:
        print(f"⚠️ Lỗi polling: {e} — Đang thử lại sau 10 giây...")
        time.sleep(10)
        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=60,
            allowed_updates=['message', 'callback_query']
        )
