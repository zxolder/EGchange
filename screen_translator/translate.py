import os
import time

import requests
from deep_translator import DeeplTranslator, GoogleTranslator, MicrosoftTranslator

_LINE_SEP = "\n"

_LANGUAGE_NAMES = {
    "zh-tw": "Traditional Chinese",
    "zh-cn": "Simplified Chinese",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "en": "English",
}


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
    raise ValueError(f"Unknown TRANSLATE_ENGINE: {engine!r} (use google, deepl, microsoft, or gemini)")


def _gemini_translate(text: str, target: str, source: str) -> str:
    api_key = os.environ["GEMINI_API_KEY"]
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    target_name = _LANGUAGE_NAMES.get(target.lower(), target)
    source_name = _LANGUAGE_NAMES.get(source.lower(), source)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    prompt = (
        f"Translate the following on-screen text lines from {source_name} to {target_name}. "
        "Keep exactly the same number of lines, in the same order, one translated line per input line. "
        "Return ONLY the translated lines with no numbering, quotes, or extra commentary. "
        "If a line has no translatable words (numbers, symbols, proper nouns), keep it unchanged.\n\n"
        f"{text}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    response = requests.post(url, params={"key": api_key}, json=payload, timeout=20)
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def translate_lines(lines, target="zh-TW", engine="google", source="en"):
    """Translate a list of source-language lines, preserving order.

    Joins every line into a single request (instead of one request per
    line) so a screen with many OCR lines doesn't trip the free Google
    endpoint's per-second rate limit.
    """
    if not lines:
        return []

    joined = _LINE_SEP.join(lines)
    is_gemini = engine.lower() == "gemini"
    translator = None if is_gemini else _build_translator(engine, target, source)

    for attempt in range(3):
        try:
            translated = _gemini_translate(joined, target, source) if is_gemini else translator.translate(joined)
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
