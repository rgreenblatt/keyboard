from keyboard.utils import (nothing, run_background, alert, InputHandler)
from keyboard.constants import code_char_map, path_keyboard_info
from evdev import KeyEvent
from collections import defaultdict
from pathlib import Path
import os
import contextlib
from subprocess import Popen, check_output
from keyboard.mod_tap import ModTap
from keyboard.mod_toggle import ModToggle
from collections import namedtuple

class MyLayerHandler(InputHandler):

    files = {"sym": "sym_activated", "sym_single": "sym_single_activated", 
             "base": "base_activated", "sym_toggle": "sym_toggle_activated", 
             "function": "function_activated", "keyboard_disabled": "keyboard_disabled_activated",
             "control": "control_activated", "shift": "shift_activated"}

    for key in files:
        files[key] = os.path.join(path_keyboard_info, files[key])

    def __init__(self, debug=False):
        super().__init__()
        self.debug = debug

        standard_key_function = self.generic_key_function_maker(False)
        disable_key_function = self.generic_key_function_maker(True)

        BaseLayer = namedtuple("BaseLayer", "bindings modifiers key_function") 

        class Layer(BaseLayer):
            def __new__(self, bindings, modifiers, key_function=standard_key_function):
                return super(Layer, self).__new__(self, bindings, modifiers, key_function)

        standard_remaps = {**self.generate_remap_pass_throughs({"[": "<backspace>"}), 
                           **self.generate_remap_pass_throughs({"<backspace>": "<capslock>"}),
                           **self.generate_remap_pass_throughs({"<capslock>": "<esc>"})}

        def make_wrapper(bindings):
            def get_wrapped_bindings(create_key_up, create_key_down, create_key_hold):
                wrapped_bindings = {}

                for (key, key_event), action in bindings.items():
                    if key_event == KeyEvent.key_down:
                        wrapped_action = create_key_down(key, action)
                    elif key_event == KeyEvent.key_up:
                        wrapped_action = create_key_up(key, action)
                    elif key_event == KeyEvent.key_hold:
                        wrapped_action = create_key_hold(key, action)

                    wrapped_bindings[key, key_event] = wrapped_action

                return wrapped_bindings
            return get_wrapped_bindings

        sym_bindings = self.generate_remap_pass_throughs(
            {"<capslock>": "<esc>", "q": "1", "w": "2", "e": "3", "r": "4", "t": "5", "y": "6", "u": "7", 
             "i": "8", "o": "9", "p": "0", "a": "!", "s": "@", "d": "#", "f": "$", "g": "%", "h": "^", 
             "j": "&", "k": "*", "l": "(", ";": ")", "'": "|", "z": "~", "x": "_", "c": "-", "v": "+", 
             "b": "=", "n": "\\", "m": "[", ",": "]", ".": "{", "/": "}", "<control_r>": "`", 
             "<control_l>": "`"}, 
            nothing
        )

        control_bindings = self.generate_remap_control_press(
            {"<capslock>": "<esc>", "<space>": "<space>", "q": "q", "w": "w", "e": "e", "r": "r", 
             "t": "t", "y": "y", "u": "u", "i": "i", "o": "o", "p": "p", "a": "a", "s": "s", "d": "d", 
             "f": "f", "g": "g", "h": "h", "j": "j", "k": "k", "l": "l", ";": ";", "'": "'", "z": "z", 
             "x": "x", "c": "c", "v": "v", "b": "b", "n": "n", "m": "m", ",": ",", ".": ".", "/": "/"}, 
            nothing
        )

        shift_bindings = self.generate_remap_shift_press(
            {"q": "q", "w": "w", "e": "e", "r": "r", 
             "t": "t", "y": "y", "u": "u", "i": "i", "o": "o", "p": "p", "a": "a", "s": "s", "d": "d", 
             "f": "f", "g": "g", "h": "h", "j": "j", "k": "k", "l": "l", ";": ";", "'": "'", "z": "z", 
             "x": "x", "c": "c", "v": "v", "b": "b", "n": "n", "m": "m", ",": ",", ".": ".", "/": "/"}, 
            nothing
        )

        function_bindings = {
            ('<esc>', KeyEvent.key_down): self.switch_to_disable,
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
                                                  "c": ["mute_vol"], "v": ["start_term"], 
                                                  "b": ["qutebrowser"]}, nothing),
            **self.generate_remap_python_callable({"h": self.i3_change_focus("h"), 
                                                   "j": self.i3_change_focus("j"),
                                                   "k": self.i3_change_focus("k"),
                                                   "l": self.i3_change_focus("l")},
                                                  nothing),
            **self.generate_remap_pass_throughs({"a": "<pageup>", "s": "<pagedown>", "d": "<c-u>", 
                                                 "f": "<c-d>", "n": "<left>", "m": "<down>", 
                                                 ",": "<up>", ".": "<right>"},
                                                nothing)
        }


        get_function_bindings = make_wrapper(function_bindings)
        get_sym_bindings = make_wrapper(sym_bindings)
        get_control_bindings = make_wrapper(control_bindings)

        def base_switch_to_sym():
            self.remove_all_files()
            self.make_file("sym")
            print("Switching to sym") if self.debug else None

        def base_switch_to_function():
            self.remove_all_files()
            self.make_file("function")
            print("Switching to function") if self.debug else None

        def base_switch_to_control():
            self.remove_all_files()
            self.make_file("control")
            print("Switching to control") if self.debug else None

        def base_switch_to_shift():
            self.remove_all_files()
            self.make_file("shift")
            print("Switching to shift") if self.debug else None

        def base_switch_to_sym_toggle():
            self.remove_all_files()
            self.make_file("sym_toggle")
            print("Switching to sym toggle") if self.debug else None

        time_no_tap = 0.2
        catch_final_if_no_tap = True

        function_escape = ModTap(self, "<capslock>", "<esc>", get_function_bindings, standard_remaps, 
                                 self.switch_to_base, base_switch_to_function, 
                                 set(['<esc>']), Layer, time_no_tap,
                                 catch_final_if_no_tap, name="esc function layer")

        function_enter = ModTap(self, "<enter>", "<enter>", get_function_bindings, standard_remaps, 
                                self.switch_to_base, base_switch_to_function, 
                                set(['<esc>']), Layer, time_no_tap,
                                 catch_final_if_no_tap, name="enter function layer")

        sym_space = ModTap(self, "<space>", "<space>", get_sym_bindings, standard_remaps, 
                           self.switch_to_base, base_switch_to_sym, set(), Layer, 
                           time_no_tap, catch_final_if_no_tap, name="space sym layer")

        sym_space_toggle = ModToggle(self, "<space>", ["<shift_l>", "<shift_r>"], sym_bindings, {},  
                                     standard_remaps, self.switch_to_base, base_switch_to_sym_toggle, set(), 
                                     Layer, name="space sym layer")

        control_z = ModTap(self, "z", "z", get_control_bindings, standard_remaps, 
                       self.switch_to_base, base_switch_to_control, set(), Layer, 
                       time_no_tap, catch_final_if_no_tap, name="z control layer")

        control_slash = ModTap(self, "/", "/", get_control_bindings, standard_remaps, 
                       self.switch_to_base, base_switch_to_control, set(), Layer, 
                       time_no_tap, catch_final_if_no_tap, name="/ control layer")

        time_no_tap_shift = 0.0
        catch_final_if_no_tap_shift = True

        get_shift_bindings = make_wrapper({**shift_bindings, **sym_space_toggle.parent_bindings})

        shift_l = ModTap(self, "<shift_l>", "<shift_l>", get_shift_bindings, standard_remaps, 
                       self.switch_to_base, base_switch_to_shift, sym_space_toggle.parent_modifiers, Layer, 
                       time_no_tap_shift, catch_final_if_no_tap_shift, name="left shift layer")


        shift_r = ModTap(self, "<shift_r>", "<shift_r>", get_shift_bindings, standard_remaps, 
                       self.switch_to_base, base_switch_to_shift, sym_space_toggle.parent_modifiers, Layer, 
                       time_no_tap_shift, catch_final_if_no_tap_shift, name="right shift layer")


        self.base_layer = Layer(
            bindings={
                **function_escape.parent_bindings,
                **function_enter.parent_bindings,
                **sym_space.parent_bindings,
                **control_z.parent_bindings,
                **control_slash.parent_bindings,
                **shift_l.parent_bindings,
                **shift_r.parent_bindings,
                **standard_remaps
            }, 
            modifiers=function_escape.modifiers.union(function_enter.modifiers).union(sym_space.modifiers).
            union(control_z.modifiers).union(control_slash.modifiers).union(shift_l.modifiers).
            union(shift_r.modifiers)
        )

        capslock_remap = self.generate_remap_pass_throughs({"<capslock>": "<esc>"})

        self.disable_keyboard_layer = Layer(
            bindings={
                ('<esc>', KeyEvent.key_up): nothing,
                ('<esc>', KeyEvent.key_down): self.switch_to_base,
                ('<esc>', KeyEvent.key_hold): nothing,
            },
            modifiers=set(['<esc>']),
            key_function=disable_key_function
        )

        self.layer = self.base_layer
        self.held_keys = {}

    def set_layer(self, layer):
        self.layer = layer

    def get_layer(self):
        return self.layer

    def add_held_key(self, key):
        self.held_keys[key] = None

    def remove_held_key(self, key):
        del self.held_keys[key]

    def generic_key_function_maker(self, is_disable):
        def generic_key_function(code, value):
            if code in code_char_map:
                key = code_char_map[code]
                key_value = key, value
                if key in self.held_keys:
                    print('held key:', key, value) if self.debug else None
                    held_layer = self.held_keys[key]
                    if value == KeyEvent.key_up:
                        print("removing held") if self.debug else None
                        self.remove_held_key(key)
                    if not is_disable:
                        if key_value in held_layer:
                            held_layer[key_value]()
                        else:
                            self.forward_key(code, value)
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
                    if not is_disable:
                        self.forward_key(code, value)
            else:
                print('key not found in known characters') if self.debug else None
                if not is_disable:
                    self.forward_key(code, value)
        return generic_key_function

    def key(self, code, value):
        self.layer.key_function(code, value)

    def remove_all_files(self):
        for f in self.files.values():
            with contextlib.suppress(FileNotFoundError):
                os.remove(f)

    def make_file(self, f_name):
        Path(self.files[f_name]).touch()

    def switch_to_disable(self):
        self.remove_all_files()
        self.make_file("keyboard_disabled")
        print("Disabling keyboard") if self.debug else None
        self.layer = self.disable_keyboard_layer

    def switch_to_base(self):
        self.remove_all_files()
        self.make_file("base")
        print("Switching to base") if self.debug else None
        self.layer = self.base_layer

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
