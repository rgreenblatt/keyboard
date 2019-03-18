# keyboard

This is a project aimed at doing arbitrary keyboard remapping using python-evdev. This python library uses
linux kernel specific features, so it won't work on any other os. I am using it for doing qmk style
remappings (layers, multi function keys, double tap etc.). This allow for thing such as application
aware keybinding (I am using this for vim window/i3 window navigation) and notifications for layer toggles.
The code is currently pretty messy and is specific to my exact layout, but it should be easy to modify.

