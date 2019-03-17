from collections import defaultdict
from evdev import ecodes as e
from bidict import bidict

control_single = {"<c-q>": "q",
                  "<c-w>": "w",
                  "<c-e>": "e",
                  "<c-r>": "r",
                  "<c-t>": "t",
                  "<c-y>": "y",
                  "<c-u>": "u",
                  "<c-i>": "i",
                  "<c-o>": "o",
                  "<c-p>": "p",
                  "<c-a>": "a",
                  "<c-s>": "s",
                  "<c-d>": "d",
                  "<c-f>": "f",
                  "<c-g>": "g",
                  "<c-h>": "h",
                  "<c-j>": "j",
                  "<c-k>": "k",
                  "<c-l>": "l",
                  "<c-;>": ";",
                  "<c-z>": "z",
                  "<c-x>": "x",
                  "<c-c>": "c",
                  "<c-b>": "b",
                  "<c-v>": "v",
                  "<c-n>": "n",
                  "<c-m>": "m",
                  "<c-,>": ",",
                  "<c-.>": ".",
                  "<c-/>": "/",
                  "<c-1>": "1",
                  "<c-2>": "2",
                  "<c-3>": "3",
                  "<c-4>": "4",
                  "<c-5>": "5",
                  "<c-6>": "6",
                  "<c-7>": "7",
                  "<c-8>": "8",
                  "<c-9>": "9",
                  "<c-0>": "0",
                  "<c-`>": "`",
                  "<c-[>": "[",
                  "<c-]>": "]",
                  "<c-=>": "=",
                  "<c-\\>":"\\",
                  "<c-'>": "\'",
                  "<c-->": "-"}

upper_lower = {"Q": "q",
               "W": "w",
               "E": "e",
               "R": "r",
               "T": "t",
               "Y": "y",
               "U": "u",
               "I": "i",
               "O": "o",
               "P": "p",
               "A": "a",
               "S": "s",
               "D": "d",
               "F": "f",
               "G": "g",
               "H": "h",
               "J": "j",
               "K": "k",
               "L": "l",
               ":": ";",
               "Z": "z",
               "X": "x",
               "C": "c",
               "B": "b",
               "V": "v",
               "N": "n",
               "M": "m",
               "<": ",",
               ">": ".",
               "?": "/",
               "!": "1",
               "@": "2",
               "#": "3",
               "$": "4",
               "%": "5",
               "^": "6",
               "&": "7",
               "*": "8",
               "(": "9",
               ")": "0",
               "~": "`",
               "{": "[",
               "}": "]",
               "+": "=",
               "|":"\\",
               "\"": "\'",
               "_": "-"}

code_char_map = bidict({1: "<esc>",
                        2: "1",
                        3: "2",
                        4: "3",
                        5: "4",
                        6: "5",
                        7: "6",
                        8: "7",
                        9: "8",
                        10: "9",
                        11: "0",
                        12: "-",
                        13: "=",
                        14: "<backspace>",
                        15: "<tab>",
                        16: "q",
                        17: "w",
                        18: "e",
                        19: "r",
                        20: "t",
                        21: "y",
                        22: "u",
                        23: "i",
                        24: "o",
                        25: "p",
                        26: "[",
                        27: "]",
                        28: "<enter>",
                        29: "<control_l>",
                        30: "a",
                        31: "s",
                        32: "d",
                        33: "f",
                        34: "g",
                        35: "h",
                        36: "j",
                        37: "k",
                        38: "l",
                        39: ";",
                        40: "'",
                        41: "`",
                        42: "<shift_l>",
                        43: "\\",
                        44: "z",
                        45: "x",
                        46: "c",
                        47: "v",
                        48: "b",
                        49: "n",
                        50: "m",
                        51: ",",
                        52: ".",
                        53: "/",
                        54: "<shift_r>",
                        56: "<alt_l>",
                        57: "<space>",
                        58: "<capslock>",
                        97: "<control_r>",
                        100: "<alt_r>",
                        103: "<up>",
                        104: "<pageup>",
                        105: "<left>",
                        106: "<right>",
                        108: "<down>",
                        109: "<pagedown>",
                        125: "<super>"})
