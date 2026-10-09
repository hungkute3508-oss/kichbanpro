import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# Đảm bảo in tiếng Việt chuẩn
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    base_dir = Path(__file__).resolve().parent
    build_dir = base_dir / "build"
    dist_dir = base_dir / "dist"
    app_name = "AI_Video_Transcriber"
    target_dist = dist_dir / app_name

    print("==================================================")
    print("   BẮT ĐẦU ĐÓNG GÓI PORTABLE PACKAGE HOÀN CHỈNH   ")
    print("==================================================")

    # 1. Dọn dẹp thư mục build & dist cũ
    print("\n1. Dọn dẹp bản build cũ...")
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)
    if target_dist.exists():
        shutil.rmtree(target_dist, ignore_errors=True)

    # 2. Chạy PyInstaller
    print("\n2. Đang biên dịch ứng dụng bằng PyInstaller (PyQt6 + Playwright + Gemini)...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name", app_name,
        "--onedir",
        "--windowed",
        "--clean",
        "--noconfirm",
        "--collect-all", "playwright",
        "--collect-all", "PyQt6",
        "--hidden-import", "google.genai",
        "--hidden-import", "google.genai.types",
        "--hidden-import", "colorama",
        str(base_dir / "main.py"),
    ]

    print("Lệnh thực thi:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(base_dir))
    if res.returncode != 0:
        print("✘ Lỗi: Quá trình PyInstaller thất bại!")
        sys.exit(res.returncode)

    if not target_dist.exists():
        print(f"✘ Lỗi: Không tìm thấy thư mục đầu ra {target_dist}")
        sys.exit(1)

    print(f"✔ Biên dịch PyInstaller thành công vào: {target_dist}")

    # 3. Tích hợp FFmpeg và FFprobe vào gói ứng dụng
    print("\n3. Đang tích hợp FFmpeg & FFprobe portable...")
    ffmpeg_source = r"C:\Users\Hung\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-essentials_build\bin"
    ff_bin = Path(ffmpeg_source)

    for bname in ["ffmpeg.exe", "ffprobe.exe"]:
        src_file = ff_bin / bname
        if src_file.exists():
            dst_file = target_dist / bname
            print(f"-> Sao chép {bname} ({src_file.stat().st_size // (1024*1024)} MB)...")
            shutil.copy2(str(src_file), str(dst_file))
        else:
            print(f"⚠ Cảnh báo: Không tìm thấy {src_file}, kiểm tra PATH...")
            # Thử tìm trên PATH
            found = shutil.which(bname.replace(".exe", ""))
            if found:
                print(f"-> Sao chép {bname} từ PATH: {found}...")
                shutil.copy2(found, str(target_dist / bname))

    # 4. Sao chép các tệp cấu hình và tệp bổ trợ
    print("\n4. Sao chép tệp cấu hình và kịch bản hỗ trợ...")
    for aux_file in ["config.json", "start_chrome_debug.bat"]:
        src = base_dir / aux_file
        if src.exists():
            shutil.copy2(str(src), str(target_dist / aux_file))
            print(f"-> Đã sao chép: {aux_file}")

    # 5. Tạo tệp Hướng dẫn sử dụng nhanh
    readme_content = """================================================================================
🎬 AI VIDEO TRANSCRIBER & SUBTITLE AUTO-RENAMER (PORTABLE PACKAGE)
================================================================================

1. CÁCH SỬ DỤNG:
   - Khởi chạy chương trình: Nhấp đúp vào file `AI_Video_Transcriber.exe`.
   - Giao diện đồ họa (GUI) sẽ xuất hiện ngay lập tức.

2. CÁC TÍNH NĂNG ĐÃ TÍCH HỢP SẴN:
   - Tích hợp sẵn FFmpeg & FFprobe (không cần cài đặt thêm phần mềm phụ trợ).
   - Tự động điều khiển Chrome Remote Debugging (port 9222) mà không cần API Key.
   - Hỗ trợ nhập Google Gemini API Key nếu muốn chạy ẩn qua API.
   - Tự động bóc băng âm thanh, tạo phụ đề .srt, đổi tên video và tạo file metadata Shopee.

3. KẾT NỐI CHROME DEBUG:
   - Nhấp đúp vào `start_chrome_debug.bat` (hoặc bấm nút "Mở Chrome Debug" trên ứng dụng).
   - Mở sẵn tab https://gemini.google.com và đăng nhập tài khoản Google của bạn.
   - Bấm "Bắt đầu xử lý" trên tool để tự động hóa toàn bộ quy trình.

Chúc bạn có những trải nghiệm tuyệt vời!
================================================================================
"""
    readme_path = target_dist / "HUONG_DAN_SU_DUNG.txt"
    with open(readme_path, "w", encoding="utf-8-sig") as f:
        f.write(readme_content)
    print("-> Đã tạo: HUONG_DAN_SU_DUNG.txt")

    # 6. Tạo file nén Portable ZIP để dễ dàng chia sẻ hoặc sao lưu
    print("\n5. Đang nén thành tệp Portable ZIP...")
    zip_path = dist_dir / "AI_Video_Transcriber_v1.0_Portable.zip"
    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(target_dist):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(dist_dir)
                zf.write(str(full_path), str(rel_path))

    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"✔ Đã tạo file nén: {zip_path.name} ({zip_size_mb:.1f} MB)")

    print("\n==================================================")
    print("🎉 HOÀN TẤT ĐÓNG GÓI HOÀN CHỈNH!")
    print(f"📁 Thư mục ứng dụng: {target_dist}")
    print(f"📦 File nén chia sẻ: {zip_path}")
    print("==================================================")

if __name__ == "__main__":
    main()
