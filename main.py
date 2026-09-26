# Pastel Pomodoro for Raspberry Pi Pico W + Pimoroni Pico Display 2.0
import gc
import time

import hw

# Framebuffer first, while the heap is still one big contiguous block.
display = hw.init_display()
gc.collect()

import gfx
from app import App
from clock import Clock


def draw_splash(app, now, status):
    T = app.T
    display.set_pen(T.bg)
    display.clear()
    gfx.tomato(160, 84, 30)
    gfx.text_c("POMODORO", 160, 132, 4, T.text)
    gfx.text_c(status, 160, 176, 2, T.subtext)
    n = (now // 300) % 4
    for i in range(3):
        gfx.circle(148 + i * 12, 204, 3, T.focus if i < n else T.surface2)
    display.update()


def splash(app, buttons, clock):
    """Show the splash while WiFi connects and NTP syncs (10 s max).
    Any button skips; syncing then continues in the background."""
    now = time.ticks_ms()
    clock.begin(now)
    if not clock.connecting:
        draw_splash(app, now, "offline mode")
        time.sleep_ms(700)
        return
    while clock.connecting:
        now = time.ticks_ms()
        if [e for e in buttons.poll(now) if e[1] == "press"]:
            break
        draw_splash(app, now, "syncing time")
        clock.poll(now, False)
        time.sleep_ms(40)
    if clock.synced:
        draw_splash(app, time.ticks_ms(), "time synced")
        time.sleep_ms(400)


def show_error(e):
    try:
        display.set_pen(display.create_pen(60, 20, 30))
        display.clear()
        display.set_pen(display.create_pen(255, 220, 220))
        display.text("Error:", 8, 8, scale=2)
        display.text(repr(e), 8, 32, wordwrap=300, scale=2)
        display.update()
    except Exception:
        pass


def run():
    buttons = hw.Buttons()
    led = hw.Led()
    clock = Clock()
    app = App(display, buttons, led, clock, time.ticks_ms())
    gc.collect()
    splash(app, buttons, clock)

    last = time.ticks_ms()
    gc_at = last
    while True:
        now = time.ticks_ms()
        dt = time.ticks_diff(now, last)
        last = now
        for key, kind in buttons.poll(now):
            app.input(key, kind, now)
        app.update(dt, now)
        if app.dirty:
            app.draw(now)
            display.update()
        if time.ticks_diff(now, gc_at) > 5000:
            gc_at = now
            gc.collect()
        time.sleep_ms(10)


try:
    run()
except KeyboardInterrupt:
    pass
except Exception as e:
    import sys
    sys.print_exception(e)
    show_error(e)
    raise
