from evdev import KeyEvent, UInput, ecodes as e
from constants import code_char_map, upper_lower, control_single
from subprocess import Popen

ui = UInput()

def press(name, flush=False):
    code = code_char_map.inverse[name]
    ui.write(e.EV_KEY, code, KeyEvent.key_down)
    ui.write(e.EV_KEY, code, KeyEvent.key_up)
    if flush:
        ui.syn()

def control_press(name):
    code = code_char_map.inverse[name]
    ui.write(e.EV_KEY, code_char_map.inverse["<control_l>"], KeyEvent.key_down)
    ui.write(e.EV_KEY, code, KeyEvent.key_down)
    ui.write(e.EV_KEY, code, KeyEvent.key_up)
    ui.write(e.EV_KEY, code_char_map.inverse["<control_l>"], KeyEvent.key_up)

def shift_press(name):
    code = code_char_map.inverse[name]
    ui.write(e.EV_KEY, code_char_map.inverse["<shift_l>"], KeyEvent.key_down)
    ui.write(e.EV_KEY, code, KeyEvent.key_down)
    ui.write(e.EV_KEY, code, KeyEvent.key_up)
    ui.write(e.EV_KEY, code_char_map.inverse["<shift_l>"], KeyEvent.key_up)

def string_sender(string):
    def send():
        for c in string:
            if c in upper_lower:
                shift_press(upper_lower[c])
            else:
                press(c)
        ui.syn()
    return send

def nothing():
    pass

def generate_remaper(inner_func):
    def remap(character_maps, callback=nothing, 
        actions=[KeyEvent.key_down, KeyEvent.key_up, KeyEvent.key_hold]):
        out = {}
        for f, t in character_maps.items():
            for v in [KeyEvent.key_down, KeyEvent.key_up, KeyEvent.key_hold]:
                def write_key(t=t, v=v):
                    inner_func(t, v)
                    return callback()
                out[(f, v)] = write_key
        return out
    return remap

def send_key(t, v):
    if t in upper_lower:
        if v != KeyEvent.key_up:
            shift_press(upper_lower[t])
    elif t in control_single:
        if v != KeyEvent.key_up:
            control_press(control_single[t])
    else:
        ui.write(e.EV_KEY, code_char_map.inverse[t], v)
    ui.syn()

def send_system_command(t, v):
    if v == KeyEvent.key_down:
        pid = Popen(t).pid

def send_string(t, v):
    if v == KeyEvent.key_down:
        string_sender(t)()

def run_python_callable(t, v):
    if v == KeyEvent.key_down:
        t()

generate_remap_pass_throughs = generate_remaper(send_key)
generate_remap_system_command= generate_remaper(send_system_command)
generate_remap_string = generate_remaper(send_string)
generate_remap_python_callable = generate_remaper(run_python_callable)

def forward_event(event):
    ui.write(e.EV_KEY, event.code, event.value)
    ui.syn()

if __name__ == '__main__':
    press('a')
    ui.syn()
