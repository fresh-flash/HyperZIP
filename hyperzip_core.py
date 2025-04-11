import os
import sys
import io

# Попытка импорта с проверкой
try:
    from colorama import init, Fore, Style
    init() # Инициализация сразу после импорта
except ImportError:
    print("Warning: colorama library not found. Colored output will be disabled.")
    print("Try: pip install colorama")
    # Определяем "заглушки" для Fore и Style, чтобы скрипт не падал
    class DummyStyle:
        def __getattr__(self, name):
            return ""
    Fore = DummyStyle()
    Style = DummyStyle()
    def init(): # Пустая функция init
        pass

# ==============================================================================
# == Default Configuration (can be overridden by GUI) ==
# ==============================================================================

DEFAULT_SETTINGS = {
    "ARCHIVE_PROFILE": "7zip_zip",
    "winrar_path": r"C:\Program Files\WinRAR\WinRAR.exe",
    "sevenzip_path": r"C:\Program Files\7-Zip\7z.exe",
    "zpaq_path": r"C:\zpaq\zpaq.exe", # Example, change if needed
    "max_size_kb": 150.0,
    "ENABLE_MINIFICATION": True,
    "ENABLE_IMAGE_COMPRESSION": True,
    "TINIFY_API_KEY": "", # MUST be provided by user
    "INITIAL_PNG_OPTIMIZATION_LEVEL": 8,
    "INITIAL_JPEG_QUALITY": 90,
    "MIN_PNG_OPTIMIZATION_LEVEL": 1,
    "MIN_JPEG_QUALITY": 10,
    "JPEG_QUALITY_STEP": 10,
    "FIND_OPTIMAL_QUALITY": True,
    "PROJECT_FOLDER": None, # Must be provided
    # Default exclusions (space-separated) - based on 7zip defaults
    "ARCHIVE_EXCLUSIONS": "*.ini *.db *.fla *.psd *.pdf *.ai *.zip *.rar *.7z *.zpaq *.DS_Store Thumbs.db *~"
}

# Supported image formats (remain constant)
PNG_EXTENSIONS = {'.png'}
JPEG_EXTENSIONS = {'.jpg', '.jpeg'}
IMAGE_EXTENSIONS = PNG_EXTENSIONS | JPEG_EXTENSIONS | {'.webp', '.gif'}

# --- Logger Function ---
# This allows redirecting print statements to the GUI or console
_log_func = print # Default to standard print

def set_logger(logger_func):
    """Sets the function used for logging messages."""
    global _log_func
    _log_func = logger_func
