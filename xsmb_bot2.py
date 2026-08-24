import os
import time
import schedule
import requests
from datetime import datetime
from dotenv import load_dotenv

# ========== CẤU HÌNH BOT XSMB ==========
load_dotenv()

XSMB_TELEGRAM_TOKEN = os.getenv("XSMB_TELEGRAM_TOKEN", "")
XSMB_CHAT_ID = os.getenv("XSMB_CHAT_ID", "")

# Kiểm tra token và chat_id lúc khởi động
if not XSMB_TELEGRAM_TOKEN or not XSMB_CHAT_ID:
    print("❌ LỖI: Thiếu XSMB_TELEGRAM_TOKEN hoặc XSMB_CHAT_ID trong file .env")
    print("⚠️  Vui lòng kiểm tra file .env của bạn")
    print("📋 Cần có:")
    print("   XSMB_TELEGRAM_TOKEN=your_bot_token")
    print("   XSMB_CHAT_ID=your_chat_id")
    exit(1)

# Biến theo dõi trạng thái để không gửi trùng lặp
last_status_sent = ""
# ==========================================

# === HÀM GỬI TIN RIÊNG CHO BOT XSMB ===
def send_xsmb(message, max_retries=5):
    for attempt in range(max_retries):
        try:
            url = f"https://api.telegram.org/bot{XSMB_TELEGRAM_TOKEN}/sendMessage"
            data = {
                "chat_id": XSMB_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            response = requests.post(url, data=data, timeout=15)
            
            if response.status_code == 200:
                print(f"✅ [BOT XSMB] Đã gửi tin thành công")
                return response.json()
            else:
                error_msg = response.text
                print(f"⚠️  [BOT XSMB] Lỗi HTTP {response.status_code}: {error_msg}")
                
                # Nếu token hoặc chat_id sai
                if response.status_code == 401:
                    print("❌ [BOT XSMB] Token không hợp lệ! Kiểm tra XSMB_TELEGRAM_TOKEN")
                    return None
                elif response.status_code == 400:
                    print("❌ [BOT XSMB] Chat ID không hợp lệ! Kiểm tra XSMB_CHAT_ID")
                    return None
                    
        except requests.exceptions.Timeout:
            print(f"⚠️  [BOT XSMB] Timeout lần {attempt+1}: Kết nối quá lâu")
            if attempt < max_retries - 1:
                time.sleep(5)
        except requests.exceptions.ConnectionError:
            print(f"⚠️  [BOT XSMB] Lỗi kết nối lần {attempt+1}: Không thể kết nối tới API Telegram")
            if attempt < max_retries - 1:
                time.sleep(5)
        except Exception as e:
            print(f"⚠️  [BOT XSMB] Lỗi lần {attempt+1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    
    print("❌ [BOT XSMB] Gửi thất bại sau 5 lần thử")
    return None

def send_status_if_changed(current_status):
    """Chỉ gửi khi trạng thái THAY ĐỔI — tránh gửi trùng lặp"""
    global last_status_sent
    if current_status != last_status_sent:
        send_xsmb(current_status)
        last_status_sent = current_status
        print("✅ [BOT XSMB] Trạng thái thay đổi — Đã gửi tin mới")
    else:
        print("⏭️  [BOT XSMB] Trạng thái không đổi — Bỏ qua gửi")

def get_current_status():
    """Tạo tin trạng thái hiện tại"""
    now = datetime.now()
    vietnam_time = now.strftime("%d/%m/%Y %H:%M:%S")
    
    status = f"""🤖 XSMB BOT ONLINE
🕐 Cập nhật: {vietnam_time}
🔒 CHẾ ĐỘ KHÓA TÍN HIỆU

⏰ 18:35 → Kết quả XSMB
⏰ 19:00 → Tính tín hiệu D+1

✅ Đã kết nối - Sẵn sàng hoạt động!"""
    return status

def scan_all():
    """Quét & gửi kết quả XSMB"""
    print(f"\n🔄 [BOT XSMB] Đang cập nhật kết quả... {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # TODO: Thêm logic lấy kết quả XSMB ở đây
    result_message = get_current_status()
    send_xsmb(result_message)

def check_silent():
    """Kiểm tra thôi, chỉ gửi khi có thay đổi"""
    current_status = get_current_status()
    send_status_if_changed(current_status)

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 BOT XSMB — KHỞI ĐỘNG THÀNH CÔNG")
    print("⏰ 18:35 → Kết quả XSMB | 19:00 → Tín hiệu D+1")
    print("🔄 Chạy 24/7 — không tự dừng, không gửi trùng lặp")
    print("=" * 50)
    print(f"🔌 Token: {XSMB_TELEGRAM_TOKEN[:10]}...{XSMB_TELEGRAM_TOKEN[-4:]}")
    print(f"💬 Chat ID: {XSMB_CHAT_ID}")
    print("=" * 50)
    
    # Gửi trạng thái 1 lần lúc khởi động
    send_status_if_changed(get_current_status())
    
    # Lịch trình chính
    schedule.every().day.at("18:35").do(scan_all)
    schedule.every().day.at("19:00").do(scan_all)
    
    # Kiểm tra mỗi 5 phút nhưng KHÔNG gửi nếu không đổi
    schedule.every(5).minutes.do(check_silent)
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n⏹️  [BOT XSMB] Dừng bot...")
            break
        except Exception as e:
            print(f"❌ [BOT XSMB] Lỗi trong vòng lặp chính: {e}")
            time.sleep(60)
