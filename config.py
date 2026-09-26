# --- WiFi / time -----------------------------------------------------------
# WiFi is used only to sync the clock over NTP, then switched off again.
# Leave WIFI_SSID empty to run fully offline.
WIFI_SSID = "MychatyNet_2.4GHz"
WIFI_PASSWORD = "prayhvk1"

# Offset from UTC in minutes, e.g. 60 = UTC+1, -300 = UTC-5.
# Fixed offset: daylight saving time is not applied automatically.
TZ_OFFSET_MIN = 120

NTP_HOST = "pool.ntp.org"

# --- Defaults (first boot only; afterwards settings.json wins) --------------
DEFAULT_SETTINGS = {
    "focus": 25,        # minutes
    "short": 5,         # minutes
    "long": 15,         # minutes
    "long_every": 4,    # focus sessions per long break
    "goal": 8,          # pomodoros per day
    "auto": 0,          # auto-start next phase
    "bright": 70,       # backlight percent
    "led": 1,           # RGB LED on/off
    "theme": 0,         # 0 = dark, 1 = light
}

# Backlight dims after this many seconds without a button press.
# Set to 0 to disable dimming entirely (screen stays lit always).
DIM_AFTER_S = 0
DIM_LEVEL = 0.15
