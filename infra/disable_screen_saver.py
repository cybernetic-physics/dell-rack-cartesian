"""Keep the dedicated virtual desktop awake without injecting mouse input.

Uses Xlib directly because the minimal desktop image does not include xset.
This affects only DISPLAY (the project's Xvfb server), not the host desktop.
"""
import ctypes as c
import json
import os


def configure():
    x = c.CDLL("libX11.so.6")
    x.XOpenDisplay.argtypes = [c.c_char_p]
    x.XOpenDisplay.restype = c.c_void_p
    x.XGetScreenSaver.argtypes = [c.c_void_p] + [c.POINTER(c.c_int)] * 4
    x.XSetScreenSaver.argtypes = [c.c_void_p] + [c.c_int] * 4
    x.XForceScreenSaver.argtypes = [c.c_void_p, c.c_int]
    x.XSync.argtypes = [c.c_void_p, c.c_int]
    x.XCloseDisplay.argtypes = [c.c_void_p]
    display = os.environ.get("DISPLAY", ":99")
    connection = x.XOpenDisplay(display.encode())
    if not connection:
        raise RuntimeError(f"Cannot open dedicated desktop {display}")

    def settings():
        values = [c.c_int() for _ in range(4)]
        x.XGetScreenSaver(connection, *[c.byref(value) for value in values])
        return dict(zip(("timeout_s", "interval_s", "prefer_blanking", "allow_exposures"),
                        (value.value for value in values)))

    try:
        before = settings()
        # timeout=0 disables the core X screensaver; reset unblanks it now.
        x.XSetScreenSaver(connection, 0, 0, 0, 1)
        x.XForceScreenSaver(connection, 0)
        x.XSync(connection, 0)
        after = settings()
        if after["timeout_s"] != 0:
            raise RuntimeError(f"Screensaver remained enabled: {after}")
        print(json.dumps({"display": display, "before": before, "after": after}))
    finally:
        x.XCloseDisplay(connection)


if __name__ == "__main__":
    configure()
