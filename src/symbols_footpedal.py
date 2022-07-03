from select import select

import evdev
from evdev.device import InputDevice
from evdev import ecodes as e
from evdev.events import KeyEvent
from evdev.uinput import UInput

from keyboard.constants import code_char_map
from keyboard.utils import InputHandler


def is_keyboard(device):
    if device.phys == "py-evdev-uinput":
        return False
    capabilities = device.capabilities()
    for code in code_char_map:
        if 1 not in capabilities or code not in capabilities[1]:
            return False
    return True


def get_keyboards_by_name(name: str):
    return filter(
        lambda x: is_keyboard(x) and name in x.name,
        [evdev.InputDevice(path) for path in evdev.list_devices()],
    )


if __name__ == "__main__":
    pedalname = "FootSwitch"
    pedals = list(get_keyboards_by_name(pedalname))
    gergoplexs = list(get_keyboards_by_name("GergoPlex"))

    inputs = list(map(InputDevice, pedals + gergoplexs))
    for inp in inputs:
        inp.grab()

    devices = {dev.fd: dev for dev in inputs}

    down = False

    input_handler = InputHandler()

    sym_map = {
        "q": "1",
        "w": "2",
        "e": "3",
        "r": "4",
        "t": "5",
        "y": "6",
        "u": "7",
        "i": "8",
        "o": "9",
        "p": "0",
        "a": "!",
        "s": "@",
        "d": "#",
        "f": "$",
        "g": "%",
        "h": "^",
        "j": "&",
        "k": "*",
        "l": "(",
        ";": ")",
        "z": "'",
        "x": "[",
        "c": "]",
        "v": "_",
        "b": "-",
        "n": "+",
        "m": "~",
        ",": "{",
        ".": "}",
        "/": '"',
    }

    while True:
        r, w, x = select(devices, [], [])
        for fd in r:
            for event in devices[fd].read():
                if pedalname in devices[fd].name:
                    if (
                        event.type == e.EV_KEY
                        and event.code in code_char_map
                        and code_char_map[event.code] == "b"
                    ):
                        if event.value == KeyEvent.key_up:
                            down = False
                        elif event.value == KeyEvent.key_down:
                            down = True
                    continue
                elif down and event.code in code_char_map:
                    key = code_char_map[event.code]
                    if key in sym_map:
                        input_handler.send_key(sym_map[key], event.value, flush=True)
                        continue

                input_handler.ui.write(event.type, event.code, event.value)
                input_handler.ui.syn()
