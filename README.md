# ⚡ AUTO CLICKER PRO - TOOL AUTO CLICK SIÊU NHẸ, KHÔNG LAG

Công cụ tự động click chuột chuyên nghiệp, tốc độ cao với 2 phiên bản lựa chọn: **C# Native (.exe)** (Khuyên dùng - 0% CPU, siêu mượt) và **Python**.

---

## 🚀 1. PHIÊN BẢN C# NATIVE (.EXE) - [KHUYÊN DÙNG]

> **Ưu điểm vượt trội**:
> - ⚡ **Mức chiếm dụng CPU gần như 0.0%**: Không ngốn CPU, không làm nóng máy hay kêu quạt.
> - 🎯 **Không gây lag chuột/bàn phím**: Sử dụng API chuẩn `RegisterHotKey` của Windows, không can thiệp sâu vào pipeline bàn phím như thư viện hook của Python.
> - 📦 **1 File duy nhất**: Chỉ cần nhấp đúp vào **`AutoClicker.exe`** là mở ngay tức thì trong 0.1 giây, không cần cài đặt Python.

### Cách chạy:
Nhấp đúp chuột vào file **`AutoClicker.exe`** tại:
`e:\Tools\autoclick\AutoClicker.exe`

---

## 🐍 2. PHIÊN BẢN PYTHON (ĐÃ ĐƯỢC TỐI ƯU HÓA)

- Đã loại bỏ vòng lặp Spin-wait (nguyên nhân gây 100% CPU ở bản cũ).
- Đã điều tiết tần suất gửi sự kiện cập nhật giao diện (Throttle UI dispatch) để tránh làm nghẽn Tkinter.
- Chạy bằng file: **`run.bat`** hoặc `python main.py`.

---

## 🌟 TÍNH NĂNG CHÍNH

1. **Giao diện trực quan**:
   - 2 nút bấm to tướng ngay trên đầu: 🟩 **`▶ BẮT ĐẦU CHẠY (Phím F6)`** và 🟥 **`⏹ DỪNG LẠI (Phím F6)`**.
   - Bảng đo: Số lần click, Tốc độ thực tế (**CPS - Clicks Per Second**), Tọa độ chuột thời gian thực.
2. **Khoảng cách thời gian click (Interval)**:
   - Tùy chỉnh: Giờ, Phút, Giây, Mili-giây (từ 1ms).
   - **Độ trễ ngẫu nhiên (Jitter) ± ms**: Giả lập click người thật chống ban/phát hiện macro.
3. **Thao tác chuột**:
   - Phím: Chuột trái, Chuột phải, Chuột giữa.
   - Kiểu: Click đơn, Click đúp, Click 3 lần, Giữ chuột liên tục (Hold).
4. **Vị trí con trỏ**:
   - Vị trí hiện tại của chuột.
   - Tọa độ cố định (X, Y) kèm phím tắt lấy nhanh **`F7`**.
5. **Số lần lặp**: Lặp vô tận hoặc lặp cố định N lần rồi tự dừng.
6. **Tiện ích**: Luôn nổi trên cùng (TopMost), đổi phím tắt (F1 - F12), reset bộ đếm.

---

## 🎮 PHÍM TẮT TOÀN CỤC

| Phím | Tác vụ |
| :--- | :--- |
| **F6** | **Bật / Tắt Auto Click** (Hoạt động cả khi ở trong Game hoặc phần mềm khác) |
| **F7** | **Lấy nhanh tọa độ con trỏ chuột** |
