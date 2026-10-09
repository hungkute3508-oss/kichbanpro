import json
import os
import sys
from pathlib import Path
from typing import Any, Dict
from core import DEFAULT_METADATA_TEMPLATE, DEFAULT_PROMPT

def get_config_file_path() -> Path:
    """Xác định vị trí config.json: cạnh .exe nếu chạy dạng đóng gói, hoặc cạnh file mã nguồn."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "config.json"
    return Path(__file__).parent / "config.json"

CONFIG_FILE = get_config_file_path()

DEFAULT_CONFIG: Dict[str, Any] = {
    "mode": "chrome",  # "chrome" (Remote Debug) hoặc "api" (Gemini API)
    "chrome_port": 9222,
    "api_key": "",
    "model": "gemini-2.5-flash",
    "rename_video": True,
    "create_subfolder": True,
    "create_metadata": True,
    "metadata_template": DEFAULT_METADATA_TEMPLATE,
    "keep_temp_audio": False,
    "output_dir": "",
    "custom_prompt": DEFAULT_PROMPT,
}




def load_config() -> Dict[str, Any]:
    """Tải cấu hình từ config.json hoặc biến môi trường."""
    config = DEFAULT_CONFIG.copy()

    # Ưu tiên lấy từ biến môi trường nếu có
    env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if env_key:
        config["api_key"] = env_key

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config.update(data)
        except Exception as e:
            print(f"Lỗi đọc file cấu hình config.json: {e}")

    return config


def save_config(config: Dict[str, Any]) -> None:
    """Lưu cấu hình vào config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi lưu file cấu hình config.json: {e}")
