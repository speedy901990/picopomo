# Wall clock: NTP sync over WiFi plus local-time helpers.
#
# Syncing never blocks the UI: connect() is started, then poll() checks the
# link once per main-loop pass. The short blocking NTP request only happens
# while the timer is not running, and WiFi is switched off right after.
import time

import config

WIFI_TIMEOUT_MS = 10000
RETRY_MS = 30 * 60 * 1000       # after a failed sync
RESYNC_MS = 12 * 3600 * 1000    # after a good sync


class Clock:
    def __init__(self):
        self.enabled = bool(config.WIFI_SSID)
        self.synced = False
        self.connecting = False
        self.wlan = None
        self.t_start = 0
        self.last_try = None

    # --- local time -------------------------------------------------------
    def local(self):
        return time.localtime(time.time() + config.TZ_OFFSET_MIN * 60)

    def valid(self):
        return self.local()[0] >= 2024

    # --- sync -------------------------------------------------------------
    def begin(self, now):
        if not self.enabled or self.connecting:
            return
        self.last_try = now
        try:
            import network
            self.wlan = network.WLAN(network.STA_IF)
            self.wlan.active(True)
            self.wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
            self.connecting = True
            self.t_start = now
        except Exception as e:
            print("wifi:", e)
            self._off()

    def poll(self, now, busy):
        """Advance a pending sync. busy=True (timer running) defers the NTP
        request; retries are only scheduled while idle."""
        if self.connecting:
            try:
                ok = self.wlan.isconnected()
                failed = self.wlan.status() < 0
            except Exception:
                ok, failed = False, True
            if ok and not busy:
                try:
                    import ntptime
                    ntptime.host = config.NTP_HOST
                    ntptime.settime()
                    self.synced = True
                    print("ntp: synced")
                except Exception as e:
                    print("ntp:", e)
                self._off()
            elif failed or time.ticks_diff(now, self.t_start) > WIFI_TIMEOUT_MS:
                self._off()
            return
        if busy or not self.enabled:
            return
        wait = RESYNC_MS if self.synced else RETRY_MS
        if self.last_try is None or time.ticks_diff(now, self.last_try) > wait:
            self.begin(now)

    def _off(self):
        self.connecting = False
        if self.wlan:
            try:
                self.wlan.disconnect()
                self.wlan.active(False)
            except Exception:
                pass
