from scraper import get_xsmb_result
from data_manager import save_result, get_saved_result

def fetch_result(date_str):
    # Đọc dữ liệu đã lưu trước
    saved = get_saved_result(date_str)
    if saved:
        print(f"📂 Đọc từ file: {date_str}")
        return saved
    # Lấy mới từ nguồn
    result = get_xsmb_result(date_str)
    if result:
        save_result(result)
    return result
