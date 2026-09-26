# Pastel palettes and the P8 pen table.
#
# PEN_P8 has 256 palette slots and no alpha, so every colour the UI needs
# (including dimmed and blended variants) is created once here. Switching
# theme rewrites the same slots with update_pen() instead of allocating more.

PALETTES = (
    {   # 0: dark
        "bg": 0x1E1E2E, "surface": 0x2A2A3C, "surface2": 0x3A3A52,
        "text": 0xF5F0FF, "subtext": 0xA6A3C2, "ink": 0x1E1E2E,
        "focus": 0xFFADAD, "short": 0xA8E6CF, "long": 0xCDB4DB,
        "goal": 0xFDFFB6, "info": 0xA0C4FF, "pink": 0xFFC8DD, "leaf": 0x8FD694,
    },
    {   # 1: light
        "bg": 0xFFF8F0, "surface": 0xF2E8DE, "surface2": 0xE4D8CC,
        "text": 0x2B2B3A, "subtext": 0x7D7890, "ink": 0x2B2B3A,
        "focus": 0xF4978E, "short": 0x6CC4A1, "long": 0xB392CF,
        "goal": 0xF2C94C, "info": 0x7FA7E8, "pink": 0xF29CB9, "leaf": 0x5DB075,
    },
)

THEME_NAMES = ("Dark", "Light")
PHASE_KEYS = ("focus", "short", "long")

# The LED needs saturated colours; pastels just look white on it.
LED_RGB = ((255, 40, 24), (24, 255, 80), (150, 40, 255))


def _rgb(h):
    return (h >> 16) & 0xFF, (h >> 8) & 0xFF, h & 0xFF


def blend(a, b, t):
    """Mix colour a towards b by t (0..1)."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class PhasePens:
    pass


class Theme:
    def __init__(self, display):
        self.d = display
        self._pens = None
        self.index = 0

    def _colors(self, pal):
        c = {k: _rgb(v) for k, v in pal.items()}
        out = [(k, c[k]) for k in ("bg", "surface", "surface2", "text", "subtext",
                                   "ink", "goal", "info", "pink", "leaf")]
        out.append(("text_dim", blend(c["text"], c["bg"], 0.55)))
        out.append(("tab_bg", blend(c["surface2"], c["bg"], 0.2)))
        for k in PHASE_KEYS:
            out.append((k, c[k]))
            out.append((k + "_dim", blend(c[k], c["bg"], 0.55)))
            for i, t in enumerate((0.25, 0.5, 0.75)):
                out.append((k + "_f%d" % i, blend(c["bg"], c[k], t)))
        # heatmap: 3 steps from surface to focus colour
        for i, t in enumerate((0.3, 0.6, 1.0)):
            out.append(("heat%d" % i, blend(c["surface2"], c["focus"], t)))
        return out

    def apply(self, index):
        self.index = index
        colors = self._colors(PALETTES[index])
        if self._pens is None:
            self._pens = {}
            for name, rgb in colors:
                self._pens[name] = self.d.create_pen(*rgb)
        else:
            for name, rgb in colors:
                self.d.update_pen(self._pens[name], *rgb)
        for name, pen in self._pens.items():
            setattr(self, name, pen)
        p = self._pens
        self.phases = []
        for k in PHASE_KEYS:
            pp = PhasePens()
            pp.base = p[k]
            pp.dim = p[k + "_dim"]
            pp.fade = (p[k + "_f0"], p[k + "_f1"], p[k + "_f2"], p[k])
            self.phases.append(pp)
        self.heat = (p["surface2"], p["heat0"], p["heat1"], p["heat2"])
