import os
import sqlite3
import logging
from datetime import datetime, timedelta
from itertools import combinations

import pandas as pd
import numpy as np
import requests
from apscheduler.schedulers.blocking import BlockingScheduler


# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    "DAN_BOT_TOKEN_VAO_DAY"
)

CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID",
    "DAN_CHAT_ID_VAO_DAY"
)

DATA_FILE = "xsmb.csv"
DB_FILE = "xsmb_bot.db"

LOOKBACK = 60

TIMEZONE = "Asia/Ho_Chi_Minh"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# ============================================================
# DATABASE
# ============================================================

def db():

    return sqlite3.connect(DB_FILE)


def init_db():

    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS locked_signal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_date TEXT UNIQUE,

        loto1 TEXT,
        loto2 TEXT,
        loto3 TEXT,

        xien1 TEXT,
        xien2 TEXT,

        dau_de TEXT,

        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sent_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_date TEXT,
        sent_at TEXT
    )
    """)

    con.commit()
    con.close()


# ============================================================
# TELEGRAM
# ============================================================

def telegram(message):

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:

        r = requests.post(
            url,
            json=payload,
            timeout=15
        )

        if r.status_code != 200:

            logging.error(
                f"Telegram error: {r.text}"
            )

            return False

        return True

    except Exception as e:

        logging.error(e)

        return False


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    df = pd.read_csv(DATA_FILE)

    df["date"] = pd.to_datetime(
        df["date"]
    )

    df = df.sort_values(
        "date"
    ).reset_index(drop=True)

    return df


# ============================================================
# CHUẨN HÓA SỐ
# ============================================================

def norm(x):

    try:

        return f"{int(x):02d}"

    except:

        return None


# ============================================================
# LẤY LÔ TRONG NGÀY
# ============================================================

def get_numbers(row):

    text = str(row["numbers"])

    text = (
        text
        .replace(",", " ")
        .replace(";", " ")
    )

    result = []

    for x in text.split():

        n = norm(x)

        if n is not None:

            result.append(n)

    return result


# ============================================================
# TẠO MATRIX 60 NGÀY
# ============================================================

def create_matrix(df):

    numbers = [
        f"{i:02d}"
        for i in range(100)
    ]

    matrix = {
        n: []
        for n in numbers
    }

    for _, row in df.iterrows():

        day_numbers = set(
            get_numbers(row)
        )

        for n in numbers:

            matrix[n].append(
                1
                if n in day_numbers
                else 0
            )

    return matrix


# ============================================================
# TỶ LỆ XUẤT HIỆN
# ============================================================

def freq(values):

    if not values:

        return 0

    return sum(values) / len(values)


# ============================================================
# LÔ RƠI
#
# Nếu số xuất hiện ngày D
# kiểm tra D+1/D+2/D+3
# ============================================================

def fall_rate(values):

    if len(values) < 5:

        return 0

    appearance = 0
    fall = 0

    for i in range(
        len(values) - 3
    ):

        if values[i] == 1:

            appearance += 1

            if (
                values[i + 1] == 1
                or values[i + 2] == 1
                or values[i + 3] == 1
            ):

                fall += 1

    if appearance == 0:

        return 0

    return fall / appearance


# ============================================================
# GAN
# ============================================================

def missing_days(values):

    count = 0

    for x in reversed(values):

        if x == 0:

            count += 1

        else:

            break

    return count


# ============================================================
# ĐIỂM TỪNG LÔ
# ============================================================

def calculate_scores(df):

    matrix = create_matrix(
        df.tail(LOOKBACK)
    )

    scores = {}

    for number, values in matrix.items():

        f60 = freq(
            values[-60:]
        )

        f30 = freq(
            values[-30:]
        )

        f14 = freq(
            values[-14:]
        )

        f7 = freq(
            values[-7:]
        )

        fall60 = fall_rate(
            values[-60:]
        )

        fall30 = fall_rate(
            values[-30:]
        )

        gan = missing_days(values)

        # ----------------------------------------------------
        # NORMALIZE GAN
        # ----------------------------------------------------

        gan_score = min(
            gan / 15,
            1
        )

        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

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

            "freq60": f60,
            "freq30": f30,
            "freq14": f14,
            "freq7": f7,

            "fall60": fall60,
            "fall30": fall30,

            "gan": gan

        }

    return scores


# ============================================================
# ĐIỂM ĐẦU ĐỀ
# ============================================================

def head_scores(df):

    result = {}

    df60 = df.tail(60)
    df30 = df.tail(30)
    df7 = df.tail(7)

    for head in range(10):

        def calc(data):

            count = 0

            for _, row in data.iterrows():

                nums = get_numbers(row)

                if any(
                    int(n[0]) == head
                    for n in nums
                ):

                    count += 1

            return (
                count / len(data)
                if len(data)
                else 0
            )

        f60 = calc(df60)
        f30 = calc(df30)
        f7 = calc(df7)

        result[head] = (

            0.45 * f60 +
            0.35 * f30 +
            0.20 * f7
        )

    return result


# ============================================================
# CÙNG XUẤT HIỆN
# ============================================================

def pair_frequency(
    a,
    b,
    df
):

    count = 0

    days = df.tail(
        LOOKBACK
    )

    for _, row in days.iterrows():

        nums = set(
            get_numbers(row)
        )

        if a in nums and b in nums:

            count += 1

    if len(days) == 0:

        return 0

    return count / len(days)


# ============================================================
# XIÊN 2
# ============================================================

def calculate_xien(
    scores,
    df
):

    ranking = sorted(
        scores.keys(),
        key=lambda x:
            scores[x]["score"],
        reverse=True
    )

    # Top 20
    candidates = ranking[:20]

    best_pair = None
    best_score = -1

    for a, b in combinations(
        candidates,
        2
    ):

        individual = (

            scores[a]["score"] +
            scores[b]["score"]

        ) / 2

        pair = pair_frequency(
            a,
            b,
            df
        )

        total = (

            0.75 * individual +
            0.25 * pair
        )

        if total > best_score:

            best_score = total
            best_pair = (a, b)

    return best_pair


# ============================================================
# CHỌN 3 LÔ
# ============================================================

def select_loto(scores):

    ranking = sorted(
        scores.keys(),
        key=lambda x:
            scores[x]["score"],
        reverse=True
    )

    candidates = []

    for n in ranking:

        data = scores[n]

        # ưu tiên lô có dấu hiệu rơi

        if data["fall60"] >= 0.10:

            candidates.append(n)

    # fallback
    if len(candidates) < 3:

        candidates = ranking

    return candidates[:3]


# ============================================================
# DỰ BÁO
# ============================================================

def predict(df):

    scores = calculate_scores(
        df
    )

    loto = select_loto(
        scores
    )

    xien = calculate_xien(
        scores,
        df
    )

    heads = head_scores(
        df
    )

    dau = max(
        heads,
        key=heads.get
    )

    return {

        "loto": loto,

        "xien": xien,

        "dau": dau,

        "scores": scores

    }


# ============================================================
# KIỂM TRA ĐÃ KHÓA CHƯA
# ============================================================

def get_locked(target_date):

    con = db()

    cur = con.cursor()

    cur.execute("""
        SELECT
            loto1,
            loto2,
            loto3,
            xien1,
            xien2,
            dau_de
        FROM locked_signal
        WHERE target_date = ?
    """, (target_date,))

    row = cur.fetchone()

    con.close()

    if not row:

        return None

    return {

        "loto": [
            row[0],
            row[1],
            row[2]
        ],

        "xien": [
            row[3],
            row[4]
        ],

        "dau": row[5]

    }


# ============================================================
# KHÓA TÍN HIỆU
# ============================================================

def lock_signal(
    target_date,
    prediction
):

    existing = get_locked(
        target_date
    )

    # --------------------------------------------------------
    # QUAN TRỌNG:
    # Nếu đã có tín hiệu -> KHÔNG tính lại.
    # --------------------------------------------------------

    if existing:

        logging.info(
            f"Tín hiệu {target_date} "
            f"đã khóa."
        )

        return existing

    loto = prediction["loto"]

    xien = prediction["xien"]

    dau = prediction["dau"]

    con = db()

    cur = con.cursor()

    cur.execute("""
        INSERT INTO locked_signal (
            target_date,

            loto1,
            loto2,
            loto3,

            xien1,
            xien2,

            dau_de,

            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        target_date,

        loto[0],
        loto[1],
        loto[2],

        xien[0],
        xien[1],

        str(dau),

        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))

    con.commit()
    con.close()

    logging.info(
        f"Đã khóa tín hiệu {target_date}"
    )

    return prediction


# ============================================================
# GỬI TÍN HIỆU
# ============================================================

def send_signal(
    signal,
    target_date
):

    loto = signal["loto"]

    xien = signal["xien"]

    dau = signal["dau"]

    message = f"""
<b>🔮 TÍN HIỆU XSMB D+1</b>

📅 Ngày: <b>{target_date}</b>

━━━━━━━━━━━━━━

<b>🔥 3 LÔ RƠI</b>

1️⃣ <b>{loto[0]}</b>
2️⃣ <b>{loto[1]}</b>
3️⃣ <b>{loto[2]}</b>

━━━━━━━━━━━━━━

<b>🎯 XIÊN 2</b>

<b>{xien[0]} - {xien[1]}</b>

━━━━━━━━━━━━━━

<b>🎲 ĐẦU ĐỀ</b>

<b>Đầu {dau}</b>

━━━━━━━━━━━━━━

🔒 <b>TÍN HIỆU ĐÃ KHÓA</b>

📊 Dữ liệu:
60 ngày + thống kê lô rơi

⏱ Bot cập nhật:
5 phút/lần

⚠️ Tín hiệu xác suất tham khảo.
"""

    telegram(message)


# ============================================================
# 19:00
#
# CHỈ TÍNH 1 LẦN
# ============================================================

def job_1900():

    logging.info(
        "19:00 - Tạo tín hiệu D+1"
    )

    df = load_data()

    if len(df) < LOOKBACK:

        telegram(
            "⚠️ Chưa đủ 60 ngày "
            "dữ liệu để dự báo."
        )

        return

    last_date = df.iloc[-1]["date"]

    target_date = (
        last_date +
        timedelta(days=1)
    ).strftime("%Y-%m-%d")

    # --------------------------------------------------------
    # KIỂM TRA DATABASE
    # --------------------------------------------------------

    existing = get_locked(
        target_date
    )

    if existing:

        logging.info(
            "Đã có tín hiệu. "
            "Không tính lại."
        )

        send_signal(
            existing,
            target_date
        )

        return

    # --------------------------------------------------------
    # TÍNH DỰ BÁO
    # --------------------------------------------------------

    prediction = predict(
        df
    )

    # --------------------------------------------------------
    # KHÓA
    # --------------------------------------------------------

    signal = lock_signal(
        target_date,
        prediction
    )

    # --------------------------------------------------------
    # GỬI
    # --------------------------------------------------------

    send_signal(
        signal,
        target_date
    )


# ============================================================
# CỨ 5 PHÚT GỬI LẠI
# ============================================================

def job_every_5_minutes():

    df = load_data()

    if len(df) == 0:

        return

    last_date = df.iloc[-1]["date"]

    target_date = (
        last_date +
        timedelta(days=1)
    ).strftime("%Y-%m-%d")

    signal = get_locked(
        target_date
    )

    # --------------------------------------------------------
    # CHƯA CÓ -> KHÔNG TỰ TÍNH
    #
    # Chỉ 19:00 mới được phép tạo tín hiệu.
    # --------------------------------------------------------

    if not signal:

        logging.info(
            "Chưa có tín hiệu khóa."
        )

        return

    logging.info(
        f"Gửi lại tín hiệu {target_date}"
    )

    send_signal(
        signal,
        target_date
    )


# ============================================================
# 18:35
# GỬI KẾT QUẢ NGÀY HÔM ĐÓ
# ============================================================

def job_1835():

    df = load_data()

    if len(df) == 0:

        return

    row = df.iloc[-1]

    date = row["date"].strftime(
        "%d/%m/%Y"
    )

    numbers = get_numbers(row)

    message = f"""
<b>📢 KẾT QUẢ XSMB</b>

📅 <b>{date}</b>

🔢 Lô:
{", ".join(numbers)}

━━━━━━━━━━━━━━

🤖 Dữ liệu đã được cập nhật.
"""

    telegram(message)


# ============================================================
# MAIN
# ============================================================

def main():

    init_db()

    scheduler = BlockingScheduler(
        timezone=TIMEZONE
    )

    # --------------------------------------------------------
    # 18:35
    # --------------------------------------------------------

    scheduler.add_job(
        job_1835,
        "cron",
        hour=18,
        minute=35,
        id="result_1835",
        replace_existing=True
    )

    # --------------------------------------------------------
    # 19:00
    # --------------------------------------------------------

    scheduler.add_job(
        job_1900,
        "cron",
        hour=19,
        minute=0,
        id="prediction_1900",
        replace_existing=True
    )

    # --------------------------------------------------------
    # CỨ 5 PHÚT
    # --------------------------------------------------------

    scheduler.add_job(
        job_every_5_minutes,
        "cron",
        minute="*/5",
        id="signal_5_minutes",
        replace_existing=True
    )

    logging.info(
        "================================="
    )

    logging.info(
        "XSMB BOT STARTED"
    )

    logging.info(
        "18:35 -> Kết quả"
    )

    logging.info(
        "19:00 -> Khóa tín hiệu D+1"
    )

    logging.info(
        "5 phút -> Gửi lại tín hiệu"
    )

    logging.info(
        "================================="
    )

    scheduler.start()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
