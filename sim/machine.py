"""Desktop stand-in for MicroPython's machine module (dev only)."""


class Pin:
    IN = 0
    OUT = 1
    PULL_UP = 1

    # Tests set Pin.levels[gpio] = 0 to "press" a button (active low).
    levels = {}

    def __init__(self, n, mode=None, pull=None):
        self.n = n

    def value(self):
        return Pin.levels.get(self.n, 1)
