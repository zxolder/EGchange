import io

import mss
from PIL import Image


def grab_screen_png():
    """Capture the full virtual screen (all monitors) as PNG bytes.

    Returns (png_bytes, (offset_x, offset_y)) where the offset is the
    top-left corner of the captured region in virtual-screen coordinates,
    needed to position the overlay window on the same spot.
    """
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        shot = sct.grab(monitor)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), (monitor["left"], monitor["top"])
