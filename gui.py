import os
import sys
import threading
import time
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import (
    QPoint,
    QRect,
    QSize,
    Qt,
    QThread,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import (
    QColor,
    QFont,
    QIcon,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from chrome_controller import is_port_open, launch_chrome_with_debug
from config import load_config, save_config
from core import DEFAULT_METADATA_TEMPLATE, DEFAULT_PROMPT, process_single_video

SUPPORTED_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv", ".ts", ".m4v"}

MODERN_STYLE = """
QMainWindow {
    background-color: #0f172a;
    color: #f8fafc;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

QWidget {
    color: #e2e8f0;
    font-size: 13px;
}

QGroupBox {
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
    color: #94a3b8;
    background-color: #1e293b;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: #1e293b;
    border-radius: 4px;
    color: #38bdf8;
}

QLineEdit, QComboBox, QTextEdit {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 7px 10px;
    color: #f8fafc;
    selection-background-color: #6366f1;
}

QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1px solid #6366f1;
    background-color: #131d38;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #1e293b;
    border: 1px solid #475569;
    selection-background-color: #4f46e5;
    color: #f8fafc;
}

QPushButton {
    background-color: #334155;
    color: #f8fafc;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #475569;
    border-color: #64748b;
}

QPushButton:pressed {
    background-color: #1e293b;
}

QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #8b5cf6);
    color: white;
    font-weight: bold;
    border: none;
    padding: 10px 24px;
    font-size: 14px;
}

QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #7c3aed);
}

QPushButton#primaryBtn:disabled {
    background: #334155;
    color: #64748b;
}

QPushButton#chromeBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0ea5e9);
    color: white;
    font-weight: 600;
    border: none;
}

QPushButton#chromeBtn:hover {
    background: #0369a1;
}

QPushButton#pauseBtn {
    background-color: #d97706;
    color: white;
    font-weight: bold;
    border: none;
    padding: 10px 18px;
}

QPushButton#pauseBtn:hover {
    background-color: #b45309;
}

QPushButton#pauseBtn:disabled {
    background-color: #334155;
    color: #64748b;
}

QPushButton#resumeBtn {
    background-color: #059669;
    color: white;
    font-weight: bold;
    border: none;
    padding: 10px 18px;
}

QPushButton#resumeBtn:hover {
    background-color: #047857;
}

QPushButton#resumeBtn:disabled {
    background-color: #334155;
    color: #64748b;
}

QPushButton#stopBtn {
    background-color: #dc2626;
    color: white;
    font-weight: bold;
    border: none;
    padding: 10px 20px;
}

QPushButton#stopBtn:hover {
    background-color: #b91c1c;
}

QPushButton#stopBtn:disabled {
    background-color: #334155;
    color: #64748b;
}

QTableWidget {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    gridline-color: #1e293b;
    color: #f8fafc;
}

QTableWidget::item {
    padding: 6px;
    border-bottom: 1px solid #1e293b;
}

QTableWidget::item:selected {
    background-color: #312e81;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #1e293b;
    color: #94a3b8;
    padding: 8px;
    border: none;
    border-right: 1px solid #334155;
    font-weight: 600;
}

QTabWidget::pane {
    border: 1px solid #334155;
    border-radius: 6px;
    background-color: #1e293b;
}

QTabBar::tab {
    background-color: #0f172a;
    color: #94a3b8;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #1e293b;
    color: #38bdf8;
    font-weight: bold;
}

QProgressBar {
    border: 1px solid #334155;
    border-radius: 6px;
    text-align: center;
    background-color: #0f172a;
    color: #f8fafc;
    font-weight: 600;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #3b82f6);
    border-radius: 5px;
}

QRadioButton {
    spacing: 8px;
    font-weight: 600;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #475569;
    background-color: #0f172a;
}

QRadioButton::indicator:checked {
    background-color: #38bdf8;
    border: 2px solid #0284c7;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #475569;
    background-color: #0f172a;
}

QCheckBox::indicator:checked {
    background-color: #6366f1;
    border: 1px solid #6366f1;
}

QScrollBar:vertical {
    border: none;
    background: #0f172a;
    width: 10px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}
"""


class WorkerThread(QThread):
    log_signal = pyqtSignal(str)
    item_updated = pyqtSignal(int, str, str, str)  # row, status, title, srt_path
    finished_signal = pyqtSignal()

    def __init__(
        self,
        tasks: List[dict],
        mode: str,
        chrome_port: int,
        api_key: str,
        model_name: str,
        custom_prompt: str,
        rename_video: bool,
        create_subfolder: bool,
        create_metadata: bool,
        metadata_template: str,
        output_dir: Optional[str],
        keep_temp_audio: bool,
    ):
        super().__init__()
        self.tasks = tasks
        self.mode = mode
        self.chrome_port = chrome_port
        self.api_key = api_key
        self.model_name = model_name
        self.custom_prompt = custom_prompt
        self.rename_video = rename_video
        self.create_subfolder = create_subfolder
        self.create_metadata = create_metadata
        self.metadata_template = metadata_template
        self.output_dir = output_dir
        self.keep_temp_audio = keep_temp_audio
        self.is_running = True
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._is_paused = False

    def pause(self):
        self._is_paused = True
        self._pause_event.clear()

    def resume(self):
        self._is_paused = False
        self._pause_event.set()

    def is_paused(self) -> bool:
        return self._is_paused

    def stop(self):
        self.is_running = False
        self._is_paused = False
        self._pause_event.set()

    def run(self):
        for task in self.tasks:
            if not self.is_running:
                break

            # Kiểm tra trạng thái tạm dừng trước khi bắt đầu video tiếp theo
            if not self._pause_event.is_set():
                self.log_signal.emit("⏸ ĐANG TẠM DỪNG: Tiến trình tạm dừng trước video kế tiếp. Đang chờ bạn nhấn '▶ Tiếp Tục'...")
                while not self._pause_event.is_set():
                    if not self.is_running:
                        break
                    time.sleep(0.3)

            if not self.is_running:
                break

            row = task["row"]
            video_path = task["video_path"]
            filename = os.path.basename(video_path)

            self.log_signal.emit(f"\n=======================================================")
            self.log_signal.emit(f"🎬 BẮT ĐẦU XỬ LÝ: {filename}")
            self.log_signal.emit(f"=======================================================")
            self.item_updated.emit(row, "Đang xử lý...", "", "")

            def log_callback(msg: str):
                self.log_signal.emit(f"[{filename}] {msg}")

            try:
                result = process_single_video(
                    video_path=video_path,
                    mode=self.mode,
                    chrome_port=self.chrome_port,
                    api_key=self.api_key,
                    model_name=self.model_name,
                    custom_prompt=self.custom_prompt,
                    rename_video=self.rename_video,
                    create_subfolder=self.create_subfolder,
                    create_metadata=self.create_metadata,
                    metadata_template=self.metadata_template,
                    output_dir=self.output_dir,
                    keep_temp_audio=self.keep_temp_audio,
                    log_cb=log_callback,
                )

                self.item_updated.emit(
                    row,
                    "✔ Hoàn thành",
                    result["title"],
                    result["srt_path"],
                )
                self.log_signal.emit(f"✔ ĐÃ HOÀN TẤT: {result['title']}\n")


            except Exception as e:
                self.item_updated.emit(row, f"✘ Lỗi: {e}", "", "")
                self.log_signal.emit(f"✘ LỖI VỚI {filename}: {str(e)}\n")

        self.finished_signal.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Video Transcriber & Subtitle Auto-Renamer")
        self.resize(1180, 780)
        self.setStyleSheet(MODERN_STYLE)

        self.config = load_config()
        self.worker: Optional[WorkerThread] = None
        self.last_completed_dir: Optional[str] = None

        self.setup_ui()
        self.setAcceptDrops(True)
        self.check_chrome_status()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        # 1. HEADER
        header_layout = QHBoxLayout()
        title_label = QLabel("🎬 AI Video Transcriber & Subtitle Auto-Renamer")
        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #38bdf8;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # 2. CHẾ ĐỘ XỬ LÝ (CHROME DEBUG vs GEMINI API)
        mode_group = QGroupBox("Chế Độ Kết Nối Gemini")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setContentsMargins(14, 12, 14, 12)
        mode_layout.setSpacing(10)

        # Mode Selection Radios
        radio_layout = QHBoxLayout()
        self.radio_chrome = QRadioButton("🌐 Điều Khiển Chrome Debug (Tab Gemini Đang Mở - KHÔNG CẦN API KEY)")
        self.radio_api = QRadioButton("🔑 Dùng Gemini API Key")

        saved_mode = self.config.get("mode", "chrome")
        if saved_mode == "api":
            self.radio_api.setChecked(True)
        else:
            self.radio_chrome.setChecked(True)

        self.mode_group_btn = QButtonGroup()
        self.mode_group_btn.addButton(self.radio_chrome)
        self.mode_group_btn.addButton(self.radio_api)
        self.radio_chrome.toggled.connect(self.on_mode_changed)

        radio_layout.addWidget(self.radio_chrome)
        radio_layout.addSpacing(25)
        radio_layout.addWidget(self.radio_api)
        radio_layout.addStretch()
        mode_layout.addLayout(radio_layout)

        # Panel 1: Chrome Debug Options
        self.chrome_panel = QFrame()
        chrome_panel_layout = QHBoxLayout(self.chrome_panel)
        chrome_panel_layout.setContentsMargins(0, 4, 0, 0)
        chrome_panel_layout.setSpacing(10)

        lbl_port = QLabel("Cổng Debug:")
        self.port_input = QLineEdit(str(self.config.get("chrome_port", 9222)))
        self.port_input.setFixedWidth(70)

        self.btn_launch_chrome = QPushButton("🚀 Mở Chrome Debug (Port 9222)")
        self.btn_launch_chrome.setObjectName("chromeBtn")
        self.btn_launch_chrome.clicked.connect(self.launch_chrome_clicked)

        self.btn_check_chrome = QPushButton("🔌 Kiểm Tra Kết Nối")
        self.btn_check_chrome.clicked.connect(self.check_chrome_status)

        self.lbl_chrome_status = QLabel("Chưa kiểm tra")
        self.lbl_chrome_status.setStyleSheet("color: #94a3b8; font-weight: bold;")

        chrome_panel_layout.addWidget(lbl_port)
        chrome_panel_layout.addWidget(self.port_input)
        chrome_panel_layout.addWidget(self.btn_launch_chrome)
        chrome_panel_layout.addWidget(self.btn_check_chrome)
        chrome_panel_layout.addWidget(self.lbl_chrome_status)
        chrome_panel_layout.addStretch()
        mode_layout.addWidget(self.chrome_panel)

        # Panel 2: Gemini API Options
        self.api_panel = QFrame()
        api_panel_layout = QHBoxLayout(self.api_panel)
        api_panel_layout.setContentsMargins(0, 4, 0, 0)
        api_panel_layout.setSpacing(10)

        api_label = QLabel("API Key:")
        self.api_input = QLineEdit(self.config.get("api_key", ""))
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_input.setPlaceholderText("Nhập Google Gemini API Key tại đây...")

        self.btn_toggle_key = QPushButton("👁")
        self.btn_toggle_key.setFixedWidth(40)
        self.btn_toggle_key.clicked.connect(self.toggle_api_visibility)

        self.btn_save_key = QPushButton("💾 Lưu Key")
        self.btn_save_key.clicked.connect(self.save_settings)

        model_label = QLabel("Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.5-pro",
            "gemini-1.5-flash",
        ])
        current_model = self.config.get("model", "gemini-2.5-flash")
        idx = self.model_combo.findText(current_model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)

        api_panel_layout.addWidget(api_label)
        api_panel_layout.addWidget(self.api_input, 2)
        api_panel_layout.addWidget(self.btn_toggle_key)
        api_panel_layout.addWidget(self.btn_save_key)
        api_panel_layout.addWidget(model_label)
        api_panel_layout.addWidget(self.model_combo, 1)
        mode_layout.addWidget(self.api_panel)

        main_layout.addWidget(mode_group)
        self.on_mode_changed()

        # 3. MIDDLE: SPLITTER (TABLE & LOGS / SRT PREVIEW)
        splitter = QSplitter(Qt.Orientation.Vertical)

        # File List Section
        top_container = QWidget()
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        # Action Toolbar
        action_layout = QHBoxLayout()
        self.btn_add_files = QPushButton("➕ Thêm Video")
        self.btn_add_files.clicked.connect(self.add_video_files)

        self.btn_add_dir = QPushButton("📁 Thêm Cả Thư Mục")
        self.btn_add_dir.clicked.connect(self.add_directory)

        self.btn_clear_list = QPushButton("🗑 Xóa Danh Sách")
        self.btn_clear_list.clicked.connect(self.clear_file_list)

        action_layout.addWidget(self.btn_add_files)
        action_layout.addWidget(self.btn_add_dir)
        action_layout.addWidget(self.btn_clear_list)
        action_layout.addStretch()

        # Output dir selection
        self.chk_custom_out = QCheckBox("Xuất ra thư mục riêng:")
        self.chk_custom_out.setChecked(bool(self.config.get("output_dir")))
        self.chk_custom_out.toggled.connect(self.toggle_output_dir)

        self.output_dir_input = QLineEdit()
        self.output_dir_input.setText(self.config.get("output_dir", ""))
        self.output_dir_input.setEnabled(self.chk_custom_out.isChecked())
        self.output_dir_input.setPlaceholderText("Mặc định lưu cùng thư mục video gốc...")

        self.btn_browse_out = QPushButton("Chọn...")
        self.btn_browse_out.setEnabled(self.chk_custom_out.isChecked())
        self.btn_browse_out.clicked.connect(self.browse_output_dir)

        action_layout.addWidget(self.chk_custom_out)
        action_layout.addWidget(self.output_dir_input)
        action_layout.addWidget(self.btn_browse_out)

        top_layout.addLayout(action_layout)

        # Table List
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Tên File Gốc",
            "Kích Thước",
            "Trạng Thái",
            "Tiêu Đề Nội Dung (Tên Mới)",
            "Đường Dẫn SRT",
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 240)
        self.table.setColumnWidth(4, 200)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.itemClicked.connect(self.on_table_item_clicked)
        top_layout.addWidget(self.table)

        # Bottom Area: Tabs (Log Console, SRT Preview, Custom Prompt)
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()

        # Tab 1: Real-time Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family: Consolas, monospace; font-size: 12px; background-color: #090d16;")
        self.tabs.addTab(self.log_text, "📜 Nhật Ký Xử Lý (Log)")

        # Tab 2: SRT Preview
        self.srt_preview = QTextEdit()
        self.srt_preview.setReadOnly(True)
        self.srt_preview.setPlaceholderText("Nội dung kịch bản / file SRT sẽ hiển thị ở đây khi xử lý xong hoặc khi click vào dòng tương ứng trong bảng.")
        self.srt_preview.setStyleSheet("font-family: Consolas, monospace; font-size: 13px; background-color: #090d16; color: #a5f3fc;")
        self.tabs.addTab(self.srt_preview, "📄 Xem Trước Phụ Đề (.srt)")

        # Tab 3: Prompt Editor
        prompt_widget = QWidget()
        p_layout = QVBoxLayout(prompt_widget)
        p_label = QLabel("Tùy biến câu lệnh (Prompt) gửi lên Gemini (Có thể thêm yêu cầu dịch thuật hoặc phong cách):")
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setText(self.config.get("custom_prompt", DEFAULT_PROMPT))
        self.prompt_edit.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")

        btn_reset_prompt = QPushButton("Khôi phục Prompt Mặc Định")
        btn_reset_prompt.clicked.connect(lambda: self.prompt_edit.setText(DEFAULT_PROMPT))

        p_layout.addWidget(p_label)
        p_layout.addWidget(self.prompt_edit)
        p_layout.addWidget(btn_reset_prompt, alignment=Qt.AlignmentFlag.AlignRight)
        self.tabs.addTab(prompt_widget, "⚙ Cấu Hình Prompt")

        # Tab 4: Metadata Template Editor
        meta_widget = QWidget()
        m_layout = QVBoxLayout(meta_widget)
        m_label = QLabel("Mẫu nội dung file metadata.txt (Dùng {product_name} để đại diện cho tên sản phẩm được nói đến):")
        self.metadata_edit = QTextEdit()
        self.metadata_edit.setText(self.config.get("metadata_template", DEFAULT_METADATA_TEMPLATE))
        self.metadata_edit.setStyleSheet("font-family: Consolas, monospace; font-size: 13px;")

        btn_reset_meta = QPushButton("Khôi phục Mẫu Mặc Định")
        btn_reset_meta.clicked.connect(lambda: self.metadata_edit.setText(DEFAULT_METADATA_TEMPLATE))

        m_layout.addWidget(m_label)
        m_layout.addWidget(self.metadata_edit)
        m_layout.addWidget(btn_reset_meta, alignment=Qt.AlignmentFlag.AlignRight)
        self.tabs.addTab(meta_widget, "📝 Mẫu File Metadata")

        bottom_layout.addWidget(self.tabs)

        splitter.addWidget(top_container)
        splitter.addWidget(bottom_container)
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)

        main_layout.addWidget(splitter)

        # 4. BOTTOM CONTROLS & PROGRESS
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 4, 0, 0)
        control_layout.setSpacing(12)

        self.chk_rename_video = QCheckBox("Đổi tên Video theo nội dung")
        self.chk_rename_video.setChecked(self.config.get("rename_video", True))
        self.chk_rename_video.setToolTip("Nếu bỏ tích, file video sẽ giữ nguyên tên cũ và chỉ tạo file SRT có tên mới")

        self.chk_subfolder = QCheckBox("📁 Đưa vào thư mục riêng")
        self.chk_subfolder.setChecked(self.config.get("create_subfolder", True))
        self.chk_subfolder.setToolTip("Tự động tạo thư mục mang tên tiêu đề video và đưa các file thành phẩm vào trong đó")

        self.chk_metadata = QCheckBox("📝 Lấy file metadata")
        self.chk_metadata.setChecked(self.config.get("create_metadata", True))
        self.chk_metadata.setToolTip("Tự động tạo file metadata.txt chứa thông tin sản phẩm và hashtag Shopee vào thư mục hoàn thành")

        self.chk_keep_audio = QCheckBox("Giữ lại mp3 tạm")
        self.chk_keep_audio.setChecked(self.config.get("keep_temp_audio", False))

        control_layout.addWidget(self.chk_rename_video)
        control_layout.addWidget(self.chk_subfolder)
        control_layout.addWidget(self.chk_metadata)
        control_layout.addWidget(self.chk_keep_audio)
        control_layout.addStretch()


        self.btn_open_folder = QPushButton("📂 Mở Thư Mục")
        self.btn_open_folder.clicked.connect(self.open_output_folder)

        self.btn_pause = QPushButton("⏸ Tạm Dừng")
        self.btn_pause.setObjectName("pauseBtn")
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self.toggle_pause)

        self.btn_stop = QPushButton("⛔ Dừng Lại")
        self.btn_stop.setObjectName("stopBtn")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_processing)

        self.btn_start = QPushButton("🚀 BẮT ĐẦU XỬ LÝ")
        self.btn_start.setObjectName("primaryBtn")
        self.btn_start.clicked.connect(self.start_processing)

        control_layout.addWidget(self.btn_open_folder)
        control_layout.addWidget(self.btn_pause)
        control_layout.addWidget(self.btn_stop)
        control_layout.addWidget(self.btn_start)

        main_layout.addWidget(control_frame)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

    def on_mode_changed(self):
        is_chrome = self.radio_chrome.isChecked()
        self.chrome_panel.setVisible(is_chrome)
        self.api_panel.setVisible(not is_chrome)

    def check_chrome_status(self):
        try:
            port = int(self.port_input.text().strip() or "9222")
        except ValueError:
            port = 9222
        if is_port_open(port):
            self.lbl_chrome_status.setText(f"✔ Đã kết nối Chrome Port {port}")
            self.lbl_chrome_status.setStyleSheet("color: #4ade80; font-weight: bold;")
        else:
            self.lbl_chrome_status.setText(f"✘ Chưa kết nối Chrome (Port {port})")
            self.lbl_chrome_status.setStyleSheet("color: #f87171; font-weight: bold;")

    def launch_chrome_clicked(self):
        try:
            port = int(self.port_input.text().strip() or "9222")
        except ValueError:
            port = 9222
        self.append_log(f"Đang mở Chrome với Remote Debugging Port {port}...")

        def log_cb(m):
            self.append_log(m)

        ok = launch_chrome_with_debug(port=port, log_cb=log_cb)
        self.check_chrome_status()
        if ok:
            QMessageBox.information(
                self,
                "Chrome Sẵn Sàng",
                f"Đã mở Chrome tại cổng {port}.\n"
                "Hãy đăng nhập tài khoản Google và mở sẵn tab Gemini trên trình duyệt vừa mở nhé!",
            )
        else:
            QMessageBox.warning(
                self,
                "Không thể mở Chrome",
                f"Không thể khởi động Chrome tự động tại cổng {port}.\n"
                "Bạn có thể chạy file 'start_chrome_debug.bat' trên máy tính.",
            )

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        for p in paths:
            path_obj = Path(p)
            if path_obj.is_file() and path_obj.suffix.lower() in SUPPORTED_EXTS:
                self.add_video_to_table(str(path_obj))
            elif path_obj.is_dir():
                self.add_directory_videos(str(path_obj))

    def toggle_api_visibility(self):
        if self.api_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_key.setText("🔒")
        else:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_key.setText("👁")

    def toggle_output_dir(self, checked: bool):
        self.output_dir_input.setEnabled(checked)
        self.btn_browse_out.setEnabled(checked)

    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục xuất")
        if dir_path:
            self.output_dir_input.setText(dir_path)

    def save_settings(self):
        self.config["mode"] = "chrome" if self.radio_chrome.isChecked() else "api"
        try:
            self.config["chrome_port"] = int(self.port_input.text().strip() or "9222")
        except ValueError:
            self.config["chrome_port"] = 9222
        self.config["api_key"] = self.api_input.text().strip()
        self.config["model"] = self.model_combo.currentText()
        self.config["rename_video"] = self.chk_rename_video.isChecked()
        self.config["create_subfolder"] = self.chk_subfolder.isChecked()
        self.config["keep_temp_audio"] = self.chk_keep_audio.isChecked()

        self.config["output_dir"] = self.output_dir_input.text().strip() if self.chk_custom_out.isChecked() else ""
        self.config["custom_prompt"] = self.prompt_edit.toPlainText().strip()
        save_config(self.config)
        QMessageBox.information(self, "Thành Công", "Đã lưu cài đặt!")

    def add_video_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Chọn file video",
            "",
            "Video Files (*.mp4 *.mkv *.mov *.avi *.webm *.flv *.wmv *.ts *.m4v);;All Files (*.*)",
        )
        for f in files:
            self.add_video_to_table(f)

    def add_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa video")
        if dir_path:
            self.add_directory_videos(dir_path)

    def add_directory_videos(self, dir_path: str):
        count = 0
        for p in Path(dir_path).rglob("*"):
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
                self.add_video_to_table(str(p))
                count += 1
        if count == 0:
            QMessageBox.information(self, "Thông báo", f"Không tìm thấy video hợp lệ trong thư mục: {dir_path}")

    def add_video_to_table(self, video_path: str):
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0).data(Qt.ItemDataRole.UserRole) == video_path:
                return

        row = self.table.rowCount()
        self.table.insertRow(row)

        p = Path(video_path)
        size_mb = p.stat().st_size / (1024 * 1024) if p.exists() else 0

        item_name = QTableWidgetItem(p.name)
        item_name.setData(Qt.ItemDataRole.UserRole, video_path)

        item_size = QTableWidgetItem(f"{size_mb:.1f} MB")
        item_size.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        item_status = QTableWidgetItem("Sẵn sàng")
        item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item_status.setForeground(QColor("#94a3b8"))

        item_title = QTableWidgetItem("")
        item_srt = QTableWidgetItem("")

        self.table.setItem(row, 0, item_name)
        self.table.setItem(row, 1, item_size)
        self.table.setItem(row, 2, item_status)
        self.table.setItem(row, 3, item_title)
        self.table.setItem(row, 4, item_srt)

    def clear_file_list(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Cảnh báo", "Đang có tiến trình xử lý! Vui lòng dừng lại trước khi xóa.")
            return
        self.table.setRowCount(0)

    def on_table_item_clicked(self, item: QTableWidgetItem):
        row = item.row()
        srt_item = self.table.item(row, 4)
        if srt_item and srt_item.text():
            srt_path = srt_item.text()
            if os.path.exists(srt_path):
                try:
                    with open(srt_path, "r", encoding="utf-8-sig") as f:
                        self.srt_preview.setText(f.read())
                        self.tabs.setCurrentIndex(1)
                except Exception as e:
                    self.log_text.append(f"Lỗi đọc preview SRT: {e}")

    def start_processing(self):
        is_chrome = self.radio_chrome.isChecked()
        mode = "chrome" if is_chrome else "api"

        try:
            chrome_port = int(self.port_input.text().strip() or "9222")
        except ValueError:
            chrome_port = 9222

        api_key = self.api_input.text().strip()

        if mode == "api" and not api_key:
            QMessageBox.warning(self, "Thiếu API Key", "Vui lòng nhập Google Gemini API Key khi dùng chế độ API!")
            self.api_input.setFocus()
            return

        if mode == "chrome":
            if not is_port_open(chrome_port):
                reply = QMessageBox.question(
                    self,
                    "Chrome Chưa Mở Cổng Debug",
                    f"Cổng Chrome Remote Debugging ({chrome_port}) chưa mở.\n"
                    "Bạn có muốn công cụ tự động khởi động Chrome ở chế độ debug ngay bây giờ không?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.launch_chrome_clicked()
                else:
                    return

        if self.table.rowCount() == 0:
            QMessageBox.information(self, "Danh sách rỗng", "Vui lòng thêm ít nhất 1 video để xử lý!")
            return

        # Lưu cài đặt
        self.config["mode"] = mode
        self.config["chrome_port"] = chrome_port
        self.config["api_key"] = api_key
        self.model_combo_text = self.model_combo.currentText()
        self.config["model"] = self.model_combo_text
        self.config["rename_video"] = self.chk_rename_video.isChecked()
        self.config["create_subfolder"] = self.chk_subfolder.isChecked()
        self.config["create_metadata"] = self.chk_metadata.isChecked()
        self.config["metadata_template"] = self.metadata_edit.toPlainText().strip()
        self.config["keep_temp_audio"] = self.chk_keep_audio.isChecked()
        self.config["output_dir"] = self.output_dir_input.text().strip() if self.chk_custom_out.isChecked() else ""
        self.config["custom_prompt"] = self.prompt_edit.toPlainText().strip()
        save_config(self.config)

        # Danh sách task
        tasks = []
        for r in range(self.table.rowCount()):
            status_item = self.table.item(r, 2)
            if "Hoàn thành" not in status_item.text():
                video_path = self.table.item(r, 0).data(Qt.ItemDataRole.UserRole)
                tasks.append({"row": r, "video_path": video_path})

        if not tasks:
            QMessageBox.information(self, "Thông báo", "Tất cả các video trong danh sách đã được xử lý xong!")
            return

        out_dir = self.output_dir_input.text().strip() if self.chk_custom_out.isChecked() else None

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setEnabled(True)
        self.btn_pause.setText("⏸ Tạm Dừng")
        self.btn_pause.setObjectName("pauseBtn")
        self.btn_pause.setStyleSheet("")
        self.btn_add_files.setEnabled(False)
        self.btn_add_dir.setEnabled(False)
        self.btn_clear_list.setEnabled(False)
        self.progress_bar.setRange(0, 0)

        self.worker = WorkerThread(
            tasks=tasks,
            mode=mode,
            chrome_port=chrome_port,
            api_key=api_key,
            model_name=self.model_combo.currentText(),
            custom_prompt=self.prompt_edit.toPlainText().strip(),
            rename_video=self.chk_rename_video.isChecked(),
            create_subfolder=self.chk_subfolder.isChecked(),
            create_metadata=self.chk_metadata.isChecked(),
            metadata_template=self.metadata_edit.toPlainText().strip(),
            output_dir=out_dir,
            keep_temp_audio=self.chk_keep_audio.isChecked(),
        )

        self.worker.log_signal.connect(self.append_log)
        self.worker.item_updated.connect(self.on_item_updated)
        self.worker.finished_signal.connect(self.on_processing_finished)
        self.worker.start()

    def toggle_pause(self):
        if not self.worker or not self.worker.isRunning():
            return

        if self.worker.is_paused():
            self.worker.resume()
            self.btn_pause.setText("⏸ Tạm Dừng")
            self.btn_pause.setObjectName("pauseBtn")
            self.btn_pause.setStyleSheet("")
            self.append_log("▶ ĐÃ TIẾP TỤC: Đang tiếp tục xử lý danh sách video...")
        else:
            self.worker.pause()
            self.btn_pause.setText("▶ Tiếp Tục")
            self.btn_pause.setObjectName("resumeBtn")
            self.btn_pause.setStyleSheet("")
            self.append_log("⏸ ĐÃ TẠM DỪNG: Tiến trình sẽ tạm dừng sau video hiện tại. Nhấn '▶ Tiếp Tục' để xử lý các video còn lại.")

    def stop_processing(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.append_log("⚠ Đang gửi tín hiệu dừng tiến trình...")
            self.btn_stop.setEnabled(False)
            self.btn_pause.setEnabled(False)

    @pyqtSlot(str)
    def append_log(self, message: str):
        self.log_text.append(message)
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    @pyqtSlot(int, str, str, str)
    def on_item_updated(self, row: int, status: str, title: str, srt_path: str):
        if row < self.table.rowCount():
            status_item = self.table.item(row, 2)
            if status_item:
                status_item.setText(status)
                if "Hoàn thành" in status:
                    status_item.setForeground(QColor("#4ade80"))
                elif "Lỗi" in status:
                    status_item.setForeground(QColor("#f87171"))
                else:
                    status_item.setForeground(QColor("#38bdf8"))

            if title:
                title_item = self.table.item(row, 3)
                if title_item:
                    title_item.setText(title)

            if srt_path:
                srt_item = self.table.item(row, 4)
                if srt_item:
                    srt_item.setText(srt_path)
                self.last_completed_dir = os.path.dirname(srt_path)

                if os.path.exists(srt_path):
                    try:
                        with open(srt_path, "r", encoding="utf-8-sig") as f:
                            self.srt_preview.setText(f.read())
                    except Exception:
                        pass

    @pyqtSlot()
    def on_processing_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText("⏸ Tạm Dừng")
        self.btn_pause.setObjectName("pauseBtn")
        self.btn_pause.setStyleSheet("")
        self.btn_add_files.setEnabled(True)
        self.btn_add_dir.setEnabled(True)
        self.btn_clear_list.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.append_log("🏁 TẤT CẢ TIẾN TRÌNH ĐÃ KẾT THÚC.")
        QMessageBox.information(self, "Hoàn Tất", "Đã hoàn thành toàn bộ danh sách video!")

    def open_output_folder(self):
        folder_to_open = self.last_completed_dir
        if not folder_to_open and self.chk_custom_out.isChecked():
            folder_to_open = self.output_dir_input.text().strip()
        if not folder_to_open and self.table.rowCount() > 0:
            first_path = self.table.item(0, 0).data(Qt.ItemDataRole.UserRole)
            if first_path:
                folder_to_open = os.path.dirname(first_path)

        if folder_to_open and os.path.exists(folder_to_open):
            os.startfile(folder_to_open)
        else:
            QMessageBox.information(self, "Thông báo", "Chưa có thư mục nào để mở.")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
