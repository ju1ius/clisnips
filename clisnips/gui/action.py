from typing import Callable, Optional

from gi.repository import GLib, Gio


def add_action(
    obj: Gio.ActionMap,
    name: str,
    callback: Callable,
    param_type: Optional[GLib.VariantType] = None
) -> Gio.SimpleAction:
    action = Gio.SimpleAction.new(name, param_type)
    action.connect('activate', callback)
    obj.add_action(action)
    return action


def add_stateful_action(
    obj: Gio.ActionMap,
    name: str,
    callback: Callable,
    param_type: Optional[GLib.VariantType] = None,
    state: Optional[GLib.Variant] = None
) -> Gio.SimpleAction:
    action = Gio.SimpleAction.new_stateful(name, param_type, state)
    action.connect('activate', callback)
    obj.add_action(action)
    return action
