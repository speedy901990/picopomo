import math
import time

import gfx
from pomodoro import FOCUS, LONG
from screens.base import Screen

AUTO_MS = 5000
PULSE_MS = 1500


def _cup(cx, cy, ink, bg):
    gfx.circle(cx + 13, cy + 1, 9, ink)          # handle
    gfx.circle(cx + 13, cy + 1, 4, bg)
    gfx.rrect(cx - 19, cy - 13, 30, 28, 8, ink)  # body
    gfx.rect(cx - 19, cy - 13, 30, 6, ink)
    for i, dx in enumerate((-12, -4, 4)):        # steam
        gfx.pill(cx + dx, cy - 29 + (i % 2) * 3, 4, 11, ink)


class CompleteScreen(Screen):
    """Full-screen card shown when a phase ends. Coloured in the *next*
    phase's colour; A starts it, B goes back to the idle timer."""

    def __init__(self, app, finished, now):
        super().__init__(app)
        self.finished = finished
        self.t0 = now

    def age(self, now):
        return time.ticks_diff(now, self.t0)

    def _start_next(self, now):
        app = self.app
        app.timer_event(app.timer.start(), now)
        app.close_overlay()

    def on_button(self, key, kind, now):
        if kind != "press":
            return
        if key == "A":
            self._start_next(now)
        elif key == "B":
            self.app.close_overlay()

    def update(self, now):
        if self.app.settings["auto"] and self.age(now) >= AUTO_MS:
            self._start_next(now)

    def animating(self, now):
        return self.age(now) < PULSE_MS or bool(self.app.settings["auto"])

    def backlight(self, now):
        base = self.app.settings["bright"] / 100
        a = self.age(now)
        if a < PULSE_MS:
            return base * (0.35 + 0.65 * abs(math.cos(math.pi * a / 500)))
        return base

    def draw(self, now):
        app, T = self.app, self.app.T
        nxt = app.timer.phase
        ph = T.phases[nxt]
        step = min(3, self.age(now) // 70)
        bg = ph.fade[step]
        gfx.d.set_pen(bg)
        gfx.d.clear()
        if step < 3:
            return

        if self.finished == FOCUS:
            gfx.tomato(160, 66, 24, T.focus if nxt != FOCUS else T.ink)
            title = "NICE WORK!"
            mins = app.settings["long" if nxt == LONG else "short"]
            sub = ("Long break: %d min" if nxt == LONG else "Take a %d min break") % mins
        else:
            _cup(160, 70, T.ink, bg)
            title = "BREAK OVER"
            sub = "Ready to focus?"
        gfx.text_c(title, 160, 104, 4, T.ink)
        gfx.text_c(sub, 160, 146, 2, T.ink)

        p = app.stats.today(app.date_key())["p"]
        goal = app.settings["goal"]
        if self.finished == FOCUS and p == goal:
            info = "Daily goal reached!"
        else:
            info = "%d of %d today" % (p, goal)
        gfx.text_c(info, 160, 170, 2, T.ink)

        if app.settings["auto"]:
            left = max(0, (AUTO_MS - self.age(now) + 999) // 1000)
            gfx.text_c("Starting in %d" % left, 160, 214, 2, T.ink)

        gfx.tab("A", "START", T.ink, ph.base)
        gfx.tab("B", "LATER", ph.fade[2], T.ink)
