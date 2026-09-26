"""Desktop stand-in for the pimoroni module (dev only)."""


class RGBLED:
    def __init__(self, r, g, b, invert=True):
        self.rgb = (0, 0, 0)

    def set_rgb(self, r, g, b):
        self.rgb = (int(r), int(g), int(b))
