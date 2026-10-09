# Tool Lấy Kịch Bản Video & Tự Động Đổi Tên (Hỗ Trợ Chrome Debug & Gemini API)

Công cụ tự động hóa toàn diện quy trình bóc băng âm thanh, tạo file phụ đề `.srt` chuẩn mốc thời gian và đặt tên cho video theo nội dung kịch bản bằng sức mạnh của **Google Gemini**.

---

## 🌟 2 Chế Độ Hoạt Động Cực Kỳ Tiện Lợi

### 1. Chế độ Điều khiển Chrome Debug (KHÔNG CẦN GEMINI API KEY)
- Bạn chỉ cần mở Chrome ở chế độ debug (có sẵn nút bấm hoặc click đúp file `start_chrome_debug.bat`).
- Đăng nhập tài khoản Google và mở tab `https://gemini.google.com` (dùng tài khoản miễn phí hoặc Gemini Advanced không giới hạn).
- Tool sẽ **tự động kết nối vào tab Chrome đang mở**, đính kèm file âm thanh, gửi prompt, lấy kết quả kịch bản phụ đề và tự động lưu/đổi tên file!

### 2. Chế độ Gemini API Key
- Dành cho những ai muốn chạy ẩn hoàn toàn không cần mở giao diện trình duyệt, sử dụng API Key từ Google AI Studio.

---

## ⚡ Các Tính Năng Chính
1. **Trích xuất âm thanh siêu tốc**:
   - Tự động dùng `FFmpeg` tách audio từ mọi video (`.mp4`, `.mkv`, `.mov`, `.avi`, `.webm`...).
   - Nén MP3 16kHz mono (64kbps) cực nhẹ, đính kèm vào chat trong chớp mắt.
2. **Kịch bản phụ đề chuẩn SubRip (.srt)**:
   - Mốc thời gian `00:00:01,000 --> 00:00:04,500` chuẩn xác từ âm thanh.
3. **Tự động đặt tên Video & File SRT theo nội dung**:
   - Phân tích nội dung và tạo tiêu đề ngắn gọn (4 - 10 từ).
   - Tự động lọc bỏ các ký tự cấm của Windows (`\ / : * ? " < > |`).
   - Đổi tên file video và lưu file `.srt` tương ứng.
4. **Giao diện trực quan**:
   - Kéo thả video, hàng đợi xử lý nhiều video, thanh tiến trình, xem trước phụ đề.

---

## 🚀 Hướng Dẫn Sử Dụng Nhanh

### Cách 1: Sử dụng qua Giao diện Đồ họa (Khuyên dùng)
1. **Mở Chrome Debug**:
   - Click đúp vào file `start_chrome_debug.bat` (hoặc bấm nút **"🚀 Mở Chrome Debug"** trên phần mềm).
   - Đăng nhập Google và giữ nguyên tab `https://gemini.google.com`.
2. **Khởi động tool**:
   - Click đúp vào `run_tool.bat` (hoặc chạy lệnh `python main.py`).
3. **Thực hiện**:
   - Kéo thả video cần bóc kịch bản vào bảng.
   - Bấm **🚀 BẮT ĐẦU XỬ LÝ**.
   - Xem phụ đề xuất hiện ngay ở tab **Xem Trước Phụ Đề (.srt)** và bấm **📂 Mở Thư Mục** để nhận video đã đổi tên!


---

### 3. Cách sử dụng bằng Dòng Lệnh (CLI)

- **Xử lý 1 file video:**
  ```bash
  python main.py "D:/videos/my_video.mp4" --api-key "AIzaSy..."
  ```

- **Xử lý cả thư mục video hàng loạt:**
  ```bash
  python main.py "D:/videos"
  ```

- **Các tham số tùy chọn:**
  - `--model`: Chọn model (mặc định: `gemini-2.5-flash`, hoặc `gemini-2.0-flash`, `gemini-2.5-pro`).
  - `--output-dir`: Thư mục lưu kết quả.
  - `--no-rename`: Không đổi tên file video gốc (chỉ tạo file srt có tên theo nội dung).
  - `--keep-audio`: Giữ lại file âm thanh `.mp3` tạm.

---

## 📁 Cấu Trúc Mã Nguồn

- `core.py`: Module lõi xử lý FFmpeg, giao tiếp Gemini API, bóc tách `[TITLE]` và `[SRT]`, chuẩn hóa tên file.
- `gui.py`: Giao diện người dùng đồ họa PyQt6 chuyên nghiệp, đa luồng (multi-threaded không bị đơ giao diện).
- `cli.py`: Giao diện dòng lệnh thân thiện với màu sắc trực quan (`colorama`).
- `config.py`: Quản lý lưu trữ API key, model, tùy chọn vào `config.json`.
- `main.py`: Điểm khởi chạy tự động nhận biết chế độ GUI hoặc CLI.
- `run_tool.bat`: Phím tắt click đúp chạy chương trình trên Windows.
