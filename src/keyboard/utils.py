from evdev import KeyEvent, UInput, ecodes as e
from keyboard.constants import code_char_map, upper_lower, control_single
from subprocess import Popen, DEVNULL
import os

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
        if t in upper_lower:
            if v != KeyEvent.key_up:
                self.input_handler.shift_press(upper_lower[t])
        elif t in control_single:
            if v != KeyEvent.key_up:
                self.input_handler.control_press(control_single[t])
        else:
            self.input_handler.ui.write(e.EV_KEY, code_char_map.inverse[t], v)
        self.input_handler.ui.syn()

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
            #get each character, this won't work for modifiers or other special characters
            for c in t:
                if c in upper_lower:
                    self.input_handler.shift_press(upper_lower[c])
                else:
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
        self.generate_remap_system_command= RemapSystemCommand()
        self.generate_remap_string = RemapString(self)
        self.generate_remap_python_callable = RemapCallable()
        self.generate_remap_control_press = RemapModifierPress(self, self.control_press)
        self.generate_remap_super_press = RemapModifierPress(self, self.super_press)
        self.generate_remap_shift_press = RemapModifierPress(self, self.shift_press)

    def press(self, key, flush=False):
        code = code_char_map.inverse[key]
        self.ui.write(e.EV_KEY, code, KeyEvent.key_down)
        self.ui.write(e.EV_KEY, code, KeyEvent.key_up)
        if flush:
            self.ui.syn()

    def super_press(self, key, flush=False):
        code = code_char_map.inverse[key]
        self.ui.write(e.EV_KEY, code_char_map.inverse["<super>"], KeyEvent.key_down)
        self.ui.write(e.EV_KEY, code, KeyEvent.key_down)
        self.ui.write(e.EV_KEY, code, KeyEvent.key_up)
        self.ui.write(e.EV_KEY, code_char_map.inverse["<super>"], KeyEvent.key_up)
        if flush:
            self.ui.syn()

    def control_press(self, key, flush=False):
        code = code_char_map.inverse[key]
        self.ui.write(e.EV_KEY, code_char_map.inverse["<control_l>"], KeyEvent.key_down)
        self.ui.write(e.EV_KEY, code, KeyEvent.key_down)
        self.ui.write(e.EV_KEY, code, KeyEvent.key_up)
        self.ui.write(e.EV_KEY, code_char_map.inverse["<control_l>"], KeyEvent.key_up)
        if flush:
            self.ui.syn()

    def shift_press(self, key, flush=False):
        code = code_char_map.inverse[key]
        self.ui.write(e.EV_KEY, code_char_map.inverse["<shift_l>"], KeyEvent.key_down)
        self.ui.write(e.EV_KEY, code, KeyEvent.key_down)
        self.ui.write(e.EV_KEY, code, KeyEvent.key_up)
        self.ui.write(e.EV_KEY, code_char_map.inverse["<shift_l>"], KeyEvent.key_up)
        if flush:
            self.ui.syn()

    def forward_key(self, code, value):
        self.ui.write(e.EV_KEY, code, value)
        self.ui.syn()

def alert(title, text="", time=10):
    os.system("notify-send -u critical -t {} '{}' '{}'".format(time * 1000, title, text))

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
