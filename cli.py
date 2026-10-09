import argparse
import os
import sys
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from colorama import Fore, Style, init
from config import load_config, save_config
from core import process_single_video


init(autoreset=True)

SUPPORTED_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv", ".ts", ".m4v"}


def print_banner():
    banner = f"""
{Fore.CYAN}========================================================================
    AI VIDEO TO SRT & AUTO RENAMER (GOOGLE GEMINI 2.5 FLASH)
    Trích xuất âm thanh -> Bóc kịch bản SRT -> Đặt tên Video theo nội dung
========================================================================{Style.RESET_ALL}
"""
    print(banner)


def main():
    parser = argparse.ArgumentParser(
        description="Tool tự động trích xuất âm thanh từ video, gửi lên Gemini để lấy kịch bản SRT và đặt tên file video theo nội dung."
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Đường dẫn tới file video hoặc thư mục chứa các file video cần xử lý.",
    )
    parser.add_argument(
        "--mode",
        choices=["chrome", "api"],
        default=None,
        help="Chế độ xử lý: 'chrome' (Điều khiển Chrome tab Gemini qua Remote Debug) hoặc 'api' (Dùng Gemini API Key). Mặc định: chrome.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9222,
        help="Cổng Chrome Remote Debugging (Mặc định: 9222).",
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        help="Google Gemini API Key (chỉ cần khi dùng mode 'api').",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model Gemini sử dụng (Mặc định: gemini-2.5-flash).",
    )
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default=None,
        help="Thư mục xuất file video và srt (Mặc định: cùng thư mục video gốc).",
    )
    parser.add_argument(
        "--no-rename",
        action="store_true",
        help="Không đổi tên video gốc (chỉ lưu file srt theo tiêu đề nội dung).",
    )
    parser.add_argument(
        "--no-subfolder",
        action="store_true",
        help="Không tạo thư mục riêng cho từng video (lưu file trực tiếp tại thư mục đích).",
    )
    parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="Giữ lại file âm thanh tạm mp3 sau khi xử lý xong.",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Không tạo file metadata.txt trong thư mục video (Mặc định: Có tạo).",
    )


    args = parser.parse_args()
    print_banner()

    cfg = load_config()
    mode = args.mode or cfg.get("mode", "chrome")
    chrome_port = args.port or cfg.get("chrome_port", 9222)
    api_key = args.api_key or cfg.get("api_key", "")

    if mode == "api" and not api_key:
        print(f"{Fore.RED}[LỖI] Chưa có Gemini API Key!{Style.RESET_ALL}")
        api_key = input(">> Nhập Gemini API Key của bạn: ").strip()
        if not api_key:
            print(f"{Fore.RED}[LỖI] Không thể tiếp tục nếu không có API Key. Thoát.{Style.RESET_ALL}")
            sys.exit(1)
        cfg["api_key"] = api_key
        save_config(cfg)
        print(f"{Fore.GREEN}[OK] Đã lưu API Key vào config.json.{Style.RESET_ALL}\n")
    elif mode == "chrome":
        print(f"{Fore.CYAN}[CHẾ ĐỘ] Đang sử dụng Chrome Remote Debugging (Port {chrome_port}). Không cần API Key!{Style.RESET_ALL}")


    input_path = args.input
    if not input_path:
        input_path = input(">> Nhập đường dẫn file video hoặc thư mục video: ").strip(' "\'')
        if not input_path:
            print(f"{Fore.RED}[LỖI] Đường dẫn không được để trống.{Style.RESET_ALL}")
            sys.exit(1)

    p = Path(input_path).resolve()
    if not p.exists():
        print(f"{Fore.RED}[LỖI] Đường dẫn không tồn tại: {p}{Style.RESET_ALL}")
        sys.exit(1)

    video_files = []
    if p.is_file():
        if p.suffix.lower() in SUPPORTED_EXTS:
            video_files.append(p)
        else:
            print(f"{Fore.YELLOW}[CẢNH BÁO] Định dạng file {p.suffix} có thể không được hỗ trợ chính thức.{Style.RESET_ALL}")
            video_files.append(p)
    elif p.is_dir():
        for file in p.iterdir():
            if file.is_file() and file.suffix.lower() in SUPPORTED_EXTS:
                video_files.append(file)
        if not video_files:
            print(f"{Fore.YELLOW}[THÔNG BÁO] Không tìm thấy file video nào trong thư mục: {p}{Style.RESET_ALL}")
            sys.exit(0)

    model_name = args.model or cfg.get("model", "gemini-2.5-flash")
    rename_video = not args.no_rename if args.no_rename else cfg.get("rename_video", True)
    output_dir = args.output_dir or cfg.get("output_dir") or None
    keep_audio = args.keep_audio or cfg.get("keep_temp_audio", False)

    create_subfolder = not args.no_subfolder if args.no_subfolder else cfg.get("create_subfolder", True)
    create_metadata = not args.no_metadata if args.no_metadata else cfg.get("create_metadata", True)
    metadata_template = cfg.get("metadata_template")

    print(f"{Fore.CYAN}Tổng số video cần xử lý: {len(video_files)}{Style.RESET_ALL}")
    print(f"Model: {Fore.YELLOW}{model_name}{Style.RESET_ALL}")
    print(f"Đổi tên video: {Fore.YELLOW}{'Có' if rename_video else 'Không'}{Style.RESET_ALL}")
    print(f"Tạo thư mục riêng: {Fore.YELLOW}{'Có' if create_subfolder else 'Không'}{Style.RESET_ALL}")
    print(f"Tạo file metadata.txt: {Fore.YELLOW}{'Có' if create_metadata else 'Không'}{Style.RESET_ALL}")
    if output_dir:
        print(f"Thư mục xuất: {Fore.YELLOW}{output_dir}{Style.RESET_ALL}")
    print("-" * 60)

    success_count = 0
    fail_count = 0

    for idx, vid in enumerate(video_files, 1):
        print(f"\n{Fore.GREEN}[{idx}/{len(video_files)}] Đang xử lý: {vid.name}{Style.RESET_ALL}")

        def log_cb(msg: str):
            print(f"  --> {msg}")

        try:
            res = process_single_video(
                video_path=str(vid),
                api_key=api_key,
                mode=mode,
                chrome_port=chrome_port,
                model_name=model_name,
                custom_prompt=cfg.get("custom_prompt"),
                rename_video=rename_video,
                create_subfolder=create_subfolder,
                create_metadata=create_metadata,
                metadata_template=metadata_template,
                output_dir=output_dir,
                keep_temp_audio=keep_audio,
                log_cb=log_cb,
            )

            print(f"{Fore.GREEN}✔ THÀNH CÔNG!{Style.RESET_ALL}")
            print(f"  • Tiêu đề mới   : {Fore.CYAN}{res['title']}{Style.RESET_ALL}")
            if res.get("product_name"):
                print(f"  • Sản phẩm      : {Fore.CYAN}{res['product_name']}{Style.RESET_ALL}")
            print(f"  • Thư mục riêng : {res.get('folder_path', '')}")
            print(f"  • File Video    : {res['video_path']}")
            print(f"  • File SRT      : {res['srt_path']}")
            if res.get("metadata_path"):
                print(f"  • File Metadata : {res['metadata_path']}")
            success_count += 1

        except Exception as e:
            print(f"{Fore.RED}✘ THẤT BẠI khi xử lý video {vid.name}: {e}{Style.RESET_ALL}")
            fail_count += 1

    print("\n" + "=" * 60)
    print(f"{Fore.CYAN}TỔNG KẾT: Hoàn thành {success_count}/{len(video_files)} video. Thất bại: {fail_count}{Style.RESET_ALL}")
    print("=" * 60)


if __name__ == "__main__":
    main()
