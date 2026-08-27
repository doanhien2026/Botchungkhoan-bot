from collections import Counter
from datetime import datetime
from data_manager import get_all_dates, get_saved_result

# ==========================================================
# 🧠 LOGIC DỰ ĐOÁN — DỰA TRÊN TẦN SUẤT + CHU KỲ NGỦ
# ==========================================================

def get_history_data(days=60):
    """Đọc dữ liệu đã lưu — CHỈ ĐỌC, KHÔNG SỬA"""
    all_dates = get_all_dates()
    if not all_dates:
        return [], [], [], []
    
    # Sắp xếp: cũ nhất → mới nhất
    sorted_dates = sorted(all_dates, key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    limit = min(days, len(sorted_dates))
    recent = sorted_dates[-limit:] if limit > 0 else []
    
    loto_list = []       # Tất cả lô 2 số
    first_digit_list = [] # Đầu số giải đặc biệt
    db_last2_list = []   # 2 số cuối giải đặc biệt
    history_map = {}     # Lịch sử theo ngày
    
    for date_str in recent:
        res = get_saved_result(date_str)
        if not res:
            continue
        history_map[date_str] = res
        # Lấy lô
        if res.get("loto"):
            loto_list.extend(res["loto"])
        # Lấy giải đặc biệt
        if res.get("special") and len(res["special"]) == 5:
            first_digit_list.append(res["special"][0])
            db_last2_list.append(res["special"][-2:])
    
    return loto_list, first_digit_list, db_last2_list, history_map

# ==========================================================
# 🔢 TÍNH TOÁN 3 CON LÔ CAO TỶ LỆ
# ==========================================================
def calc_top3_loto(loto_list, history_map):
    """Tính 3 con lô: tần suất + chu kỳ ngủ"""
    if not loto_list:
        return []
    
    # Đếm tần suất
    freq = Counter(loto_list)
    total = len(loto_list)
    
    # Tính chu kỳ ngủ (số ngày chưa về)
    all_dates_sorted = sorted(history_map.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    last_appear = {}
    for idx, date_str in enumerate(all_dates_sorted):
        res = history_map[date_str]
        nums = set(res.get("loto", []))
        if res.get("special") and len(res["special"]) == 5:
            nums.add(res["special"][-2:])
        for n in nums:
            if n not in last_appear:
                last_appear[n] = idx  # số ngày ngủ
    
    # Tính điểm tổng hợp = tần suất * (1 + ngủ/30)
    scored = []
    for num, count in freq.items():
        rate = round(count / total * 100, 1)
        sleep_days = last_appear.get(num, 999)
        score = round(count * (1 + min(sleep_days, 30) / 30), 2)
        scored.append({
            "num": num,
            "count": count,
            "rate": rate,
            "sleep": sleep_days,
            "score": score
        })
    
    # Sắp xếp theo điểm giảm dần → lấy top 3
    scored.sort(key=lambda x: -x["score"])
    return scored[:3]

# ==========================================================
# 🔀 1 CẶP LÔ XIÊN — 2 CON CAO NHẤT KẾT HỢP
# ==========================================================
def calc_xien_pair(top3):
    """Lấy 2 con cao nhất làm cặp xiên"""
    if len(top3) >= 2:
        return [top3[0]["num"], top3[1]["num"]]
    if len(top3) == 1:
        return [top3[0]["num"], "99"]
    return ["00", "00"]

# ==========================================================
# 🔢 ĐẦU SỐ ĐỀ — TỶ LỆ XUẤT HIỆN CAO NHẤT
# ==========================================================
def calc_first_digit(first_digit_list):
    if not first_digit_list:
        return "?", 0, 0.0
    freq = Counter(first_digit_list)
    total = len(first_digit_list)
    digit, count = freq.most_common(1)[0]
    rate = round(count / total * 100, 1)
    return digit, count, rate

# ==========================================================
# 📊 TẠO BÁO CÁO ĐẦY ĐỦ
# ==========================================================
def generate_prediction(days=60):
    """Tạo kết quả dự đoán có giải thích logic"""
    loto_list, first_list, db_last2_list, history_map = get_history_data(days)
    
    if not loto_list and not first_list:
        return None
    
    top3 = calc_top3_loto(loto_list, history_map)
    pair_xien = calc_xien_pair(top3)
    first_digit, f_count, f_rate = calc_first_digit(first_list)
    
    # === TẠO BÁO CÁO ===
    lines = [
        f"📊 **DỰ ĐOÁN KẾT QUẢ — DỰA TRÊN {days} NGÀY**",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🎯 **3 CON LÔ TỶ LỆ CAO NHẤT:**",
        "   (Theo tần suất + chu kỳ ngủ)"
    ]
    
    for i, item in enumerate(top3, 1):
        lines.append(
            f"   {i}. `{item['num']}` — {item['count']} lần, "
            f"tỷ lệ {item['rate']}%, ngủ {item['sleep']} ngày"
        )
    
    lines.extend([
        "",
        "🔀 **1 CẶP LÔ XIÊN:**",
        f"   → Kết hợp 2 con cao nhất: `{pair_xien[0]} - {pair_xien[1]}`",
        "",
        "🔢 **DỰ KIẾN ĐẦU SỐ ĐỀ:**",
        f"   → Đầu số `{first_digit}` — xuất hiện {f_count} lần → {f_rate}%",
        "",
        "🧠 **Cách tính:** Tần suất xuất hiện + số ngày chưa về (ngủ) → điểm tổng hợp cao nhất",
        "⚠️ *Dự đoán dựa trên dữ liệu lịch sử — Tham khảo, không đảm bảo 100%*",
        "⚠️ *Chơi có trách nhiệm!*"
    ])
    
    return "\n".join(lines)
