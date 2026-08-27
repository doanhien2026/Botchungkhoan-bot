from collections import Counter
from datetime import datetime
from data_manager import get_all_dates, get_saved_result

# ==============================================
# ✅ THỐNG KÊ & DỰ ĐOÁN — KHÔNG SỬA DỮ LIỆU GỐC
# ==============================================

def get_history_data(days=60):
    """Đọc dữ liệu đã lưu — CHỈ ĐỌC, KHÔNG SỬA"""
    all_dates = get_all_dates()
    if not all_dates:
        return [], [], []
    
    # Sắp xếp ngày mới nhất trước
    sorted_dates = sorted(all_dates, key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    limit = min(days, len(sorted_dates))
    
    loto_list = []       # Tất cả lô 2 số
    first_digit_list = [] # Đầu số giải đặc biệt
    db_last2_list = []   # 2 số cuối giải đặc biệt
    
    for date_str in sorted_dates[:limit]:
        res = get_saved_result(date_str)
        if not res:
            continue
        # Lấy lô
        if res.get("loto"):
            loto_list.extend(res["loto"])
        # Lấy giải đặc biệt → đầu số + 2 số cuối
        if res.get("special") and len(res["special"]) == 5:
            first_digit_list.append(res["special"][0])
            db_last2_list.append(res["special"][-2:])
    
    return loto_list, first_digit_list, db_last2_list

def analyze_top3_loto(loto_list):
    """3 con lô tần suất cao nhất"""
    if not loto_list:
        return []
    cnt = Counter(loto_list)
    total = len(loto_list)
    # Tính tỷ lệ + sắp xếp
    ranked = sorted(
        [(num, c, round(c/total*100,1)) for num,c in cnt.items()],
        key=lambda x: (-x[1], -x[2])
    )
    return ranked[:3]

def get_xien_pair(loto_list, top3):
    """1 cặp lô xiên — lấy 2 con cao nhất"""
    if len(top3) >= 2:
        return [top3[0][0], top3[1][0]]
    if len(set(loto_list)) >= 2:
        top2 = Counter(loto_list).most_common(2)
        return [top2[0][0], top2[1][0]]
    return ["00", "00"]

def get_top_first_digit(first_digit_list):
    """Đầu số đề xuất hiện nhiều nhất"""
    if not first_digit_list:
        return "?", 0, 0.0
    cnt = Counter(first_digit_list)
    total = len(first_digit_list)
    digit, c = cnt.most_common(1)[0]
    rate = round(c/total*100,1)
    return digit, c, rate

def generate_prediction(days=60):
    """Tạo báo cáo dự đoán hoàn chỉnh"""
    loto_list, first_list, db_last2_list = get_history_data(days)
    
    if not loto_list and not first_list:
        return None  # Chưa có đủ dữ liệu
    
    top3 = analyze_top3_loto(loto_list)
    pair_xien = get_xien_pair(loto_list, top3)
    first_digit, f_count, f_rate = get_top_first_digit(first_list)
    
    # === TẠO BÁO CÁO ===
    lines = [
        f"📊 **THỐNG KÊ & DỰ ĐOÁN — {days} NGÀY GẦN NHẤT**",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🎯 **3 CON LÔ TỶ LỆ TRÚNG CAO:**"
    ]
    for i, (num, cnt, rate) in enumerate(top3, 1):
        lines.append(f"   {i}. `{num}` — xuất hiện {cnt} lần → {rate}%")
    
    lines.extend([
        "",
        "🔀 **1 CẶP LÔ XIÊN:**",
        f"   → `{pair_xien[0]} - {pair_xien[1]}`",
        "",
        "🔢 **DỰ KIẾN ĐẦU SỐ ĐỀ:**",
        f"   → Đầu số: `{first_digit}` — xuất hiện {f_count} lần → {f_rate}%",
        "",
        "⚠️ *Dựa trên tần suất dữ liệu đã lưu — Chỉ tham khảo!*",
        "⚠️ *Không đảm bảo 100% — Chơi có trách nhiệm!*"
    ])
    
    return "\n".join(lines)
