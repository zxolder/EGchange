import tkinter as tk

_KEY_COLOR = "black"


class Overlay:
    """Transparent, click-through window used to draw translated text
    boxes on top of the original on-screen text, sized to the captured
    region (a single window or the full virtual screen)."""

    def __init__(self, root: tk.Tk):
        self._root = root
        self._window = None

    def show(self, region, items):
        self.hide()
        if not items:
            return

        left, top, width, height = region
        window = tk.Toplevel(self._root)
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        window.attributes("-transparentcolor", _KEY_COLOR)
        window.configure(bg=_KEY_COLOR)
        window.geometry(f"{width}x{height}+{left}+{top}")

        canvas = tk.Canvas(window, bg=_KEY_COLOR, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        for item in items:
            x0, y0, x1, y1 = item["bbox"]
            text = item["translated"]
            if not text:
                continue

            font_size = max(10, min(20, int((y1 - y0) * 0.7)))
            # Give the text more horizontal room than the original box so a
            # short translation doesn't need to wrap just because the source
            # line was narrow.
            wrap_width = max(x1 - x0, 220)
            text_id = canvas.create_text(
                (x0 + x1) / 2,
                (y0 + y1) / 2,
                text=text,
                fill="#ffdd57",
                font=("Microsoft JhengHei", font_size, "bold"),
                width=wrap_width,
                justify="center",
            )
            # Size the background to the text's actual rendered extent
            # (which may span more than one line) instead of the original
            # line's box, so it never spills out from behind its own text
            # into a neighboring line.
            pad = 3
            bx0, by0, bx1, by1 = canvas.bbox(text_id)
            rect_id = canvas.create_rectangle(
                bx0 - pad, by0 - pad, bx1 + pad, by1 + pad, fill="#1e1e1e", outline=""
            )
            canvas.tag_lower(rect_id, text_id)

        window.bind("<Escape>", lambda _event: self.hide())
        self._window = window

    def hide(self):
        if self._window is not None:
            try:
                self._window.destroy()
            except tk.TclError:
                pass
            self._window = None

    @property
    def visible(self):
        return self._window is not None
