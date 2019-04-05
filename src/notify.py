import os
from subprocess import check_output
from time import sleep

from keyboard.layers import MyLayerHandler
from keyboard.utils import alert

if __name__ == "__main__":
    prev_capslock_on = False
    prev_sym_lock_on = False
    while(True):
        capslock_on = check_output("check_caps_on").decode(
            "utf-8").strip() == "on"
        sym_lock_on = os.path.isfile(MyLayerHandler.files["sym_toggle"])
        if capslock_on and not prev_capslock_on:
            alert("CAPS LOCK", time=1)
        if sym_lock_on and not prev_sym_lock_on:
            alert("SYM LOCK", time=1)
        prev_capslock_on = capslock_on
        prev_sym_lock_on = sym_lock_on
        sleep(0.02)
