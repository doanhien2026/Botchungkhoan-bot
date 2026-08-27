# ========== ✅ LỆNH TEST KẾT QUẢ NGÀY D — KHÔNG GHI ĐỔI DỮ LIỆU ==========
@bot.message_handler(commands=['test'])
def cmd_test_result(message):
    user_id = str(message.chat.id)
    if user_id not in [CHAT_ID, CHAT_ID.replace('-100','')]:
        return
    
    # Lấy tham số sau lệnh /test
    parts = message.text.strip().split()
    if len(parts) < 2 or not re.match(r"^\d{8}$", parts[1]):
        bot.send_message(user_id,
            "⚠️ Định dạng lệnh TEST sai!\n"
            "✅ Cách dùng: **/test DDMMYYYY**\n"
            "Ví dụ: /test 25082026 → Kiểm tra kết quả ngày 25/08/2026"
        )
        return
    
    text = parts[1]
    d, m, y = text[:2], text[2:4], text[4:8]
    date_str = f"{d}/{m}/{y}"
    
    try:
        datetime(int(y), int(m), int(d))
    except ValueError:
        bot.send_message(user_id, "❌ Ngày không hợp lệ! Kiểm tra lại nhé.")
        return
    
    bot.send_message(user_id, f"🔍 **TEST KẾT QUẢ NGÀY: {date_str}**\nĐang lấy dữ liệu...")
    
    # === LẤY KẾT QUẢ — CHỈ ĐỌC, KHÔNG GHI ĐỔI DỮ LIỆU ===
    result = fetch_result(date_str)
    
    if not result:
        bot.send_message(user_id,
            f"📅 Ngày: {date_str}\n"
            f"📡 Nguồn: Đang kiểm tra...\n"
            f"⚠️ **KẾT QUẢ: CHƯA CÓ / KHÔNG TỒN TẠI**\n\n"
            f"→ Nếu là hôm nay: Kết quả sau 18:35\n"
            f"→ Nếu là tương lai: Chưa có kết quả\n"
            f"→ Nếu là quá khứ: Nguồn không có dữ liệu\n\n"
            f"✅ Dữ liệu đã lưu: **KHÔNG BỊ THAY ĐỔI**"
        )
        return
    
    # === HIỂN THỊ KẾT QUẢ TEST ===
    reply = (
        f"🧪 **KẾT QUẢ TEST — NGÀY {date_str}**\n"
        f"📡 Nguồn: {result['source']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 Đặc Biệt: `{result['special']}`\n"
    )
    if result.get('g1'):
        reply += f"🥈 Giải Nhất: `{result['g1']}`\n"
    if result.get('loto'):
        reply += f"🎯 Lô về ({len(result['loto'])} số): `{', '.join(result['loto'])}`\n"
    reply += f"\n✅ **TEST HOÀN TẤT — DỮ LIỆU GỐC KHÔNG ĐỔI**"
    
    bot.send_message(user_id, reply, parse_mode="Markdown")
