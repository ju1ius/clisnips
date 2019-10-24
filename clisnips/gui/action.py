from typing import Optional

from gi.repository import Gio, GLib


def add_action(
    obj: Gio.ActionMap,
    name: str,
    callback: callable,
    param_type: Optional[GLib.VariantType] = None
) -> Gio.SimpleAction:
    action = Gio.SimpleAction.new(name, param_type)
    action.connect('activate', callback)
    obj.add_action(action)
    return action


def add_stateful_action(
    obj: Gio.ActionMap,
    name: str,
    callback: callable,
    param_type: Optional[GLib.VariantType] = None,
    state: Optional[GLib.Variant] = None
) -> Gio.SimpleAction:
    action = Gio.SimpleAction.new_stateful(name, param_type, state)
    action.connect('activate', callback)
    obj.add_action(action)
    return action
