import time
from collections import OrderedDict

from evdev import KeyEvent
from recordclass import recordclass

from keyboard.utils import nothing
from keyboard.constants import code_char_map


class ModTap():

    ModKeyEvents = recordclass("ModKeyEvents",
                               "no_keypress_on_finish layer_exited")

    def __init__(self,
                 handler,
                 key,
                 map_tap,
                 get_layer_hold,
                 no_callback_remaps,
                 switch_to_parent,
                 base_switch_to_self,
                 additional_modifiers,
                 Layer,
                 time_no_tap,
                 name="hold"):
        self.key = key
        self.handler = handler
        self.map_tap = map_tap
        self.get_layer_hold = get_layer_hold
        self.no_callback_remaps = no_callback_remaps
        self.switch_to_parent = switch_to_parent
        self.base_switch_to_self = base_switch_to_self
        self.Layer = Layer
        self.time_no_tap = time_no_tap
        self.name = name

        self.parent_bindings = {
            (self.key, KeyEvent.key_up): nothing,
            (self.key, KeyEvent.key_down): self.switch_to_self,
            (self.key, KeyEvent.key_hold): nothing
        }

        self.parent_modifiers = set([key])
        self.modifiers = self.parent_modifiers.union(additional_modifiers)

        self.reset()

    def reset(self):
        self.key_not_held = True
        self.mod_key_events = ModTap.ModKeyEvents(no_keypress_on_finish=False,
                                                  layer_exited=False)
        self.currently_pressed_no_hold = OrderedDict()

    @staticmethod
    def send_buffered_keys(currently_pressed_no_hold):
        for call_capable in currently_pressed_no_hold.values():
            call_capable()
        currently_pressed_no_hold.clear()

    @staticmethod
    def send_buffered_keys_parent(currently_pressed_no_hold, handler):
        for key in currently_pressed_no_hold:
            handler.remove_held_key(key)
            handler.key(code_char_map.inverse[key], KeyEvent.key_down)
        currently_pressed_no_hold.clear()

    def mod_key_up(self):
        t_delta = time.time() - self.t_enter

        self.mod_key_events.no_keypress_on_finish |= t_delta > self.time_no_tap

        self.switch_to_parent()

        if self.mod_key_events.no_keypress_on_finish:
            ModTap.send_buffered_keys(self.currently_pressed_no_hold)
        else:
            self.handler.press(self.map_tap, flush=True)

            ModTap.send_buffered_keys_parent(self.currently_pressed_no_hold,
                                             self.handler)

        self.mod_key_events.layer_exited = True

        self.reset()

    def mod_key_hold(self):
        self.mod_key_events.no_keypress_on_finish = True
        ModTap.send_buffered_keys(self.currently_pressed_no_hold)

    def create_key_down(self, key, map_to_callable):
        def key_down(key=key,
                     currently_pressed_no_hold=self.currently_pressed_no_hold,
                     mod_key_events=self.mod_key_events,
                     t_enter=self.t_enter):
            t_delta = time.time() - t_enter

            mod_key_events.no_keypress_on_finish |= t_delta > self.time_no_tap

            if mod_key_events.no_keypress_on_finish:
                ModTap.send_buffered_keys(currently_pressed_no_hold)
                map_to_callable()
            else:
                currently_pressed_no_hold[key] = map_to_callable

        return key_down

    def create_key_up(self, key, map_to_callable):
        def key_up(key=key,
                   mod_key_events=self.mod_key_events,
                   currently_pressed_no_hold=self.currently_pressed_no_hold,
                   t_enter=self.t_enter):
            t_delta = time.time() - t_enter

            mod_key_events.no_keypress_on_finish |= t_delta > self.time_no_tap
            if mod_key_events.layer_exited and not \
                    mod_key_events.no_keypress_on_finish:
                self.handler.key(code_char_map.inverse[key], KeyEvent.key_up)
            else:
                mod_key_events.no_keypress_on_finish = True
                ModTap.send_buffered_keys(currently_pressed_no_hold)
                map_to_callable()

        return key_up

    def create_key_hold(self, key, map_to_callable):
        def key_hold(key=key,
                     mod_key_events=self.mod_key_events,
                     currently_pressed_no_hold=self.currently_pressed_no_hold,
                     t_enter=self.t_enter):
            t_delta = time.time() - t_enter

            mod_key_events.no_keypress_on_finish |= t_delta > self.time_no_tap

            if mod_key_events.layer_exited and not \
                    mod_key_events.no_keypress_on_finish:
                self.handler.key(code_char_map.inverse[key], KeyEvent.key_hold)
            else:
                ModTap.send_buffered_keys(currently_pressed_no_hold)
                map_to_callable()
                mod_key_events.no_keypress_on_finish = True

        return key_hold

    def switch_to_self(self):
        self.t_enter = time.time()
        # self.additional_mods_and_press = additional_mods_and_press
        self.base_switch_to_self()
        print("Switching to", self.name, "using", self.key) \
            if self.handler.debug else None
        self.handler.layer = self.Layer(bindings={
            **self.get_layer_hold(self.create_key_up, self.create_key_down, self.create_key_hold),
            **self.no_callback_remaps,
            (self.key, KeyEvent.key_up):
            self.mod_key_up,
            (self.key, KeyEvent.key_down):
            lambda: print(self.name, "MOD WAS PRESSED NOT EXPECTED"),
            (self.key, KeyEvent.key_hold):
            self.mod_key_hold,
        },
                                        modifiers=self.modifiers)
