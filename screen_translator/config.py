import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def _app_dir() -> Path:
    """Directory the .env file should live next to.

    When frozen by PyInstaller, that's the exe's own folder (not the
    current working directory, which some launch methods - e.g. "Run as
    administrator" - point elsewhere). When running from source, it's
    the project root.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


load_dotenv(_app_dir() / ".env")

HOTKEY = os.getenv("SCREEN_TRANSLATOR_HOTKEY", "ctrl+alt+t")
OCR_SOURCE_LANG = os.getenv("OCR_SOURCE_LANG", "en")
TRANSLATE_TARGET = os.getenv("TRANSLATE_TARGET", "zh-TW")
TRANSLATE_ENGINE = os.getenv("TRANSLATE_ENGINE", "google")
AUTO_HIDE_SECONDS = int(os.getenv("AUTO_HIDE_SECONDS", "8"))
