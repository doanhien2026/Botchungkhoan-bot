import re
import time
import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from itertools import combinations
import sys

try:
    import requests
    from bs4 import BeautifulSoup
    from apscheduler.schedulers.blocking import BlockingScheduler
except ImportError as e:
    print(f"❌ Thiếu thư viện: {e}")
    print("👉 Cài lệnh: pip install requests beautifulsoup4 apscheduler")
    sys.exit(1)

# ============================================================
# CẤU HÌNH — ✅ ĐÃ ĐIỀN SẴN
# ============================================================
BOT_TOKEN = "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0"
CHAT_ID = "1030583610"
SOURCE_URL = "https://xsmb.com.vn/so-ket-qua-xsmb-60-ngay"
DB_FILE = "xsmb_bot.db"
LOOKBACK = 60

# ✅ TÙY CHỌN: Buộc tính lại tín hiệu mới (xóa dữ liệu cũ)
# Đặt = True → bot sẽ xóa tín hiệu cũ và tính lại mới
# Đặt = False → giữ nguyên logic khóa bình thường
FORCE_RECALCULATE = False  # ⚠️ ĐỔI THÀNH True KHI MUỐN TÍNH LẠI SỐ MỚI

VIETNAM_TZ = timezone(timedelta(hours=7))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8"
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)

# ============================================================
# TELEGRAM
# ============================================================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code != 200:
            logging.error(f"Telegram lỗi {response.status_code}: {response.text[:200]}")
            return False
        return True
    except Exception as e:
        logging.error(f"Telegram lỗi kết nối: {e}")
        return False

# ============================================================
# DATABASE
# ============================================================
def get_db():
    return sqlite3.connect(DB_FILE)

def init_database():
    con = get_db()
    cur = con.cursor()
    
    # ✅ XÓA TÍN HIỆU CŨ NẾU ĐƯỢC YÊU CẦU TÍNH LẠI
    if FORCE_RECALCULATE:
        logging.warning("⚠️ ĐANG XÓA TÍN HIỆU CŨ ĐỂ TÍNH LẠI MỚI...")
        cur.execute("DELETE FROM signals")
        con.commit()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS results (
            date TEXT PRIMARY KEY,
            db TEXT,
            all_numbers TEXT,
            imported_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            target_date TEXT PRIMARY KEY,
            loto1 TEXT, loto2 TEXT, loto3 TEXT,
            xien1 TEXT, xien2 TEXT,
            dau TEXT,
            created_at TEXT,
            backtest_loto_rate REAL,
            backtest_xien_rate REAL,
            backtest_dau_rate REAL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS backtest (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_date TEXT,
            loto1 TEXT, loto2 TEXT, loto3 TEXT,
            xien1 TEXT, xien2 TEXT,
            dau TEXT,
            loto_hit INTEGER, xien_hit INTEGER, dau_hit INTEGER
        )
    """)
    con.commit()
    con.close()

# ============================================================
# TẢI TRANG XSMB
# ============================================================
def download_page():
    try:
        response = requests.get(SOURCE_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logging.error(f"Không tải được trang XSMB: {e}")
        return None

# ============================================================
# PARSE DỮ LIỆU
# ============================================================
def parse_xsmb_page(html):
    if not html:
        return []
    
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    
    results = []
    current_date = None
    current_numbers = []
    db_number = None
    
    date_pattern = re.compile(r"(\d{2})/(\d{2})/(\d{4})")
    
    for line in lines:
        match = date_pattern.search(line)
        if match:
            if current_date and len(current_numbers) >= 20:
                results.append({
                    "date": current_date,
                    "db": db_number,
                    "numbers": current_numbers.copy()
                })
            day, month, year = match.groups()
            current_date = f"{year}-{month}-{day}"
            current_numbers = []
            db_number = None
            continue
        
        if line in ["Đầu", "Lô tô", "Đuôi"] or line.startswith("XSMB") or line.startswith("Sổ kết quả"):
            continue
        
        found = re.findall(r"\b\d{2,5}\b", line)
        if not found:
            continue
        
        if current_date:
            for n in found:
                if len(n) in (2, 3, 4, 5):
                    current_numbers.append(n)
            if db_number is None and len(found) >= 1 and len(found[0]) == 5:
                db_number = found[0]
    
    if current_date and len(current_numbers) >= 20:
        results.append({
            "date": current_date,
            "db": db_number,
            "numbers": current_numbers
        })
    
    clean = []
    for item in results:
        loto = [n[-2:] for n in item["numbers"] if len(n) >= 2]
        unique_loto = list(dict.fromkeys(loto))
        if len(unique_loto) >= 20:
            clean.append({
                "date": item["date"],
                "db": item["db"],
                "loto": unique_loto
            })
    return clean

# ============================================================
# LƯU KẾT QUẢ
# ============================================================
def save_results(results):
    con = get_db()
    cur = con.cursor()
    for item in results:
        unique_loto = list(dict.fromkeys(item["loto"]))
        cur.execute("""
            INSERT OR REPLACE INTO results
            (date, db, all_numbers, imported_at)
            VALUES (?, ?, ?, ?)
        """, (
            item["date"],
            item["db"],
            ",".join(unique_loto),
            datetime.now(VIETNAM_TZ).isoformat()
        ))
    con.commit()
    con.close()
    logging.info(f"✅ Đã lưu {len(results)} ngày dữ liệu mới")

# ============================================================
# LẤY DỮ LIỆU LỊCH SỬ
# ============================================================
def load_history():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT date, db, all_numbers FROM results ORDER BY date ASC")
    rows = cur.fetchall()
    con.close()
    history = []
    for row in rows:
        numbers = [x for x in row[2].split(",") if x]
        history.append({"date": row[0], "db": row[1], "loto": numbers})
    return history

# ============================================================
# TÍNH TOÁN THỐNG KÊ
# ============================================================
def create_matrix(history):
    matrix = {f"{i:02d}": [] for i in range(100)}
    for day in history:
        nums = set(day["loto"])
        for n in matrix:
            matrix[n].append(1 if n in nums else 0)
    return matrix

def frequency(values):
    return sum(values) / len(values) if values else 0.0

def missing_days(values):
    count = 0
    for v in reversed(values):
        if v == 0: count += 1
        else: break
    return count

def fall_rate(values):
    if len(values) < 5: return 0.0
    appearances = falls = 0
    for i in range(len(values) - 3):
        if values[i] == 1:
            appearances += 1
            if 1 in (values[i+1], values[i+2], values[i+3]):
                falls += 1
    return falls / appearances if appearances else 0.0

def calculate_scores(history):
    history = history[-LOOKBACK:]
    matrix = create_matrix(history)
    scores = {}
    for num, vals in matrix.items():
        f60 = frequency(vals[-60:])
        f30 = frequency(vals[-30:])
        f14 = frequency(vals[-14:])
        f7 = frequency(vals[-7:])
        fall60 = fall_rate(vals[-60:])
        fall30 = fall_rate(vals[-30:])
        gan = missing_days(vals)
        gan_score = min(gan / 15, 1)
        score = 0.20*f60 + 0.20*f30 + 0.10*f14 + 0.10*f7 + 0.25*fall60 + 0.10*fall30 + 0.05*gan_score
        scores[num] = {"score": score, "f60": f60, "f30": f30, "fall60": fall60, "gan": gan}
    return scores

def calculate_head_scores(history):
    history = history[-LOOKBACK:]
    result = {}
    windows = {60: 0.45, 30: 0.35, 7: 0.20}
    for head in range(10):
        total = 0
        for w, weight in windows.items():
            data = history[-w:]
            if not data: continue
            hit = sum(1 for d in data if any(int(n[0]) == head for n in d["loto"]))
            total += (hit / len(data)) * weight
        result[head] = total
    return result

def pair_frequency(a, b, history):
    data = history[-LOOKBACK:]
    cnt = sum(1 for d in data if a in d["loto"] and b in d["loto"])
    return cnt / len(data) if data else 0.0

def select_xien(scores, history):
    ranking = sorted(scores.keys(), key=lambda x: scores[x]["score"], reverse=True)[:20]
    best_pair, best_score = None, -1
    for a, b in combinations(ranking, 2):
        individual = (scores[a]["score"] + scores[b]["score"]) / 2
        pair = pair_frequency(a, b, history)
        s = 0.75*individual + 0.25*pair
        if s > best_score:
            best_score = s
            best_pair = (a, b)
    return best_pair

def select_loto(scores):
    ranking = sorted(scores.keys(), key=lambda x: scores[x]["score"], reverse=True)
    candidates = [n for n in ranking if scores[n]["fall60"] >= 0.10]
    return candidates[:3] if len(candidates) >= 3 else ranking[:3]

def make_prediction(history):
    scores = calculate_scores(history)
    loto = select_loto(scores)
    xien = select_xien(scores, history)
    heads = calculate_head_scores(history)
    dau = max(heads, key=heads.get)
    return {"loto": loto, "xien": xien, "dau": dau, "scores": scores}

def backtest(history):
    if len(history) < 65: return {"loto_rate": 0, "xien_rate": 0, "dau_rate": 0}
    loto_hits = xien_hits = dau_hits = total = 0
    start = max(60, len(history) - 60)
    for i in range(start, len(history)):
        train = history[:i]
        actual = set(history[i]["loto"])
        pred = make_prediction(train)
        if any(n in actual for n in pred["loto"]): loto_hits += 1
        if pred["xien"][0] in actual and pred["xien"][1] in actual: xien_hits += 1
        db = history[i]["db"]
        if db and db[-2] == str(pred["dau"]): dau_hits += 1
        total += 1
    return {
        "loto_rate": loto_hits/total if total else 0,
        "xien_rate": xien_hits/total if total else 0,
        "dau_rate": dau_hits/total if total else 0
    }

# ============================================================
# QUẢN LÝ TÍN HIỆU
# ============================================================
def get_locked_signal(target_date):
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT loto1,loto2,loto3,xien1,xien2,dau,backtest_loto_rate,backtest_xien_rate,backtest_dau_rate FROM signals WHERE target_date=?", (target_date,))
    row = cur.fetchone()
    con.close()
    if not row: return None
    return {"loto": [row[0],row[1],row[2]], "xien": [row[3],row[4]], "dau": row[5], "backtest": {"loto": row[6], "xien": row[7], "dau": row[8]}}

def lock_signal(target_date, prediction, bt):
    existing = get_locked_signal(target_date)
    if existing and not FORCE_RECALCULATE:
        logging.info(f"✅ Dùng tín hiệu ĐÃ KHÓA: {target_date}")
        return existing
    
    # Nếu FORCE_RECALCULATE = True → xóa cũ + lưu mới
    if FORCE_RECALCULATE and existing:
        logging.warning(f"🔄 TÍNH LẠI tín hiệu: {target_date}")
        con = get_db()
        cur = con.cursor()
        cur.execute("DELETE FROM signals WHERE target_date=?", (target_date,))
        con.commit()
        con.close()
    
    loto, xien, dau = prediction["loto"], prediction["xien"], prediction["dau"]
    con = get_db()
    cur = con.cursor()
    cur.execute("""INSERT INTO signals VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (
        target_date, loto[0], loto[1], loto[2], xien[0], xien[1], str(dau),
        datetime.now(VIETNAM_TZ).isoformat(), bt["loto_rate"], bt["xien_rate"], bt["dau_rate"]
    ))
    con.commit()
    con.close()
    return {"loto": loto, "xien": xien, "dau": dau, "backtest": bt}

# ============================================================
# GỬI TÍN HIỆU
# ============================================================
def send_prediction(signal, target_date):
    loto, xien, dau, bt = signal["loto"], signal["xien"], signal["dau"], signal["backtest"]
    mode_note = "🔄 <b>[ĐÃ TÍNH LẠI MỚI]</b>\n" if FORCE_RECALCULATE else ""
    message = f"""
{mode_note}<b>🔮 TÍN HIỆU XSMB D+1</b>

📅 Ngày dự báo:
<b>{target_date}</b>

━━━━━━━━━━━━━━━━

<b>🔥 3 LÔ RƠI</b>

1️⃣ <b>{loto[0]}</b>
2️⃣ <b>{loto[1]}</b>
3️⃣ <b>{loto[2]}</b>

━━━━━━━━━━━━━━━━

<b>🎯 XIÊN 2</b>

<b>{xien[0]} - {xien[1]}</b>

━━━━━━━━━━━━━━━━

<b>🎲 ĐẦU ĐỀ</b>

<b>Đầu {dau}</b>

━━━━━━━━━━━━━━━━

📊 <b>BACKTEST 60 NGÀY</b>

Lô: <b>{bt['loto']*100:.1f}%</b>
Xiên: <b>{bt['xien']*100:.1f}%</b>
Đề: <b>{bt['dau']*100:.1f}%</b>

━━━━━━━━━━━━━━━━

🔒 <b>TÍN HIỆU ĐÃ KHÓA</b>
⏱ Gửi lại mỗi 5 phút
⚠️ Tham khảo - không đảm bảo
"""
    send_telegram(message)

# ============================================================
# CÁC JOB LỊCH TRÌNH
# ============================================================

def update_results():
    logging.info("🔄 Đang tải dữ liệu XSMB...")
    html = download_page()
    if not html: return []
    results = parse_xsmb_page(html)
    if not results:
        logging.warning("⚠️ Không có dữ liệu mới")
        return []
    save_results(results)
    return results

def get_latest_result():
    history = load_history()
    return history[-1] if history else None

def job_1835():
    logging.info("========== 18:35 KẾT QUẢ ==========")
    try:
        update_results()
        result = get_latest_result()
        if not result: return
        date = datetime.strptime(result["date"], "%Y-%m-%d").strftime("%d/%m/%Y")
        msg = f"""
<b>📢 KẾT QUẢ XSMB</b>
📅 <b>{date}</b>
🏆 ĐB: <b>{result['db'] or 'N/A'}</b>
🔢 Lô tô: {', '.join(result['loto'])}
🤖 Đã cập nhật dữ liệu 60 ngày
"""
        send_telegram(msg)
        evaluate_previous_signal(result)
    except Exception as e:
        logging.exception(f"Lỗi 18:35: {e}")

def evaluate_previous_signal(result):
    signal = get_locked_signal(result["date"])
    if not signal: return
    actual = set(result["loto"])
    loto_hit = any(n in actual for n in signal["loto"])
    xien_hit = signal["xien"][0] in actual and signal["xien"][1] in actual
    db = result["db"]
    dau_hit = db and db[-2] == signal["dau"]
    msg = f"""
<b>📊 ĐÁNH GIÁ TÍN HIỆU</b>
📅 Ngày: <b>{result['date']}</b>
🔥 3 lô: {"✅ CÓ" if loto_hit else "❌ KHÔNG"}
🎯 Xiên 2: {"✅ CÓ" if xien_hit else "❌ KHÔNG"}
🎲 Đầu đề: {"✅ CÓ" if dau_hit else "❌ KHÔNG"}
"""
    send_telegram(msg)

def job_1900():
    logging.info("========== 19:00 TÍNH DỰ BÁO ==========")
    try:
        update_results()
        history = load_history()
        if len(history) < LOOKBACK:
            send_telegram(f"⚠️ Cần {LOOKBACK} ngày dữ liệu, mới có {len(history)} ngày")
            return
        latest = history[-1]
        latest_date = datetime.strptime(latest["date"], "%Y-%m-%d")
        target_date = (latest_date + timedelta(days=1)).strftime("%Y-%m-%d")
        
        existing = get_locked_signal(target_date)
        if existing and not FORCE_RECALCULATE:
            logging.info(f"✅ Dùng tín hiệu đã khóa: {target_date}")
            send_prediction(existing, target_date)
            return
        
        bt = backtest(history)
        prediction = make_prediction(history[-LOOKBACK:])
        signal = lock_signal(target_date, prediction, bt)
        send_prediction(signal, target_date)
        logging.info(f"✅ Đã tạo tín hiệu: {target_date}")
    except Exception as e:
        logging.exception(f"Lỗi 19:00: {e}")

def job_every_5_minutes():
    try:
        now = datetime.now(VIETNAM_TZ)
        if now.hour == 18 and now.minute >= 35: return
        history = load_history()
        if not history: return
        latest_date = datetime.strptime(history[-1]["date"], "%Y-%m-%d")
        target_date = (latest_date + timedelta(days=1)).strftime("%Y-%m-%d")
        signal = get_locked_signal(target_date)
        if signal: send_prediction(signal, target_date)
    except Exception as e:
        logging.exception(f"Lỗi 5 phút: {e}")

def test_telegram():
    mode = "🔄 CHẾ ĐỘ TÍNH LẠI MỚI" if FORCE_RECALCULATE else "🔒 CHẾ ĐỘ KHÓA TÍN HIỆU"
    send_telegram(f"""
<b>🤖 XSMB BOT ONLINE</b>
{mode}
⏰ 18:35 → Kết quả XSMB
⏰ 19:00 → Tính tín hiệu D+1
⏱ Mỗi 5 phút → Gửi lại tín hiệu
""")

# ============================================================
# MAIN
# ============================================================
def main():
    init_database()
    try:
        update_results()
    except Exception as e:
        logging.error(f"Không cập nhật dữ liệu: {e}")
    test_telegram()
    scheduler = BlockingScheduler(timezone=VIETNAM_TZ)
    scheduler.add_job(job_1835, "cron", hour=18, minute=35, id="r1")
    scheduler.add_job(job_1900, "cron", hour=19, minute=0, id="r2")
    scheduler.add_job(job_every_5_minutes, "cron", minute="*/5", id="r3")
    logging.info("🚀 BOT ĐANG CHẠY...")
    scheduler.start()

if __name__ == "__main__":
    main()
