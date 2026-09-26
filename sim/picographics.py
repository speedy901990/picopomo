"""Desktop stand-in for Pimoroni's picographics module (dev only).

Implements the subset the app uses and renders into a Pillow image, with the
real bitmap8 glyphs so text metrics match the device exactly.
"""
from PIL import Image, ImageDraw

from font8 import WIDTHS, DATA

DISPLAY_PICO_DISPLAY_2 = 2
PEN_P8 = 3

W, H = 320, 240


def _ints(*vals):
    # The real binding converts with mp_obj_get_int(): floats raise TypeError.
    for v in vals:
        if not isinstance(v, int) or isinstance(v, bool):
            raise TypeError("picographics needs int, got %r" % (v,))


class PicoGraphics:
    def __init__(self, display=None, pen_type=None, rotate=0):
        self.img = Image.new("RGB", (W, H))
        self.dr = ImageDraw.Draw(self.img)
        self.palette = []
        self.pen = 0
        self.backlight = 1.0
        self.frames = 0

    # -- palette ---------------------------------------------------------
    def get_bounds(self):
        return (W, H)

    def create_pen(self, r, g, b):
        _ints(r, g, b)
        if len(self.palette) >= 256:
            raise RuntimeError("P8 palette exhausted (256 pens)")
        self.palette.append((r, g, b))
        return len(self.palette) - 1

    def update_pen(self, i, r, g, b):
        _ints(i, r, g, b)
        self.palette[i] = (r, g, b)

    def set_pen(self, p):
        self.pen = p

    def _c(self):
        return self.palette[self.pen]

    # -- primitives ------------------------------------------------------
    def clear(self):
        self.dr.rectangle([0, 0, W - 1, H - 1], fill=self._c())

    def pixel(self, x, y):
        _ints(x, y)
        if 0 <= x < W and 0 <= y < H:
            self.img.putpixel((x, y), self._c())

    def rectangle(self, x, y, w, h):
        _ints(x, y, w, h)
        if w <= 0 or h <= 0:
            return
        self.dr.rectangle([x, y, x + w - 1, y + h - 1], fill=self._c())

    def circle(self, x, y, r):
        _ints(x, y, r)
        # Same rule as the C++ implementation: fill where dx*dx + dy*dy <= r*r
        c = self._c()
        rr = r * r
        for dy in range(-r, r + 1):
            dx = 0
            while (dx + 1) * (dx + 1) + dy * dy <= rr:
                dx += 1
            self.dr.line([x - dx, y + dy, x + dx, y + dy], fill=c)

    def triangle(self, x1, y1, x2, y2, x3, y3):
        _ints(x1, y1, x2, y2, x3, y3)
        self.dr.polygon([(x1, y1), (x2, y2), (x3, y3)], fill=self._c())

    def line(self, x1, y1, x2, y2, thickness=1):
        _ints(x1, y1, x2, y2, thickness)
        self.dr.line([x1, y1, x2, y2], fill=self._c(), width=thickness)

    # -- text (bitmap8 only) ----------------------------------------------
    def set_font(self, name):
        pass

    def set_thickness(self, t):
        pass

    def measure_text(self, text, scale=2, spacing=1, fixed_width=False):
        w = 0
        for ch in text:
            i = ord(ch) - 32
            if 0 <= i < 96:
                w += WIDTHS[i] * scale + spacing * scale
        return w - spacing * scale if w else 0

    def text(self, text, x, y, wordwrap=2 ** 31 - 1, scale=2, angle=0, spacing=1, fixed_width=False):
        _ints(x, y, wordwrap, angle, spacing)
        c = self._c()
        for ch in text:
            i = ord(ch) - 32
            if not (0 <= i < 96):
                continue
            for cx in range(WIDTHS[i]):
                col = DATA[i][cx]
                for cy in range(8):
                    if col & (1 << cy):
                        px, py = x + cx * scale, y + cy * scale
                        self.dr.rectangle([px, py, px + scale - 1, py + scale - 1], fill=c)
            x += WIDTHS[i] * scale + spacing * scale

    # -- device ----------------------------------------------------------
    def set_backlight(self, v):
        self.backlight = v

    def update(self):
        self.frames += 1

    def save(self, path, zoom=2):
        img = self.img
        if self.backlight < 0.5:  # show the idle-dim state only
            img = img.point(lambda v: int(v * max(self.backlight, 0.1)))
        img.resize((W * zoom, H * zoom), Image.NEAREST).save(path)
