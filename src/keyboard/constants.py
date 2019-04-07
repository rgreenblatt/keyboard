from collections import defaultdict

from bidict import bidict
from evdev import ecodes as e

path_keyboard_info = '/tmp/keyboard_info/'

standard_keys = ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p",  "a",  "s",
                 "d", "f", "g", "h", "j", "k", "l", ";", "z", "x",  "c",  "b",
                 "v", "n", "m", ",", ".", "/", "1", "2", "3", "4",  "5",  "6", 
                 "7", "8", "9", "0", "`", "[", "]", "+", "=", "\\", "\'", "-"] 

shift_maps = {"Q": "q", "W": "w", "E": "e",  "R": "r",   "T": "t", "Y": "y",
              "U": "u", "I": "i", "O": "o",  "P": "p",   "A": "a", "S": "s",
              "D": "d", "F": "f", "G": "g",  "H": "h",   "J": "j", "K": "k",
              "L": "l", ":": ";", "Z": "z",  "X": "x",   "C": "c", "B": "b",
              "V": "v", "N": "n", "M": "m",  "<": ",",   ">": ".", "?": "/",
              "!": "1", "@": "2", "#": "3",  "$": "4",   "%": "5", "^": "6",
              "&": "7", "*": "8", "(": "9",  ")": "0",   "~": "`", "{": "[",
              "}": "]", "+": "=", "|": "\\", "\"": "\'", "_": "-"}

def make_mod_map(mod_sym):
    return {"<{}-{}>".format(mod_sym, key): key for key in standard_keys}

control_maps = make_mod_map("c")
alt_maps = make_mod_map("a")
control_alt_maps = make_mod_map("c-a")

code_char_map = bidict({1:   "<esc>",
                        2:   "1",
                        3:   "2",
                        4:   "3",
                        5:   "4",
                        6:   "5",
                        7:   "6",
                        8:   "7",
                        9:   "8",
                        10:  "9",
                        11:  "0",
                        12:  "-",
                        13:  "=",
                        14:  "<backspace>",
                        15:  "<tab>",
                        16:  "q",
                        17:  "w",
                        18:  "e",
                        19:  "r",
                        20:  "t",
                        21:  "y",
                        22:  "u",
                        23:  "i",
                        24:  "o",
                        25:  "p",
                        26:  "[",
                        27:  "]",
                        28:  "<enter>",
                        29:  "<control_l>",
                        30:  "a",
                        31:  "s",
                        32:  "d",
                        33:  "f",
                        34:  "g",
                        35:  "h",
                        36:  "j",
                        37:  "k",
                        38:  "l",
                        39:  ";",
                        40:  "'",
                        41:  "`",
                        42:  "<shift_l>",
                        43:  "\\",
                        44:  "z",
                        45:  "x",
                        46:  "c",
                        47:  "v",
                        48:  "b",
                        49:  "n",
                        50:  "m",
                        51:  ",",
                        52:  ".",
                        53:  "/",
                        54:  "<shift_r>",
                        56:  "<alt_l>",
                        57:  "<space>",
                        58:  "<capslock>",
                        97:  "<control_r>",
                        98:  "<altgr>",
                        100: "<alt_r>",
                        103: "<up>",
                        104: "<pageup>",
                        105: "<left>",
                        106: "<right>",
                        108: "<down>",
                        109: "<pagedown>",
                        125: "<super>"})
