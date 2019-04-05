import os
import time
from signal import SIGKILL
from sys import argv, exit

from evdev import InputDevice
from evdev import ecodes as e
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from keyboard.layers import MyLayerHandler
from keyboard.utils import alert
from test_keyboards import get_keyboards

if __name__ == '__main__':
    alert("Keyboard is mapped", time=3)
    debug = len(argv) > 1 and bool(argv[1])
    handler = MyLayerHandler(debug)
    dev = InputDevice("/dev/input/event4")
    dev.grab()
    for event in dev.read_loop():
        if event.type == e.EV_KEY:
            handler.key(event.code, event.value)
