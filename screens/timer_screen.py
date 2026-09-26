import gfx
from pomodoro import PHASE_NAMES, IDLE, RUNNING, PAUSED, FOCUS
from screens.base import Screen

CX, CY = 160, 136
R_OUT, THICK = 96, 12


class TimerScreen(Screen):
    def _needs_hold(self, key):
        t = self.app.timer
        if key == "B":
            return t.state == IDLE
        if key == "Y":
            return t.state != IDLE
        return False

    def on_button(self, key, kind, now):
        app, t = self.app, self.app.timer
        if key == "A" and kind == "press":
            app.timer_event(t.toggle(), now)
        elif key == "X" and kind == "press":
            app.go(app.stats_screen)
        elif key == "B":
            if t.state == IDLE:
                if kind == "long":
                    t.reset_cycle()
                    app.toast("Cycle reset", now)
                elif kind == "press":
                    app.toast("Hold to reset cycle", now)
            elif kind == "press":
                app.timer_event(t.reset_phase(), now)
                app.toast("Reset", now)
        elif key == "Y":
            if t.state == IDLE and kind == "press":
                app.timer_event(t.skip(), now)
                app.toast("Skipped", now)
            elif t.state != IDLE:
                if kind == "long":
                    app.timer_event(t.skip(), now)
                    app.toast("Skipped", now)
                elif kind == "press":
                    app.toast("Hold to skip", now)

    def animating(self, now):
        return self.app.timer.state == PAUSED

    def draw(self, now):
        app, T, t = self.app, self.app.T, self.app.timer
        ph = T.phases[t.phase]
        paused = t.state == PAUSED
        accent = ph.dim if paused else ph.base

        gfx.d.set_pen(T.bg)
        gfx.d.clear()
        app.draw_header(app.date_str())

        gfx.ring(CX, CY, R_OUT, THICK, t.fraction_left(), accent, track=T.surface, bg=T.bg)

        # phase pill
        name = PHASE_NAMES[t.phase]
        w = gfx.width(name, 2) + 22
        gfx.pill(CX - w // 2, CY - 56, w, 21, accent)
        gfx.text_c(name, CX, CY - 52, 2, T.ink)

        # time
        gfx.dm_text_c(t.remaining_str(), CX, CY - 20, 6, 5,
                      T.text_dim if paused else T.text, T.surface)

        # cycle dots: focus sessions done in this long-break cycle
        n = app.settings["long_every"]
        done = min(t.cycle, n)
        x0 = CX - (n - 1) * 8
        for i in range(n):
            if i < done:
                gfx.circle(x0 + i * 16, CY + 36, 4, T.focus)
            else:
                gfx.circle(x0 + i * 16, CY + 36, 4, T.surface2)

        # status line
        if paused:
            if (now // 600) % 2 == 0:
                gfx.text_c("PAUSED", CX, CY + 50, 2, ph.base)
        elif t.state == RUNNING:
            end = app.clock_after(t.remaining_ms())
            if end:
                gfx.text_c("ENDS " + end, CX, CY + 50, 2, T.subtext)
        else:
            gfx.text_c("%d MIN" % (t.duration_ms() // 60000), CX, CY + 50, 2, T.subtext)

        # button tabs
        primary = ("START", "PAUSE", "RESUME")[t.state]
        gfx.tab("A", primary, ph.base, T.ink)
        show_reset = not (t.state == IDLE and t.phase == FOCUS and t.cycle == 0)
        if show_reset:
            gfx.tab("B", "RESET", T.tab_bg, T.text,
                    app.hold("B", now) if self._needs_hold("B") else 0, ph.base)
        gfx.tab("X", "STATS", T.tab_bg, T.text)
        gfx.tab("Y", "SKIP", T.tab_bg, T.text,
                app.hold("Y", now) if self._needs_hold("Y") else 0, ph.base)
