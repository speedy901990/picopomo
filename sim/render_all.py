"""Render every screen/state to PNG for a desktop design review.

    python sim/render_all.py [out_dir]

Writes one PNG per state (2x zoom) plus contact_sheet.png.
"""
import os
import sys
import tempfile

import sim_env  # noqa: F401  (must come first)
from sim_env import advance, make_app, NOW

from PIL import Image

from machine import Pin
from pomodoro import FOCUS, SHORT
from stats import days_from_key, key_from_days


def seed_stats(app):
    st = app.stats
    today = days_from_key("2026-09-26")
    demo = [3, 6, 0, 8, 5, 9, 4, 7, 2, 8, 10, 5]  # pomodoros per day, oldest first
    for i, p in enumerate(demo):
        key = key_from_days(today - len(demo) + 1 + i)
        for j in range(p):
            st.on_start(key)
            st.on_focus_done(key, 8 + (j * 3 + i) % 11, 25, j % 3 == 0 and 1 or 0, 8)
        st.on_break(key, p * 5)
        if i % 3 == 0:
            st.on_start(key)
            st.on_focus_abandoned(key, 15, 12)
            st.on_pause(key)


def press(app, key, long=False):
    """Simulate a real button press through the Buttons poller."""
    gpio = {"A": 12, "B": 13, "X": 14, "Y": 15}[key]
    Pin.levels[gpio] = 0
    for _ in range(40 if long else 3):
        advance(30)
        for k, kind in app.buttons.poll(NOW[0]):
            app.input(k, kind, NOW[0])
    Pin.levels[gpio] = 1
    advance(30)
    for k, kind in app.buttons.poll(NOW[0]):
        app.input(k, kind, NOW[0])
    app.update(0, NOW[0])


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(sim_env.ROOT, "sim", "out")
    out = os.path.abspath(out)
    os.makedirs(out, exist_ok=True)
    shots = []

    def shot(app, name):
        app.update(0, NOW[0])
        app.draw(NOW[0])
        path = os.path.join(out, name + ".png")
        app.d.save(path)
        shots.append(path)

    for theme in (0, 1):
        tag = "" if theme == 0 else "light_"
        app = make_app(tempfile.mkdtemp(prefix="pomo_sim_"), theme)
        seed_stats(app)
        # stable "today" state: 5 done, cycle 1
        app.timer.cycle = 1

        shot(app, tag + "01_timer_idle")
        press(app, "A")
        advance(7 * 60 * 1000 + 13000)
        app.update(7 * 60 * 1000 + 13000, NOW[0])
        shot(app, tag + "02_timer_running")
        press(app, "A")
        NOW[0] = (NOW[0] // 1200) * 1200  # land on the visible half of the blink
        shot(app, tag + "03_timer_paused")
        press(app, "A")
        # finish the focus phase -> complete card
        rem = app.timer.remaining_ms()
        advance(rem)
        app.update(rem, NOW[0])
        advance(2000)
        shot(app, tag + "04_complete_focus")
        press(app, "B")
        shot(app, tag + "05_timer_break_idle")

        press(app, "X")
        shot(app, tag + "06_stats_today")
        press(app, "Y")
        shot(app, tag + "07_stats_week")
        press(app, "Y")
        shot(app, tag + "08_stats_alltime")
        press(app, "X")
        shot(app, tag + "09_settings")
        press(app, "Y")
        press(app, "A")
        press(app, "X")
        shot(app, tag + "10_settings_edit")
        press(app, "B")
        for _ in range(8):
            press(app, "Y")
        shot(app, tag + "11_settings_reset_row")
        press(app, "B")

        # break finished card
        app.timer.phase = SHORT
        app.timer.state = 0
        press(app, "A")
        rem = app.timer.remaining_ms()
        advance(rem)
        app.update(rem, NOW[0])
        advance(2000)
        shot(app, tag + "12_complete_break")
        press(app, "B")
        assert app.timer.phase == FOCUS

        # hold-to-skip in progress
        press(app, "A")
        Pin.levels[15] = 0
        for _ in range(12):
            advance(30)
            for k, kind in app.buttons.poll(NOW[0]):
                app.input(k, kind, NOW[0])
        shot(app, tag + "13_timer_hold_skip")
        Pin.levels[15] = 1
        advance(30)
        for k, kind in app.buttons.poll(NOW[0]):
            app.input(k, kind, NOW[0])
        press(app, "A")
        press(app, "Y")
        shot(app, tag + "14_toast")

    # contact sheet
    ims = [Image.open(p) for p in shots]
    w, h = ims[0].size
    cols = 4
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (w + 16) + 16, rows * (h + 16) + 16), (90, 90, 100))
    for i, im in enumerate(ims):
        sheet.paste(im, (16 + (i % cols) * (w + 16), 16 + (i // cols) * (h + 16)))
    sheet.save(os.path.join(out, "contact_sheet.png"))
    print("wrote %d screens to %s" % (len(shots), out))


if __name__ == "__main__":
    main()
