import gfx
from screens.base import Screen

TITLES = ("TODAY", "THIS WEEK", "ALL TIME")
DAY_INITIALS = "MTWTFSS"

X0, X1 = 66, 254          # content column, clear of the edge tabs


def _tiles(items, y, h):
    """Row of 3 tiles: items = [(label, value, value_pen)]."""
    T = gfx.T
    w = (X1 - X0 - 8) // 3
    for i, (label, value, pen) in enumerate(items):
        x = X0 + i * (w + 4)
        gfx.rrect(x, y, w, h, 8, T.surface)
        cx = x + w // 2
        gfx.text_c(label, cx, y + 5, 2, T.subtext)
        scale = 3 if gfx.width(value, 3) <= w - 6 else 2
        gfx.text_c(value, cx, y + h - 5 - 7 * scale, scale, pen)


def _mins(m):
    return "%dm" % m if m < 100 else "%dh" % ((m + 30) // 60)


class StatsScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.page = 0

    def enter(self):
        self.page = 0

    def on_button(self, key, kind, now):
        app = self.app
        if kind != "press":
            return
        if key == "A":
            app.timer_event(app.timer.toggle(), now)
        elif key == "B":
            app.go(app.timer_screen)
        elif key == "X":
            app.go(app.settings_screen)
        elif key == "Y":
            self.page = (self.page + 1) % 3

    def draw(self, now):
        app, T = self.app, self.app.T
        gfx.d.set_pen(T.bg)
        gfx.d.clear()
        app.draw_header(TITLES[self.page])
        key = app.date_key()
        (self._today, self._week, self._overview)[self.page](key)

        t = app.timer
        ph = T.phases[t.phase]
        gfx.tab("A", ("START", "PAUSE", "RESUME")[t.state], ph.base, T.ink)
        gfx.tab("B", "BACK", T.tab_bg, T.text)
        gfx.tab("X", "SETUP", T.tab_bg, T.text)
        gfx.tab("Y", "NEXT", T.tab_bg, T.text)
        gfx.page_dots(3, self.page, 233, T.info, T.surface2)

    # --- page 1: today --------------------------------------------------
    def _today(self, key):
        app, T = self.app, self.app.T
        s = app.stats.today(key)
        goal = app.settings["goal"]

        num = str(s["fm"])
        nw = gfx.dm_width(num, 5)
        uw = gfx.width("min", 2)
        x = 160 - (nw + 6 + uw) // 2
        gfx.dm_text(num, x, 34, 5, 4, T.focus)
        gfx.text("min", x + nw + 6, 34 + 35 - 14, 2, T.subtext)

        # goal segments
        n = goal
        gap = 3 if n > 10 else 4
        seg = (X1 - X0 - (n - 1) * gap) // n
        sx = 160 - (n * seg + (n - 1) * gap) // 2
        for i in range(n):
            pen = T.focus if i < s["p"] else T.surface2
            gfx.pill(sx + i * (seg + gap), 80, seg, 9, pen)
        if s["p"] >= goal:
            label = "GOAL MET! %d DONE" % s["p"]
            pen = T.goal
        else:
            label = "%d OF %d POMODOROS" % (s["p"], goal)
            pen = T.subtext
        gfx.text_c(label, 160, 94, 2, pen)

        _tiles((("DONE", str(s["p"]), T.focus),
                ("RATE", "%d%%" % s["rate"], T.short),
                ("PAUSE", str(s["pz"]), T.pink)), 112, 48)
        _tiles((("BEST", _mins(s["lf"]), T.info),
                ("BREAK", _mins(s["bm"]), T.long),
                ("QUIT", str(s["ab"]), T.subtext)), 164, 48)

    # --- page 2: week ---------------------------------------------------
    def _week(self, key):
        app, T = self.app, self.app.T
        week = app.stats.week(key)
        goal_min = app.settings["goal"] * app.settings["focus"]
        top, base = 52, 148
        max_h = base - top
        vmax = max(goal_min, max(fm for _, fm, _ in week), 1)
        bw, gap = 18, 8
        x0 = 160 - (7 * bw + 6 * gap) // 2
        for i, (wd, fm, _) in enumerate(week):
            x = x0 + i * (bw + gap)
            today = i == 6
            if fm > 0:
                h = max(bw // 2 + 1, fm * max_h // vmax)
                gfx.rrect(x, base - h, bw, h, 8, T.focus if today else T.info)
                gfx.rect(x, base - 4, bw, 4, T.focus if today else T.info)
                if today or fm == max(f for _, f, _ in week):
                    gfx.text_c(str(fm), x + bw // 2, base - h - 16, 2,
                               T.text if today else T.subtext)
            else:
                gfx.rect(x, base - 3, bw, 3, T.surface2)
            gfx.text_c(DAY_INITIALS[wd], x + bw // 2, base + 6, 2,
                       T.text if today else T.subtext)
        # dashed goal line
        gy = base - goal_min * max_h // vmax
        for x in range(x0 - 4, x0 + 7 * bw + 6 * gap + 4, 8):
            gfx.rect(x, gy, 4, 2, T.goal)

        total = sum(fm for _, fm, _ in week)
        active = len([1 for _, fm, _ in week if fm > 0])
        avg = total // active if active else 0
        best = max(fm for _, fm, _ in week)
        _tiles((("AVG", _mins(avg), T.info),
                ("BEST", _mins(best), T.focus),
                ("TOTAL", _mins(total), T.short)), 172, 48)

    # --- page 3: all time -----------------------------------------------
    def _overview(self, key):
        app, T = self.app, self.app.T
        st = app.stats
        fm = st.all["fm"]
        streak = st.streak(key, app.settings["goal"])
        _tiles((("TOTAL", str(st.all["p"]), T.focus),
                ("HOURS", "%d.%d" % (fm // 60, (fm % 60) // 6), T.short),
                ("STREAK", str(streak), T.goal)), 60, 48)
        gfx.text_c("BEST STREAK %d DAYS" % st.best(), 160, 114, 2, T.subtext)

        gfx.text_c("FOCUS BY HOUR", 160, 134, 2, T.text)
        h = st.all["h"]
        hmax = max(h)
        cell, gap = 13, 2
        gx = 160 - (12 * cell + 11 * gap) // 2 + 10
        for row in range(2):
            y = 152 + row * (cell + 4)
            gfx.text("AM" if row == 0 else "PM", gx - 26, y, 2, T.subtext)
            for c in range(12):
                v = h[row * 12 + c]
                lvl = 0 if v == 0 or hmax == 0 else min(3, 1 + 3 * v // (hmax + 1))
                gfx.rrect(gx + c * (cell + gap), y, cell, cell, 3, T.heat[lvl])
        for c, lbl in ((0, "12"), (3, "3"), (6, "6"), (9, "9")):
            gfx.text(lbl, gx + c * (cell + gap) + 2, 186, 1, T.subtext)

        peak = st.peak_hour()
        if peak < 0:
            msg, pen = "No focus data yet", T.subtext
        else:
            msg, pen = "PEAK %02d:00-%02d:00" % (peak, (peak + 1) % 24), T.focus
        gfx.text_c(msg, 160, 198, 2, pen)
