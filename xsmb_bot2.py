# ==========================================================
# xsmb_bot2.py — V28.0 | TOÀN BỘ TRONG 1 FILE
# ✅ Không cần file khác | ✅ Lấy dữ liệu thật 2 nguồn | ✅ Dự đoán 90 ngày
# Token: 8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w
# Chat ID: -1001030583610
# ==========================================================

import telebot, json, os, re, time, requests, threading
from datetime import datetime, timedelta
from flask import Flask
from collections import Counter

# ====================== 🔧 CẤU HÌNH ======================
TELEGRAM_TOKEN = "8933441659:AAHbDy-fkWjdplemKGc-81gWJAq8eXRpu0w"
CHAT_ID = "-1001030583610"
DATA_FILE = "xsmb_data.json"
PORT = 10000
ANALYSIS_DAYS = 90
SEND_RESULT_TIME = "18:40"
SEND_PREDICT_TIME = "18:41"

app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# ====================== 💾 QUẢN LÝ DỮ LIỆU ======================
def load_data():
    if not os.path.exists(DATA_FILE): return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except: return {}

def save_data(date_str, special, g1, loto, source="api"):
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", date_str): return False
    if len(special) != 5 or len(g1) != 5: return False
    data = load_data()
    data[date_str] = {
        "special": special.strip(),
        "g1": g1.strip(),
        "loto": [str(x).zfill(2) for x in loto if str(x).isdigit()],
        "source": source,
        "saved_at": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 LƯU OK: {date_str} | Tổng: {len(data)} ngày")
        return True
    except: return False

def get_stats():
    data = load_data()
    if not data: return 0, "--", "--"
    dates = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    return len(data), dates[0], dates[-1]

# ====================== 📡 LẤY DỮ LIỆU THẬT ======================
def lay_ket_qua_xsmb(ngay_str=None):
    if not ngay_str: ngay_str = datetime.now().strftime("%d/%m/%Y")
    try:
        d, m, y = ngay_str.split("/")
        d, m = d.zfill(2), m.zfill(2)
        ymd, ymd_short = f"{y}-{m}-{d}", f"{y}{m}{d}"
        print(f"🔍 Lấy: {ngay_str}")
    except: return None

    # Nguồn 1: api.xoso.me
    try:
        url = f"https://api.xoso.me/xsmb?date={ymd}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            db = str(data.get("dacbiet") or data.get("special", "")).strip()
            g1 = str(data.get("giainhut") or data.get("prize1", "")).strip()
            tat_ca_so = []
            for k, v in data.items():
                if isinstance(v, str) and len(v) == 5 and v.isdigit(): tat_ca_so.append(v)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, str) and len(item) == 5 and item.isdigit(): tat_ca_so.append(item)
            if db: tat_ca_so.append(db)
            if g1: tat_ca_so.append(g1)
            loto = sorted(list(set([n[-2:] for n in tat_ca_so if len(n) == 5 and n.isdigit()])))
            if len(db) == 5 and db.isdigit() and len(g1) == 5 and g1.isdigit() and len(loto) >= 10:
                print(f"✅ Nguồn 1 OK | ĐB:{db} G1:{g1} | {len(loto)} lô")
                return {"date": ngay_str, "special": db, "g1": g1, "loto": loto, "source": "api.xoso.me"}
    except Exception as e: print(f"⚠️ Nguồn 1: {str(e)[:60]}")

    # Nguồn 2: xosodaiphat.com
    try:
        url = f"https://xosodaiphat.com/xsmb-{ymd_short}.html"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            html = resp.text
            dbm = re.search(r'class="special-prize[^>]*>(\d{5})<', html)
            g1m = re.search(r'class="prize-1[^>]*>(\d{5})<', html)
            db = dbm.group(1) if dbm else ""
            g1 = g1m.group(1) if g1m else ""
            all5 = re.findall(r'>(\d{5})<', html)
            loto = sorted(list(set([n[-2:] for n in all5 if len(n)==5 and n.isdigit()])))
            if len(db) == 5 and db.isdigit() and len(g1) == 5 and g1.isdigit() and len(loto) >= 10:
                print(f"✅ Nguồn 2 OK | ĐB:{db} G1:{g1} | {len(loto)} lô")
                return {"date": ngay_str, "special": db, "g1": g1, "loto": loto, "source": "xosodaiphat.com"}
    except Exception as e: print(f"⚠️ Nguồn 2: {str(e)[:60]}")

    print(f"❌ Tất cả nguồn thất bại — {ngay_str}")
    return None

# ====================== 📊 DỰ ĐOÁN ======================
def tinh_du_doan():
    data = load_data()
    tong = len(data)
    if tong < 30: return f"⚠️ Cần ít nhất 30 ngày dữ liệu. Hiện có {tong} ngày.\n👉 Gõ /lay90 trước!"
    sap_xep = sorted(data.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    so_ngay = min(ANALYSIS_DAYS, tong)
    ds = sap_xep[:so_ngay]
    tat_ca_lo, tat_ca_dau = [], []
    for ngay in ds:
        kq = data[ngay]
        for lo in kq.get("loto", []):
            if len(lo) == 2 and lo.isdigit(): tat_ca_lo.append(lo)
        db = kq.get("special", "")
        if len(db) == 5 and db.isdigit():
            tat_ca_lo.append(db[-2:])
            tat_ca_dau.append(db[0])
    if not tat_ca_lo: return "⚠️ Dữ liệu trống. Gõ /lay90!"
    dem_lo = Counter(tat_ca_lo)
    ds_lo = [{"so": s, "lan": c, "ty_le": round(c/so_ngay*100,1)} for s,c in dem_lo.items()]
    ds_lo.sort(key=lambda x: -x["ty_le"])
    top3 = ds_lo[:3]
    xien = [top3[0]["so"], top3[1]["so"]] if len(top3)>=2 else ["00","01"]
    dau_de, ty_le_dau = "9", 10.0
    if tat_ca_dau:
        d = Counter(tat_ca_dau).most_common(1)[0]
        dau_de, ty_le_dau = d[0], round(d[1]/len(tat_ca_dau)*100,1)
    ngay_mai = (datetime.now()+timedelta(days=1)).strftime("%d/%m/%Y")
    return f"""
📊 *DỰ ĐOÁN NGÀY MAI: {ngay_mai}*
📈 Phân tích: {so_ngay} ngày dữ liệu THẬT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 *3 CON LÔ TỶ LỆ CAO NHẤT:*
   1 • `{top3[0]['so']}` → {top3[0]['lan']} lần | {top3[0]['ty_le']}%
   2 • `{top3[1]['so']}` → {top3[1]['lan']} lần | {top3[1]['ty_le']}%
   3 • `{top3[2]['so']}` → {top3[2]['lan']} lần | {top3[2]['ty_le']}%
🔀 *CẶP LÔ XIÊN:* `{xien[0]}` + `{xien[1]}`
🔢 *ĐẦU SỐ ĐỀ:* `{dau_de}` | {ty_le_dau}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Chỉ tham khảo!
"""

# ====================== 🤖 LỆNH BOT ======================
@app.route('/')
def home(): return "✅ Bot XSMB V28.0 — Chạy từ xsmb_bot2.py!"

@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id,
        "🤖 *BOT XSMB — V28.0 | TOÀN BỘ TRONG 1 FILE ✅*\n"
        "/lay90 = Lấy 90 ngày dữ liệu thật\n"
        "/dudoan = Xem dự đoán\n"
        "/status = Xem trạng thái dữ liệu\n"
        "Ngày VD: 29082026 → Xem kết quả lịch sử\n\n"
        "📌 Gõ /lay90 → Bắt đầu!",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['status'])
def cmd_status(m):
    tong, tu, den = get_stats()
    bot.send_message(m.chat.id,
        f"📊 *TRẠNG THÁI DỮ LIỆU*\n• Tổng ngày: *{tong} ngày*\n• Phạm vi: {tu} → {den}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['lay90'])
def cmd_lay90(m):
    bot.send_message(m.chat.id, "🚀 *ĐANG LẤY 90 NGÀY DỮ LIỆU...*\n⏰ 2-3 phút nhé!", parse_mode="Markdown")
    def lay_async():
        today = datetime.now()
        lay_moi = that_bai = 0
        for offset in range(1, ANALYSIS_DAYS+1):
            target_date = today - timedelta(days=offset)
            date_str = target_date.strftime("%d/%m/%Y")
            if date_str in load_data(): continue
            kq = lay_ket_qua_xsmb(date_str)
            if kq and save_data(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"]):
                lay_moi += 1
            else:
                that_bai += 1
            time.sleep(0.8)
        tong, _, _ = get_stats()
        bot.send_message(m.chat.id,
            f"✅ *HOÀN THÀNH!* 🎉\n📊 Tổng: *{tong} ngày*\n• Lấy mới: {lay_moi}\n• Thất bại: {that_bai}\n👉 Gõ /dudoan!",
            parse_mode="Markdown"
        )
    threading.Thread(target=lay_async, daemon=True).start()

@bot.message_handler(commands=['dudoan'])
def cmd_dudoan(m):
    bot.send_message(m.chat.id, tinh_du_doan(), parse_mode="Markdown")

# Xem ngày cũ
@bot.message_handler(func=lambda msg: msg.text and len(msg.text.strip())==8 and msg.text.strip().isdigit())
def xem_ngay_cu(m):
    text = m.text.strip()
    try:
        d, mo, y = text[:2], text[2:4], text[4:]
        date_str = f"{d}/{mo}/{y}"
        data = load_data()
        if date_str in data:
            kq = data[date_str]
            bot.send_message(m.chat.id,
                f"📅 *KẾT QUẢ NGÀY: {date_str}*\n🏆 Đặc Biệt: `{kq['special']}`\n🥇 Giải Nhất: `{kq['g1']}`\n📌 Nguồn: {kq.get('source')}",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(m.chat.id, f"🔍 *ĐANG LẤY DỮ LIỆU NGÀY {date_str}...*", parse_mode="Markdown")
            kq = lay_ket_qua_xsmb(date_str)
            if kq and save_data(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"]):
                bot.send_message(m.chat.id,
                    f"✅ *ĐÃ LẤY ĐƯỢC!* 🎉\n📅 {date_str}\n🏆 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`",
                    parse_mode="Markdown"
                )
            else:
                bot.send_message(m.chat.id, f"⚠️ *Không lấy được dữ liệu ngày {date_str}*", parse_mode="Markdown")
    except:
        bot.send_message(m.chat.id, "⚠️ Sai định dạng! VD: `29082026`", parse_mode="Markdown")

# ====================== ⏰ TỰ ĐỘNG GỬI ======================
def gui_tu_dong():
    da_gui_kq, da_gui_dd = set(), set()
    while True:
        try:
            now = datetime.now()
            hom_nay = now.strftime("%d/%m/%Y")
            gio = now.strftime("%H:%M")
            if gio == SEND_RESULT_TIME and hom_nay not in da_gui_kq:
                kq = lay_ket_qua_xsmb(hom_nay)
                if kq and save_data(hom_nay, kq["special"], kq["g1"], kq["loto"], kq["source"]):
                    bot.send_message(CHAT_ID,
                        f"🏆 *KẾT QUẢ NGÀY D — {hom_nay}*\n🎯 ĐB: `{kq['special']}`\n🥇 G1: `{kq['g1']}`\n📌 Nguồn: {kq['source']}",
                        parse_mode="Markdown"
                    )
                da_gui_kq.add(hom_nay)
            if gio == SEND_PREDICT_TIME and hom_nay not in da_gui_dd:
                bot.send_message(CHAT_ID, tinh_du_doan(), parse_mode="Markdown")
                da_gui_dd.add(hom_nay)
            time.sleep(30)
        except Exception as e:
            print(f"⚠️ Lỗi tự động gửi: {e}")
            time.sleep(10)

# ====================== 🚀 CHẠY BOT ======================
def run_bot():
    print("✅ BOT V28.0 — CHẠY TỪ xsmb_bot2.py | TOÀN BỘ TRONG 1 FILE!")
    try: bot.remove_webhook()
    except: pass
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=40, allowed_updates=None)
        except Exception as e:
            print(f"⚠️ Lỗi polling: {e} → đợi 5s...")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False), daemon=True).start()
    threading.Thread(target=gui_tu_dong, daemon=True).start()
    run_bot()
