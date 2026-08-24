import os
import time
import schedule
import requests
from datetime import datetime

# ========== CẤU HÌNH BOT XSMB — ✅ ĐÃ ĐIỀN SẴN, KHÔNG CẦN SỬA ==========
TELEGRAM_TOKEN = "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0"
CHAT_ID = "1030583610"

# Theo dõi trạng thái để không gửi trùng lặp
status_sent = ""

# ========== HÀM GỬI TIN NHẮN TELEGRAM ==========
def send_xsmb(message, max_retries=5):
    for attempt in range(max_retries):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 200:
                print(f"✅ [BOT XSMB] Đã gửi tin thành công")
                return response.json()
            else:
                print(f"⚠️ Lỗi {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Lỗi kết nối (lần {attempt+1}): {e}")
            time.sleep(3)
    print(f"❌ Thất bại sau {max_retries} lần thử")
    return None

# ========== HÀM LẤY DỮ LIỆU XSMB ==========
def download_xsmb_data():
    try:
        url = "https://xsmb.com.vn/so-ket-qua-xsmb-60-ngay"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ Không tải được dữ liệu: {e}")
        return None

# ========== PHÂN TÍCH & TÍNH TÍN HIỆU ==========
def parse_and_calculate(html):
    import re
    from collections import Counter
    
    if not html:
        return None
    
    # Lấy tất cả số 2 chữ số
    numbers = re.findall(r"\b\d{2}\b", html)
    if not numbers:
        return None
    
    # Đếm tần suất xuất hiện
    freq = Counter(numbers)
    # Top 3 lô xuất hiện nhiều nhất
    top3_loto = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:3]
    # Đầu đề xuất hiện nhiều nhất
    dau_counts = Counter([n[0] for n in numbers])
    best_dau = sorted(dau_counts.items(), key=lambda x: x[1], reverse=True)[0]
    
    return {
        "loto": [n[0] for n in top3_loto],
        "dau": best_dau[0],
        "date": datetime.now().strftime("%d/%m/%Y")
    }

# ========== TẠO TÍN HIỆU & GỬI ==========
def generate_signal():
    global status_sent
    
    html = download_xsmb_data()
    pred = parse_and_calculate(html)
    
    if not pred:
        send_xsmb("⚠️ Không lấy được dữ liệu XSMB, thử lại sau...")
        return
    
    # Tạo thông báo định dạng đẹp
    message = f"""
🔮 *TÍN HIỆU XSMB D+1*

📅 Ngày dự báo: *{pred['date']}*

━━━━━━━━━━━━━━━━

🔥 *3 LÔ RƠI*

1️⃣ *{pred['loto'][0]}*
2️⃣ *{pred['loto'][1]}*
3️⃣ *{pred['loto'][2]}*

━━━━━━━━━━━━━━━━

🎲 *ĐẦU ĐỀ*

*Đầu {pred['dau']}*

━━━━━━━━━━━━━━━━

⚠️ *Chỉ tham khảo - không đảm bảo trúng*
🎲 *Chơi có trách nhiệm*
"""
    
    # Chỉ gửi nếu tín hiệu thay đổi (tránh gửi trùng)
    current_signal = f"{pred['loto']}-{pred['dau']}"
    if current_signal != status_sent:
        send_xsmb(message)
        status_sent = current_signal
        print(f"✅ Đã gửi tín hiệu mới: {status_sent}")
    else:
        print(f"⏭ Tín hiệu không đổi, bỏ qua gửi")

# ========== CHƯƠNG TRÌNH CHÍNH ==========
def main():
    # Kiểm tra cấu hình
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Thiếu TOKEN hoặc CHAT_ID")
        return
    
    # Tin nhắn khởi động
    send_xsmb("🤖 *XSMB BOT ĐÃ ONLINE*\n\n✅ Đã kết nối thành công\n⏰ Tự động cập nhật mỗi giờ\n⚠️ Chỉ tham khảo - không đảm bảo trúng")
    
    # Lên lịch: mỗi giờ chạy 1 lần
    schedule.every(1).hours.do(generate_signal)
    
    print("🚀 BOT ĐANG CHẠY...")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
