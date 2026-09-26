import gfx
from screens.base import Screen
from theme import THEME_NAMES

# (label, settings key, min, max, step, kind)
ROWS = (
    ("Focus", "focus", 5, 90, 5, "min"),
    ("Short break", "short", 1, 15, 1, "min"),
    ("Long break", "long", 5, 30, 5, "min"),
    ("Long every", "long_every", 2, 6, 1, "num"),
    ("Daily goal", "goal", 1, 16, 1, "num"),
    ("Auto-start", "auto", 0, 1, 1, "onoff"),
    ("Brightness", "bright", 20, 100, 10, "pct"),
    ("LED", "led", 0, 1, 1, "onoff"),
    ("Theme", "theme", 0, 1, 1, "theme"),
    ("Reset stats", None, 0, 0, 0, "reset"),
)
VISIBLE = 7
ROW_H = 24
LIST_Y = 34
LX, LW = 62, 196
RESET_HOLD_MS = 2000


def _fmt(kind, v):
    if kind == "min":
        return "%d min" % v
    if kind == "pct":
        return "%d%%" % v
    if kind == "onoff":
        return "On" if v else "Off"
    if kind == "theme":
        return THEME_NAMES[v]
    if kind == "reset":
        return "hold A"
    return str(v)


class SettingsScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.sel = 0
        self.top = 0
        self.editing = False
        self.orig = None
        self.snapshot = None
        self.reset_armed = True

    def enter(self):
        self.sel = 0
        self.top = 0
        self.editing = False
        self.snapshot = dict(self.app.settings)

    def leave(self):
        self.interrupt()
        if self.app.settings != self.snapshot:
            self.app.save_settings()

    def interrupt(self):
        if self.editing:
            self._set(self.orig)
            self.editing = False

    # --- helpers --------------------------------------------------------
    def _row(self):
        return ROWS[self.sel]

    def _set(self, v):
        key = self._row()[1]
        self.app.settings[key] = v
        if key == "theme":
            self.app.T.apply(v)
        elif key == "bright":
            self.app.apply_backlight()

    def _move(self, delta):
        self.sel = (self.sel + delta) % len(ROWS)
        if self.sel < self.top:
            self.top = self.sel
        elif self.sel >= self.top + VISIBLE:
            self.top = self.sel - VISIBLE + 1

    # --- input ----------------------------------------------------------
    def on_button(self, key, kind, now):
        app = self.app
        label, skey, lo, hi, step, rkind = self._row()
        if key == "A" and kind == "up":
            self.reset_armed = True
        if kind != "press":
            return
        if self.editing:
            v = app.settings[skey]
            if key == "X":
                self._set(lo if v + step > hi and rkind in ("onoff", "theme") else min(hi, v + step))
            elif key == "Y":
                self._set(hi if v - step < lo and rkind in ("onoff", "theme") else max(lo, v - step))
            elif key == "A":
                self.editing = False
            elif key == "B":
                self.interrupt()
            return
        if key == "A":
            if rkind == "reset":
                app.toast("Hold A to clear", now)
            else:
                self.editing = True
                self.orig = app.settings[skey]
        elif key == "B":
            app.go(app.timer_screen)
        elif key == "X":
            self._move(-1)
        elif key == "Y":
            self._move(1)

    def update(self, now):
        if self._row()[5] == "reset" and not self.editing and self.reset_armed:
            if self.app.held_ms("A", now) >= RESET_HOLD_MS:
                self.reset_armed = False
                self.app.stats.reset()
                self.app.save_stats()
                self.app.toast("Stats cleared", now)

    def animating(self, now):
        return self._row()[5] == "reset"

    # --- drawing --------------------------------------------------------
    def draw(self, now):
        app, T = self.app, self.app.T
        gfx.d.set_pen(T.bg)
        gfx.d.clear()
        app.draw_header("SETTINGS")

        for i in range(self.top, min(len(ROWS), self.top + VISIBLE)):
            label, skey, lo, hi, step, kind = ROWS[i]
            y = LIST_Y + (i - self.top) * ROW_H
            selected = i == self.sel
            value = _fmt(kind, app.settings[skey] if skey else 0)
            frac = 0
            if selected:
                gfx.rrect(LX, y, LW, 22, 10, T.surface)
                if kind == "reset" and self.reset_armed:
                    frac = app.held_ms("A", now) / RESET_HOLD_MS
                    if frac > 0:
                        gfx.rrect(LX, y, max(21, int(LW * min(1, frac))), 22, 10, T.focus)
            lpen = T.text if selected else T.subtext
            if kind == "reset":
                lpen = T.ink if frac > 0 else (T.focus if selected else T.subtext)
            gfx.text(label, LX + 10, y + 4, 2, lpen)
            vw = gfx.width(value, 2)
            if selected and self.editing:
                gfx.rrect(LX + LW - vw - 24, y, vw + 24, 22, 10, T.info)
                gfx.text(value, LX + LW - vw - 12, y + 4, 2, T.ink)
            else:
                gfx.text(value, LX + LW - vw - 10, y + 4, 2,
                         T.ink if frac > 0 else (T.info if selected else T.text_dim))

        # scrollbar
        track_y, track_h = LIST_Y + 2, VISIBLE * ROW_H - 6
        gfx.pill(LX + LW + 5, track_y, 3, track_h, T.surface)
        th = track_h * VISIBLE // len(ROWS)
        ty = track_y + (track_h - th) * self.top // (len(ROWS) - VISIBLE)
        gfx.pill(LX + LW + 5, ty, 3, th, T.subtext)

        if self.editing:
            gfx.tab("A", "OK", T.info, T.ink)
            gfx.tab("B", "CANCEL", T.tab_bg, T.text)
            gfx.tab("X", "+", T.tab_bg, T.text)
            gfx.tab("Y", "-", T.tab_bg, T.text)
        else:
            if self._row()[5] == "reset":
                gfx.tab("A", "HOLD", T.focus, T.ink)
            else:
                gfx.tab("A", "EDIT", T.info, T.ink)
            gfx.tab("B", "BACK", T.tab_bg, T.text)
            gfx.tab("X", "UP", T.tab_bg, T.text)
            gfx.tab("Y", "DOWN", T.tab_bg, T.text)
