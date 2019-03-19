import evdev
from constants import code_char_map

def is_keyboard(device):
    if device.phys == "py-evdev-uinput":
        return False
    capabilities = device.capabilities()
    for code in code_char_map:
        if 1 not in capabilities or code not in capabilities[1]:
            return False
    return True

def get_keyboards():
    return filter(is_keyboard, [evdev.InputDevice(path) for path in evdev.list_devices()])

if __name__ == "__main__":
    for keyboard in get_keyboards():
        print(keyboard.path, keyboard.name, keyboard.phys)
        print("")
