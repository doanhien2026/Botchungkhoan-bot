import os
import sys
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

print("="*60)
print("DEBUG MODE - KIEM TRA CU TI TELEGRAM")
print("="*60)
print()

# ========== BUOC 1: KIEM TRA .env ==========
print("BUOC 1: KIEM TRA FILE .ENV")
print("-" * 60)
env_path = ".env"
if os.path.exists(env_path):
    print(f"✓ File .env tim thay at: {os.path.abspath(env_path)}")
    with open(env_path, 'r') as f:
        content = f.read()
        print(f"Noi dung file:\n{content}")
else:
    print(f"✗ File .env KHONG tim thay!")
    print(f"Hay tao file .env tai: {os.path.abspath('.')}")
    sys.exit(1)

print()

# ========== BUOC 2: KIEM TRA TOKEN VA CHAT_ID ==========
print("BUOC 2: KIEM TRA TOKEN VA CHAT_ID")
print("-" * 60)
print(f"TELEGRAM_TOKEN: {'✓ CO' if TELEGRAM_TOKEN else '✗ KHONG CO'}")
if TELEGRAM_TOKEN:
    print(f"  -> Gia tri: {TELEGRAM_TOKEN[:20]}...{TELEGRAM_TOKEN[-10:]}")
else:
    print("  ✗ LỖI: TELEGRAM_TOKEN chua duoc dat trong .env")
    
print(f"CHAT_ID: {'✓ CO' if CHAT_ID else '✗ KHONG CO'}")
if CHAT_ID:
    print(f"  -> Gia tri: {CHAT_ID}")
else:
    print("  ✗ LỖI: CHAT_ID chua duoc dat trong .env")

print()

# ========== BUOC 3: TEST TELEGRAM API ==========
print("BUOC 3: TEST TELEGRAM API")
print("-" * 60)

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("✗ Khong the test - Token hoac Chat_ID bi thieu")
    sys.exit(1)

# Test 1: Kiem tra bot info
print("\nTest 1: Kiem tra thong tin Bot")
try:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Bot info:")
        print(f"  - Bot ID: {data['result']['id']}")
        print(f"  - Bot name: {data['result']['first_name']}")
        print(f"  - Bot username: @{data['result']['username']}")
    else:
        print(f"✗ Loi: {response.text}")
except Exception as e:
    print(f"✗ Exception: {e}")

print()

# Test 2: Gui tin nhan test
print("Test 2: Gui tin nhan test")
test_message = "TEST MESSAGE - Bot debug - Neu nhan duoc tin nay thi bot hoat dong OK!"

try:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": test_message
    }
    print(f"Sending to Chat ID: {CHAT_ID}")
    print(f"Message: {test_message}")
    print()
    
    response = requests.post(url, data=data, timeout=15)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("\n✓ THANH CONG! Tin nhan da duoc gui!")
    else:
        print(f"\n✗ THAT BAI! Loi: {response.status_code}")
        error_data = response.json()
        if 'description' in error_data:
            print(f"Chi tiet loi: {error_data['description']}")
            
except Exception as e:
    print(f"✗ Exception: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
print("KET THUC DEBUG")
print("="*60)
