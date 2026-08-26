# ========== CHƯƠNG TRÌNH CHÍNH ==========
def main():
    print("🚀 Bot XSMB khởi động...")
    
    # Bước 1: Đọc dữ liệu đã lưu
    data = load_data()
    print(f"📂 Đã có {len(data['history'])} ngày dữ liệu")
    
    # Bước 2: Khởi động Flask
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(2)
    print("✅ Flask đã chạy")
    
    # Bước 3: GỬI NGAY LẦN ĐẦU ĐỂ KIỂM TRA
    print("📤 Đang gửi báo cáo kiểm tra...")
    new_result = fetch_xsmb_results()
    if new_result:
        data["history"].append(new_result)
        data["last_date"] = new_result["date"]
        save_data(data)
    
    pred = analyze_data(data)
    if pred:
        msg = f"""
🎯 *DỰ BÁO XSMB — {pred['date_next']}* — KIỂM TRA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Dữ liệu: {len(data['history'])} ngày | Cập nhật: {pred['generated_at']}

🏆 *TOP 3 LÔ NÓI TIẾP*
1️⃣ {pred['top3_loto'][0]['num']} | {pred['top3_loto'][0]['rate']}
2️⃣ {pred['top3_loto'][1]['num']} | {pred['top3_loto'][1]['rate']}
3️⃣ {pred['top3_loto'][2]['num']} | {pred['top3_loto'][2]['rate']}

🎲 *ĐẦU ĐỀ NÓI*
→ Đầu {pred['best_dau']['num']} | {pred['best_dau']['rate']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ *Chỉ tham khảo — Chơi có trách nhiệm!*
💾 *Dữ liệu đã lưu tự động*
"""
        send_telegram(msg)
        print("✅ Đã gửi tin kiểm tra thành công!")
    
    # Bước 4: Vòng lặp chính
    last_sent_date = datetime.now().strftime("%d/%m/%Y")
    
    while True:
        time.sleep(CHECK_INTERVAL)
        now = datetime.now()
        current_date = now.strftime("%d/%m/%Y")
        
        if data.get("last_date") != current_date:
            print(f"🔄 Đang lấy dữ liệu mới — {current_date}")
            new_result = fetch_xsmb_results()
            if new_result and new_result["date"] != data.get("last_date"):
                data["history"].append(new_result)
                data["last_date"] = new_result["date"]
                if len(data["history"]) > 90:
                    data["history"] = data["history"][-90:]
                save_data(data)
        
        if last_sent_date != current_date and len(data["history"]) >= 10:
            pred = analyze_data(data)
            if pred:
                # Gửi tin hàng ngày
                pass
