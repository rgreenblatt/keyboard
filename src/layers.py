from utils import (nothing, run_background, alert, InputHandler)
from constants import code_char_map
from evdev import KeyEvent
from collections import defaultdict
from pathlib import Path
import os
import contextlib
from subprocess import Popen, check_output
from collections import namedtuple

class MyLayerHandler(InputHandler):
    def __init__(self, debug=False):
        super().__init__()
        self.debug = debug
        self.files = {"sym": "/tmp/sym_activated", "sym_single": "/tmp/sym_single_activated", 
                      "base": "/tmp/base_activated", "sym_toggle": "/tmp/sym_toggle_activated", 
                      "function": "/tmp/function_activated"}

        Layer = namedtuple("Layer", "bindings modifiers") 

        on_press_wrapper = lambda c: lambda value: c() if value == KeyEvent.key_down else None

        base_function = {
            ("<capslock>", KeyEvent.key_up): lambda: print("FUNCTION MOD WAS RELEASED NOT EXPECTED"),
            ("<capslock>", KeyEvent.key_down): self.switch_to_function_maker("<capslock>", "<esc>"),
            ("<capslock>", KeyEvent.key_hold): lambda: print("FUNCTION MOD WAS RELEASED NOT EXPECTED"),
            ("<enter>", KeyEvent.key_up): lambda: print("FUNCTION MOD WAS RELEASED NOT EXPECTED"),
            ("<enter>", KeyEvent.key_down): self.switch_to_function_maker("<enter>", "<enter>"),
            ("<enter>", KeyEvent.key_hold): lambda: print("FUNCTION MOD WAS RELEASED NOT EXPECTED")
        }

        standard_remaps = {**self.generate_remap_pass_throughs({"[": "<backspace>"}), 
                           **self.generate_remap_pass_throughs({"<backspace>": "<capslock>"})}

        self.base_layer = Layer(
            bindings={
                ("<alt_l>", KeyEvent.key_up): nothing,
                ("<alt_l>", KeyEvent.key_down): self.switch_to_sym,
                ("<alt_l>", KeyEvent.key_hold): nothing,
                ("<alt_r>", KeyEvent.key_up): nothing,
                ("<alt_r>", KeyEvent.key_down): self.switch_to_sym,
                ("<alt_r>", KeyEvent.key_hold): nothing,
                **base_function,
                **standard_remaps
            }, 
            modifiers=set(["<alt_l>", "<alt_r>", "<capslock>", "<enter>"])
        )

        capslock_remap = self.generate_remap_pass_throughs({"<capslock>": "<esc>"})

        def get_sym_remaps(callback):
            callback = on_press_wrapper(callback)
            return self.generate_remap_pass_throughs(
                {"q": "1", "w": "2", "e": "3", "r": "4", "t": "5", "y": "6", "u": "7", "i": "8", "o": "9", 
                 "p": "0", "a": "!", "s": "@", "d": "#", "f": "$", "g": "%", "h": "^", "j": "&", "k": "*",
                 "l": "(", ";": ")", "'": "|", "z": "~", "x": "_", "c": "-", "v": "+", "b": "=", "n": "\\", 
                 "m": "[", ",": "]", ".": "{", "/": "}", "<control_r>": "`", "<control_l>": "`"}, 
                callback
            )

        self.sym_layer = Layer(
            bindings={
                ("<alt_l>", KeyEvent.key_up): self.switch_to_sym_single_maker("<alt_l>", "<alt_r>"),
                ("<alt_l>", KeyEvent.key_down): lambda: print("MOD WAS PRESSED NOT EXPECTED"),
                ("<alt_l>", KeyEvent.key_hold): nothing,
                ("<alt_r>", KeyEvent.key_up): self.switch_to_sym_single_maker("<alt_r>", "<alt_l>"),
                ("<alt_r>", KeyEvent.key_down): lambda: print("MOD WAS PRESSED NOT EXPECTED"),
                ("<alt_r>", KeyEvent.key_hold): nothing,
                **get_sym_remaps(self.switch_to_sym_key_pressed),
                **standard_remaps,
                **capslock_remap
            },
            modifiers=set(["<alt_l>", "<alt_r>"])
        ) 

        self.sym_layer_key_pressed = Layer(
            bindings={
                ("<alt_l>", KeyEvent.key_up): self.switch_to_base,
                ("<alt_l>", KeyEvent.key_down): lambda: print("MOD WAS PRESSED NOT EXPECTED"),
                ("<alt_l>", KeyEvent.key_hold): nothing,
                ("<alt_r>", KeyEvent.key_up): self.switch_to_base,
                ("<alt_r>", KeyEvent.key_down): lambda: print("MOD WAS PRESSED NOT EXPECTED"),
                ("<alt_r>", KeyEvent.key_hold): nothing,
                **get_sym_remaps(nothing),
                **standard_remaps,
                **capslock_remap
            },
            modifiers=set(["<alt_l>", "<alt_r>"])
        )

        self.sym_layer_toggle = Layer(
            bindings={
                ("<alt_l>", KeyEvent.key_up): nothing,
                ("<alt_l>", KeyEvent.key_down): self.switch_to_base,
                ("<alt_l>", KeyEvent.key_hold): nothing,
                ("<alt_r>", KeyEvent.key_up): nothing,
                ("<alt_r>", KeyEvent.key_down): self.switch_to_base,
                ("<alt_r>", KeyEvent.key_hold): nothing,
                ("<shift_l>", KeyEvent.key_up): nothing,
                ("<shift_l>", KeyEvent.key_down): self.switch_to_sym_toggle_shift,
                ("<shift_l>", KeyEvent.key_hold): nothing,
                ("<shift_r>", KeyEvent.key_up): nothing,
                ("<shift_r>", KeyEvent.key_down): self.switch_to_sym_toggle_shift,
                ("<shift_r>", KeyEvent.key_hold): nothing,
                **get_sym_remaps(nothing),
                **standard_remaps,
                **capslock_remap
            },
            modifiers=set(["<alt_l>", "<alt_r>", "<shift_l>", "<shift_r>"])
        )

        self.sym_layer_toggle_shift = Layer(
            bindings={
                ("<alt_l>", KeyEvent.key_up): nothing,
                ("<alt_l>", KeyEvent.key_down): self.switch_to_base,
                ("<alt_l>", KeyEvent.key_hold): nothing,
                ("<alt_r>", KeyEvent.key_up): nothing,
                ("<alt_r>", KeyEvent.key_down): self.switch_to_base,
                ("<alt_r>", KeyEvent.key_hold): nothing,
                ("<shift_l>", KeyEvent.key_up): self.switch_to_sym_toggle,
                ("<shift_l>", KeyEvent.key_down): lambda: print("SHIFT WAS PRESSED NOT EXPECTED"),
                ("<shift_l>", KeyEvent.key_hold): nothing,
                ("<shift_r>", KeyEvent.key_up): self.switch_to_sym_toggle,
                ("<shift_r>", KeyEvent.key_down): lambda: print("SHIFT WAS PRESSED NOT EXPECTED"),
                ("<shift_r>", KeyEvent.key_hold): nothing,
                **standard_remaps,
                **capslock_remap
            },
            modifiers=set(["<alt_l>", "<alt_r>", "<shift_l>", "<shift_r>"])
        )

        self.get_sym_layer_single = lambda key, other: Layer(
            bindings={
                (key, KeyEvent.key_up): lambda: print("MOD WAS RELEASED NOT EXPECTED"),
                (key, KeyEvent.key_down): self.switch_to_sym_toggle,
                (key, KeyEvent.key_hold): lambda: print("MOD WAS HELD NOT EXPECTED"),
                (other, KeyEvent.key_up): lambda: print("MOD WAS RELEASED NOT EXPECTED"),
                (other, KeyEvent.key_down): self.switch_to_sym,
                (other, KeyEvent.key_hold): lambda: print("MOD WAS HELD NOT EXPECTED"),
                **base_function, 
                **get_sym_remaps(self.switch_to_base)
            },
            modifiers=set(["<alt_l>", "<alt_r>", "<capslock>", "<enter>"])
        )

        def get_function_remaps(callback):
            callback = on_press_wrapper(callback)
            return {
                **self.generate_remap_system_command({"q": ["i3-msg", "workspace", "1"],
                                                      "w": ["i3-msg", "workspace", "2"],
                                                      "e": ["i3-msg", "workspace", "3"],
                                                      "r": ["i3-msg", "workspace", "4"],
                                                      "t": ["i3-msg", "workspace", "5"],
                                                      "y": ["i3-msg", "move", "workspace", "1"],
                                                      "u": ["i3-msg", "move", "workspace", "2"],
                                                      "i": ["i3-msg", "move", "workspace", "3"],
                                                      "o": ["i3-msg", "move", "workspace", "4"],
                                                      "p": ["i3-msg", "move", "workspace", "5"],
                                                      ";": ["inc_bright"], "'": ["dec_bright"],
                                                      "z": ["inc_vol", "5"], "x": ["dec_vol", "5"],
                                                      "c": ["mute_vol"]}, callback),
                **self.generate_remap_python_callable({"h": self.i3_change_focus("h"), 
                                                       "j": self.i3_change_focus("j"),
                                                       "k": self.i3_change_focus("k"),
                                                       "l": self.i3_change_focus("l")},
                                                      callback),
                **self.generate_remap_pass_throughs({"a": "<pageup>", "s": "<pagedown>", "d": "<c-u>", 
                                                     "f": "<c-d>", "n": "<left>", "m": "<down>", 
                                                     ",": "<up>", ".": "<right>"},
                                                    callback)
            }

        self.get_function_layer = lambda key, map_to: Layer(
            bindings={
                (key, KeyEvent.key_up): lambda : (self.press(map_to, flush=True), self.switch_to_base()),
                (key, KeyEvent.key_down): lambda: print("FUNCTION MOD WAS PRESSED NOT EXPECTED"),
                (key, KeyEvent.key_hold): nothing,
                **get_function_remaps(self.switch_to_function_key_pressed_maker(key)),
                **standard_remaps
            },
            modifiers=set([key])
        )

        self.get_function_layer_key_pressed = lambda key: Layer(
            bindings={
                (key, KeyEvent.key_up): self.switch_to_base,
                (key, KeyEvent.key_down): lambda: print("FUNCTION MOD WAS PRESSED NOT EXPECTED"),
                (key, KeyEvent.key_hold): nothing,
                **get_function_remaps(nothing),
                **standard_remaps
            },
            modifiers=set([key])
        )

        self.layer = self.base_layer
        self.held_keys = {}

    def key(self, code, value):
        if code in code_char_map:
            key = code_char_map[code]
            key_value = key, value
            if key in self.held_keys:
                print('held key:', key, value) if self.debug else None
                held_layer = self.held_keys[key]
                if key_value in held_layer:
                    held_layer[key_value]()
                else:
                    self.forward_key(code, value)
                if value == KeyEvent.key_up:
                    print("removing held") if self.debug else None
                    del self.held_keys[key]
            elif key_value in self.layer.bindings:
                print('key:', key, value) if self.debug else None
                if value == KeyEvent.key_down and key not in self.layer.modifiers:
                    print("added to hold") if self.debug else None
                    self.held_keys[key] = self.layer.bindings
                self.layer.bindings[key_value]()
            else:
                print('key not found in current bindings') if self.debug else None
                if value == KeyEvent.key_down:
                    print("added to hold") if self.debug else None
                    self.held_keys[key] = self.layer.bindings
                self.forward_key(code, value)
        else:
            print('key not found in known characters') if self.debug else None
            self.forward_key(code, value)

    def remove_all_files(self):
        for f in self.files.values():
            with contextlib.suppress(FileNotFoundError):
                os.remove(f)

    def make_file(self, f_name):
        Path(self.files[f_name]).touch()

    def switch_to_sym(self):
        self.remove_all_files()
        self.make_file("sym")
        print("Switching to sym") if self.debug else None
        self.layer = self.sym_layer

    def switch_to_sym_single_maker(self, key, other):
        return lambda: self.switch_to_sym_single(key, other)

    def switch_to_sym_single(self, key, other):
        self.remove_all_files()
        self.make_file("sym_single")
        print("Switching to single") if self.debug else None
        self.layer = self.get_sym_layer_single(key, other)

    def switch_to_sym_key_pressed(self):
        self.remove_all_files()
        self.make_file("sym")
        print("Switching to pressed") if self.debug else None
        self.layer = self.sym_layer_key_pressed

    def switch_to_base(self):
        self.remove_all_files()
        self.make_file("base")
        print("Switching to base") if self.debug else None
        self.layer = self.base_layer

    def switch_to_sym_toggle(self):
        self.remove_all_files()
        self.make_file("sym_toggle")
        print("Switching to toggle") if self.debug else None
        self.layer = self.sym_layer_toggle

    def switch_to_sym_toggle_shift(self):
        print("Switching to toggle shift") if self.debug else None
        self.layer = self.sym_layer_toggle_shift

    def switch_to_function_maker(self, key, map_to):
        return lambda: self.switch_to_function(key, map_to)

    def switch_to_function(self, key, map_to):
        self.remove_all_files()
        self.make_file("function")
        print("Switching to function using", key) if self.debug else None
        self.layer = self.get_function_layer(key, map_to)

    def switch_to_function_key_pressed_maker(self, key):
        return lambda: self.switch_to_function_key_pressed(key)

    def switch_to_function_key_pressed(self, key):
        self.remove_all_files()
        self.make_file("function")
        print("Switching to function pressed using", key) if self.debug else None
        self.layer = self.get_function_layer_key_pressed(key)

    def i3_change_focus(self, direction):
        def change():
            try:
                window_id = check_output(['xdotool', 'getwindowfocus']).decode("utf-8").strip()
                print("window_id for change focus:", window_id) if self.debug else None
                window_name = check_output(['xdotool', 'getwindowname', window_id]).decode("utf-8").strip()
                print("window_name for change focus:", window_name) if self.debug else None 
            except Exception as e:
                print("xdotool change focus command error:", e)
                alert("XDOTOOL CHANGE FOCUS ERROR", str(e))
                return

            if window_name == "nvim":
                self.control_press("\\")
                self.control_press("n")
                self.press("g")
                self.press("z")
                self.press(direction, flush=True)
            else:
                if direction == "h":
                    full_direction_name = "right"
                elif direction == "j":
                    full_direction_name = "down"
                elif direction == "k":
                    full_direction_name = "up"
                elif direction == "l":
                    full_direction_name = "left"
                run_background(["i3-msg", "focus", full_direction_name])
        return change
