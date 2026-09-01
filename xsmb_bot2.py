# Chỉ cần đảm bảo phần gọi lấy dữ liệu có log rõ như sau:
print(f"📥 Đang lấy dữ liệu: {date_str}...")
kq = lay_ket_qua_xsmb(date_str)

if kq and save_data(date_str, kq["special"], kq["g1"], kq["loto"], kq["source"]):
    print(f"✅ ✅ ĐÃ LƯU THÀNH CÔNG: {date_str} | ĐB:{kq['special']}")
else:
    print(f"❌ KHÔNG LẤY ĐƯỢC DỮ LIỆU: {date_str}")
