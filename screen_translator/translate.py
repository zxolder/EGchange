import os

from deep_translator import DeeplTranslator, GoogleTranslator, MicrosoftTranslator


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
    """Translate a list of source-language lines, preserving order."""
    if not lines:
        return []
    translator = _build_translator(engine, target, source)
    return translator.translate_batch(lines)
