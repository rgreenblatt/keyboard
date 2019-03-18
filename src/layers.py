from utils import (generate_remap_pass_throughs, generate_remap_system_command, generate_remap_string,
                   generate_remap_python_callable, nothing, press, control_press, run_background,
                   alert)
from constants import code_char_map, debug
from evdev import KeyEvent
from collections import defaultdict
from pathlib import Path
import os
import contextlib
from subprocess import Popen, check_output

def i3_change_focus(direction):
    def change():
        try:
            window_id = check_output(['xdotool', 'getwindowfocus']).decode("utf-8").strip()
            print("window_id for change focus:", window_id) if debug else None
            window_name = check_output(['xdotool', 'getwindowname', window_id]).decode("utf-8").strip()
            print("window_name for change focus:", window_name) if debug else None 
        except Exception as e:
            print("xdotool change focus command error:", e)
            alert("XDOTOOL CHANGE FOCUS ERROR", str(e))
            return

        if window_name == "nvim":
            control_press("\\")
            control_press("n")
            press("g")
            press("z")
            press(direction, flush=True)
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

files = {"sym": "/tmp/sym_activated", "sym_single": "/tmp/sym_single", "base": "/tmp/base_activated",
         "sym_toggle": "/tmp/sym_toggle", "function": "/tmp/function_activated"}

def remove_all_files():
    for f in files.values():
        with contextlib.suppress(FileNotFoundError):
            os.remove(f)

def make_file(f):
    Path(f).touch()

modifier_keys = base_modifier_keys = set(["<alt_l>", "<alt_r>", "<capslock>", "<enter>"])

def switch_to_sym():
    remove_all_files()
    make_file(files["sym"])
    print("Switching to sym") if debug else None
    return sym_layer, set(["<alt_l>", "<alt_r>"])

def switch_to_sym_single():
    remove_all_files()
    make_file(files["sym_single"])
    print("Switching to single") if debug else None
    return sym_layer_single, None

def switch_to_sym_key_pressed():
    remove_all_files()
    make_file(files["sym"])
    print("Switching to pressed") if debug else None
    return sym_layer_key_pressed, None

def switch_to_base():
    remove_all_files()
    make_file(files["base"])
    print("Switching to base") if debug else None
    return base_layer, base_modifier_keys

def switch_to_sym_toggle():
    remove_all_files()
    make_file(files["sym_toggle"])
    print("Switching to toggle") if debug else None
    return sym_layer_toggle, set(["<alt_l>", "<alt_r>", "<shift_l>", "<shift_r>"])

def switch_to_sym_toggle_shift():
    print("Switching to toggle shift") if debug else None
    return sym_layer_toggle_shift, None

def switch_to_function_maker(key, map_to):
    def switch_to_function():
        remove_all_files()
        make_file(files["function"])
        print("Switching to function using", key) if debug else None
        modifier_keys.intersection(set([key]))
        return {(key, KeyEvent.key_up): lambda : (press(map_to, flush=True), switch_to_base())[1],
                (key, KeyEvent.key_down): lambda: print("FUNCTION MOD WAS PRESSED NOT EXPECTED"),
                (key, KeyEvent.key_hold): nothing,
                **get_function_remaps(switch_to_function_maker_key_pressed(key)),
                **standard_remaps}, set([key])
    return switch_to_function

def switch_to_function_maker_key_pressed(key):
    def switch_to_function():
        remove_all_files()
        make_file(files["function"])
        print("Switching to function pressed using", key) if debug else None
        return {(key, KeyEvent.key_up): switch_to_base,
                (key, KeyEvent.key_down): lambda: print("FUNCTION MOD WAS PRESSED NOT EXPECTED"),
                (key, KeyEvent.key_hold): nothing,
                **get_function_remaps(nothing),
                **standard_remaps}, None
    return switch_to_function


def get_function_remaps(callback):
    return {**generate_remap_system_command({"q": ["i3-msg", "workspace", "1"],
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
            **generate_remap_python_callable({"h": i3_change_focus("h"), "j": i3_change_focus("j"),
                                              "k": i3_change_focus("k"), "l": i3_change_focus("l")},
                                             callback),
            **generate_remap_pass_throughs({"a": "<pageup>", "s": "<pagedown>", "d": "<c-u>", "f": "<c-d>",
                                            "n": "<left>", "m": "<down>", ",": "<up>", ".": "<right>"},
                                           callback)}

standard_remaps = {**generate_remap_pass_throughs({"[": "<backspace>"}), 
                   **generate_remap_pass_throughs({"<backspace>": "<capslock>"})}

capslock_remap = generate_remap_pass_throughs({"<capslock>": "<esc>"})

base_layer = {("<alt_l>", KeyEvent.key_up): nothing,
              ("<alt_l>", KeyEvent.key_down): switch_to_sym,
              ("<alt_l>", KeyEvent.key_hold): nothing,
              ("<alt_r>", KeyEvent.key_up): nothing,
              ("<alt_r>", KeyEvent.key_down): switch_to_sym,
              ("<alt_r>", KeyEvent.key_hold): nothing,
              ("<capslock>", KeyEvent.key_up): lambda: print("FUNCTION MOD WAS RELEASED NOT EXPECTED"),
              ("<capslock>", KeyEvent.key_down): switch_to_function_maker("<capslock>", "<esc>"),
              ("<capslock>", KeyEvent.key_hold): lambda: print("FUNCTION MOD WAS RELEASED NOT EXPECTED"),
              ("<enter>", KeyEvent.key_up): lambda: print("FUNCTION MOD WAS RELEASED NOT EXPECTED"),
              ("<enter>", KeyEvent.key_down): switch_to_function_maker("<enter>", "<enter>"),
              ("<enter>", KeyEvent.key_hold): lambda: print("FUNCTION MOD WAS RELEASED NOT EXPECTED"),
              **standard_remaps}

def get_sym_remaps(callback):
    return generate_remap_pass_throughs({"q": "1", "w": "2", "e": "3", "r": "4", "t": "5", "y": "6",
                                         "u": "7", "i": "8", "o": "9", "p": "0", "a": "!", "s": "@",
                                         "d": "#", "f": "$", "g": "%", "h": "^", "j": "&", "k": "*",
                                         "l": "(", ";": ")", "'": "|", "z": "~", "x": "_", "c": "-",
                                         "v": "+", "b": "=", "n": "\\", "m": "[", ",": "]", ".": "{",
                                         "/": "}", "<control_r>": "`", "<control_l>": "`"}, callback)


sym_layer = {("<alt_l>", KeyEvent.key_up): switch_to_sym_single,
             ("<alt_l>", KeyEvent.key_down): lambda: print("MOD WAS PRESSED NOT EXPECTED"),
             ("<alt_l>", KeyEvent.key_hold): nothing,
             ("<alt_r>", KeyEvent.key_up): switch_to_sym_single,
             ("<alt_r>", KeyEvent.key_down): lambda: print("MOD WAS PRESSED NOT EXPECTED"),
             ("<alt_r>", KeyEvent.key_hold): nothing,
             **get_sym_remaps(switch_to_sym_key_pressed),
             **standard_remaps,
             **capslock_remap}

sym_layer_single = {("<alt_l>", KeyEvent.key_up): lambda: print("MOD WAS RELEASED NOT EXPECTED"),
                    ("<alt_l>", KeyEvent.key_down): switch_to_sym_toggle,
                    ("<alt_l>", KeyEvent.key_hold): nothing,
                    ("<alt_r>", KeyEvent.key_up): lambda: print("MOD WAS RELEASED NOT EXPECTED"),
                    ("<alt_r>", KeyEvent.key_down): switch_to_sym_toggle,
                    ("<alt_r>", KeyEvent.key_hold): nothing,
                    **get_sym_remaps(switch_to_base),
                    **standard_remaps,
                    **capslock_remap}


sym_layer_key_pressed = {("<alt_l>", KeyEvent.key_up): switch_to_base,
                         ("<alt_l>", KeyEvent.key_down): lambda: print("MOD WAS PRESSED NOT EXPECTED"),
                         ("<alt_l>", KeyEvent.key_hold): nothing,
                         ("<alt_r>", KeyEvent.key_up): switch_to_base,
                         ("<alt_r>", KeyEvent.key_down): lambda: print("MOD WAS PRESSED NOT EXPECTED"),
                         ("<alt_r>", KeyEvent.key_hold): nothing,
                         **get_sym_remaps(nothing),
                         **standard_remaps,
                         **capslock_remap}

sym_layer_toggle = {("<alt_l>", KeyEvent.key_up): nothing,
                    ("<alt_l>", KeyEvent.key_down): switch_to_base,
                    ("<alt_l>", KeyEvent.key_hold): nothing,
                    ("<alt_r>", KeyEvent.key_up): nothing,
                    ("<alt_r>", KeyEvent.key_down): switch_to_base,
                    ("<alt_r>", KeyEvent.key_hold): nothing,
                    ("<shift_l>", KeyEvent.key_up): nothing,
                    ("<shift_l>", KeyEvent.key_down): switch_to_sym_toggle_shift,
                    ("<shift_l>", KeyEvent.key_hold): nothing,
                    ("<shift_r>", KeyEvent.key_up): nothing,
                    ("<shift_r>", KeyEvent.key_down): switch_to_sym_toggle_shift,
                    ("<shift_r>", KeyEvent.key_hold): nothing,
                    **get_sym_remaps(nothing),
                    **standard_remaps,
                    **capslock_remap}


sym_layer_toggle_shift = {("<alt_l>", KeyEvent.key_up): nothing,
                          ("<alt_l>", KeyEvent.key_down): switch_to_base,
                          ("<alt_l>", KeyEvent.key_hold): nothing,
                          ("<alt_r>", KeyEvent.key_up): nothing,
                          ("<alt_r>", KeyEvent.key_down): switch_to_base,
                          ("<alt_r>", KeyEvent.key_hold): nothing,
                          ("<shift_l>", KeyEvent.key_up): switch_to_sym_toggle,
                          ("<shift_l>", KeyEvent.key_down): lambda: print("SHIFT WAS PRESSED NOT EXPECTED"),
                          ("<shift_l>", KeyEvent.key_hold): nothing,
                          ("<shift_r>", KeyEvent.key_up): switch_to_sym_toggle,
                          ("<shift_r>", KeyEvent.key_down): lambda: print("SHIFT WAS PRESSED NOT EXPECTED"),
                          ("<shift_r>", KeyEvent.key_hold): nothing,
                          **standard_remaps,
                          **capslock_remap}


current_layer = base_layer
