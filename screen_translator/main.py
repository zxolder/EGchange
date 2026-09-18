import queue
import tkinter as tk

from screen_translator import capture, config, hotkey, ocr
from screen_translator import translate as tr
from screen_translator.overlay import Overlay


def run():
    root = tk.Tk()
    root.withdraw()
    overlay = Overlay(root)
    # The hotkey listener runs on its own OS thread; Tkinter isn't safe to
    # call into from any thread but the one running mainloop(). Hand events
    # off through a thread-safe queue instead of touching Tk directly from
    # the hotkey thread (which can silently hang or misbehave depending on
    # timing).
    hotkey_events = queue.Queue()

    def do_toggle():
        if overlay.visible:
            overlay.hide()
            return
        try:
            if config.CAPTURE_MODE == "active_window":
                png_bytes, region = capture.grab_active_window_png()
            else:
                png_bytes, region = capture.grab_screen_png()
            lines = ocr.recognize_sync(png_bytes, config.OCR_SOURCE_LANG)
            if not lines:
                print("[screen-translator] no text detected on screen")
                return

            translated = tr.translate_lines(
                [line["text"] for line in lines],
                target=config.TRANSLATE_TARGET,
                engine=config.TRANSLATE_ENGINE,
                source=config.OCR_SOURCE_LANG,
            )
            items = [
                {"bbox": line["bbox"], "translated": text}
                for line, text in zip(lines, translated)
            ]
            overlay.show(region, items)

            if config.AUTO_HIDE_SECONDS > 0:
                root.after(config.AUTO_HIDE_SECONDS * 1000, overlay.hide)
        except Exception as exc:  # noqa: BLE001 - surface any failure to the console instead of crashing the hotkey thread
            print(f"[screen-translator] error: {exc}")

    def poll_hotkey_queue():
        try:
            while True:
                hotkey_events.get_nowait()
                do_toggle()
        except queue.Empty:
            pass
        root.after(50, poll_hotkey_queue)

    def on_hotkey():
        # Called from the hotkey thread - must not touch Tk directly.
        hotkey_events.put_nowait(None)

    # Keep a reference so the hotkey listener thread isn't garbage collected.
    _hotkey_thread = hotkey.register_hotkey(config.HOTKEY, on_hotkey)  # noqa: F841
    print(f"Screen Translator running. Press {config.HOTKEY} to translate the screen.")
    print(f"Translation engine: {config.TRANSLATE_ENGINE} (target: {config.TRANSLATE_TARGET})")
    print("Press Ctrl+C in this console window to quit.")
    root.after(50, poll_hotkey_queue)
    root.mainloop()


if __name__ == "__main__":
    run()
