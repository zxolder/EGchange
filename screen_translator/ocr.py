import asyncio

from winsdk.windows.globalization import Language
from winsdk.windows.graphics.imaging import BitmapDecoder
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.storage.streams import InMemoryRandomAccessStream, DataWriter


async def _png_bytes_to_bitmap(png_bytes: bytes):
    stream = InMemoryRandomAccessStream()
    writer = DataWriter(stream.get_output_stream_at(0))
    writer.write_bytes(png_bytes)
    await writer.store_async()
    await writer.flush_async()
    stream.seek(0)
    decoder = await BitmapDecoder.create_async(stream)
    return await decoder.get_software_bitmap_async()


async def recognize(png_bytes: bytes, lang_tag: str = "en"):
    """Run Windows' built-in OCR engine over a PNG screenshot.

    Returns a list of {"text": str, "bbox": (x0, y0, x1, y1)} per detected line.
    """
    language = Language(lang_tag)
    if not OcrEngine.is_language_supported(language):
        raise RuntimeError(
            f"OCR language pack for '{lang_tag}' is not installed. "
            "Add it via Windows Settings > Time & language > Language & region."
        )

    engine = OcrEngine.try_create_from_language(language)
    bitmap = await _png_bytes_to_bitmap(png_bytes)
    result = await engine.recognize_async(bitmap)

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


def recognize_sync(png_bytes: bytes, lang_tag: str = "en", timeout: float = 15.0):
    async def _with_timeout():
        return await asyncio.wait_for(recognize(png_bytes, lang_tag), timeout)

    try:
        return asyncio.run(_with_timeout())
    except asyncio.TimeoutError as exc:
        raise RuntimeError(f"OCR timed out after {timeout:.0f}s") from exc
