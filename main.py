import logging
import os
import re
from datetime import datetime

from telegram import Update, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

from config import BOT_TOKEN, CHAT_ID
from fetcher import get_xsmb_result

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    logger.info(f"User {user_id} /start")

    if CHAT_ID and str(user_id) != str(CHAT_ID):
        update.message.reply_text("❌ Bạn không có quyền sử dụng bot này.")
        return

    update.message.reply_text(
        "🤖 Bot Dự Báo Kết Quả XSMB\n\n"
        "Gõ ngày cần xem theo định dạng:\n"
        "DDMMYYYY → ví dụ: 22082026\n\n"
        "Bot sẽ lấy kết quả thực từ KETQUA.net.\n"
        "Nếu chưa có dữ liệu sẽ báo rõ, không tạo số giả."
    )


def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.effective_message.text.strip()

    logger.info(f"Nhận tin từ {user_id}: {text}")

    if CHAT_ID and str(user_id) != str(CHAT_ID):
        update.message.reply_text("❌ Bạn không có quyền sử dụng bot này.")
        return

    if not re.match(r"^\d{8}$", text):
        update.message.reply_text(
            "⚠️ Định dạng ngày không đúng.\n"
            "Vui lòng gõ ngày theo định dạng DDMMYYYY.\n"
            "Ví dụ: 22082026"
        )
        return

    try:
        d = text[0:2]
        m = text[2:4]
        y = text[4:8]

        date_obj = datetime(int(y), int(m), int(d))
        date_str = date_obj.strftime("%d/%m/%Y")

        update.message.reply_text(f"🔍 Đang tìm dữ liệu ngày {date_str}...")

        result = get_xsmb_result(date_str)

        if not result:
            update.message.reply_text(
                f"⚠️ KHÔNG TÌM THẤY DỮ LIỆU NGÀY {date_str}\n\n"
                "→ Kết quả có thể chưa cập nhật (trước 18:30)\n"
                "→ Hoặc ngày không hợp lệ\n"
                "→ Hoặc nguồn dữ liệu tạm thời không truy cập được\n\n"
                "Vui lòng thử lại sau."
            )
            return

        special = result.get("special", "Không có")
        g1 = result.get("g1", "Không có")
        loto = result.get("loto", [])
        source = result.get("source", "Không rõ nguồn")

        reply = (
            f"📅 NGÀY: {date_str}\n"
            f"📊 Nguồn: {source}\n\n"
            f"🏆 Đặc Biệt: {special}\n"
            f"🥈 Giải Nhất: {g1}\n\n"
            f"🎯 Lô về ({len(loto)} số):\n"
        )

        if loto:
            reply += ", ".join(loto)
        else:
            reply += "Không có dữ liệu lô."

        update.message.reply_text(reply, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Lỗi xử lý ngày: {str(e)}")
        update.message.reply_text(
            "❌ Lỗi xử lý ngày. Vui lòng kiểm tra lại định dạng DDMMYYYY."
        )


def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Update {update} caused error {context.error}")


def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN chưa được đặt.")
        return

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_error_handler(error_handler)

    logger.info("Bot đang chạy...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
