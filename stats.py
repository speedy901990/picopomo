# Stats model and aggregations. Pure logic, runs on CPython for tests.
#
# Data layout (kept small: the Pico parses it with ~100 KB of free heap):
# {"v": 1, "last": "2026-09-26",
#  "days": {"2026-09-26": {"p":5,"fm":125,"bm":30,"st":6,"ab":1,"pz":3,"lf":25}},
#  "all": {"p": 210, "fm": 5250, "h": [24 ints, focus minutes per hour]},
#  "best": 9}
#   p = pomodoros, fm/bm = focus/break minutes, st = focus sessions started,
#   ab = abandoned, pz = pauses, lf = longest uninterrupted focus (minutes)

KEEP_DAYS = 60
WEEKDAYS = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")


# --- date helpers (days since 1970-01-01, no time module needed) -----------

def days_from_civil(y, m, d):
    if m <= 2:
        y -= 1
    era = (y if y >= 0 else y - 399) // 400
    yoe = y - era * 400
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


def civil_from_days(z):
    z += 719468
    era = (z if z >= 0 else z - 146096) // 146097
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    y = yoe + era * 400
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    d = doy - (153 * mp + 2) // 5 + 1
    m = mp + (3 if mp < 10 else -9)
    return y + (1 if m <= 2 else 0), m, d


def key_from_days(n):
    y, m, d = civil_from_days(n)
    return "%04d-%02d-%02d" % (y, m, d)


def days_from_key(k):
    return days_from_civil(int(k[0:4]), int(k[5:7]), int(k[8:10]))


def weekday(n):
    """0 = Monday."""
    return (n + 3) % 7


def _empty_day():
    return {"p": 0, "fm": 0, "bm": 0, "st": 0, "ab": 0, "pz": 0, "lf": 0}


class Stats:
    def __init__(self, data=None):
        if not data or data.get("v") != 1:
            data = {"v": 1, "last": None, "days": {},
                    "all": {"p": 0, "fm": 0, "h": [0] * 24}, "best": 0}
        self.data = data
        self.days = data["days"]
        self.all = data["all"]

    # --- recording ------------------------------------------------------
    def day(self, key):
        d = self.days.get(key)
        if d is None:
            d = self.days[key] = _empty_day()
            self.data["last"] = key
            self.prune(key)
        return d

    def on_start(self, key):
        self.day(key)["st"] += 1

    def on_pause(self, key):
        self.day(key)["pz"] += 1

    def on_focus_done(self, key, hour, minutes, pauses, goal):
        d = self.day(key)
        d["p"] += 1
        d["fm"] += minutes
        if pauses == 0 and minutes > d["lf"]:
            d["lf"] = minutes
        self.all["p"] += 1
        self.all["fm"] += minutes
        self.all["h"][hour % 24] += minutes
        self.update_best(key, goal)

    def on_focus_abandoned(self, key, hour, minutes):
        d = self.day(key)
        d["ab"] += 1
        d["fm"] += minutes
        self.all["fm"] += minutes
        self.all["h"][hour % 24] += minutes

    def on_break(self, key, minutes):
        if minutes > 0:
            self.day(key)["bm"] += minutes

    def prune(self, today_key):
        cutoff = days_from_key(today_key) - KEEP_DAYS
        for k in list(self.days.keys()):
            if days_from_key(k) < cutoff:
                del self.days[k]

    def reset(self):
        self.__init__(None)

    # --- queries --------------------------------------------------------
    def today(self, key):
        d = self.days.get(key) or _empty_day()
        st = d["st"]
        rate = int(round(100 * d["p"] / st)) if st else 0
        return {"p": d["p"], "fm": d["fm"], "bm": d["bm"], "st": st, "ab": d["ab"],
                "pz": d["pz"], "lf": d["lf"], "rate": min(rate, 100)}

    def week(self, key):
        """Last 7 days ending today: list of (weekday_index, focus_min, poms)."""
        n = days_from_key(key)
        out = []
        for i in range(n - 6, n + 1):
            d = self.days.get(key_from_days(i))
            out.append((weekday(i), d["fm"] if d else 0, d["p"] if d else 0))
        return out

    def streak(self, key, goal):
        """Consecutive days meeting the goal. Today counts once met; while it
        is still in progress the streak carries over from yesterday."""
        n = days_from_key(key)
        d = self.days.get(key)
        if not (d and d["p"] >= goal):
            n -= 1
        run = 0
        while True:
            d = self.days.get(key_from_days(n))
            if not (d and d["p"] >= goal):
                return run
            run += 1
            n -= 1

    def update_best(self, key, goal):
        s = self.streak(key, goal)
        if s > self.data["best"]:
            self.data["best"] = s

    def best(self):
        return self.data["best"]

    def peak_hour(self):
        h = self.all["h"]
        m = max(h)
        return h.index(m) if m > 0 else -1
