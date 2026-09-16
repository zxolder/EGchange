import os
import re
import time

import requests
from deep_translator import DeeplTranslator, GoogleTranslator, MicrosoftTranslator

_LINE_SEP = "\n"
_NUMBERED_LINE_RE = re.compile(r"^\s*(\d+)\s*[:.]\s?(.*)$")

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


def _gemini_translate_lines(lines, target: str, source: str) -> list:
    """Translate each line independently via Gemini, matched back up by an
    explicit line number instead of positional order.

    A plain "translate this block, keep the same number of lines" prompt
    breaks down once a screen has many short, unrelated OCR fragments (menu
    items, tab labels, etc.): the model occasionally merges or reorders a
    couple of lines, and every line after that point then lands on the
    wrong on-screen text box. Numbering each line and asking for the same
    numbers back lets us realign correctly even when the model doesn't
    preserve order or drops a line.
    """
    api_key = os.environ["GEMINI_API_KEY"]
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    target_name = _LANGUAGE_NAMES.get(target.lower(), target)
    source_name = _LANGUAGE_NAMES.get(source.lower(), source)

    numbered = _LINE_SEP.join(f"{i + 1}: {line}" for i, line in enumerate(lines))
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    prompt = (
        f"Each numbered line below is a separate, unrelated piece of on-screen UI text in {source_name}. "
        f"Translate each one to {target_name} independently. Do not merge, reorder, drop, or combine lines, "
        "even if some look like fragments of a sentence. "
        "Reply with the exact same numbers, one per output line, in the format 'N: translated text', in "
        "ascending numeric order, with no extra commentary. If a line has no translatable words (numbers, "
        "symbols, proper nouns), repeat it unchanged after its number.\n\n"
        f"{numbered}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        # Flash models "think" before answering by default, which adds several
        # seconds of latency that isn't worth it for a plain translation task.
        "generationConfig": {"thinkingConfig": {"thinkingBudget": 0}},
    }

    response = requests.post(url, params={"key": api_key}, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    reply = data["candidates"][0]["content"]["parts"][0]["text"]

    translated_by_number = {}
    for raw_line in reply.splitlines():
        match = _NUMBERED_LINE_RE.match(raw_line)
        if match:
            translated_by_number[int(match.group(1))] = match.group(2).strip()

    return [translated_by_number.get(i + 1, "") for i in range(len(lines))]


def translate_lines(lines, target="zh-TW", engine="google", source="en"):
    """Translate a list of source-language lines, preserving order.

    Joins every line into a single request (instead of one request per
    line) so a screen with many OCR lines doesn't trip the free Google
    endpoint's per-second rate limit.
    """
    if not lines:
        return []

    is_gemini = engine.lower() == "gemini"
    translator = None if is_gemini else _build_translator(engine, target, source)
    joined = _LINE_SEP.join(lines)

    for attempt in range(3):
        try:
            if is_gemini:
                return _gemini_translate_lines(lines, target, source)
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
