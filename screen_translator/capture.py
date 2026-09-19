import ctypes
from ctypes import wintypes

import mss

_user32 = ctypes.windll.user32
_dwmapi = ctypes.windll.dwmapi

_DWMWA_EXTENDED_FRAME_BOUNDS = 9


class _RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


_user32.GetForegroundWindow.restype = wintypes.HWND
_user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(_RECT)]
_user32.GetWindowRect.restype = wintypes.BOOL
_dwmapi.DwmGetWindowAttribute.argtypes = [
    wintypes.HWND,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
]
_dwmapi.DwmGetWindowAttribute.restype = ctypes.c_long


def _grab_region(left, top, width, height):
    with mss.mss() as sct:
        region = {"left": left, "top": top, "width": width, "height": height}
        shot = sct.grab(region)
        # Raw BGRA8 pixels, tightly packed - handed straight to Windows OCR
        # without an intermediate PNG encode/decode (which depends on
        # imaging codecs that aren't always present, e.g. on Windows
        # editions without the Media Feature Pack).
        return bytes(shot.bgra), (left, top, width, height)


def grab_screen():
    """Capture the full virtual screen (all monitors).

    Returns (bgra_bytes, (left, top, width, height)) describing the
    captured region in virtual-screen coordinates, needed to position
    the overlay window on the same spot.
    """
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        return _grab_region(monitor["left"], monitor["top"], monitor["width"], monitor["height"])


def _active_window_bounds():
    hwnd = _user32.GetForegroundWindow()
    if not hwnd:
        return None

    rect = _RECT()
    hr = _dwmapi.DwmGetWindowAttribute(
        hwnd, _DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(rect), ctypes.sizeof(rect)
    )
    if hr != 0 and not _user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return None

    width = rect.right - rect.left
    height = rect.bottom - rect.top
    if width <= 0 or height <= 0:
        return None
    return rect.left, rect.top, width, height


def grab_active_window():
    """Capture only the current foreground window.

    Falls back to a full-screen capture if the active window can't be
    determined (no foreground window, or its bounds look invalid).
    Returns (bgra_bytes, (left, top, width, height)).
    """
    bounds = _active_window_bounds()
    if bounds is None:
        return grab_screen()
    return _grab_region(*bounds)
