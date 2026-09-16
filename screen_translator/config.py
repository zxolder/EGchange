import os

HOTKEY = os.getenv("SCREEN_TRANSLATOR_HOTKEY", "ctrl+alt+t")
OCR_SOURCE_LANG = os.getenv("OCR_SOURCE_LANG", "en")
TRANSLATE_TARGET = os.getenv("TRANSLATE_TARGET", "zh-TW")
TRANSLATE_ENGINE = os.getenv("TRANSLATE_ENGINE", "google")
AUTO_HIDE_SECONDS = int(os.getenv("AUTO_HIDE_SECONDS", "8"))
