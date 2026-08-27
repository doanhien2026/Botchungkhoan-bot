if __name__ == "__main__":
    # Chạy Web server Flask
    threading.Thread(target=run_server, daemon=True).start()
    
    # Chạy luồng tự động gửi tin nhắn hàng ngày
    threading.Thread(target=auto_send_daily, daemon=True).start()
    
    # Dọn dẹp session cũ để tránh lỗi 409 Conflict
    try:
        print("🔄 Đang ngắt kết nối session cũ từ Telegram...")
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(5)  # Chờ 5 giây để Telegram nhả kết nối cũ hoàn toàn
    except Exception as e:
        print(f"⚠️ Lỗi xóa Webhook: {e}")

    # Vòng lặp Polling tự động khôi phục nếu mất kết nối
    while True:
        try:
            print("🚀 Bot bắt đầu nhận tin nhắn (Polling)...")
            bot.polling(non_stop=True, interval=1, timeout=30)
        except Exception as e:
            print(f"⚠️ Polling ngắt kết nối ({e}), đang thử lại sau 5s...")
            time.sleep(5)
