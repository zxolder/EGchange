import os
import time

from deep_translator import DeeplTranslator, GoogleTranslator, MicrosoftTranslator

_LINE_SEP = "\n"


def _build_translator(engine: str, target: str, source: str):
    engine = engine.lower()
    if engine == "google":
        return GoogleTranslator(source=source, target=target)
    if engine == "deepl":
        api_key = os.environ["DEEPL_API_KEY"]
        return DeeplTranslator(api_key=api_key, source=source, target=target)
    if engine == "microsoft":
        api_key = os.environ["MS_TRANSLATOR_KEY"]
        region = os.getenv("MS_TRANSLATOR_REGION", "global")
        return MicrosoftTranslator(api_key=api_key, target=target, region=region)
    raise ValueError(f"Unknown TRANSLATE_ENGINE: {engine!r} (use google, deepl, or microsoft)")


def translate_lines(lines, target="zh-TW", engine="google", source="en"):
    """Translate a list of source-language lines, preserving order.

    Joins every line into a single request (instead of one request per
    line) so a screen with many OCR lines doesn't trip the free Google
    endpoint's per-second rate limit.
    """
    if not lines:
        return []

    translator = _build_translator(engine, target, source)
    joined = _LINE_SEP.join(lines)

    for attempt in range(3):
        try:
            translated = translator.translate(joined)
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1.5)

    translated_lines = translated.split(_LINE_SEP)
    if len(translated_lines) < len(lines):
        translated_lines += [""] * (len(lines) - len(translated_lines))
    elif len(translated_lines) > len(lines):
        translated_lines = translated_lines[: len(lines)]
    return translated_lines
