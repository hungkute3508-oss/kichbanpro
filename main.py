import sys

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def main():
    # Nếu không có tham số dòng lệnh -> Chạy giao diện đồ họa (GUI)
    if len(sys.argv) == 1:
        try:
            import gui
            gui.main()
        except ImportError as e:
            print(f"Không thể mở GUI: {e}. Đang chuyển sang chế độ CLI...")
            import cli
            cli.main()
    else:
        # Nếu có truyền tham số -> Chạy giao diện dòng lệnh (CLI)
        import cli
        cli.main()

if __name__ == "__main__":
    main()
