def generate_message():
    """Tạo tin nhắn báo cáo - ĐÃ BỎ PHẦN THÔNG BÁO TRẠNG THÁI"""
    now = get_vietnam_time()
    vietnam_date = now.strftime("%d/%m/%Y")
    vietnam_time = now.strftime("%H:%M:%S")
    weekday = now.weekday()
    hour = now.hour
    is_trading_hour = (weekday < 5) and (9 <= hour < 15)
    
    watch_list_str = ", ".join(WATCH_LIST[:3])
    if len(WATCH_LIST) > 3:
        watch_list_str += f" và {len(WATCH_LIST)-3} mã khác"
    
    message = f"🚀 BOT ĐÃ KHỞI ĐỘNG!\n"
    message += f"📅 Ngày giờ: {vietnam_date} {vietnam_time}\n"
    message += f"📊 Theo dõi: {watch_list_str}\n"
    message += f"💡 Cập nhật giá tự động từ vnstock\n\n"
    message += f"⏱️ Mở cửa: mỗi 5 phút kiểm tra\n"
    message += f"⏱️ Đóng cửa: mỗi 1 giờ gửi báo cáo\n"
    message += f"✅ Sẵn sàng!\n\n"
    message += "─" * 20 + "\n\n"
    
    # === ĐÃ BỎ: PHẦN THÔNG BÁO TRẠNG THÁI ===
    
    message += f"📊 BÁO CÁO CỔ PHIẾU\n"
    message += f"🕐 Thời gian: {vietnam_date} {vietnam_time} (VN)\n\n"
    
    stock_count = 0
    for symbol in WATCH_LIST:
        data = analyze_stock(symbol)
        if not data:
            continue
        
        stock_count += 1
        
        stock_info = "─" * 20 + "\n"
        stock_info += f"📊 {data['symbol']} – Giá: {format_currency(data['price'])} VND | {data['change_pct']:+.2f}%\n"
        stock_info += f"📡 Nguồn: 🔒 Giá phiên cuối (lưu lúc {data['source_date']} 15:00:00)\n"
        stock_info += f"📈 MA5: {format_currency(data['ma5'])} | MA10: {format_currency(data['ma10'])} | RSI: {data['rsi']}\n"
        stock_info += f"🛡️ Hỗ trợ: {format_currency(data['support'])} | Kháng cự: {format_currency(data['resistance'])}\n\n"
        
        stock_info += "🎯 KHUYẾN NGHỊ:\n"
        stock_info += f"⏸️ MUA: {data['mua_note']} — Giá hiện tại {format_currency(data['price'])} VND gần hỗ trợ\n"
        stock_info += f"⏸️ BÁN: {data['ban_note']} — Giá hiện tại {format_currency(data['price'])} VND gần kháng cự\n"
        
        if data['hold']:
            stock_info += f"🟢 NẮM GIỮ – {data['hold_note']}\n"
        else:
            stock_info += f"🟡 NẮM GIỮ – Chờ tín hiệu rõ hơn\n"
        
        stock_info += f"💰 Giá hiện tại: {format_currency(data['price'])} VND\n"
        stock_info += f"🎯 Mục tiêu bán: {format_currency(data['target_sell'])} VND\n"
        stock_info += f"🔴 Cắt lỗ dưới: {format_currency(data['stop_loss'])} VND\n\n"
        
        if len(message) + len(stock_info) < MAX_MESSAGE_LENGTH - 100:
            message += stock_info
        else:
            print(f"⚠️ Tin nhắn quá dài, dừng ở mã {symbol}")
            break
    
    message += f"📈 Tổng cộng: {stock_count}/{len(WATCH_LIST)} mã\n"
    message += "⚠️ Chỉ tham khảo — tự quyết định giao dịch!\n"
    
    return message
