from constants import code_char_map
from evdev import KeyEvent, ecodes as e
import evdev
from layers import current_layer, modifier_keys
from utils import forward_event

dev = evdev.InputDevice('/dev/input/event5')
dev.grab()

held_keys = {}

for event in dev.read_loop():
    if event.type == e.EV_KEY:
        print(event.code)
        if event.code in code_char_map:
            if code_char_map[event.code] in held_keys:
                if (code_char_map[event.code], event.value) in held_keys[code_char_map[event.code]]:
                    held_keys[code_char_map[event.code]][(code_char_map[event.code], event.value)]()
                else:
                    forward_event(event)
                if event.value == KeyEvent.key_up:
                    print("removing held")
                    del held_keys[code_char_map[event.code]]
                print('held key:', code_char_map[event.code], event.value)
            elif (code_char_map[event.code], event.value) in current_layer:
                print('key:', code_char_map[event.code], event.value)
                next_layer = current_layer[(code_char_map[event.code], event.value)]()
                if event.value == KeyEvent.key_down and code_char_map[event.code] not in modifier_keys:
                    print("added to hold")
                    held_keys[code_char_map[event.code]] = current_layer
                if next_layer is not None:
                    current_layer = next_layer
            else:
                print('key not found in current bindings')
                forward_event(event)
                if event.value == KeyEvent.key_down:
                    print("added to hold")
                    held_keys[code_char_map[event.code]] = current_layer

        else:
            print('key not found in known characters')
            forward_event(event)


