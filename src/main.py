from constants import code_char_map, debug
from evdev import KeyEvent, ecodes as e
import evdev
from layers import current_layer, modifier_keys
from utils import forward_event

dev = evdev.InputDevice('/dev/input/event6')
dev.grab()

held_keys = {}

for event in dev.read_loop():
    if event.type == e.EV_KEY:
        print(event.code) if debug else None
        if event.code in code_char_map:
            if code_char_map[event.code] in held_keys:
                if (code_char_map[event.code], event.value) in held_keys[code_char_map[event.code]]:
                    held_keys[code_char_map[event.code]][(code_char_map[event.code], event.value)]()
                else:
                    forward_event(event)
                if event.value == KeyEvent.key_up:
                    print("removing held") if debug else None
                    del held_keys[code_char_map[event.code]]
                print('held key:', code_char_map[event.code], event.value) if debug else None
            elif (code_char_map[event.code], event.value) in current_layer:
                print('key:', code_char_map[event.code], event.value) if debug else None
                changes = current_layer[(code_char_map[event.code], event.value)]()
                if event.value == KeyEvent.key_down and code_char_map[event.code] not in modifier_keys:
                    print("added to hold") if debug else None
                    held_keys[code_char_map[event.code]] = current_layer
                if changes is not None:
                    if changes[0] is not None:
                        current_layer = changes[0]
                    if changes[1] is not None:
                         modifier_keys = changes[1]
            else:
                print('key not found in current bindings') if debug else None
                forward_event(event)
                if event.value == KeyEvent.key_down:
                    print("added to hold") if debug else None
                    held_keys[code_char_map[event.code]] = current_layer

        else:
            print('key not found in known characters') if debug else None
            forward_event(event)
