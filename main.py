# Trong hàm lookup — thay phần:
if data:
    # ... hiển thị kết quả
else:
    # ✅ Thay vì dữ liệu giả → báo lỗi rõ ràng
    bot.edit_message_text(
        f"❌ <b>KHÔNG TÌM THẤY DỮ LIỆU XSMB NGÀY {d}!</b>\n"
        "• Kết quả có thể chưa cập nhật (chưa đến 18:30)\n"
        "• Hoặc nguồn dữ liệu tạm thời không truy cập được\n"
        "🔄 Vui lòng thử lại sau!",
        chat_id=status.chat.id,
        message_id=status.message_id,
        parse_mode="HTML"
    )
