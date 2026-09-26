# Pomodoro state machine. Pure logic: no drawing, no clock access.
# Time only advances through tick(dt_ms), which the main loop feeds from
# time.ticks_ms(), so RTC/NTP changes can never disturb a running timer.

FOCUS, SHORT, LONG = 0, 1, 2
IDLE, RUNNING, PAUSED = 0, 1, 2

PHASE_NAMES = ("FOCUS", "BREAK", "LONG BREAK")
_PHASE_SETTING = ("focus", "short", "long")


class Pomodoro:
    def __init__(self, settings):
        self.s = settings
        self.phase = FOCUS
        self.state = IDLE
        self.cycle = 0          # focus sessions finished in this long-break cycle
        self.elapsed = 0        # ms into the current phase
        self.pauses = 0         # pauses during the current phase

    # --- queries ------------------------------------------------------------
    def duration_ms(self, phase=None):
        p = self.phase if phase is None else phase
        return self.s[_PHASE_SETTING[p]] * 60000

    def remaining_ms(self):
        return max(0, self.duration_ms() - self.elapsed)

    def fraction_left(self):
        dur = self.duration_ms()
        return self.remaining_ms() / dur if dur else 0

    def remaining_str(self):
        secs = (self.remaining_ms() + 999) // 1000
        return "%02d:%02d" % (secs // 60, secs % 60)

    def fresh(self):
        return self.state == IDLE and self.elapsed == 0

    # --- actions (each returns an event tuple or None) ----------------------
    def start(self):
        if self.state == RUNNING:
            return None
        was_fresh = self.elapsed == 0
        self.state = RUNNING
        if was_fresh:
            return ("started", self.phase)
        return ("resumed", self.phase)

    def pause(self):
        if self.state != RUNNING:
            return None
        self.state = PAUSED
        self.pauses += 1
        return ("paused", self.phase)

    def toggle(self):
        return self.pause() if self.state == RUNNING else self.start()

    def tick(self, dt_ms):
        if self.state != RUNNING:
            return None
        self.elapsed += dt_ms
        if self.elapsed >= self.duration_ms():
            done = ("done", self.phase, self.duration_ms() // 60000, self.pauses)
            self._advance(completed=True)
            return done
        return None

    def reset_phase(self):
        """Back to the start of the current phase. Reports partial work."""
        ev = None
        if self.elapsed > 0:
            ev = ("abandoned", self.phase, self.elapsed // 60000)
        self.elapsed = 0
        self.pauses = 0
        self.state = IDLE
        return ev

    def reset_cycle(self):
        ev = self.reset_phase()
        self.phase = FOCUS
        self.cycle = 0
        return ev

    def skip(self):
        ev = None
        if self.elapsed > 0:
            ev = ("abandoned", self.phase, self.elapsed // 60000)
        self._advance(completed=False)
        return ev

    # --- internals ----------------------------------------------------------
    def next_phase(self, completed=True):
        if self.phase == FOCUS:
            cyc = self.cycle + (1 if completed else 0)
            return LONG if cyc >= self.s["long_every"] else SHORT
        return FOCUS

    def _advance(self, completed):
        nxt = self.next_phase(completed)
        if self.phase == FOCUS and completed:
            self.cycle += 1
        if self.phase == LONG:
            self.cycle = 0
        self.phase = nxt
        self.elapsed = 0
        self.pauses = 0
        self.state = IDLE
