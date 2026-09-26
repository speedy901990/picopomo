# App controller: owns state, routes button events, decides when to redraw,
# drives the backlight and LED.
import math
import time

import config
import gfx
import store
from pomodoro import Pomodoro, FOCUS, RUNNING
from stats import Stats, WEEKDAYS, MONTHS, days_from_civil, weekday
from theme import Theme, LED_RGB

FRAME_MS = 80          # animation frame interval
TOAST_MS = 1500


class App:
    def __init__(self, display, buttons, led, clock, now):
        self.d = display
        self.buttons = buttons
        self.led = led
        self.clock = clock
        self.settings = store.load_settings(config.DEFAULT_SETTINGS)
        self.T = Theme(display)
        self.T.apply(self.settings["theme"])
        gfx.init(display, self.T)
        self.stats = Stats(store.load(store.STATS_FILE))
        self.timer = Pomodoro(self.settings)

        from screens.timer_screen import TimerScreen
        from screens.stats_screen import StatsScreen
        from screens.settings_screen import SettingsScreen
        self.timer_screen = TimerScreen(self)
        self.stats_screen = StatsScreen(self)
        self.settings_screen = SettingsScreen(self)
        self.screen = self.timer_screen
        self.overlay = None

        self.dirty = True
        self.toast_msg = None
        self.toast_until = 0
        self.last_input = now
        self.dimmed = False
        self.swallow = []
        self.last_sec = -1
        self.last_min = -1
        self.next_frame = now
        self.backlight = None
        self.apply_backlight()

    # --- time helpers -------------------------------------------------------
    def date_key(self):
        if self.clock.valid():
            t = self.clock.local()
            return "%04d-%02d-%02d" % (t[0], t[1], t[2])
        return self.stats.data.get("last") or "2000-01-01"

    def hour(self):
        return self.clock.local()[3] if self.clock.valid() else 12

    def clock_str(self):
        if not self.clock.valid():
            return "--:--"
        t = self.clock.local()
        return "%02d:%02d" % (t[3], t[4])

    def date_str(self):
        if not self.clock.valid():
            return "POMODORO"
        t = self.clock.local()
        wd = weekday(days_from_civil(t[0], t[1], t[2]))
        return "%s %d %s" % (WEEKDAYS[wd], t[2], MONTHS[t[1] - 1])

    def clock_after(self, ms):
        """HH:MM that is `ms` from now, or None without a valid clock."""
        if not self.clock.valid():
            return None
        t = self.clock.local()
        m = (t[3] * 60 + t[4] + (t[5] + ms // 1000 + 59) // 60) % 1440
        return "%02d:%02d" % (m // 60, m % 60)

    # --- shared drawing -----------------------------------------------------
    def draw_header(self, title):
        T = self.T
        if self.clock.connecting:
            sync = T.goal
        elif self.clock.synced:
            sync = T.short
        else:
            sync = T.surface2
        today = self.stats.today(self.date_key())["p"]
        gfx.header(title, self.clock_str(), sync, today, self.settings["goal"])

    def held_ms(self, key, now):
        # A press that only woke the screen must not count as a hold.
        if key in self.swallow:
            return 0
        return self.buttons.held_ms(key, now)

    def hold(self, key, now, ms=700):
        return min(1.0, self.held_ms(key, now) / ms)

    # --- navigation ---------------------------------------------------------
    def go(self, screen):
        if screen is not self.screen:
            self.screen.leave()
            self.screen = screen
            screen.enter()
        self.dirty = True

    def toast(self, msg, now):
        self.toast_msg = msg
        self.toast_until = time.ticks_add(now, TOAST_MS)
        self.dirty = True

    def close_overlay(self):
        self.overlay = None
        self.go(self.timer_screen)

    # --- timer events -------------------------------------------------------
    def timer_event(self, ev, now):
        if not ev:
            return
        kind, phase = ev[0], ev[1]
        key = self.date_key()
        if kind == "started" and phase == FOCUS:
            self.stats.on_start(key)
        elif kind == "paused" and phase == FOCUS:
            self.stats.on_pause(key)
        elif kind == "done":
            minutes, pauses = ev[2], ev[3]
            if phase == FOCUS:
                self.stats.on_focus_done(key, self.hour(), minutes, pauses, self.settings["goal"])
            else:
                self.stats.on_break(key, minutes)
            self.save_stats()
            from screens.complete_screen import CompleteScreen
            self.screen.interrupt()
            self.overlay = CompleteScreen(self, phase, now)
            self.wake(now)
        elif kind == "abandoned":
            minutes = ev[2]
            if phase == FOCUS:
                self.stats.on_focus_abandoned(key, self.hour(), minutes)
            else:
                self.stats.on_break(key, minutes)
            self.save_stats()
        self.dirty = True

    def save_stats(self):
        store.save(store.STATS_FILE, self.stats.data)

    def save_settings(self):
        store.save(store.SETTINGS_FILE, self.settings)

    # --- backlight / LED ----------------------------------------------------
    def apply_backlight(self, level=None):
        if level is None:
            level = config.DIM_LEVEL if self.dimmed else self.settings["bright"] / 100
        if level != self.backlight:
            self.d.set_backlight(level)
            self.backlight = level

    def wake(self, now):
        self.last_input = now
        if self.dimmed:
            self.dimmed = False
            self.apply_backlight()
            self.dirty = True

    def update_led(self, now):
        if not self.settings["led"]:
            self.led.off()
            return
        ov = self.overlay
        if ov is not None and hasattr(ov, "finished") and time.ticks_diff(now, ov.t0) < 30000:
            age = time.ticks_diff(now, ov.t0)
            color = LED_RGB[ov.finished]
            if age < 1500:
                # Sharp flash right on completion, colour keyed to *what finished*
                # (FOCUS -> red, SHORT/LONG break -> green/purple) so focus-done
                # and break-done are never confused at a glance.
                level = 0.05 + 0.35 * abs(math.cos(math.pi * age / 500))
            else:
                t = age / 2000
                level = 0.02 + 0.10 * (0.5 - 0.5 * math.cos(2 * math.pi * t))
            self.led.set(color, level)
        elif self.timer.state == RUNNING:
            t = time.ticks_diff(now, 0) / 4000
            level = 0.01 + 0.015 * (0.5 - 0.5 * math.cos(2 * math.pi * t))
            self.led.set(LED_RGB[self.timer.phase], level)
        else:
            self.led.off()

    # --- main loop hooks ----------------------------------------------------
    def input(self, key, kind, now):
        if kind == "down":
            if self.dimmed:
                self.wake(now)
                self.swallow.append(key)   # first press only wakes the screen
                return
            self.last_input = now
        if key in self.swallow:
            if kind == "up":
                self.swallow.remove(key)
            return
        target = self.overlay or self.screen
        target.on_button(key, kind, now)
        self.dirty = True

    def update(self, dt, now):
        self.timer_event(self.timer.tick(dt), now)
        target = self.overlay or self.screen
        if hasattr(target, "update"):
            target.update(now)
        self.clock.poll(now, self.timer.state == RUNNING)

        sec = self.timer.remaining_ms() // 1000
        if sec != self.last_sec:
            self.last_sec = sec
            self.dirty = True
        if self.clock.valid():
            m = self.clock.local()[4]
            if m != self.last_min:
                self.last_min = m
                self.dirty = True
        if self.toast_msg and time.ticks_diff(now, self.toast_until) >= 0:
            self.toast_msg = None
            self.dirty = True
        if (target.animating(now) or self.buttons.any_down()) and \
                time.ticks_diff(now, self.next_frame) >= 0:
            self.next_frame = time.ticks_add(now, FRAME_MS)
            self.dirty = True

        if self.overlay is None and not self.dimmed and config.DIM_AFTER_S > 0 and \
                time.ticks_diff(now, self.last_input) > config.DIM_AFTER_S * 1000:
            self.dimmed = True
            self.apply_backlight()
        if self.overlay is not None and hasattr(self.overlay, "backlight"):
            self.apply_backlight(self.overlay.backlight(now))
        elif not self.dimmed:
            self.apply_backlight()
        self.update_led(now)

    def draw(self, now):
        target = self.overlay or self.screen
        target.draw(now)
        if self.toast_msg:
            gfx.toast(self.toast_msg)
        self.dirty = False
