"""Makes the device code importable on desktop CPython.

Import this first: it puts the stub modules (picographics, pimoroni, machine)
on sys.path and adds MicroPython's ticks functions to `time`, driven by a
fake clock you can advance by hand.
"""
import os
import sys
import time

SIM_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SIM_DIR)
for p in (SIM_DIR, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

NOW = [100000]


def advance(ms):
    NOW[0] += ms


time.ticks_ms = lambda: NOW[0]
time.ticks_diff = lambda a, b: a - b
time.ticks_add = lambda a, b: a + b
time.sleep_ms = lambda ms: advance(ms)


class FakeClock:
    """Pretends NTP worked and it is Saturday 26 Sep 2026, 14:05."""

    def __init__(self, t=(2026, 9, 26, 14, 5, 30, 5, 269), synced=True):
        self.t = t
        self.synced = synced
        self.connecting = False
        self.enabled = True

    def local(self):
        return self.t

    def valid(self):
        return self.t[0] >= 2024

    def begin(self, now):
        pass

    def poll(self, now, busy):
        pass


def make_app(workdir, theme=0, clock=None):
    """Build an App against the stub display, with files under workdir."""
    os.chdir(workdir)
    import hw
    from app import App
    d = hw.init_display()
    app = App(d, hw.Buttons(), hw.Led(), clock or FakeClock(), NOW[0])
    if theme:
        app.settings["theme"] = theme
        app.T.apply(theme)
    return app
