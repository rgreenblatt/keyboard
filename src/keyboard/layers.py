import contextlib
import os
from collections import namedtuple
from pathlib import Path
from subprocess import check_output

from evdev import KeyEvent

from keyboard.constants import code_char_map, path_keyboard_info
from keyboard.mod_tap import ModTap
from keyboard.mod_toggle import ModToggle
from keyboard.utils import (InputHandler, alert, nothing, run_background,
                            debug_print)

files = {
    "sym": "sym_activated",
    "sym_single": "sym_single_activated",
    "base": "base_activated",
    "sym_toggle": "sym_toggle_activated",
    "function": "function_activated",
    "keyboard_disabled": "keyboard_disabled_activated",
}

for file in files:
    files[file] = os.path.join(path_keyboard_info, files[file])


class MyLayerHandler(InputHandler):
    def __init__(self, debug=False):
        super().__init__()
        self.debug = debug

        standard_key_function = self.generic_key_function_maker(False)
        disable_key_function = self.generic_key_function_maker(True)

        BaseLayer = namedtuple("BaseLayer", "bindings modifiers key_function")

        class Layer(BaseLayer):
            def __new__(cls,
                        bindings,
                        modifiers,
                        key_function=standard_key_function):
                return super(Layer, cls).__new__(cls, bindings, modifiers,
                                                 key_function)

        standard_dict = {
            "[": "<backspace>",
            "<backspace>": "<capslock>",
            "<capslock>": "<esc>",
            "<control_l>": ["<control_l>", "<alt_l>"],
            "<control_r>": ["<control_r>", "<alt_r>"],
        }

        standard_bindings = self.generate_remap_pass_throughs(standard_dict)

        def make_wrapper(bindings):
            def get_wrapped_bindings(create_key_up, create_key_down,
                                     create_key_hold):
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

        self_dict = {
            "<space>": "<space>",
            "<tab>": "<tab>",
            "<enter>": "<enter>",
            "<esc>": "<esc>",
            "<shift_l>": "-",
            "<shift_r>": "=",
            "<alt_l>": "<tab>",
            "<alt_r>": "<backspace>",
            "q": "q",
            "w": "w",
            "e": "e",
            "r": "r",
            "t": "t",
            "y": "y",
            "u": "u",
            "i": "i",
            "o": "o",
            "p": "p",
            "a": "a",
            "s": "s",
            "d": "d",
            "f": "f",
            "g": "g",
            "h": "h",
            "j": "j",
            "k": "k",
            "l": "l",
            ";": ";",
            "'": "'",
            "z": "z",
            "x": "x",
            "c": "c",
            "v": "v",
            "b": "b",
            "n": "n",
            "m": "m",
            ",": ",",
            ".": ".",
            "/": "/",
            "`": "`",
            **standard_dict
        }

        sym_bindings = self.generate_remap_pass_throughs(
            {
                "<capslock>": "<esc>",
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
                "/": "\""
            }, nothing)
        function_bindings = {
            ('<esc>', KeyEvent.key_down):
            self.switch_to_disable,
            **self.generate_remap_system_command(
                {
                    "q": ["i3-msg", "workspace", "1"],
                    "w": ["i3-msg", "workspace", "2"],
                    "e": ["i3-msg", "workspace", "3"],
                    "r": ["i3-msg", "workspace", "4"],
                    "t": ["i3-msg", "workspace", "5"],
                    "y": ["i3-msg", "move", "workspace", "1"],
                    "u": ["i3-msg", "move", "workspace", "2"],
                    "i": ["i3-msg", "move", "workspace", "3"],
                    "o": ["i3-msg", "move", "workspace", "4"],
                    "p": ["i3-msg", "move", "workspace", "5"],
                    ";": ["inc_bright"],
                    "'": ["dec_bright"],
                    "v": ["i3-sensible-terminal"],
                    "<enter>": ["qutebrowser"],
                    "<space>": ["start_term"]
                }, nothing),
            **self.generate_remap_pass_throughs(
                {
                    "h": "<a-h>",
                    "j": "<a-j>",
                    "k": "<a-k>",
                    "l": "<a-l>",
                    ";": "=",
                    "a": "<pageup>",
                    "s": "<pagedown>",
                    "d": "<c-u>",
                    "f": "<c-d>",
                    "z": "\\",
                    "x": "`",
                    "c": "|",
                    "n": "<left>",
                    "m": "<down>",
                    ",": "<up>",
                    ".": "<right>"
                }, nothing)
        }

        get_function_bindings = make_wrapper(function_bindings)
        get_sym_bindings = make_wrapper(sym_bindings)

        def base_switch_to_sym():
            self.remove_all_files()
            self.make_file("sym")
            debug_print(self.debug, "Switching to sym")

        def base_switch_to_function():
            self.remove_all_files()
            self.make_file("function")
            debug_print(self.debug, "Switching to function")

        def base_switch_to_sym_toggle():
            self.remove_all_files()
            self.make_file("sym_toggle")
            debug_print(self.debug, "Switching to sym toggle")

        time_no_tap = 0.2

        enter_function_escape_key = "<capslock>"

        function_escape = ModTap(self,
                                 enter_function_escape_key,
                                 "<esc>",
                                 get_function_bindings,
                                 standard_bindings,
                                 self.switch_to_base,
                                 base_switch_to_function,
                                 set(['<esc>']),
                                 Layer,
                                 time_no_tap,
                                 name="esc function layer")

        function_enter = ModTap(self,
                                "<enter>",
                                "<enter>",
                                get_function_bindings,
                                standard_bindings,
                                self.switch_to_base,
                                base_switch_to_function,
                                set(['<esc>']),
                                Layer,
                                time_no_tap,
                                name="enter function layer")

        sym_space = ModTap(self,
                           "<space>",
                           "<space>",
                           get_sym_bindings,
                           standard_bindings,
                           self.switch_to_base,
                           base_switch_to_sym,
                           set(),
                           Layer,
                           time_no_tap,
                           name="space sym layer")

        sym_space_toggle = ModToggle(
            self,
            "`",
            ["<shift_l>", "<shift_r>"],
            sym_bindings,
            {},
            standard_bindings,
            self.switch_to_base,
            base_switch_to_sym_toggle,
            set(),
            Layer,
            name="space sym layer",
        )

        ModMap = namedtuple(
            'ModMap', 'map_tap map_hold name extra_maps extra_modifiers')

        shift_to_shift = self.generate_remap_pass_throughs({
            '<shift_l>':
            '<shift_l>',
            '<shift_r>':
            '<shift_r>'
        })

        mod_maps = [
            ('<shift_l>',
             ModMap(map_tap='-',
                    map_hold='<shift_l>',
                    name='shift_l',
                    extra_maps=sym_space_toggle.parent_bindings,
                    extra_modifiers=sym_space_toggle.parent_modifiers)),
            ('<shift_r>',
             ModMap(map_tap='=',
                    map_hold='<shift_r>',
                    name='shift_r',
                    extra_maps=sym_space_toggle.parent_bindings,
                    extra_modifiers=sym_space_toggle.parent_modifiers)),
            ('<alt_l>',
             ModMap(map_tap='<tab>',
                    map_hold='<super>',
                    name='alt_l',
                    extra_maps=shift_to_shift,
                    extra_modifiers=set())),
            ('<alt_r>',
             ModMap(map_tap='<backspace>',
                    map_hold='<control_r>',
                    name='alt_r',
                    extra_maps=shift_to_shift,
                    extra_modifiers=set())),
            ('z',
             ModMap(map_tap='z',
                    map_hold='<alt_l>',
                    name='z_alt',
                    extra_maps={},
                    extra_modifiers=set())),
            ('/',
             ModMap(map_tap='/',
                    map_hold='<alt_r>',
                    name='slash_alt',
                    extra_maps={},
                    extra_modifiers=set())),
        ]

        mod_taps = []

        for key, mod_map in mod_maps:

            def base_switch_to_mod(mod_map=mod_map):
                files[mod_map.name] = \
                    os.path.join(path_keyboard_info,
                                 mod_map.name + "_activated")
                self.remove_all_files()
                self.make_file(mod_map.name)
                debug_print(self.debug, "Switching to ", mod_map.name)

            get_bindings = make_wrapper({
                **self.make_generate_remap_mod_press(mod_map.map_hold)(self_dict),
                **mod_map.extra_maps
            })

            mod_taps.append(
                ModTap(self,
                       key,
                       mod_map.map_tap,
                       get_bindings, {},
                       self.switch_to_base,
                       base_switch_to_mod,
                       mod_map.extra_modifiers,
                       Layer,
                       time_no_tap,
                       name=" ".join([key, mod_map.name, "layer"])))

        mod_parent_bindings = {}

        for mod_tap in mod_taps:
            mod_parent_bindings.update(mod_tap.parent_bindings)

        mod_modifiers = set()

        for mod_tap in mod_taps:
            mod_modifiers = mod_modifiers.union(mod_tap.parent_modifiers)

        full_bindings = {
            **standard_bindings,
            **function_escape.parent_bindings,
            **function_enter.parent_bindings
        }
        full_modifiers = function_escape.parent_modifiers.union(
            function_enter.parent_modifiers)

        full_bindings.update({
            **sym_space.parent_bindings,
            **mod_parent_bindings
        })
        full_modifiers = full_modifiers.union(
            sym_space.parent_modifiers).union(mod_modifiers)

        self.base_layer = Layer(bindings=full_bindings,
                                modifiers=full_modifiers)

        self.disable_keyboard_layer = Layer(bindings={
            ('<esc>', KeyEvent.key_up):
            nothing,
            ('<esc>', KeyEvent.key_down):
            self.switch_to_base,
            ('<esc>', KeyEvent.key_hold):
            nothing,
        },
                                            modifiers=set(['<esc>']),
                                            key_function=disable_key_function)

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
                    debug_print(self.debug, 'held key:', key, value)
                    held_layer = self.held_keys[key]
                    if value == KeyEvent.key_up:
                        debug_print(self.debug, "removing held")
                        self.remove_held_key(key)
                    if not is_disable:
                        if key_value in held_layer:
                            held_layer[key_value]()
                        else:
                            self.write(key, value, True)
                elif key_value in self.layer.bindings:
                    debug_print(self.debug, 'key:', key, value)
                    if value == KeyEvent.key_down and key not in self.layer.modifiers:
                        debug_print(self.debug, "added to hold")
                        self.held_keys[key] = self.layer.bindings
                    self.layer.bindings[key_value]()
                else:
                    debug_print(self.debug,
                                'key not found in current bindings')
                    if value == KeyEvent.key_down:
                        debug_print(self.debug, "added to hold")
                        self.held_keys[key] = self.layer.bindings
                    if not is_disable:
                        self.write(key, value, True)
            else:
                debug_print(self.debug, 'key not found in known characters')
                if not is_disable:
                    self.write_raw(code, value, True)

        return generic_key_function

    def key(self, code, value):
        self.layer.key_function(code, value)

    def remove_all_files(self):
        for f in files.values():
            with contextlib.suppress(FileNotFoundError):
                os.remove(f)

    def make_file(self, f_name):
        Path(files[f_name]).touch()

    def switch_to_disable(self):
        self.remove_all_files()
        self.make_file("keyboard_disabled")
        debug_print("Disabling keyboard")
        self.layer = self.disable_keyboard_layer

    def switch_to_base(self):
        self.remove_all_files()
        self.make_file("base")
        debug_print(self.debug, "Switching to base")
        self.layer = self.base_layer

    def i3_change_focus(self, direction):
        def change():
            try:
                window_id = check_output(['xdotool', 'getwindowfocus'
                                          ]).decode("utf-8").strip()
                debug_print(self.debug, "window_id for change focus:",
                            window_id)
                window_name = check_output(
                    ['xdotool', 'getwindowname',
                     window_id]).decode("utf-8").strip()
                debug_print("window_name for change focus:", window_name)
            except Exception as e:
                alert("XDOTOOL CHANGE FOCUS ERROR", str(e))
                return

            if (window_name.endswith(":nvim") or window_name == "nvim"
                    or window_name == "editor"):
                self.control_press("\\")
                self.control_press("n")
                self.press("g")
                self.press("z")
                self.press(direction, flush=True)
            else:
                if direction == "h":
                    full_direction_name = "left"
                elif direction == "j":
                    full_direction_name = "down"
                elif direction == "k":
                    full_direction_name = "up"
                elif direction == "l":
                    full_direction_name = "right"
                run_background(["i3-msg", "focus", full_direction_name])

        return change
