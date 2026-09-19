import asyncio

from winsdk.windows.globalization import Language
from winsdk.windows.graphics.imaging import BitmapAlphaMode, BitmapPixelFormat, SoftwareBitmap
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.security.cryptography import CryptographicBuffer


def _bgra_to_bitmap(bgra_bytes: bytes, width: int, height: int):
    """Build a SoftwareBitmap straight from raw BGRA8 pixels.

    Avoids encoding to PNG and having Windows decode it back (via
    BitmapDecoder/WIC), which depends on imaging codecs that can be
    missing or broken on some Windows installs (e.g. editions without
    the Media Feature Pack) and were observed to hang indefinitely on
    one such machine. This is a plain in-memory buffer copy instead.
    """
    buffer = CryptographicBuffer.create_from_byte_array(bgra_bytes)
    return SoftwareBitmap.create_copy_from_buffer(buffer, BitmapPixelFormat.BGRA8, width, height, BitmapAlphaMode.IGNORE)


async def recognize(bgra_bytes: bytes, width: int, height: int, lang_tag: str = "en"):
    """Run Windows' built-in OCR engine over a raw BGRA8 screenshot.

    Returns a list of {"text": str, "bbox": (x0, y0, x1, y1)} per detected line.
    """
    language = Language(lang_tag)
    supported = OcrEngine.is_language_supported(language)
    print(f"[screen-translator] ocr: language {lang_tag!r} supported = {supported}")
    if not supported:
        raise RuntimeError(
            f"OCR language pack for '{lang_tag}' is not installed. "
            "Add it via Windows Settings > Time & language > Language & region."
        )

    engine = OcrEngine.try_create_from_language(language)
    print(f"[screen-translator] ocr: engine created = {engine is not None}")
    bitmap = _bgra_to_bitmap(bgra_bytes, width, height)
    print("[screen-translator] ocr: bitmap ready, running recognize_async...")
    result = await engine.recognize_async(bitmap)
    print(f"[screen-translator] ocr: recognize_async done, {len(list(result.lines))} line(s)")

    lines = []
    for line in result.lines:
        words = list(line.words)
        if not words:
            continue
        xs = [w.bounding_rect.x for w in words]
        ys = [w.bounding_rect.y for w in words]
        rights = [w.bounding_rect.x + w.bounding_rect.width for w in words]
        bottoms = [w.bounding_rect.y + w.bounding_rect.height for w in words]
        bbox = (min(xs), min(ys), max(rights), max(bottoms))
        lines.append({"text": line.text, "bbox": bbox})
    return lines


def recognize_sync(bgra_bytes: bytes, width: int, height: int, lang_tag: str = "en", timeout: float = 15.0):
    async def _with_timeout():
        return await asyncio.wait_for(recognize(bgra_bytes, width, height, lang_tag), timeout)

    try:
        return asyncio.run(_with_timeout())
    except asyncio.TimeoutError as exc:
        raise RuntimeError(f"OCR timed out after {timeout:.0f}s") from exc
