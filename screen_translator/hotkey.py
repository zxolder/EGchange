import ctypes
import threading
from ctypes import wintypes

_user32 = ctypes.windll.user32

_MOD_ALT = 0x0001
_MOD_CONTROL = 0x0002
_MOD_SHIFT = 0x0004
_MOD_WIN = 0x0008
_WM_HOTKEY = 0x0312

_MODIFIERS = {
    "ctrl": _MOD_CONTROL,
    "control": _MOD_CONTROL,
    "alt": _MOD_ALT,
    "shift": _MOD_SHIFT,
    "win": _MOD_WIN,
    "windows": _MOD_WIN,
}

_FUNCTION_KEYS = {f"f{i}": 0x70 + i - 1 for i in range(1, 25)}
_NAMED_KEYS = {
    "space": 0x20,
    "tab": 0x09,
    "esc": 0x1B,
    "escape": 0x1B,
    "enter": 0x0D,
    "return": 0x0D,
}


def _vk_code(key: str) -> int:
    key = key.lower()
    if key in _FUNCTION_KEYS:
        return _FUNCTION_KEYS[key]
    if key in _NAMED_KEYS:
        return _NAMED_KEYS[key]
    if len(key) == 1:
        return ord(key.upper())
    raise ValueError(f"Unsupported key in hotkey: {key!r}")


def _parse_hotkey(hotkey_str: str):
    modifiers = 0
    vk = None
    for part in hotkey_str.split("+"):
        part = part.strip().lower()
        if part in _MODIFIERS:
            modifiers |= _MODIFIERS[part]
        else:
            vk = _vk_code(part)
    if vk is None:
        raise ValueError(f"Could not find a non-modifier key in hotkey {hotkey_str!r}")
    return modifiers, vk


def register_hotkey(hotkey_str: str, callback) -> threading.Thread:
    """Register a system-wide hotkey via Win32's RegisterHotKey/WM_HOTKEY.

    This is the mechanism most desktop hotkey utilities use, registering
    just the one key combination with the OS instead of hooking every
    keystroke - it also tends to keep working in environments (VMs, remote
    desktop sessions, locked-down machines) where a low-level keyboard hook
    can silently fail to receive any events at all.

    Runs its own message loop in a background thread; call join() on the
    returned thread, or simply keep it referenced so it isn't garbage
    collected, for the lifetime of the app.
    """
    modifiers, vk = _parse_hotkey(hotkey_str)

    def _run():
        hotkey_id = 1
        if not _user32.RegisterHotKey(None, hotkey_id, modifiers, vk):
            error = ctypes.GetLastError()
            print(
                f"[screen-translator] failed to register hotkey {hotkey_str!r} "
                f"(Win32 error {error}); another program may already be using it"
            )
            return

        msg = wintypes.MSG()
        try:
            while _user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == _WM_HOTKEY:
                    callback()
        finally:
            _user32.UnregisterHotKey(None, hotkey_id)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread
