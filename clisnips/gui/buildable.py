from typing import Callable, Dict, Optional, Type, TypeVar, Any

from gi.repository import GObject, Gtk

from .._types import AnyPath

__all__ = ['Buildable']


def _register(cls, builder: Optional[Gtk.Builder], strict_callbacks: bool = False):
    bound_widgets: Dict[str, str] = {}
    bound_methods: Dict[str, str] = {}

    for attr, obj in list(cls.__dict__.items()):
        if isinstance(obj, _Child):
            widget_id = obj.widget_id or attr
            if widget_id in bound_widgets:
                raise RuntimeError(
                    f'Error exposing child {widget_id!r} as {attr!r}, '
                    f'already available as {bound_widgets[widget_id]!r}'
                )
            bound_widgets[widget_id] = attr
        elif isinstance(obj, _Callback):
            setattr(cls, attr, obj.callback)
            name = obj.name or attr
            if name in bound_methods:
                raise RuntimeError(
                    f'Error exposing handler {name!r} as {attr!r}, '
                    f'already available as {bound_methods[name]!r}'
                )
            bound_methods[name] = attr

    cls.__gtk_widgets__ = bound_widgets
    cls.__gtk_callbacks__ = bound_methods
    base_init = cls.__init__

    def instance_init(self, *args, **kwargs):
        _init_buildable(self, cls, builder, strict_callbacks, args, kwargs)
        base_init(self, *args, **kwargs)

    cls.__init__ = instance_init


def _init_buildable(self, cls, builder: Optional[Gtk.Builder], strict_callbacks: bool, args: tuple, kwargs: dict):
    if builder:
        # builder was passed via decorator, store it on the instance
        self._gtk_builder = builder
    else:
        # try to see if a builder was passed via constructor arguments
        builder = _require_builder_from_args(args, kwargs)
    if self.__class__ is not cls:
        raise TypeError('Cannot inherit from class decorated with @Buildable')

    for widget_id, attr in self.__gtk_widgets__.items():
        self.__dict__[attr] = builder.get_object(widget_id)

    builder.connect_signals_full(_builder_connect_callback, {
        'strict': strict_callbacks,
        'callbacks': {name: getattr(self, attr) for name, attr in cls.__gtk_callbacks__.items()}
    })


def _builder_connect_callback(
    builder: Gtk.Builder,
    gobj: GObject.GObject,
    signal_name: str,
    handler_name: str,
    connect_obj: GObject.GObject,
    flags: GObject.ConnectFlags,
    data: dict
):
    try:
        handler = data['callbacks'][handler_name]
    except KeyError:
        if data['strict']:
            raise AttributeError(f'Handler not found: {handler_name!s}')
        return
    args = ()  # TODO: args
    after = flags & GObject.ConnectFlags.AFTER
    if not connect_obj:
        connect = getattr(gobj, 'connect_after' if after else 'connect')
        connect(signal_name, handler, *args)
    else:
        connect = getattr(gobj, 'connect_object_after' if after else 'connect_object')
        connect(signal_name, handler, connect_obj, *args)


def _require_builder_from_args(args: tuple, kwargs: dict) -> Gtk.Builder:
    builders = [b for b in args if isinstance(b, Gtk.Builder)]
    if not builders:
        builders = [b for b in kwargs.values() if isinstance(b, Gtk.Builder)]
    if not builders:
        raise RuntimeError('No Gtk.Builder could be created')
    return builders[0]


class _Child:

    def __init__(self, widget_id: Optional[str] = None):
        self.widget_id: Optional[str] = widget_id


class _Callback:

    def __init__(self, callback: Callable, name: Optional[str]):
        self.callback = callback
        self.name = name


class _CallbackDecorator:

    def __init__(self, name: str = None):
        self.name: Optional[str] = name

    def __call__(self, callback: Callable) -> _Callback:
        return _Callback(callback, self.name)


_TBuildable = TypeVar('_TBuildable', bound='Buildable')
_T = TypeVar('_T')


class Buildable(object):

    Child: Any = _Child
    Callback = _CallbackDecorator

    @classmethod
    def from_file(cls: Type[_TBuildable], file_name: AnyPath) -> _TBuildable:
        return cls(file_name=file_name)

    @classmethod
    def from_string(cls: Type[_TBuildable], string: str) -> _TBuildable:
        return cls(xml=string)

    def __init__(self, xml: Optional[str] = None, file_name: Optional[AnyPath] = None, strict_callbacks: bool = False):
        self._xml: Optional[str] = xml
        self._file_name: Optional[AnyPath] = file_name
        self._strict_callbacks = strict_callbacks

    def __call__(self, cls: _T) -> _T:
        builder = None
        if self._xml:
            builder = Gtk.Builder()
            builder.add_from_string(self._xml)
        elif self._file_name:
            builder = Gtk.Builder()
            builder.add_from_file(str(self._file_name))
        _register(cls, builder, self._strict_callbacks)
        return cls
