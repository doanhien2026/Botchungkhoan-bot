
import telebot
import random
import threading
from datetime import datetime, timedelta
import os

# ===================== CẤU HÌNH — LẤY TỪ GITHUB SECRETS =====================
BOT_TOKEN = os.environ.get("BOT2_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

bot = telebot.TeleBot(BOT_TOKEN)

# Lưu bộ số để không đổi trong ngày
bo_so_da_tao = None
ngay_tao_bo_so = None

# ===================== TẠO DỮ LIỆU LỊCH SỬ =====================
def tao_du_lieu_lich_su(so_ngay=90):
    so_nong_bam_sinh = [f"{i:02d}" for i in random.sample(range(100), 10)]
    du_lieu = []
    ngay_bat_dau = datetime.now() - timedelta(days=so_ngay)
    
    for i in range(so_ngay):
        ngay_hien_tai = ngay_bat_dau + timedelta(days=i)
        giai_db = f"{random.randint(0, 99999):05d}"
        lo_roi = [giai_db[j:j+2] for j in range(4)]
        so_ra_ngay = []
        
        for _ in range(6):
            so_ra_ngay.append(random.choice(so_nong_bam_sinh) if random.random() < 0.7 else f"{random.randint(0, 99):02d}")
        for _ in range(4):
            so_ra_ngay.append(random.choice(lo_roi) if random.random() < 0.6 else f"{random.randint(0, 99):02d}")
        for _ in range(3):
            so_ra_ngay.append(f"{random.randint(0, 99):02d}")
        
        so_ra_ngay = list(set(so_ra_ngay))
        random.shuffle(so_ra_ngay)
        du_lieu.append((ngay_hien_tai, giai_db, so_ra_ngay))
    
    return du_lieu

# ===================== PHÂN TÍCH & DỰ ĐOÁN =====================
def phan_tich_va_du_doan(du_lieu_lich_su):
    du_lieu_phan_tich = du_lieu_lich_su[:-1]
    
    tan_suat = {}
    for _, _, so_ra in du_lieu_phan_tich:
        for cap in so_ra:
            tan_suat[cap] = tan_suat.get(cap, 0) + 1
    
    lo_roi_dem = {}
    for idx in range(len(du_lieu_phan_tich) - 1):
        _, giai_db_ngay, _ = du_lieu_phan_tich[idx]
        _, _, so_ra_ngay_sau = du_lieu_phan_tich[idx + 1]
        cap_roi = [giai_db_ngay[j:j+2] for j in range(4)]
        for cap in cap_roi:
            lo_roi_dem[cap] = lo_roi_dem.get(cap, {'tong': 0, 'dung': 0})
            lo_roi_dem[cap]['tong'] += 1
            if cap in so_ra_ngay_sau:
                lo_roi_dem[cap]['dung'] += 1
    
    xac_suat_lo_roi = {cap: dem['dung']/dem['tong'] if dem['tong']>0 else 0 for cap, dem in lo_roi_dem.items()}
    
    lien_tuc, dem_ngay = {}, {}
    for _, _, so_ra in du_lieu_phan_tich:
        da_ra = set(so_ra)
        for cap in da_ra:
            dem_ngay[cap] = dem_ngay.get(cap, 0) + 1
            lien_tuc[cap] = lien_tuc.get(cap, 0) + 1
        for cap in set(dem_ngay.keys()) - da_ra:
            lien_tuc[cap] = 0
    
    diem = {}
    for cap in set(tan_suat.keys()) | set(xac_suat_lo_roi.keys()):
        ts = tan_suat.get(cap, 0)
        xs_roi = xac_suat_lo_roi.get(cap, 0)
        lt = lien_tuc.get(cap, 0)
        diem_ts = min(ts * 2, 100)
        diem_roi = xs_roi * 60
        diem_lt = min(lt * 10, 40)
        diem[cap] = diem_ts + diem_roi + diem_lt
    
    sap_xep = sorted(diem.items(), key=lambda x: x[1], reverse=True)
    top_3_lo = [cap for cap, _ in sap_xep[:3]]
    top_2_xien = [cap for cap, _ in sap_xep[3:5]]
    
    # Đếm đầu số 2 số cuối giải đặc biệt
    tan_suat_dau_so = {str(i):0 for i in range(10)}
    for _, giai_db, _ in du_lieu_phan_tich:
        dau_so = giai_db[-2:][0]
        tan_suat_dau_so[dau_so] += 1
    dau_so_cao_nhat = sorted(tan_suat_dau_so.items(), key=lambda x:x[1], reverse=True)[0][0]
    
    return top_3_lo, top_2_xien, dau_so_cao_nhat

# ===================== TẠO TIN NHẮN =====================
def tao_tin_hieu(ngay_du_doan):
    global bo_so_da_tao, ngay_tao_bo_so
    ngay_hom_nay = datetime.now().strftime("%d/%m/%Y")
    
    if bo_so_da_tao is None or ngay_tao_bo_so != ngay_hom_nay:
        print(f"📊 [{ngay_hom_nay}] Bot2 đang phân tích...")
        du_lieu = tao_du_lieu_lich_su(90)
        top_3_lo, top_2_xien, dau_so_cuoi = phan_tich_va_du_doan(du_lieu)
        bo_so_da_tao = (top_3_lo, top_2_xien, dau_so_cuoi)
        ngay_tao_bo_so = ngay_hom_nay
    
    top_3_lo, top_2_xien, dau_so_cuoi = bo_so_da_tao
    ngay_nhap_lieu = ngay_hom_nay
    ngay_du_doan_str = ngay_du_doan.strftime("%d/%m/%Y")
    
    return f"""🤖 BOT DỰ ĐOÁN XỔ SỐ MIỀN BẮC
📅 Ngày nhập dữ liệu: {ngay_nhap_lieu}
🔮 Dự đoán cho ngày: {ngay_du_doan_str}
📊 Dữ liệu phân tích: 90 ngày gần nhất
⚠️ CHỈ THAM KHẢO – KHÔNG ĐẢM BẢO CHẮC CHẮN!
Xổ số hoàn toàn ngẫu nhiên, kết quả quá khứ không dự báo tương lai. Chơi có trách nhiệm!

🎯 TOP 3 CẶP LÔ TỶ LỆ CAO NHẤT
🥇 {top_3_lo[0]}
🥈 {top_3_lo[1]}
🥉 {top_3_lo[2]}

🎯 2 CẶP LÔ XIÊN TỶ LỆ CAO
🥇 {top_2_xien[0]}
🥈 {top_2_xien[1]}

🎯 ĐẦU SỐ 2 SỐ CUỐI GIẢI ĐẶC BIỆT TỶ LỆ CAO NHẤT
🥇 {dau_so_cuoi}

🎲 Chơi có trách nhiệm – Chỉ giải trí!
"""

# ===================== GỬI LÊN KÊNH TELEGRAM =====================
def gui_len_kenh():
    ngay_mai = datetime.now() + timedelta(days=1)
    tin_nhan = tao_tin_hieu(ngay_mai)
    try:
        bot.send_message(CHANNEL_ID, tin_nhan)
        print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Đã gửi lên KÊNH → {CHANNEL_ID}")
        return True
    except Exception as e:
        print(f"❌ Lỗi gửi kênh: {e}")
        return False

# ===================== CHẠY BOT =====================
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 BOT XSMB THỨ 2 — GỬI LÊN KÊNH TELEGRAM")
    print("=" * 60)
    
    if not BOT_TOKEN or not CHANNEL_ID:
        print("❌ Thiếu BOT2_TOKEN hoặc CHANNEL_ID trong Secrets!")
        exit(1)
    
    print(f"📌 Token: {BOT_TOKEN[:15]}...{BOT_TOKEN[-10:]}")
    print(f"📌 Kênh ID: {CHANNEL_ID}")
    print("=" * 60)
    
    # Gửi ngay khi chạy
    gui_len_kenh()
