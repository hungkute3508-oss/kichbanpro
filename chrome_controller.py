import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Callable, Optional, Tuple

from playwright.sync_api import Page, sync_playwright

from core import DEFAULT_PROMPT, parse_gemini_response


def is_port_open(port: int = 9222) -> bool:
    """Kiểm tra xem cổng remote debugging của Chrome có đang mở không."""
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.5)
        return req.getcode() == 200
    except Exception:
        return False


def get_chrome_executable() -> Optional[str]:
    """Tìm đường dẫn chrome.exe trên máy tính Windows."""
    possible_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None


def launch_chrome_with_debug(port: int = 9222, log_cb: Optional[Callable[[str], None]] = None) -> bool:
    """Tự động khởi động Chrome ở chế độ Remote Debugging."""
    if is_port_open(port):
        if log_cb:
            log_cb(f"Chrome Debugging (Port {port}) đã sẵn sàng.")
        return True

    chrome_path = get_chrome_executable()
    if not chrome_path:
        if log_cb:
            log_cb("Không tìm thấy Chrome trên máy tính.")
        return False

    profile_dir = Path(os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\DebugProfile"))
    profile_dir.mkdir(parents=True, exist_ok=True)

    if log_cb:
        log_cb(f"Đang khởi động Chrome Debug tại cổng {port}...")

    cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={str(profile_dir)}",
        "https://gemini.google.com",
    ]
    subprocess.Popen(cmd)

    # Đợi cổng mở
    for _ in range(15):
        time.sleep(1)
        if is_port_open(port):
            if log_cb:
                log_cb("Khởi động Chrome Debug thành công!")
            return True

    return False


def find_or_create_gemini_page(context, log_cb: Optional[Callable[[str], None]] = None) -> Page:
    """Tìm tab Gemini đang mở hoặc mở tab mới nếu chưa có."""
    # 1. Tìm tab đã mở gemini.google.com
    for page in context.pages:
        url = page.url.lower()
        if "gemini.google.com" in url:
            if log_cb:
                log_cb(f"Đã tìm thấy tab Gemini sẵn có: {page.title() or url}")
            page.bring_to_front()
            return page

    # 2. Nếu không tìm thấy, mở tab mới
    if log_cb:
        log_cb("Không tìm thấy tab Gemini có sẵn, đang mở https://gemini.google.com...")
    page = context.new_page()
    page.goto("https://gemini.google.com", wait_until="domcontentloaded")
    return page


def prepare_fresh_gemini_chat(
    page: Page,
    log_cb: Optional[Callable[[str], None]] = None,
    force_reload: bool = False,
):
    """
    Đảm bảo tab Gemini luôn ở một phiên chat MỚI (New Chat):
    - Tránh tình trạng nhồi nhét hàng chục file audio vào 1 phiên chat gây tràn bộ nhớ / rate limit.
    - Tránh việc Gemini lặp lại tiêu đề/kịch bản của video trước đó.
    - Tránh lỗi Gemini từ chối trả lời ("Là một mô hình ngôn ngữ...").
    """
    if log_cb:
        log_cb("Đang làm mới phiên chat Gemini để đảm bảo độc lập từng video...")

    current_url = page.url.lower()

    # Kiểm tra xem có đang ở trong 1 cuộc trò chuyện cũ không (URL có ID dạng /app/xxxx hoặc có lịch sử chat)
    has_history = False
    try:
        resp_count = page.locator('model-response, message-content, [data-test-id="model-response"]').count()
        if resp_count > 0:
            has_history = True
    except Exception:
        pass

    if force_reload or has_history or "/app/" in current_url:
        # Cách 1: Bấm nút "Cuộc trò chuyện mới" (New chat) nếu có
        new_chat_selectors = [
            'button[aria-label*="Cuộc trò chuyện mới" i]',
            'button[aria-label*="Trò chuyện mới" i]',
            'button[aria-label*="New chat" i]',
            'a[data-test-id="new-chat-button"]',
            'a[href="/app"]',
            'button:has(mat-icon:has-text("add"))',
            'button:has-text("Trò chuyện mới")',
            'button:has-text("New chat")',
        ]

        clicked = False
        if not force_reload:
            for sel in new_chat_selectors:
                btn = page.locator(sel).first
                if btn.is_visible():
                    try:
                        btn.click()
                        time.sleep(1)
                        clicked = True
                        break
                    except Exception:
                        pass

        # Cách 2: Nếu chưa click được hoặc force_reload, điều hướng thẳng về https://gemini.google.com/app
        if force_reload or not clicked:
            try:
                page.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=20000)
            except Exception:
                pass

    # Đợi khung nhập chat sẵn sàng
    input_selectors = [
        'rich-textarea div[contenteditable="true"]',
        'div.ql-editor[contenteditable="true"]',
        'div[contenteditable="true"]',
        'textarea',
    ]

    for _ in range(15):
        for sel in input_selectors:
            loc = page.locator(sel).first
            if loc.is_visible():
                time.sleep(0.5)
                return
        time.sleep(1)


def upload_audio_to_gemini(page: Page, audio_path: str, log_cb: Optional[Callable[[str], None]] = None):
    """Tải file âm thanh lên giao diện web Gemini."""
    abs_audio = str(Path(audio_path).resolve())
    if not os.path.exists(abs_audio):
        raise FileNotFoundError(f"Không tìm thấy file audio: {abs_audio}")

    if log_cb:
        log_cb("Đang đính kèm file âm thanh vào khung chat Gemini...")

    # Cách 1: Tìm trực tiếp thẻ <input type="file">
    file_inputs = page.locator('input[type="file"]')
    if file_inputs.count() > 0:
        try:
            file_inputs.first.set_input_files(abs_audio, timeout=3000)
            if log_cb:
                log_cb("Đã đính kèm file qua input[type='file'].")
            return
        except Exception:
            pass

    # Cách 2: Bấm nút đính kèm (+) / Thêm tệp để kích hoạt menu hoặc file chooser
    add_btn_selectors = [
        'button[aria-label*="tệp" i]',
        'button[aria-label*="file" i]',
        'button[aria-label*="Tải lên" i]',
        'button[aria-label*="Upload" i]',
        'button[aria-label*="Thêm" i]',
        'button[aria-label*="Add" i]',
        'button[aria-label*="Đính kèm" i]',
        'button:has(mat-icon:has-text("add"))',
        'button:has(svg)',
    ]

    for sel in add_btn_selectors:
        btn = page.locator(sel).first
        if btn.is_visible():
            try:
                # Thử với expect_file_chooser nếu nút mở thẳng file dialog
                try:
                    with page.expect_file_chooser(timeout=2000) as fc_info:
                        btn.click()
                    file_chooser = fc_info.value
                    file_chooser.set_files(abs_audio)
                    if log_cb:
                        log_cb("Đã đính kèm file qua hộp thoại chọn file.")
                    return
                except Exception:
                    # Nếu nút mở ra popup menu (Tải tệp lên / Upload from computer)
                    time.sleep(0.5)
                    sub_options = [
                        'button:has-text("Tải tệp lên")',
                        'button:has-text("Tải lên từ thiết bị")',
                        'button:has-text("Upload from computer")',
                        '[role="menuitem"]:has-text("Tải")',
                        '[role="menuitem"]:has-text("Upload")',
                        '[role="menuitem"]:has-text("tệp")',
                        '[role="menuitem"]:has-text("file")',
                    ]
                    for sub in sub_options:
                        sub_btn = page.locator(sub).first
                        if sub_btn.is_visible():
                            try:
                                with page.expect_file_chooser(timeout=3000) as fc_info2:
                                    sub_btn.click()
                                file_chooser2 = fc_info2.value
                                file_chooser2.set_files(abs_audio)
                                if log_cb:
                                    log_cb("Đã đính kèm file qua menu tải lên.")
                                return
                            except Exception:
                                pass
            except Exception:
                pass

    # Cách 3: Thử lại input[type="file"] một lần nữa với timeout ngắn
    file_inputs = page.locator('input[type="file"]')
    if file_inputs.count() > 0:
        try:
            file_inputs.first.set_input_files(abs_audio, timeout=5000)
            if log_cb:
                log_cb("Đã đính kèm file qua input[type='file'].")
            return
        except Exception:
            pass

    raise RuntimeError("Không thể tìm thấy nút đính kèm file hoặc ô chọn file trên giao diện Gemini.")


def wait_for_file_upload_ready(page: Page, timeout_sec: int = 180, log_cb: Optional[Callable[[str], None]] = None):
    """Đợi giao diện Gemini xử lý xong file audio vừa đính kèm (tăng lên 180s để đảm bảo không bị miss file lớn)."""
    if log_cb:
        log_cb("Đang đợi Gemini tải xong file âm thanh...")

    start_time = time.time()
    # Chờ 2 giây tối thiểu để UI hiển thị chip
    time.sleep(2)

    while time.time() - start_time < timeout_sec:
        # Kiểm tra spinner/loading có đang quay không
        spinners = page.locator('mat-spinner, mat-progress-spinner, [role="progressbar"], .loading')
        has_spinner = False
        for i in range(spinners.count()):
            if spinners.nth(i).is_visible():
                has_spinner = True
                break

        if not has_spinner:
            # File đã tải xong
            time.sleep(1.5)
            if log_cb:
                log_cb("File âm thanh đã sẵn sàng gửi!")
            return

        time.sleep(1)

    if log_cb:
        log_cb("Đã hết thời gian chờ spinner, tiếp tục thử gửi...")


def send_prompt_and_wait_response(
    page: Page,
    prompt: str,
    timeout_sec: int = 600,
    log_cb: Optional[Callable[[str], None]] = None,
) -> str:
    """Nhập prompt, nhấn gửi và đợi nhận kết quả kịch bản từ Gemini với thời gian chờ đủ lâu để không bị miss kịch bản."""
    # 1. Tìm ô nhập prompt
    input_selectors = [
        'rich-textarea div[contenteditable="true"]',
        'div.ql-editor[contenteditable="true"]',
        'div[contenteditable="true"]',
        'textarea[aria-label]',
        'textarea',
    ]

    input_elem = None
    for sel in input_selectors:
        loc = page.locator(sel).first
        if loc.is_visible():
            input_elem = loc
            break

    if not input_elem:
        raise RuntimeError("Không tìm thấy khung nhập nội dung chat trên trang Gemini.")

    if log_cb:
        log_cb("Đang điền prompt vào khung chat...")

    input_elem.click()
    time.sleep(0.3)

    # Sử dụng insert_text để hỗ trợ Unicode / xuống dòng nhanh chóng
    page.keyboard.insert_text(prompt)
    time.sleep(0.5)

    # Đếm số lượng phản hồi hiện tại trước khi gửi
    response_locators = page.locator('model-response, .model-response-text, message-content, [data-test-id="model-response"]')
    initial_response_count = response_locators.count()

    # 2. Bấm nút gửi
    send_selectors = [
        'button[aria-label*="Gửi" i]',
        'button[aria-label*="Send" i]',
        'button.send-button',
        'button:has(mat-icon:has-text("send"))',
        'button[data-test-id="send-button"]',
    ]

    sent = False
    for sel in send_selectors:
        btn = page.locator(sel).first
        if btn.is_visible() and btn.is_enabled():
            btn.click()
            sent = True
            if log_cb:
                log_cb("Đã bấm nút Gửi!")
            break

    if not sent:
        # Fallback: Thử bấm Enter
        if log_cb:
            log_cb("Bấm nút Gửi bằng Enter...")
        page.keyboard.press("Enter")

    # 3. Đợi phản hồi mới bắt đầu xuất hiện (tăng lên tối đa 90 giây)
    if log_cb:
        log_cb("Đang đợi Gemini bắt đầu sinh kịch bản và phụ đề...")

    start_wait = time.time()
    while time.time() - start_wait < 90:
        current_count = response_locators.count()
        stop_btn = page.locator('button[aria-label*="Dừng" i], button[aria-label*="Stop" i], button.stop-button, [data-test-id="stop-button"]')
        if current_count > initial_response_count or (stop_btn.count() > 0 and stop_btn.first.is_visible()):
            break
        time.sleep(1)

    # 4. Đợi Gemini kết thúc quá trình sinh toàn bộ kịch bản và khối SRT
    if log_cb:
        log_cb(f"Gemini đang bóc băng và viết kịch bản... Đang theo dõi tiến trình (Thời gian chờ tối đa {timeout_sec}s)...")

    last_text = ""
    stable_count = 0
    last_log_time = time.time()

    while time.time() - start_wait < timeout_sec:
        time.sleep(2)

        # Lấy nội dung phản hồi mới nhất
        current_count = response_locators.count()
        if current_count > 0:
            target_response = response_locators.last
            current_text = target_response.inner_text().strip()
        else:
            current_text = ""

        # Kiểm tra nút dừng
        stop_btn = page.locator('button[aria-label*="Dừng" i], button[aria-label*="Stop" i], button.stop-button, [data-test-id="stop-button"]')
        is_generating = stop_btn.count() > 0 and stop_btn.first.is_visible()

        text_len = len(current_text)
        has_srt_open = "[SRT]" in current_text.upper()
        has_srt_close = "[/SRT]" in current_text.upper()

        # Định kỳ thông báo tiến độ cứ mỗi 12 giây để người dùng dễ theo dõi
        if log_cb and (time.time() - last_log_time >= 12):
            last_log_time = time.time()
            elapsed = int(time.time() - start_wait)
            if has_srt_close:
                status_info = "Đã có thẻ đóng [/SRT], đang đợi hoàn tất đồng bộ"
            elif has_srt_open:
                status_info = "Đang viết khối phụ đề [SRT]..."
            else:
                status_info = "Đang sinh tiêu đề & chuẩn bị SRT..."
            log_cb(f"⏳ Tiến trình: {text_len} ký tự ({elapsed}s trôi qua) - {status_info}")

        if text_len > 50:
            if current_text == last_text:
                stable_count += 1

                # Trường hợp 1: ĐÃ CÓ thẻ đóng [/SRT] và nút Dừng đã tắt -> Gemini đã tạo trọn vẹn 100%!
                if has_srt_close and not is_generating:
                    if stable_count >= 3:  # Ổn định trong 6 giây sau khi đóng thẻ [/SRT]
                        if log_cb:
                            log_cb(f"✔ Gemini đã hoàn tất 100% kịch bản & phụ đề ({text_len} ký tự)!")
                        return current_text

                # Trường hợp 2: Đã mở [SRT] nhưng CHƯA CÓ [/SRT] -> Gemini vẫn đang viết dở dang!
                # Tuyệt đối KHÔNG ngắt sớm khi Gemini chỉ tạm ngừng suy nghĩ vài giây.
                # Phải đợi ít nhất 20 lần lặp (~40 giây không đổi) và nút Dừng thực sự biến mất.
                elif has_srt_open and not has_srt_close:
                    if not is_generating and stable_count >= 20:
                        if log_cb:
                            log_cb(f"⚠️ Gemini dừng phản hồi sau khi viết một phần SRT ({text_len} ký tự).")
                        return current_text

                # Trường hợp 3: Không có tag chuẩn (hoặc câu trả lời từ chối/văn bản thường)
                elif not is_generating and stable_count >= 6:  # Ổn định trong 12 giây
                    if log_cb:
                        log_cb(f"Gemini đã hoàn tất tạo phản hồi ({text_len} ký tự)!")
                    return current_text
            else:
                # Text vẫn đang dài thêm -> Reset bộ đếm ổn định
                stable_count = 0

        last_text = current_text

    if last_text:
        if log_cb:
            log_cb(f"Hết thời gian chờ {timeout_sec}s, lấy nội dung hiện có ({len(last_text)} ký tự).")
        return last_text

    raise TimeoutError(f"Hết thời gian chờ Gemini trả về kết quả ({timeout_sec}s).")


def transcribe_via_chrome(
    audio_path: str,
    port: int = 9222,
    custom_prompt: Optional[str] = None,
    log_cb: Optional[Callable[[str], None]] = None,
    max_retries: int = 2,
) -> Tuple[str, str, str]:
    """
    Toàn bộ quy trình điều khiển Chrome:
    1. Kết nối qua Playwright CDP tới port 9222
    2. Tìm tab gemini.google.com và ĐẢM BẢO MỞ PHIÊN CHAT MỚI (New Chat)
    3. Đính kèm audio
    4. Gửi prompt
    5. Đợi kết quả và bóc tách Title + SRT + Tên sản phẩm (tự động thử lại nếu Gemini từ chối)
    """
    if not is_port_open(port):
        if log_cb:
            log_cb(f"Cổng {port} chưa mở, đang thử khởi động Chrome...")
        launched = launch_chrome_with_debug(port=port, log_cb=log_cb)
        if not launched:
            raise ConnectionError(
                f"Không thể kết nối Chrome Debug tại cổng {port}.\n"
                "Vui lòng chạy file 'start_chrome_debug.bat' hoặc mở Chrome với cờ: --remote-debugging-port=9222"
            )

    prompt = custom_prompt or DEFAULT_PROMPT

    if log_cb:
        log_cb(f"Đang kết nối Chrome qua Remote Debugging Port {port}...")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        context = browser.contexts[0] if browser.contexts else browser.new_context()

        page = find_or_create_gemini_page(context, log_cb=log_cb)

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                # 1. BẮT BUỘC: Đưa tab về phiên chat mới độc lập (tránh tràn ngữ cảnh, trùng lặp tiêu đề, hoặc bị từ chối)
                prepare_fresh_gemini_chat(page, log_cb=log_cb, force_reload=(attempt > 1))

                # 2. Đính kèm audio
                upload_audio_to_gemini(page, audio_path, log_cb=log_cb)

                # 3. Đợi audio tải xong (timeout 180s cho các file âm thanh dài/mạng chậm)
                wait_for_file_upload_ready(page, timeout_sec=180, log_cb=log_cb)

                # 4. Gửi prompt và nhận câu trả lời (timeout 600s = 10 phút để không bao giờ bị miss kịch bản dài)
                response_text = send_prompt_and_wait_response(page, prompt, timeout_sec=600, log_cb=log_cb)

                if log_cb:
                    log_cb("Đang phân tích cú pháp tiêu đề và nội dung SRT...")

                # 5. Phân tích kết quả - kiểm tra tính hợp lệ & câu từ chối
                title, srt, product_name = parse_gemini_response(response_text)
                return title, srt, product_name

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    if log_cb:
                        log_cb(f"⚠️ Phát hiện phản hồi chưa chuẩn hoặc Gemini từ chối ({e}). Đang làm mới phiên chat và thử lại (Lần {attempt + 1}/{max_retries})...")
                    time.sleep(2)
                else:
                    raise last_error
