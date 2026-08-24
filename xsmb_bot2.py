import re
import time
import sqlite3
import logging
from datetime import datetime, timedelta
from itertools import combinations

import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.blocking import BlockingScheduler


# ============================================================
# CẤU HÌNH — ✅ ĐÃ ĐIỀN SẴN THEO THÔNG TIN BẠN GỬI
# ============================================================

BOT_TOKEN = "8814072179:AAFRwRv8CIVi6IgYDMe1tfoYLY9kARyAYx0"
CHAT_ID = "1030583610"

SOURCE_URL = "https://xsmb.com.vn/so-ket-qua-xsmb-60-ngay"

DB_FILE = "xsmb_bot.db"

LOOKBACK = 60

TIMEZONE = "Asia/Ho_Chi_Minh"

HEADERS = {
    "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/131.0 Safari/537.36"
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message):

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:

        response = requests.post(
            url,
            json=data,
            timeout=20
        )

        if response.status_code != 200:

            logging.error(
                "Telegram lỗi: %s",
                response.text
            )

            return False

        return True

    except Exception as e:

        logging.error(
            "Telegram exception: %s",
            e
        )

        return False


# ============================================================
# DATABASE
# ============================================================

def get_db():

    return sqlite3.connect(DB_FILE)


def init_database():

    con = get_db()

    cur = con.cursor()

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
            loto1 TEXT,
            loto2 TEXT,
            loto3 TEXT,
            xien1 TEXT,
            xien2 TEXT,
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
            loto1 TEXT,
            loto2 TEXT,
            loto3 TEXT,
            xien1 TEXT,
            xien2 TEXT,
            dau TEXT,
            loto_hit INTEGER,
            xien_hit INTEGER,
            dau_hit INTEGER
        )
    """)

    con.commit()
    con.close()


# ============================================================
# CHUẨN HÓA SỐ
# ============================================================

def normalize_number(number):

    try:

        return f"{int(number):02d}"

    except:

        return None


# ============================================================
# TẢI TRANG XSMB
# ============================================================

def download_page():

    response = requests.get(
        SOURCE_URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.text


# ============================================================
# PARSE DỮ LIỆU
# ============================================================

def parse_xsmb_page(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    text = soup.get_text(
        "\n",
        strip=True
    )

    lines = [
        x.strip()
        for x in text.splitlines()
        if x.strip()
    ]

    results = []

    current_date = None
    current_numbers = []
    db_number = None

    date_pattern = re.compile(
        r"(\d{2})/(\d{2})/(\d{4})"
    )

    for line in lines:

        match = date_pattern.search(line)

        if match:

            if current_date and current_numbers:

                results.append({
                    "date": current_date,
                    "db": db_number,
                    "numbers": current_numbers
                })

            day, month, year = match.groups()
            current_date = f"{year}-{month}-{day}"
            current_numbers = []
            db_number = None
            continue

        if line in ["Đầu", "Lô tô", "Đuôi"]:
            continue

        if line.startswith("XSMB"):
            continue

        if line.startswith("Sổ kết quả"):
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

    if current_date and current_numbers:
        results.append({
            "date": current_date,
            "db": db_number,
            "numbers": current_numbers
        })

    clean = []

    for item in results:
        loto = []
        for n in item["numbers"]:
            if len(n) >= 2:
                loto.append(n[-2:])

        if len(loto) >= 20:
            clean.append({
                "date": item["date"],
                "db": item["db"],
                "loto": loto
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
            datetime.now().isoformat()
        ))

    con.commit()
    con.close()


# ============================================================
# LẤY DỮ LIỆU LỊCH SỬ
# ============================================================

def load_history():

    con = get_db()
    cur = con.cursor()

    cur.execute("""
        SELECT date, db, all_numbers
        FROM results
        ORDER BY date ASC
    """)

    rows = cur.fetchall()
    con.close()

    history = []

    for row in rows:
        date = row[0]
        db_number = row[1]
        numbers = [x for x in row[2].split(",") if x]
        history.append({
            "date": date,
            "db": db_number,
            "loto": numbers
        })

    return history


# ============================================================
# TẠO MATRIX 100 SỐ
# ============================================================

def create_matrix(history):

    matrix = {f"{i:02d}": [] for i in range(100)}

    for day in history:
        numbers = set(day["loto"])
        for n in matrix:
            matrix[n].append(1 if n in numbers else 0)

    return matrix


# ============================================================
# TẦN SUẤT
# ============================================================

def frequency(values):

    if not values:
        return 0.0

    return sum(values) / len(values)


# ============================================================
# GAN
# ============================================================

def missing_days(values):

    count = 0
    for value in reversed(values):
        if value == 0:
            count += 1
        else:
            break
    return count


# ============================================================
# LÔ RƠI
# ============================================================

def fall_rate(values):

    if len(values) < 5:
        return 0.0

    appearances = 0
    falls = 0

    for i in range(len(values) - 3):
        if values[i] == 1:
            appearances += 1
            if values[i + 1] == 1 or values[i + 2] == 1 or values[i + 3] == 1:
                falls += 1

    if appearances == 0:
        return 0.0

    return falls / appearances


# ============================================================
# TÍNH SCORE
# ============================================================

def calculate_scores(history):

    history = history[-LOOKBACK:]

    matrix = create_matrix(history)

    scores = {}

    for number, values in matrix.items():

        f60 = frequency(values[-60:])
        f30 = frequency(values[-30:])
        f14 = frequency(values[-14:])
        f7 = frequency(values[-7:])
        fall60 = fall_rate(values[-60:])
        fall30 = fall_rate(values[-30:])
        gan = missing_days(values)
        gan_score = min(gan / 15, 1)

        score = (
            0.20 * f60 +
            0.20 * f30 +
            0.10 * f14 +
            0.10 * f7 +
            0.25 * fall60 +
            0.10 * fall30 +
            0.05 * gan_score
        )

        scores[number] = {
            "score": score,
            "f60": f60,
            "f30": f30,
            "f14": f14,
            "f7": f7,
            "fall60": fall60,
            "fall30": fall30,
            "gan": gan
        }

    return scores


# ============================================================
# ĐIỂM ĐẦU ĐỀ
# ============================================================

def calculate_head_scores(history):

    history = history[-LOOKBACK:]

    result = {}

    windows = {
        60: 0.45,
        30: 0.35,
        7: 0.20
    }

    for head in range(10):

        total_score = 0

        for window, weight in windows.items():

            data = history[-window:]

            if not data:
                continue

            hit_days = 0

            for day in data:
                if any(int(n[0]) == head for n in day["loto"]):
                    hit_days += 1

            rate = hit_days / len(data)
            total_score += rate * weight

        result[head] = total_score

    return result


# ============================================================
# ĐỒNG XUẤT HIỆN
# ============================================================

def pair_frequency(a, b, history):

    data = history[-LOOKBACK:]

    if not data:
        return 0.0

    count = 0

    for day in data:
        nums = set(day["loto"])
        if a in nums and b in nums:
            count += 1

    return count / len(data)


# ============================================================
# CHỌN XIÊN 2
# ============================================================

def select_xien(scores, history):

    ranking = sorted(
        scores.keys(),
        key=lambda x: scores[x]["score"],
        reverse=True
    )

    candidates = ranking[:20]

    best_pair = None
    best_score = -1

    for a, b in combinations(candidates, 2):

        individual = (scores[a]["score"] + scores[b]["score"]) / 2
        pair = pair_frequency(a, b, history)
        score = 0.75 * individual + 0.25 * pair

        if score > best_score:
            best_score = score
            best_pair = (a, b)

    return best_pair


# ============================================================
# CHỌN 3 LÔ RƠI
# ============================================================

def select_loto(scores):

    ranking = sorted(
        scores.keys(),
        key=lambda x: scores[x]["score"],
        reverse=True
    )

    candidates = [
        n for n in ranking
        if scores[n]["fall60"] >= 0.10
    ]

    if len(candidates) < 3:
        candidates = ranking

    return candidates[:3]


# ============================================================
# DỰ BÁO
# ============================================================

def make_prediction(history):

    scores = calculate_scores(history)
    loto = select_loto(scores)
    xien = select_xien(scores, history)
    heads = calculate_head_scores(history)
    dau = max(heads, key=heads.get)

    return {
        "loto": loto,
        "xien": xien,
        "dau": dau,
        "scores": scores
    }


# ============================================================
# BACKTEST
# ============================================================

def backtest(history):

    if len(history) < 65:
        return {
            "loto_rate": 0,
            "xien_rate": 0,
            "dau_rate": 0
        }

    loto_hits = 0
    xien_hits = 0
    dau_hits = 0
    total = 0

    start = max(60, len(history) - 60)

    for i in range(start, len(history)):

        train = history[:i]
        actual = set(history[i]["loto"])
        prediction = make_prediction(train)

        loto = prediction["loto"]
        xien = prediction["xien"]
        dau = prediction["dau"]

        if any(n in actual for n in loto):
            loto_hits += 1

        if xien[0] in actual and xien[1] in actual:
            xien_hits += 1

        db = history[i]["db"]
        if db:
            db_head = int(db[-2])
            if db_head == dau:
                dau_hits += 1

        total += 1

    if total == 0:
        return {
            "loto_rate": 0,
            "xien_rate": 0,
            "dau_rate": 0
        }

    return {
        "loto_rate": loto_hits / total,
        "xien_rate": xien_hits / total,
        "dau_rate": dau_hits / total
    }


# ============================================================
# LẤY TÍN HIỆU ĐÃ KHÓA
# ============================================================

def get_locked_signal(target_date):

    con = get_db()
    cur = con.cursor()

    cur.execute("""
        SELECT loto1, loto2, loto3, xien1, xien2, dau,
               backtest_loto_rate, backtest_xien_rate, backtest_dau_rate
        FROM signals
        WHERE target_date = ?
    """, (target_date,))

    row = cur.fetchone()
    con.close()

    if not row:
        return None

    return {
        "loto": [row[0], row[1], row[2]],
        "xien": [row[3], row[4]],
        "dau": row[5],
        "backtest": {
            "loto": row[6],
            "xien": row[7],
            "dau": row[8]
        }
    }


# ============================================================
# KHÓA TÍN HIỆU
# ============================================================

def lock_signal(target_date, prediction, backtest_result):

    existing = get_locked_signal(target_date)

    if existing:
        return existing

    loto = prediction["loto"]
    xien = prediction["xien"]
    dau = prediction["dau"]

    con = get_db()
    cur = con.cursor()

    cur.execute("""
        INSERT INTO signals
        (target_date, loto1, loto2, loto3, xien1, xien2, dau,
         created_at, backtest_loto_rate, backtest_xien_rate, backtest_dau_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        target_date,
        loto[0],
        loto[1],
        loto[2],
        xien[0],
        xien[1],
        str(dau),
        datetime.now().isoformat(),
        backtest_result["loto_rate"],
        backtest_result["xien_rate"],
        backtest_result["dau_rate"]
    ))

    con.commit()
    con.close()

    return {
        "loto": loto,
        "xien": xien,
        "dau": dau,
        "backtest": backtest_result
    }


# ============================================================
# GỬI TÍN HIỆU
# ============================================================

def send_prediction(signal, target_date):

    loto = signal["loto"]
    xien = signal["xien"]
    dau = signal["dau"]
    bt = signal["backtest"]

    message = f"""
<b>🔮 TÍN HIỆU XSMB D+1</b>

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

Lô:
<b>{bt['loto'] * 100:.1f}%</b>

Xiên:
<b>{bt['xien'] * 100:.1f}%</b>

Đề:
<b>{bt['dau'] * 100:.1f}%</b>

━━━━━━━━━━━━━━━━

🔒 <b>TÍN HIỆU ĐÃ KHÓA</b>

⏱ Gửi lại mỗi 5 phút.
Không thay đổi số.

⚠️ Tín hiệu thống kê tham khảo,
không đảm bảo kết quả.
"""

    send_telegram(message)


# ============================================================
# TỰ LẤY KẾT QUẢ
# ============================================================

def update_results():

    logging.info("Đang lấy dữ liệu XSMB...")

    html = download_page()
    results = parse_xsmb_page(html)

    if not results:
        logging.error("Không đọc được dữ liệu.")
        return []

    save_results(results)
    logging.info("Đã cập nhật %d ngày.", len(results))

    return results


# ============================================================
# NGÀY MỚI NHẤT
# ============================================================

def get_latest_result():

    history = load_history()

    if not history:
        return None

    return history[-1]


# ============================================================
# GỬI KẾT QUẢ 18:35
# ============================================================

def job_1835():

    logging.info("========== 18:35 ==========")

    try:

        update_results()
        result = get_latest_result()

        if not result:
            logging.error("Không có kết quả.")
            return

        date = datetime.strptime(
            result["date"],
            "%Y-%m-%d"
        ).strftime("%d/%m/%Y")

        numbers = result["loto"]
        db_number = result["db"] or "N/A"

        message = f"""
<b>📢 KẾT QUẢ XSMB</b>

📅 <b>{date}</b>

🏆 ĐB:
<b>{db_number}</b>

🔢 Lô tô:
{", ".join(numbers)}

━━━━━━━━━━━━━━━━

🤖 Đã cập nhật dữ liệu 60 ngày.
19:00 bot sẽ tính tín hiệu D+1.
"""

        send_telegram(message)
        evaluate_previous_signal(result)

    except Exception as e:
        logging.exception("Lỗi 18:35: %s", e)


# ============================================================
# CHẤM TÍN HIỆU NGÀY TRƯỚC
# ============================================================

def evaluate_previous_signal(result):

    target_date = result["date"]
    signal = get_locked_signal(target_date)

    if not signal:
        return

    actual = set(result["loto"])

    loto_hit = any(n in actual for n in signal["loto"])
    xien_hit = signal["xien"][0] in actual and signal["xien"][1] in actual

    db = result["db"]
    dau_hit = False

    if db:
        actual_dau = db[-2]
        dau_hit = str(signal["dau"]) == actual_dau

    message = f"""
<b>📊 ĐÁNH GIÁ TÍN HIỆU</b>

📅 Ngày:
<b>{target_date}</b>

🔥 3 lô:
{"✅ CÓ" if loto_hit else "❌ KHÔNG"}

🎯 Xiên 2:
{"✅ CÓ" if xien_hit else "❌ KHÔNG"}

🎲 Đầu đề:
{"✅ CÓ" if dau_hit else "❌ KHÔNG"}
"""

    send_telegram(message)


# ============================================================
# 19:00 - TÍNH DỰ BÁO
# ============================================================

def job_1900():

    logging.info("========== 19:00 ==========")

    try:

        update_results()
        history = load_history()

        if len(history) < LOOKBACK:
            send_telegram(f"""
⚠️ <b>CHƯA ĐỦ DỮ LIỆU</b>

Hiện có:
<b>{len(history)}</b> ngày

Cần:
<b>{LOOKBACK}</b> ngày
""")
            return

        latest = history[-1]
        latest_date = datetime.strptime(latest["date"], "%Y-%m-%d")
        target_date = (latest_date + timedelta(days=1)).strftime("%Y-%m-%d")

        existing = get_locked_signal(target_date)

        if existing:
            logging.info("Dự báo đã tồn tại: %s", target_date)
            send_prediction(existing, target_date)
            return

        train = history[-LOOKBACK:]

        logging.info("Đang chạy backtest...")
        bt = backtest(history)

        logging.info("Đang tính D+1...")
        prediction = make_prediction(train)

        signal = lock_signal(target_date, prediction, bt)
        send_prediction(signal, target_date)

        logging.info("ĐÃ KHÓA DỰ BÁO %s", target_date)

    except Exception as e:
        logging.exception("Lỗi 19:00: %s", e)


# ============================================================
# GỬI LẠI MỖI 5 PHÚT
# ============================================================

def job_every_5_minutes():

    try:

        now = datetime.now()

        if now.hour == 18 and now.minute >= 35:
            return

        history = load_history()

        if not history:
            return

        latest = history[-1]
        latest_date = datetime.strptime(latest["date"], "%Y-%m-%d")
        target_date = (latest_date + timedelta(days=1)).strftime("%Y-%m-%d")

        signal = get_locked_signal(target_date)

        if not signal:
            return

        logging.info("Gửi tín hiệu khóa %s", target_date)
        send_prediction(signal, target_date)

    except Exception as e:
        logging.exception("Lỗi gửi 5 phút: %s", e)


# ============================================================
# KIỂM TRA TELEGRAM
# ============================================================

def test_telegram():

    message = """
<b>🤖 XSMB BOT ONLINE</b>

Telegram kết nối thành công.

⏰ 18:35:
Lấy kết quả XSMB

⏰ 19:00:
Tính D+1

⏱ Mỗi 5 phút:
Gửi lại tín hiệu đã khóa.
"""

    return send_telegram(message)


# ============================================================
# MAIN
# ============================================================

def main():

    init_database()

    try:
        update_results()
    except Exception as e:
        logging.error("Không cập nhật được dữ liệu: %s", e)

    test_telegram()

    scheduler = BlockingScheduler(timezone=TIMEZONE)

    scheduler.add_job(
        job_1835,
        "cron",
        hour=18,
        minute=35,
        id="get_result",
        replace_existing=True
    )

    scheduler.add_job(
        job_1900,
        "cron",
        hour=19,
        minute=0,
        id="create_prediction",
        replace_existing=True
    )

    scheduler.add_job(
        job_every_5_minutes,
        "cron",
        minute="*/5",
        id="send_signal",
        replace_existing=True
    )

    logging.info("====================================")
    logging.info("XSMB TELEGRAM BOT ĐANG CHẠY")
    logging.info("18:35 -> Kết quả")
    logging.info("19:00 -> Tính + khóa D+1")
    logging.info("5 phút -> Gửi lại tín hiệu")
    logging.info("====================================")

    scheduler.start()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
