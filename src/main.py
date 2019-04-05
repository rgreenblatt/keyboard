import os
import time
from distutils.util import strtobool
from signal import SIGKILL
from sys import argv, exit

from evdev import InputDevice
from evdev import ecodes as e
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from keyboard.constants import path_keyboard_info
from keyboard.layers import MyLayerHandler
from keyboard.utils import alert
from test_keyboards import get_keyboards

class KeyboardHandler(FileSystemEventHandler):

    path_input = '/dev/input/'

    def __init__(self, debug, parent_pid):
        self.pid_map = {}
        self.debug = debug
        self.last_update = 0
        self.parent_pid = parent_pid

    def on_created(self, event):
        if event.src_path == os.path.join(path_keyboard_info, 'kill'):
            for pid in self.pid_map.values():
                os.kill(pid, SIGKILL)
            alert("TURNING OFF MAPPINGS", time=3)
            os.kill(self.parent_pid, SIGKILL)
            exit()


    def on_any_event(self, event):
        if event.src_path.startswith(self.path_input):
            self.update()

    def update(self):
        if time.time() - self.last_update > 1:
            to_remove = []
            for key, pid in self.pid_map.items():
                found_pid, status = os.waitpid(pid, os.WNOHANG)
                if found_pid == pid:
                    to_remove.append(key)
            for remove in to_remove:
                del self.pid_map[remove]
            self.pid_map.update(self.fork_keyboards(filter(lambda x: x.path not in self.pid_map, 
                                                      get_keyboards())))
        self.last_update = time.time()

    def fork_keyboards(self, keyboards):
        pid_map = {}
        for keyboard in keyboards:
            pid = os.fork()
            if pid == 0:
                try:
                    handler = MyLayerHandler(self.debug)
                    dev = InputDevice(keyboard.path)
                    dev.grab()
                    for event in dev.read_loop():
                        if event.type == e.EV_KEY:
                            handler.key(event.code, event.value)
                except Exception as excep:
                    if type(excep) == OSError and excep.errno == 19:
                        print("Keyboard disconnected:", excep)
                        alert("Keyboard disconnected", "")
                    else:
                        print("Keyboard error:", excep)
                        alert("KEYBOARD ERROR", str(excep))
                finally:
                    exit()
            else:
                pid_map[keyboard.path] = pid
        return pid_map

if __name__ == '__main__':
    debug = len(argv) > 1 and bool(strtobool(argv[1]))
    
    alert("Keyboard is mapped", time=3)

    k_handler = KeyboardHandler(debug, os.getpid())
    k_handler.update()

    observer = Observer()
    observer.schedule(k_handler, KeyboardHandler.path_input, recursive=False)
    observer.schedule(k_handler, path_keyboard_info, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
