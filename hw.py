# Hardware: display, the four buttons and the RGB LED on the Pico Display 2.0.
import time

from machine import Pin

BUTTON_PINS = (("A", 12), ("B", 13), ("X", 14), ("Y", 15))
DEBOUNCE_MS = 25
LONG_MS = 700


def init_display():
    # Allocate the 76.8 KB P8 framebuffer before anything else fragments the heap.
    from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_P8
    return PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_P8, rotate=0)


class Buttons:
    """Polls the buttons and turns them into events:
    ("A", "down")   pressed (fires immediately)
    ("A", "press")  released before LONG_MS (a short press)
    ("A", "long")   held for LONG_MS (fires once, while still held)
    ("A", "up")     released (after either of the above)
    """

    def __init__(self):
        self.keys = [k for k, _ in BUTTON_PINS]
        self.pins = [Pin(p, Pin.IN, Pin.PULL_UP) for _, p in BUTTON_PINS]
        n = len(self.pins)
        self.down = [False] * n
        self.t_down = [0] * n
        self.t_change = [0] * n
        self.long = [False] * n

    def poll(self, now):
        events = []
        for i, pin in enumerate(self.pins):
            k = self.keys[i]
            pressed = pin.value() == 0
            if pressed != self.down[i]:
                if time.ticks_diff(now, self.t_change[i]) < DEBOUNCE_MS:
                    continue
                self.t_change[i] = now
                self.down[i] = pressed
                if pressed:
                    self.t_down[i] = now
                    self.long[i] = False
                    events.append((k, "down"))
                else:
                    if not self.long[i]:
                        events.append((k, "press"))
                    events.append((k, "up"))
            elif pressed and not self.long[i] and time.ticks_diff(now, self.t_down[i]) >= LONG_MS:
                self.long[i] = True
                events.append((k, "long"))
        return events

    def held_ms(self, key, now):
        i = self.keys.index(key)
        return time.ticks_diff(now, self.t_down[i]) if self.down[i] else 0

    def any_down(self):
        return any(self.down)


class Led:
    def __init__(self):
        try:
            from pimoroni import RGBLED
            self.led = RGBLED(6, 7, 8)
        except Exception:
            self.led = None
        self.cur = None

    def set(self, rgb, level):
        level = max(0.0, min(1.0, level))
        v = (int(rgb[0] * level), int(rgb[1] * level), int(rgb[2] * level))
        if v != self.cur and self.led:
            self.led.set_rgb(*v)
            self.cur = v

    def off(self):
        self.set((0, 0, 0), 0)
