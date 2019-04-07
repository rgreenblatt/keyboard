import os
from subprocess import DEVNULL, Popen

from evdev import KeyEvent, UInput
from evdev import ecodes as e

from keyboard.constants import (code_char_map, shift_maps, control_maps, 
                                alt_maps, control_alt_maps)

def nothing(*a):
    pass

class Remaper():
    def __call__(self, character_maps, callback=nothing, 
        actions=[KeyEvent.key_down, KeyEvent.key_up, KeyEvent.key_hold]):
        out = {}
        for f, t in character_maps.items():
            for v in actions:
                def write_key(t=t, v=v):
                    self.remap_action(t, v)
                    callback(v)
                out[(f, v)] = write_key
        return out

    def remap_action(self):
        raise NotImplementedError("remap_action must be implemented")

class RemapPassThroughs(Remaper):
    def __init__(self, input_handler):
        self.input_handler = input_handler

    def remap_action(self, t, v):
        self.input_handler.send_event(t, v, True)

class RemapSystemCommand(Remaper):
    def remap_action(self, t, v):
        if v == KeyEvent.key_down:
            run_background(t)

class RemapModifierPress(Remaper):
    def __init__(self, input_handler, press_func):
        self.input_handler = input_handler
        self.press_func = press_func

    def remap_action(self, t, v):
        if v == KeyEvent.key_down or v == KeyEvent.key_hold:
            self.press_func(t, flush=True)

class RemapString(Remaper):
    def __init__(self, input_handler):
        self.input_handler = input_handler

    def remap_action(self, t, v):
        if v == KeyEvent.key_down:
            #won't work for modifiers or other special characters
            for c in t:
                self.input_handler.press(c)
            self.input_handler.ui.syn()

class RemapCallable(Remaper):
    def remap_action(self, t, v):
        if v == KeyEvent.key_down:
            t()

class InputHandler():
    def __init__(self):
        self.ui = UInput()
        self.generate_remap_pass_throughs = RemapPassThroughs(self)
        self.generate_remap_system_command = RemapSystemCommand()
        self.generate_remap_string = RemapString(self)
        self.generate_remap_python_callable = RemapCallable()
        self.make_generate_remap_mod_press = \
            lambda mod: RemapModifierPress(self, self.make_mod_press(mod))
        self.shift_press = self.make_mod_press('<shift_l>')
        self.control_press = self.make_mod_press('<control_l>')
        self.alt_press = self.make_mod_press('<control_l>')
        self.control_alt_press = self.make_mod_press(['<control_l>', '<alt_l>'])

        self.mod_combos = [(shift_maps, self.shift_press),
                           (control_maps, self.control_press),
                           (alt_maps, self.alt_press),
                           (control_alt_maps, self.control_alt_press)]


    def send_event(self, values, press_type, flush=False):
        if isinstance(values, str):
            self.send_key(values, press_type)
        else:
            for key in values:
                self.send_key(key, press_type)
        if flush:
            self.ui.syn()

    def write(self, key, press_type, flush=False):
        self.write_raw(code_char_map.inverse[key], press_type, flush)

    def write_raw(self, code, press_type, flush=False):
        self.ui.write(e.EV_KEY, code, press_type)
        if flush:
            self.ui.syn()

    def send_key(self, key, press_type, flush=False):
        for mod_map, mod_press in self.mod_combos:
            if key in mod_map:
                if press_type != KeyEvent.key_up:
                    mod_press(mod_map[key], flush)
                return
        self.write(key, press_type, flush)

    def press(self, key, flush=False):
        self.send_event(key, KeyEvent.key_down)
        self.send_event(key, KeyEvent.key_up, flush)

    def make_mod_press(self, mod):
        def mod_press(key, flush=False):
            self.send_event(mod, KeyEvent.key_down)
            self.press(key)
            self.send_event(mod, KeyEvent.key_up, flush)
        
        return mod_press

def alert(title, text="", time=10):
    os.system("notify-send -u critical -t {} '{}' '{}'".format(time * 1000, 
                                                               title, text))

def run_background(command):
    try:
        Popen(command, stdout=DEVNULL).pid
    except Exception as e:
        print("Background command error:", e)
        alert("BACKGROUND PROCESS ERROR", str(e))

if __name__ == '__main__':
    u_input = InputHandler()
    u_input.press('a')
    u_input.ui.syn()
