from evdev import KeyEvent
from recordclass import recordclass

from keyboard.utils import nothing

class ModToggle():

    def __init__(self, handler, key, key_modifiers, bindings_toggle, 
                 bindings_modified, no_callback_remaps, switch_to_parent, 
                 base_switch_to_self, additional_modifiers, Layer, name="hold"):
        self.handler = handler
        self.key = key
        self.key_modifiers = key_modifiers
        self.switch_to_parent = switch_to_parent
        self.no_callback_remaps = no_callback_remaps
        self.bindings_toggle = bindings_toggle
        self.bindings_modified = bindings_modified
        self.base_switch_to_self = base_switch_to_self
        self.Layer = Layer
        self.name = name

        self.parent_bindings = {
            (self.key, KeyEvent.key_up): nothing,
            (self.key, KeyEvent.key_down): self.switch_to_self,
            (self.key, KeyEvent.key_hold): nothing
        }
        self.parent_modifiers = set([key])
        self.modifiers = set(key_modifiers).union(additional_modifiers)

        self.key_down_callables = {}

    def create_switch_to_self_modified(self, switch_key):
        def switch_to_self_modified():
            print("Switching to modified ", self.name, "using", self.key) \
                if self.handler.debug else None

            self.handler.layer = self.Layer(
                bindings={
                    **self.bindings_modified,
                    **self.no_callback_remaps,
                    (switch_key, KeyEvent.key_up): self.switch_to_self,
                    (switch_key, KeyEvent.key_down): 
                    lambda: print(self.name, 
                                  "MODIFIER WAS PRESSED NOT EXPECTED"), 
                    (switch_key, KeyEvent.key_hold): nothing,
                    (self.key, KeyEvent.key_down): self.switch_to_parent,
                    (self.key, KeyEvent.key_up): nothing,
                    (self.key, KeyEvent.key_hold): nothing
                },
                modifiers=set([switch_key, self.key])
            )
        return switch_to_self_modified

    def switch_to_self(self):
        self.base_switch_to_self()
        print("Switching to", self.name, "using", self.key) \
            if self.handler.debug else None
        mod_binding_sets = [{(mod, KeyEvent.key_up): nothing, 
                             (mod, KeyEvent.key_down): 
                             self.create_switch_to_self_modified(mod), 
                             (mod, KeyEvent.key_hold): nothing}
                              for mod in self.key_modifiers]
        mod_bindings = {}
        for mod_binding_set in mod_binding_sets:
            mod_bindings.update(mod_binding_set)

        self.handler.layer = self.Layer(
            bindings={
                **self.bindings_toggle,
                **self.no_callback_remaps,
                **mod_bindings
            },
            modifiers=self.modifiers
        )
