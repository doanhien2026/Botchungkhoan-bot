import requests, re
from datetime import datetime, timedelta

# 1. Nhập ngày muốn test
raw_input = input("👉 Nhập ngày test (định dạng YYYY/MM/DD, VD: 2026/08/25): ").strip()

try:
    # Tách Năm, Tháng, Ngày
    y, m, d = raw_input.split('/')
    
    # Hàm lấy dữ liệu XSMB theo ngày
    def get_xsmb(year, month, day):
        url = f"https://xoso.com.vn/xsmb-{day}-{month}-{year}.html"
        html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5).text
        db = re.search(r'class="v-gdb"[^>]*>(\d+)</td>', html).group(1)
        lo_list = [n[-2:] for n in re.findall(r'class="v-g[db0-7]+"[^>]*>(\d+)</td>', html)]
        return db, lo_list

    # Lấy dữ liệu ngày hiện tại
    db, lo_list = get_xsmb(y, m, d)
    
    # Tính ngày hôm trước để check Lô rơi
    dt_curr = datetime(int(y), int(m), int(d))
    dt_prev = dt_curr - timedelta(days=1)
    prev_y, prev_m, prev_d = dt_prev.strftime("%Y"), dt_prev.strftime("%m"), dt_prev.strftime("%d")
    
    print(f"\n📊 KẾT QUẢ XSMB NGÀY {y}/{m}/{d}:")
    print(f"• Giải Đặc Biệt: {db}")
    print(f"• Số Đề (Đầu {db[-2]} - Đuôi {db[-1]}): {db[-2:]}")
    print(f"• 27 con Lô về: {', '.join(lo_list)}")
    
    # Check Lô rơi từ ngày hôm trước
    try:
        prev_db, _ = get_xsmb(prev_y, prev_m, prev_d)
        prev_de = prev_db[-2:]
        nhay = lo_list.count(prev_de)
        
        print(f"\n🔍 CHECK LÔ RƠI TỪ ĐỀ HÔM TRƯỚC ({prev_y}/{prev_m}/{prev_d}):")
        print(f"• Đề ngày hôm trước: {prev_de}")
        if nhay > 0:
            print(f"🎯 KẾT QUẢ: TRÚNG! (Lô {prev_de} rơi lại {nhay} nháy)")
        else:
            print(f"❌ KẾT QUẢ: TRẠCH! (Lô {prev_de} không rơi)")
    except Exception:
        print("\n⚠️ Không lấy được dữ liệu ngày hôm trước để check lô rơi.")

except Exception:
    print("\n❌ Sai định dạng hoặc không có dữ liệu! Vui lòng gõ chuẩn YYYY/MM/DD (VD: 2026/08/25).")
