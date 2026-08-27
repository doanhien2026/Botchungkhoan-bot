# Sửa đoạn khởi chạy bot polling cũ thành đoạn này:
def run_bot_safe():
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ Lỗi Polling (Tự kết nối lại sau 5s): {e}")
            time.sleep(5)

threading.Thread(target=run_bot_safe, daemon=True).start()
