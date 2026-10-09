import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional, Tuple
from google import genai
from google.genai import types

DEFAULT_METADATA_TEMPLATE = (
    "Description: {product_name} #ShopeeCreator #LuotVuiMuaLien #ShopeeVideo #VideohangDienTu #HangMoiVe\n"
    "Link Affiliate: "
)

# Default prompt instructed to return structured content localized for Vietnamese audience
DEFAULT_PROMPT = """Bạn là một chuyên gia bóc băng âm thanh (Transcriber) và chuyển ngữ phụ đề (Subtitle Translator) chuyên nghiệp hàng đầu.
Hãy lắng nghe kỹ TOÀN BỘ file âm thanh được cung cấp từ giây đầu tiên đến giây cuối cùng và thực hiện các nhiệm vụ sau:

⚠️ NGUYÊN TẮC BẮT BUỘC SỐ 1: BẮT BUỘC VIẾT TIẾNG VIỆT CÓ DẤU ĐẦY ĐỦ 100%!
- TẤT CẢ [PRODUCT], [TITLE] VÀ [SRT] PHẢI ĐƯỢC VIẾT BẰNG TIẾNG VIỆT CÓ DẤU ĐẦY ĐỦ, CHUẨN CHÍNH TẢ VÀ NGỮ PHÁP.
- TUYỆT ĐỐI CẤM VIẾT TIẾNG VIỆT KHÔNG DẤU (Ví dụ: PHẢI VIẾT "Dán cường lực Torras Titan siêu bền mượt mà", TUYỆT ĐỐI CẤM VIẾT "Dan cuong luc Torras Titan sieu ben muot ma")!
- Hệ điều hành Windows hỗ trợ đầy đủ tiếng Việt có dấu Unicode cho cả tên file và tên thư mục.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NHIỆM VỤ 1: XÁC ĐỊNH TÊN SẢN PHẨM & ĐẶT TIÊU ĐỀ NỘI DUNG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. TÊN SẢN PHẨM CHÍNH (PRODUCT NAME):
   - Xác định chính xác TÊN THƯƠNG HIỆU & MODEL SẢN PHẨM chính được giới thiệu trong video (Ví dụ: "Aulumu A16", "CukTech 10", "Tai nghe Sanag S6S Ultra", "Kính cường lực Torras Titan", "Máy cạo râu Laifen T2 Pro"...).
   - Chỉ ghi tên sản phẩm ngắn gọn, súc tích (1 - 5 từ), không ghi thêm câu phụ.

2. TIÊU ĐỀ VIDEO (TÊN FILE & THƯ MỤC):
   - BẮT BUỘC VIẾT TIẾNG VIỆT CÓ DẤU ĐẦY ĐỦ 100%, CHUẨN CHÍNH TẢ!
   - Đặt 1 tiêu đề ngắn gọn (khoảng 4 - 8 từ), giật tít hấp dẫn, chuẩn tiếng Việt tự nhiên mô tả đúng nội dung video.
   - Chỉ loại bỏ các ký tự đặc biệt cấm đặt tên file trên Windows: \\ / : * ? " < > | (vẫn giữ đầy đủ dấu tiếng Việt: á, à, ả, ã, ạ, ă, â, đ, ê, ô, ơ, ư...).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NHIỆM VỤ 2: BÓC BĂNG & TẠO PHỤ ĐỀ SRT 100% TOÀN BỘ VIDEO (KHÔNG TÓM TẮT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ NGUYÊN TẮC BẮT BUỘC VỀ ĐỘ DÀI (CỰC KỲ QUAN TRỌNG):
1. BÓC TÁCH ĐẦY ĐỦ 100% TỪ ĐẦU ĐẾN HẾT AUDIO:
   - Bạn PHẢI lắng nghe và tạo phụ đề cho TOÀN BỘ chiều dài của file âm thanh.
   - TUYỆT ĐỐI KHÔNG ĐƯỢC TÓM TẮT, KHÔNG ĐƯỢC CẮT BỚT, KHÔNG ĐƯỢC TỰ Ý KẾT BÀI SỚM khi audio vẫn đang nói.
   - Người nói trong audio nói bao nhiêu câu, nói đến phút/giây thứ mấy thì BẮT BUỘC phải bóc phụ đề đầy đủ đến tận giây đó.
   - Dòng SRT cuối cùng BẮT BUỘC PHẢI KHỚP VỚI GIÂY KẾT THÚC của file âm thanh (Ví dụ: Video dài hơn 1 phút thì SRT phải kéo dài đến tận 01:xx, tuyệt đối KHÔNG được dừng ở 30s hay 40s).

2. PHONG CÁCH HIỆN ĐẠI, TRẺ TRUNG & PHÙ HỢP TỪNG CHỦ ĐỀ:
   - Dịch thoát ý tự nhiên, cuốn hút như một Reviewer / Content Creator người Việt chuyên nghiệp đang trò chuyện trực tiếp.
   - Tuyệt đối TRÁNH dịch máy móc, dịch thô cứng theo ngữ pháp ngoại lai.
   - Dùng thuật ngữ đúng chủ đề:
     + Đồ công nghệ / Gadget / Đồ gia dụng: dùng từ ngữ quen thuộc của dân mê công nghệ (deal hời, cực xịn sò, chống va đập đỉnh chóp, trải nghiệm thực tế, hoàn thiện tinh xảo...).
     + Đời sống / Mẹo vặt / Ẩm thực: giọng điệu dí dỏm, hào hứng, gần gũi, cuốn hút.

3. XƯNG HÔ NGÔI THỨ NHẤT THÂN THIỆN:
   - Chuyển toàn bộ lời dẫn / nhân vật sang ngôi thứ nhất:
     + Dùng "mình", "tôi" để xưng hô.
     + Gọi người xem là "các bạn", "anh em", "mọi người" (Ví dụ: "Hôm nay mình chia sẻ cho anh em...", "Các bạn xem này...").

4. BẢN ĐỊA HÓA GIÁ TIỀN & ĐƠN VỊ ĐO LƯỜNG:
   - Nếu trong audio gốc có nhắc đến giá cả (nhân dân tệ, USD, won...), hãy ước tính quy đổi sang tiền Việt Nam hoặc dùng cách ví von hóm hỉnh, đời thường:
     + Dùng từ ngữ quen thuộc của giới trẻ: "giá chỉ khoảng 150 cá", "tầm 150 cành", "vài chục k"...
     + Hoặc ví von đời sống: "tương đương 3 cốc trà sữa", "chưa bằng một bát phở", "rẻ như cho"...

5. ĐỊNH DẠNG PHỤ ĐỀ SUBRIP (.SRT):
   - Cấu trúc chuẩn thời gian: HH:MM:SS,mmm --> HH:MM:SS,mmm
   - Đánh số thứ tự tăng dần liên tục: 1, 2, 3, 4, 5... đến hết video.
   - Ngắt câu ngắn gọn (1-2 dòng, 3-7 giây) bám sát nhịp nói của âm thanh.
   - TUYỆT ĐỐI KHÔNG ghi thêm từ "MP3", "audio", "nguồn" hay bất kỳ nhãn nào dưới mỗi câu phụ đề. Trong khối [SRT] CHỈ ĐƯỢC CÓ số thứ tự, mốc thời gian và câu thoại tiếng Việt CÓ DẤU ĐẦY ĐỦ.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUY CÁCH PHẢN HỒI (BẮT BUỘC TUÂN THỦ CHÍNH XÁC):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Trả về DUY NHẤT theo cấu trúc sau (TẤT CẢ BẮT BUỘC LÀ TIẾNG VIỆT CÓ DẤU ĐẦY ĐỦ):

[PRODUCT]
<Tên thương hiệu & model sản phẩm chính, ví dụ: Kính cường lực Torras Titan, Aulumu A16>
[/PRODUCT]

[TITLE]
<Tiêu đề tiếng Việt có dấu đầy đủ ở đây, ví dụ: Dán cường lực Torras Titan siêu bền mượt mà>
[/TITLE]

[SRT]
1
00:00:01,000 --> 00:00:04,500
Lời thoại câu 1...

2
00:00:05,000 --> 00:00:08,200
Lời thoại câu 2...
[/SRT]
"""




def sanitize_filename(name: str, max_length: int = 120) -> str:
    """Loại bỏ các ký tự không hợp lệ trên Windows và làm sạch tên file."""
    # Xóa khoảng trắng thừa
    name = name.strip()
    # Loại bỏ các ký tự cấm: \ / : * ? " < > |
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    # Thay thế ký tự xuống dòng hoặc tab
    name = re.sub(r"[\r\n\t]+", " ", name)
    # Rút gọn khoảng trắng
    name = re.sub(r"\s+", " ", name).strip()

    if not name:
        name = "Video_Subtitled_" + time.strftime("%Y%m%d_%H%M%S")

    # Giới hạn độ dài tên file để tránh lỗi hệ điều hành
    if len(name) > max_length:
        name = name[:max_length].rstrip()

    return name


def find_binary(binary_name: str) -> str:
    """
    Tìm đường dẫn binary (ffmpeg, ffprobe) ưu tiên cạnh file .exe / thư mục cài đặt trước,
    sau đó fallback sang PATH hệ thống.
    """
    exe_name = f"{binary_name}.exe" if sys.platform.startswith("win") and not binary_name.endswith(".exe") else binary_name

    # 1. Kiểm tra cạnh sys.executable (khi chạy dưới dạng PyInstaller .exe)
    exe_dir = Path(sys.executable).parent
    for sub in [exe_dir, exe_dir / "_internal", exe_dir / "bin"]:
        p = sub / exe_name
        if p.is_file():
            return str(p)

    # 2. Kiểm tra cạnh file script hiện tại
    script_dir = Path(__file__).resolve().parent
    for sub in [script_dir, script_dir / "bin"]:
        p = sub / exe_name
        if p.is_file():
            return str(p)

    # 3. Fallback theo tên trong PATH
    return binary_name


def get_media_duration(file_path: str) -> Tuple[float, str]:
    """Lấy thời lượng chính xác của video hoặc audio bằng ffprobe."""
    try:
        cmd = [
            find_binary("ffprobe"),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ]
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        sec = float(out)
        mins = int(sec // 60)
        s = int(sec % 60)
        return sec, f"{mins:02d}:{s:02d}"
    except Exception:
        return 0.0, "00:00"


def extract_audio(
    video_path: str,
    output_audio_path: Optional[str] = None,
    log_cb: Optional[Callable[[str], None]] = None,
) -> str:

    """
    Trích xuất âm thanh từ video sang định dạng mp3 tối ưu cho Whisper/Gemini.
    Sử dụng bitrate 64k mono 16kHz để file cực nhẹ, upload siêu tốc.
    """
    if log_cb:
        log_cb(f"Đang trích xuất âm thanh từ: {os.path.basename(video_path)}...")

    video_p = Path(video_path)
    if not video_p.exists():
        raise FileNotFoundError(f"Không tìm thấy file video: {video_path}")

    if output_audio_path is None:
        temp_dir = video_p.parent / "_temp_audio"
        temp_dir.mkdir(parents=True, exist_ok=True)
        output_audio_path = str(temp_dir / f"{video_p.stem}_audio.mp3")

    cmd = [
        find_binary("ffmpeg"),
        "-y",
        "-i",
        str(video_p),
        "-vn",  # Bỏ hình ảnh
        "-acodec",
        "libmp3lame",
        "-ar",
        "16000",  # 16kHz chuẩn giọng nói
        "-ac",
        "1",  # Mono
        "-b:a",
        "64k",  # 64kbps siêu nhẹ
        str(output_audio_path),
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg trích xuất âm thanh thất bại: {result.stderr}")

    if log_cb:
        size_mb = os.path.getsize(output_audio_path) / (1024 * 1024)
        log_cb(f"Trích xuất âm thanh thành công ({size_mb:.2f} MB)")

    return output_audio_path


def clean_srt_content(srt_text: str) -> str:
    """
    Loại bỏ các nhãn định dạng âm thanh (như 'MP3', '[MP3]', 'audio', v.v.)
    sinh ra do các nút/chip phát âm thanh nguồn trên giao diện Gemini.
    Đồng thời chuẩn hóa định dạng phụ đề SubRip (.srt).
    """
    if not srt_text:
        return ""

    lines = srt_text.splitlines()
    cleaned_lines = []

    # Danh sách nhãn định dạng / chip nguồn cần loại bỏ
    ARTIFACT_KEYWORDS = {
        "MP3", "[MP3]", "(MP3)", "AUDIO", "[AUDIO]", "(AUDIO)",
        "M4A", "[M4A]", "WAV", "[WAV]", "AAC", "[AAC]",
        "MP4", "[MP4]", "ATTACHMENT", "NGUỒN", "[NGUỒN]",
    }

    for line in lines:
        stripped = line.strip()

        # 1. Bỏ qua nếu dòng chỉ chứa nhãn MP3 / Audio
        if stripped.upper() in ARTIFACT_KEYWORDS:
            continue

        # 2. Xóa nhãn MP3 / Audio ở cuối câu nếu bị dính vào dòng thoại
        line_clean = re.sub(
            r"\s+(?:\[MP3\]|\(MP3\)|MP3|\[AUDIO\]|AUDIO)\s*$",
            "",
            line,
            flags=re.IGNORECASE,
        )

        cleaned_lines.append(line_clean)

    # Nối lại và chuẩn hóa khoảng trống giữa các khối phụ đề
    result = "\n".join(cleaned_lines)
    # Loại bỏ nhiều dòng trống liên tiếp (giữ tối đa 1 dòng trống phân cách giữa các block SRT)
    result = re.sub(r"\n{3,}", "\n\n", result).strip()

    return result


REFUSAL_KEYWORDS = [
    "mô hình ngôn ngữ",
    "trí tuệ nhân tạo dựa trên văn bản",
    "không thể giúp",
    "không thể trợ giúp",
    "không được thiết kế để",
    "không được lập trình",
    "nằm ngoài mục đích",
    "nằm ngoài khả năng",
    "không có khả năng hiểu",
    "không có thông tin hoặc khả năng",
    "as an ai",
    "language model",
    "i cannot help",
    "i am unable to",
    "không thể hỗ trợ",
    "chính sách an toàn",
    "điều đó nằm ngoài",
    "tôi chỉ là một",
]


def is_refusal_text(text: str) -> bool:
    """Kiểm tra xem nội dung văn bản có chứa câu từ chối phản hồi của AI không."""
    low = text.lower()
    return any(k in low for k in REFUSAL_KEYWORDS)


def has_valid_srt_timestamps(srt_text: str) -> bool:
    """Kiểm tra xem nội dung SRT có chứa ít nhất 1 mốc timestamp chuẩn không."""
    return bool(re.search(r"\d{1,2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,\.]\d{3}", srt_text))


def parse_gemini_response(text: str) -> Tuple[str, str, str]:
    """
    Bóc tách Tiêu đề, Nội dung SRT và Tên sản phẩm từ phản hồi của Gemini.
    Đồng thời kiểm tra tính hợp lệ: phát hiện câu từ chối (refusal) và đảm bảo có timestamp SRT.
    Trả về: (title, srt_content, product_name)
    """
    if not text or not text.strip():
        raise RuntimeError("Gemini trả về kết quả rỗng.")

    # 1. Kiểm tra nếu toàn bộ câu trả lời là câu từ chối của AI
    if is_refusal_text(text) and not re.search(r"\d{1,2}:\d{2}:\d{2}[,\.]\d{3}\s*-->", text):
        clean_snippet = text.strip().replace("\n", " ")[:120]
        raise RuntimeError(f"Gemini từ chối xử lý âm thanh này: \"{clean_snippet}...\"")

    product_name = ""
    title = ""
    srt_content = ""

    # Tìm [PRODUCT]...[/PRODUCT]
    product_match = re.search(r"\[PRODUCT\]\s*(.*?)\s*\[/PRODUCT\]", text, re.DOTALL | re.IGNORECASE)
    if product_match:
        product_name = product_match.group(1).strip()
        product_name = re.sub(r"[\r\n\t]+", " ", product_name).strip()

    # Tìm [TITLE]...[/TITLE]
    title_match = re.search(r"\[TITLE\]\s*(.*?)\s*\[/TITLE\]", text, re.DOTALL | re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()

    # Tìm [SRT]...[/SRT]
    srt_match = re.search(r"\[SRT\]\s*(.*?)\s*\[/SRT\]", text, re.DOTALL | re.IGNORECASE)
    if srt_match:
        srt_content = srt_match.group(1).strip()
    else:
        # Nếu model không đặt trong tag, thử tìm khối ```srt ... ``` hoặc tìm block có timestamp
        code_block = re.search(r"```(?:srt)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if code_block:
            srt_content = code_block.group(1).strip()
        else:
            # Fallback: tìm từ vị trí xuất hiện timestamp đầu tiên
            ts_pos = re.search(r"\d{1,2}:\d{2}:\d{2}[,\.]\d{3}\s*-->", text)
            if ts_pos:
                start_idx = ts_pos.start()
                # lùi về đầu dòng trước đó nếu có số thứ tự
                line_start = text.rfind("\n", 0, start_idx)
                if line_start != -1:
                    srt_content = text[line_start:].strip()
                else:
                    srt_content = text[start_idx:].strip()
            else:
                # Không tìm thấy bất kỳ timestamp nào
                srt_content = text.strip()

    # Làm sạch nội dung SRT, loại bỏ các nhãn MP3 / Audio artifacts
    srt_content = clean_srt_content(srt_content)

    # 2. Kiểm tra tính hợp lệ của SRT: Bắt buộc phải có mốc thời gian timestamp!
    if not has_valid_srt_timestamps(srt_content):
        clean_snippet = text.strip().replace("\n", " ")[:120]
        raise RuntimeError(
            f"Gemini không tạo được phụ đề SRT hợp lệ (thiếu mốc thời gian timestamp).\n"
            f"Nội dung nhận được: \"{clean_snippet}...\""
        )

    # Nếu không tìm thấy title từ tag, lấy dòng đầu tiên hoặc tóm tắt ngắn (trừ các dòng SRT & từ chối)
    if not title:
        lines = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("[")]
        for line in lines:
            if not re.search(r"\d{2}:\d{2}:\d{2}", line) and not line.isdigit() and not is_refusal_text(line):
                title = line
                break
        if not title:
            title = "Video_Subtitled"

    # 3. Kiểm tra xem title có bị dính câu từ chối không
    if is_refusal_text(title) or len(title) > 100:
        clean_snip = title.strip().replace("\n", " ")[:80]
        raise RuntimeError(f"Tiêu đề không hợp lệ do phản hồi từ chối: \"{clean_snip}...\"")

    # Làm sạch title
    title = sanitize_filename(title)

    # Nếu chưa có product_name thì lấy theo title
    if not product_name or is_refusal_text(product_name):
        product_name = title

    return title, srt_content, product_name



def transcribe_and_title(
    api_key: str,
    audio_path: str,
    model_name: str = "gemini-2.5-flash",
    custom_prompt: Optional[str] = None,
    log_cb: Optional[Callable[[str], None]] = None,
) -> Tuple[str, str, str]:
    """
    Gửi file âm thanh lên Gemini API, nhận về tiêu đề, nội dung SRT và tên sản phẩm.
    """
    if log_cb:
        log_cb(f"Khởi tạo kết nối Gemini API (Model: {model_name})...")

    client = genai.Client(api_key=api_key, http_options={"timeout": 600000})
    prompt = custom_prompt or DEFAULT_PROMPT

    if log_cb:
        log_cb(f"Đang tải file âm thanh lên Google Files API...")

    uploaded_file = client.files.upload(file=audio_path)

    try:
        # Đợi file ở trạng thái ACTIVE nếu cần
        if log_cb:
            log_cb(f"File đã tải lên ({uploaded_file.name}). Đang gửi yêu cầu sinh phụ đề và tiêu đề...")

        response = client.models.generate_content(
            model=model_name,
            contents=[uploaded_file, prompt],
        )

        response_text = response.text or ""
        if not response_text:
            raise RuntimeError("Gemini không trả về nội dung nào.")

        if log_cb:
            log_cb("Nhận kết quả thành công từ Gemini. Đang xử lý bóc tách...")

        title, srt, product_name = parse_gemini_response(response_text)
        return title, srt, product_name

    finally:
        # Xóa file đã upload trên Google Cloud để dọn dẹp
        try:
            client.files.delete(name=uploaded_file.name)
            if log_cb:
                log_cb("Đã dọn dẹp file tạm trên Google Gemini Cloud.")
        except Exception:
            pass


def process_single_video(
    video_path: str,
    api_key: Optional[str] = None,
    mode: str = "chrome",
    chrome_port: int = 9222,
    model_name: str = "gemini-2.5-flash",
    custom_prompt: Optional[str] = None,
    rename_video: bool = True,
    create_subfolder: bool = True,
    create_metadata: bool = True,
    metadata_template: Optional[str] = None,
    output_dir: Optional[str] = None,
    keep_temp_audio: bool = False,
    log_cb: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Quy trình hoàn chỉnh cho 1 video:
    1. Trích xuất audio
    2. Gửi qua Chrome Debugging (tab Gemini) hoặc Gemini API để nhận title, srt và tên sản phẩm
    3. Tạo thư mục riêng theo title (nếu create_subfolder=True)
    4. Đổi tên video và di chuyển vào thư mục riêng
    5. Ghi file .srt vào thư mục riêng
    6. Ghi file metadata.txt vào thư mục riêng (nếu create_metadata=True)
    7. Xóa audio tạm
    """
    video_p = Path(video_path).resolve()
    if not video_p.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {video_path}")

    # 1. Trích xuất audio
    temp_audio = extract_audio(str(video_p), log_cb=log_cb)

    # Đo thời lượng thực tế của video / audio bằng ffprobe
    dur_sec, dur_str = get_media_duration(temp_audio)
    if dur_sec <= 0:
        dur_sec, dur_str = get_media_duration(str(video_p))

    base_prompt = custom_prompt or DEFAULT_PROMPT
    if dur_sec > 0:
        duration_header = (
            f"⚠️ LƯU Ý BẮT BUỘC QUAN TRỌNG NHẤT:\n"
            f"1. BẮT BUỘC VIẾT TIẾNG VIỆT CÓ DẤU ĐẦY ĐỦ 100% cho cả [PRODUCT], [TITLE] và [SRT]! TUYỆT ĐỐI KHÔNG VIẾT TIẾNG VIỆT KHÔNG DẤU (Cấm viết 'Dan cuong luc...', phải viết 'Dán cường lực...')!\n"
            f"2. File âm thanh này có tổng thời lượng chính xác là: {dur_str} (xấp xỉ {int(dur_sec)} giây).\n"
            f"   - Bạn PHẢI bóc phụ đề đầy đủ toàn bộ lời thoại từ giây 00:00:00 cho đến tận giây cuối cùng (khoảng {dur_str}).\n"
            f"   - TUYỆT ĐỐI KHÔNG ĐƯỢC tóm tắt hay kết bài sớm ở 30s! Dòng SRT cuối cùng BẮT BUỘC phải chạm mốc kết thúc (~{dur_str}). Phải bóc tách trọn vẹn cả phần sau của video!\n\n"
        )
        prompt_to_send = duration_header + base_prompt
        if log_cb:
            log_cb(f"Thời lượng video: {dur_str} ({int(dur_sec)} giây). Đã truyền mốc thời lượng vào Prompt.")
    else:
        prompt_to_send = base_prompt

    try:
        # 2. Xử lý nhận kịch bản theo mode
        if mode == "chrome":
            from chrome_controller import transcribe_via_chrome
            title, srt_content, product_name = transcribe_via_chrome(
                audio_path=temp_audio,
                port=chrome_port,
                custom_prompt=prompt_to_send,
                log_cb=log_cb,
            )
        else:
            if not api_key:
                raise ValueError("Cần cung cấp API Key khi sử dụng chế độ Gemini API.")
            title, srt_content, product_name = transcribe_and_title(
                api_key=api_key,
                audio_path=temp_audio,
                model_name=model_name,
                custom_prompt=prompt_to_send,
                log_cb=log_cb,
            )

        base_dir = Path(output_dir).resolve() if output_dir else video_p.parent

        # 3. Tạo thư mục riêng cùng tên với tiêu đề nếu bật create_subfolder
        if create_subfolder:
            item_folder = base_dir / title
            # Tránh trùng lặp tên thư mục nếu đã tồn tại và không phải thư mục gốc
            counter = 1
            while item_folder.exists() and not (item_folder.is_dir() and video_p.parent == item_folder):
                # Kiểm tra nếu thư mục đã có sẵn file của chính video này
                if (item_folder / f"{title}{video_p.suffix}").exists() and (item_folder / f"{title}{video_p.suffix}") == video_p:
                    break
                item_folder = base_dir / f"{title}_{counter}"
                counter += 1
            item_folder.mkdir(parents=True, exist_ok=True)
            target_dir = item_folder
        else:
            base_dir.mkdir(parents=True, exist_ok=True)
            target_dir = base_dir

        ext = video_p.suffix
        new_video_name = f"{title}{ext}"
        new_srt_name = f"{title}.srt"

        final_video_path = target_dir / new_video_name
        final_srt_path = target_dir / new_srt_name

        # Tránh trùng lặp tên nếu file đã tồn tại và khác file nguồn
        counter = 1
        while final_video_path.exists() and final_video_path != video_p:
            final_video_path = target_dir / f"{title}_{counter}{ext}"
            final_srt_path = target_dir / f"{title}_{counter}.srt"
            counter += 1

        # 4. Ghi file SRT (mã hóa utf-8 có BOM để tương thích tốt mọi phần mềm)
        if log_cb:
            log_cb(f"Đang ghi file phụ đề: {final_srt_path.name}...")

        with open(final_srt_path, "w", encoding="utf-8-sig") as f:
            f.write(srt_content)

        # 5. Đổi tên hoặc di chuyển video vào thư mục thành phẩm
        if rename_video:
            if video_p != final_video_path:
                if log_cb:
                    log_cb(f"Đang di chuyển video vào thư mục: '{target_dir.name}/{final_video_path.name}'...")
                shutil.move(str(video_p), str(final_video_path))
        else:
            if video_p != final_video_path:
                if log_cb:
                    log_cb(f"Đang sao chép video vào thư mục: '{target_dir.name}/{final_video_path.name}'...")
                shutil.copy2(str(video_p), str(final_video_path))
            else:
                final_video_path = video_p

        # 6. Ghi file metadata.txt (nếu bật create_metadata)
        metadata_path = None
        if create_metadata:
            meta_file_path = target_dir / "metadata.txt"
            tpl = metadata_template or DEFAULT_METADATA_TEMPLATE
            meta_content = tpl.format(product_name=product_name)
            if log_cb:
                log_cb(f"Đang tạo file metadata: metadata.txt (Sản phẩm: {product_name})...")
            with open(meta_file_path, "w", encoding="utf-8-sig") as f:
                f.write(meta_content)
            metadata_path = str(meta_file_path)

        if log_cb:
            file_count = 3 if create_metadata else 2
            log_cb(f"HOÀN THÀNH: Đã lưu {file_count} file vào thư mục '{target_dir.name}'")

        return {
            "success": True,
            "title": title,
            "product_name": product_name,
            "folder_path": str(target_dir),
            "video_path": str(final_video_path),
            "srt_path": str(final_srt_path),
            "metadata_path": metadata_path,
            "srt_content": srt_content,
        }


    finally:
        # Xóa audio tạm
        if not keep_temp_audio and os.path.exists(temp_audio):
            try:
                os.remove(temp_audio)
                # Dọn thư mục tạm nếu rỗng
                parent_temp = Path(temp_audio).parent
                if parent_temp.name == "_temp_audio" and not any(parent_temp.iterdir()):
                    parent_temp.rmdir()
            except Exception:
                pass
