import tkinter as tk

import keyboard

from screen_translator import capture, config, ocr
from screen_translator import translate as tr
from screen_translator.overlay import Overlay


def run():
    root = tk.Tk()
    root.withdraw()
    overlay = Overlay(root)

    def do_toggle():
        if overlay.visible:
            overlay.hide()
            return
        try:
            png_bytes, offset = capture.grab_screen_png()
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
            overlay.show(offset, items)

            if config.AUTO_HIDE_SECONDS > 0:
                root.after(config.AUTO_HIDE_SECONDS * 1000, overlay.hide)
        except Exception as exc:  # noqa: BLE001 - surface any failure to the console instead of crashing the hotkey thread
            print(f"[screen-translator] error: {exc}")

    def on_hotkey():
        root.after(0, do_toggle)

    keyboard.add_hotkey(config.HOTKEY, on_hotkey)
    print(f"Screen Translator running. Press {config.HOTKEY} to translate the screen.")
    print(f"Translation engine: {config.TRANSLATE_ENGINE} (target: {config.TRANSLATE_TARGET})")
    print("Press Ctrl+C in this console window to quit.")
    root.mainloop()


if __name__ == "__main__":
    run()
