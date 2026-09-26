"""Logic tests, run on desktop CPython:  python -m unittest discover sim/tests"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sim_env  # noqa: E402,F401
from sim_env import NOW, advance, make_app, FakeClock  # noqa: E402

import store  # noqa: E402
from pomodoro import Pomodoro, FOCUS, SHORT, LONG, IDLE, RUNNING, PAUSED  # noqa: E402
from stats import (Stats, days_from_civil, civil_from_days, key_from_days,  # noqa: E402
                   days_from_key, weekday, KEEP_DAYS)

SETTINGS = {"focus": 25, "short": 5, "long": 15, "long_every": 4, "goal": 3}
MIN = 60000


class PomodoroTest(unittest.TestCase):
    def test_full_cycle_cadence(self):
        p = Pomodoro(dict(SETTINGS))
        seen = []
        for _ in range(8):
            self.assertEqual(p.start()[0], "started")
            ev = p.tick(p.duration_ms())
            self.assertEqual(ev[0], "done")
            seen.append(ev[1])
        self.assertEqual(seen, [FOCUS, SHORT, FOCUS, SHORT, FOCUS, SHORT, FOCUS, LONG])
        self.assertEqual(p.phase, FOCUS)
        self.assertEqual(p.cycle, 0)

    def test_pause_resume_and_timing(self):
        p = Pomodoro(dict(SETTINGS))
        p.start()
        p.tick(10 * MIN)
        self.assertEqual(p.pause()[0], "paused")
        self.assertIsNone(p.tick(60 * MIN))       # paused: time frozen
        self.assertEqual(p.remaining_str(), "15:00")
        self.assertEqual(p.start()[0], "resumed")
        self.assertEqual(p.state, RUNNING)
        ev = p.tick(15 * MIN)
        self.assertEqual(ev, ("done", FOCUS, 25, 1))

    def test_reset_reports_abandoned_minutes(self):
        p = Pomodoro(dict(SETTINGS))
        p.start()
        p.tick(7 * MIN + 500)
        self.assertEqual(p.reset_phase(), ("abandoned", FOCUS, 7))
        self.assertEqual((p.state, p.elapsed, p.phase), (IDLE, 0, FOCUS))
        self.assertIsNone(p.reset_phase())

    def test_skip_does_not_count_focus(self):
        p = Pomodoro(dict(SETTINGS))
        p.skip()
        self.assertEqual((p.phase, p.cycle), (SHORT, 0))
        p.skip()
        self.assertEqual(p.phase, FOCUS)

    def test_remaining_rounds_up(self):
        p = Pomodoro(dict(SETTINGS))
        p.start()
        p.tick(1)
        self.assertEqual(p.remaining_str(), "25:00")
        p.tick(999)
        self.assertEqual(p.remaining_str(), "24:59")


class DateTest(unittest.TestCase):
    def test_roundtrip(self):
        for n in range(days_from_civil(2023, 12, 25), days_from_civil(2029, 3, 5)):
            self.assertEqual(days_from_civil(*civil_from_days(n)), n)
        self.assertEqual(key_from_days(days_from_civil(2028, 2, 29)), "2028-02-29")

    def test_weekday(self):
        self.assertEqual(weekday(days_from_key("2026-09-26")), 5)  # Saturday
        self.assertEqual(weekday(days_from_key("1970-01-01")), 3)  # Thursday


class StatsTest(unittest.TestCase):
    def fill(self, st, key, n, goal=3):
        for _ in range(n):
            st.on_start(key)
            st.on_focus_done(key, 10, 25, 0, goal)

    def test_today_and_rate(self):
        st = Stats()
        self.fill(st, "2026-09-26", 3)
        st.on_start("2026-09-26")
        st.on_focus_abandoned("2026-09-26", 11, 10)
        t = st.today("2026-09-26")
        self.assertEqual((t["p"], t["fm"], t["st"], t["ab"], t["rate"]), (3, 85, 4, 1, 75))
        self.assertEqual(st.all["h"][10], 75)
        self.assertEqual(st.all["h"][11], 10)
        self.assertEqual(st.peak_hour(), 10)

    def test_week_window(self):
        st = Stats()
        self.fill(st, "2026-09-20", 1)   # 6 days ago -> first slot
        self.fill(st, "2026-09-19", 5)   # 7 days ago -> outside
        self.fill(st, "2026-09-26", 2)
        w = st.week("2026-09-26")
        self.assertEqual(len(w), 7)
        self.assertEqual(w[0], (6, 25, 1))   # Sunday
        self.assertEqual(w[6], (5, 50, 2))   # Saturday

    def test_streak_and_best(self):
        st = Stats()
        for k in ("2026-09-22", "2026-09-23", "2026-09-24", "2026-09-25"):
            self.fill(st, k, 3)
        self.fill(st, "2026-09-26", 1)       # today in progress
        self.assertEqual(st.streak("2026-09-26", 3), 4)
        self.fill(st, "2026-09-26", 2)       # goal met today
        self.assertEqual(st.streak("2026-09-26", 3), 5)
        self.assertEqual(st.best(), 5)
        self.assertEqual(st.streak("2026-09-28", 3), 0)  # a gap breaks it
        self.assertEqual(st.best(), 5)

    def test_midnight_rollover_and_prune(self):
        st = Stats()
        self.fill(st, "2026-06-01", 2)
        self.fill(st, "2026-09-26", 1)
        self.fill(st, "2026-09-27", 1)
        self.assertNotIn("2026-06-01", st.days)       # older than KEEP_DAYS
        self.assertEqual(st.today("2026-09-27")["p"], 1)
        self.assertEqual(st.all["p"], 4)             # all-time survives pruning
        self.assertEqual(st.data["last"], "2026-09-27")
        self.assertTrue(KEEP_DAYS <= 60)

    def test_store_roundtrip(self):
        os.chdir(tempfile.mkdtemp())
        st = Stats()
        self.fill(st, "2026-09-26", 2)
        store.save(store.STATS_FILE, st.data)
        store.save(store.STATS_FILE, st.data)   # overwrite existing
        st2 = Stats(store.load(store.STATS_FILE))
        self.assertEqual(st2.today("2026-09-26")["p"], 2)
        self.assertFalse(os.path.exists(store.STATS_FILE + ".tmp"))
        with open(store.SETTINGS_FILE, "w") as f:
            f.write("{broken")
        self.assertEqual(store.load_settings({"focus": 25})["focus"], 25)


class AppFlowTest(unittest.TestCase):
    def test_focus_completion_records_stats_and_shows_card(self):
        app = make_app(tempfile.mkdtemp())
        app.settings["focus"] = 1
        app.input("A", "press", NOW[0])
        self.assertEqual(app.timer.state, RUNNING)
        app.go(app.settings_screen)                  # phase ends off the timer screen
        app.input("A", "press", NOW[0])              # start editing a row
        self.assertTrue(app.settings_screen.editing)
        advance(MIN)
        app.update(MIN, NOW[0])
        self.assertIsNotNone(app.overlay)
        self.assertFalse(app.settings_screen.editing)   # edit was cancelled
        self.assertEqual(app.stats.today("2026-09-26")["p"], 1)
        self.assertTrue(os.path.exists(store.STATS_FILE))
        app.input("A", "press", NOW[0])              # start the break
        self.assertIsNone(app.overlay)
        self.assertIs(app.screen, app.timer_screen)
        self.assertEqual((app.timer.phase, app.timer.state), (SHORT, RUNNING))

    def test_wake_press_is_swallowed(self):
        app = make_app(tempfile.mkdtemp())
        advance(120000)
        app.update(0, NOW[0])
        self.assertTrue(app.dimmed)
        for kind in ("down", "press", "up"):
            app.input("A", kind, NOW[0])
        self.assertFalse(app.dimmed)
        self.assertEqual(app.timer.state, IDLE)       # did not start

    def test_wake_hold_cannot_reset_stats(self):
        app = make_app(tempfile.mkdtemp())
        app.stats.on_start("2026-09-26")
        app.stats.on_focus_done("2026-09-26", 10, 25, 0, 8)
        app.go(app.settings_screen)
        for _ in range(9):
            app.input("Y", "press", NOW[0])
        self.assertEqual(app.settings_screen._row()[5], "reset")
        advance(120000)
        app.update(0, NOW[0])
        self.assertTrue(app.dimmed)
        from machine import Pin
        Pin.levels[12] = 0                      # hold A to wake
        for _ in range(100):                    # 3 s
            advance(30)
            for k, kind in app.buttons.poll(NOW[0]):
                app.input(k, kind, NOW[0])
            app.update(30, NOW[0])
        Pin.levels[12] = 1
        self.assertEqual(app.stats.all["p"], 1)

    def test_unsynced_clock_uses_last_date(self):
        app = make_app(tempfile.mkdtemp(), clock=FakeClock(t=(2021, 1, 1, 0, 0, 0, 4, 1)))
        app.stats.data["last"] = "2026-09-20"
        self.assertEqual(app.date_key(), "2026-09-20")
        self.assertEqual(app.clock_str(), "--:--")

    def test_pen_budget(self):
        app = make_app(tempfile.mkdtemp())
        n = len(app.d.palette)
        app.T.apply(1)
        app.T.apply(0)
        self.assertEqual(len(app.d.palette), n)       # theme switch reuses slots
        self.assertLess(n, 64)


if __name__ == "__main__":
    unittest.main()
