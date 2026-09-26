# Drawing primitives shared by all screens.
#
# Text uses Pimoroni's bitmap8 font (y = top of glyph). Big numbers use a
# 5x7 dot-matrix font drawn here as rounded dots, so they look identical on
# every firmware version.
import math

d = None
T = None

W, H = 320, 240


def init(display, theme):
    global d, T
    d = display
    T = theme
    d.set_font("bitmap8")


# --- shapes -----------------------------------------------------------------

def rect(x, y, w, h, pen):
    d.set_pen(pen)
    d.rectangle(x, y, w, h)


def rrect(x, y, w, h, r, pen):
    """Filled rounded rectangle. Use odd heights for perfectly round pills."""
    if w <= 0 or h <= 0:
        return
    r = min(r, (h - 1) // 2, (w - 1) // 2)
    d.set_pen(pen)
    if r <= 0:
        d.rectangle(x, y, w, h)
        return
    d.rectangle(x + r, y, w - 2 * r, h)
    d.rectangle(x, y + r, w, h - 2 * r)
    x2, y2 = x + w - 1 - r, y + h - 1 - r
    d.circle(x + r, y + r, r)
    d.circle(x2, y + r, r)
    d.circle(x + r, y2, r)
    d.circle(x2, y2, r)


def pill(x, y, w, h, pen):
    rrect(x, y, w, h, h // 2, pen)


def circle(x, y, r, pen):
    d.set_pen(pen)
    d.circle(x, y, r)


def ring(cx, cy, r_out, thick, frac, pen, track=None, bg=None):
    """Progress ring. frac=1 is a full circle; it shrinks clockwise towards
    12 o'clock as frac falls. Rounded caps on both ends."""
    r_in = r_out - thick
    if track is not None:
        circle(cx, cy, r_out, track)
        circle(cx, cy, r_in, bg)
    if frac <= 0:
        return
    frac = min(frac, 1.0)
    d.set_pen(pen)
    a0 = math.radians(-90 + (1 - frac) * 360)
    a1 = math.radians(270)
    steps = max(1, int((a1 - a0) / math.radians(3)) + 1)
    da = (a1 - a0) / steps
    # Slices are drawn as separate triangle pairs abutting at exact angles;
    # rasterizer rounding can leave 1px radial gaps at those seams, which
    # shift every frame as a0 rotates. Widen each slice slightly so it
    # overlaps its neighbours instead of exactly meeting them.
    overlap = (1.5 / r_in) if r_in > 0 else 0.0
    for i in range(1, steps + 1):
        lo = a0 + da * (i - 1) - overlap
        hi = a0 + da * i + overlap
        c, s = math.cos(lo), math.sin(lo)
        ox, oy = cx + c * r_out, cy + s * r_out
        ix, iy = cx + c * r_in, cy + s * r_in
        c, s = math.cos(hi), math.sin(hi)
        nox, noy = cx + c * r_out, cy + s * r_out
        nix, niy = cx + c * r_in, cy + s * r_in
        d.triangle(int(ox), int(oy), int(nox), int(noy), int(ix), int(iy))
        d.triangle(int(ix), int(iy), int(nox), int(noy), int(nix), int(niy))
    rm = (r_out + r_in) / 2
    cap = thick // 2
    for a in (a0, a1):
        d.circle(int(cx + math.cos(a) * rm), int(cy + math.sin(a) * rm), cap)


def bar(x, y, w, h, frac, bg, fg):
    pill(x, y, w, h, bg)
    if frac > 0:
        fw = max(h, int(w * min(frac, 1.0)))
        pill(x, y, fw, h, fg)


# --- text -------------------------------------------------------------------

def text(s, x, y, scale, pen, spacing=1):
    d.set_pen(pen)
    d.text(s, x, y, scale=scale, spacing=spacing)


def width(s, scale, spacing=1):
    return d.measure_text(s, scale=scale, spacing=spacing)


def text_c(s, cx, y, scale, pen, spacing=1):
    text(s, cx - width(s, scale, spacing) // 2, y, scale, pen, spacing)


def text_r(s, rx, y, scale, pen, spacing=1):
    text(s, rx - width(s, scale, spacing), y, scale, pen, spacing)


# --- dot-matrix numbers -----------------------------------------------------
# Each glyph: tuple of 7 row bitmasks, bit 4 = leftmost column. Width in cols.
_DM = {
    "0": (5, (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E)),
    "1": (5, (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E)),
    "2": (5, (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F)),
    "3": (5, (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E)),
    "4": (5, (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02)),
    "5": (5, (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E)),
    "6": (5, (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E)),
    "7": (5, (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08)),
    "8": (5, (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E)),
    "9": (5, (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C)),
    ":": (1, (0x00, 0x01, 0x01, 0x00, 0x01, 0x01, 0x00)),
    ".": (1, (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01)),
    "%": (5, (0x18, 0x19, 0x02, 0x04, 0x08, 0x13, 0x03)),
    "-": (3, (0x00, 0x00, 0x00, 0x07, 0x00, 0x00, 0x00)),
    " ": (2, (0, 0, 0, 0, 0, 0, 0)),
}


def dm_width(s, pitch):
    cols = 0
    for ch in s:
        cols += _DM.get(ch, _DM[" "])[0] + 1
    return max(0, cols - 1) * pitch


def _dot(x, y, size):
    if size >= 5:
        d.rectangle(x + 1, y, size - 2, size)
        d.rectangle(x, y + 1, size, size - 2)
    elif size == 4:
        d.rectangle(x + 1, y, 2, 4)
        d.rectangle(x, y + 1, 4, 2)
    else:
        d.rectangle(x, y, size, size)


def dm_text(s, x, y, pitch, size, on, off=None):
    """Dot-matrix text. `off` draws the unlit dots too (only for 5-col glyphs)."""
    for ch in s:
        cols, rows = _DM.get(ch, _DM[" "])
        for ry in range(7):
            bits = rows[ry]
            for cx in range(cols):
                lit = bits & (1 << (cols - 1 - cx))
                if lit:
                    d.set_pen(on)
                elif off is not None and cols == 5:
                    d.set_pen(off)
                else:
                    continue
                _dot(x + cx * pitch, y + ry * pitch, size)
        x += (cols + 1) * pitch


def dm_text_c(s, cx, y, pitch, size, on, off=None):
    dm_text(s, cx - dm_width(s, pitch) // 2, y, pitch, size, on, off)


# --- icons ------------------------------------------------------------------

def tomato(cx, cy, r, pen=None):
    circle(cx, cy, r, T.focus if pen is None else pen)
    d.set_pen(T.leaf)
    k = max(2, r // 2)
    top = cy - r
    d.triangle(cx - k - 1, top - 1, cx + k + 1, top - 1, cx, top + k)
    d.rectangle(cx, top - k, max(1, r // 4), k)


def check(x, y, pen):
    """Small tick mark, 9x7."""
    d.set_pen(pen)
    for i in range(3):
        d.rectangle(x + i, y + 3 + i, 2, 2)
    for i in range(5):
        d.rectangle(x + 3 + i, y + 4 - i, 2, 2)


# --- chrome -----------------------------------------------------------------

HEADER_H = 26
TAB_H = 21
TAB_Y = {"A": 34, "B": 207, "X": 34, "Y": 207}


def header(title, clock_str, sync_pen, today, goal):
    rect(0, 0, W, HEADER_H, T.bg)
    text(clock_str, 8, 6, 2, T.text)
    text_c(title, W // 2, 6, 2, T.subtext)
    # right side: sync dot, tomato, today/goal
    s = "%d/%d" % (today, goal)
    tw = width(s, 2)
    text(s, W - 8 - tw, 6, 2, T.goal if today >= goal else T.text)
    tomato(W - 8 - tw - 11, 13, 6)
    circle(W - 8 - tw - 29, 13, 3, sync_pen)


def tab(key, label, bg, fg, hold=0.0, hold_pen=None):
    """Edge tab next to a physical button. `hold` (0..1) grows a fill from the
    screen edge while a hold-to-confirm button is pressed."""
    if not label:
        return
    y = TAB_Y[key]
    left = key in ("A", "B")
    tw = width(label, 2)
    w = tw + 30
    x = -10 if left else W - w + 10
    rrect(x, y, w, TAB_H, 10, bg)
    if hold > 0:
        hp = fg if hold_pen is None else hold_pen
        fw = int((w - 10) * min(hold, 1.0))
        if left:
            rrect(x, y, 10 + fw, TAB_H, 10, hp)
        else:
            rrect(x + w - 10 - fw, y, 10 + fw, TAB_H, 10, hp)
        fg = bg if hold_pen is None else T.ink
    tx = 10 if left else W - 10 - tw
    text(label, tx, y + 4, 2, fg)


def toast(msg):
    tw = width(msg, 2)
    w = tw + 24
    x = (W - w) // 2
    rrect(x, H - 30, w, 23, 11, T.text)
    text(msg, x + 12, H - 26, 2, T.bg)


def page_dots(n, i, y, pen_on, pen_off):
    x = W // 2 - (n - 1) * 7
    for k in range(n):
        if k == i:
            pill(x + k * 14 - 6, y - 3, 13, 7, pen_on)
        else:
            circle(x + k * 14, y, 3, pen_off)
